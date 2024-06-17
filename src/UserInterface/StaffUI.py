# Copyright 2024 IAV GmbH
#
# This file is part of the IAV-Distortion project an interactive
# and educational showcase designed to demonstrate the need
# of automotive cybersecurity in a playful, engaging manner.
# and is released under the "Apache 2.0". Please see the LICENSE
# file that should have been included as part of this package.
#

from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from flask_socketio import SocketIO
import re
import secrets
from typing import Any, Dict, Tuple, List
import logging
import subprocess
import platform
from CyberSecurityManager.CyberSecurityManager import CyberSecurityManager
from EnvironmentManagement.EnvironmentManager import EnvironmentManager


class StaffUI:
    """
    Provides the staff userinterface

    Parameters
    ----------
    cybersecurity_mng: CyberSecurityManager
        Provides access to information about current hacking scenarios and their control.
    socketio: SocketIO
        Flask extension to enable websocket connection.
    environment_mng: EnvironmentManager
        Access to the EnvironmentManager to exchange information about queues and add or remove players and vehicles.
    password: str
        Configured password to log in to the staff ui.
    """

    def __init__(self, cybersecurity_mng, socketio, environment_mng, password: str):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        console_handler = logging.StreamHandler()
        self.logger.addHandler(console_handler)

        self.cybersecurity_mng: CyberSecurityManager = cybersecurity_mng

        self.password = password
        self.admin_token = secrets.token_urlsafe(12)
        self.staffUI_blueprint: Blueprint = Blueprint(name='staffUI_bp', import_name='staffUI_bp')
        self.scenarios: List[dict] = cybersecurity_mng.get_all_hacking_scenarios()
        self.socketio: SocketIO = socketio
        self.environment_mng: EnvironmentManager = environment_mng
        self.devices: list = []

        self.environment_mng.set_staff_ui_update_callback(self.publish_new_data)
        self.environment_mng.set_publish_removed_player_callback(self.publish_removed_player)
        self.environment_mng.set_publish_player_active_callback(self.publish_player_active)

        def is_authenticated() -> bool:
            """
            Check if client has been authenticated for the staff ui.

            Returns
            -------
            bool
                Status of authentication
            """
            request_token = request.cookies.get('admin_token')
            return request_token is not None and request_token == self.admin_token

        def login_redirect() -> Any:
            """
            Redirect client to the login page.

            Returns
            -------
            Response
                Returns a Response object representing a redirect to the login page.
            """
            return redirect(url_for("staffUI_bp.login_site"))

        def home_staff_control() -> Any:
            """
            Load the default page of the staff ui.

            Redirect the client to the login page if client is not authenticated. Gets information about hacking
            scenarios from CyberSecurityManager as well as the list of controlled cars from the EnvironmentManager to
            provide these to the staff ui.

            Returns
            -------
                Returns a Response object representing a redirect to the default staff ui page.
            """
            if not is_authenticated():
                self.logger.warning("Not authenticated")
                return login_redirect()
            names, descriptions = self.sort_scenarios()
            active_scenarios = cybersecurity_mng.get_active_hacking_scenarios()  # {'UUID': 'scenarioID'}
            # TODO: Show selection of choose hacking scenarios always sorted by player number
            return render_template('staff_control.html', activeScenarios=active_scenarios,
                                   uuids=environment_mng.get_controlled_cars_list(), names=names,
                                   descriptions=descriptions)

        self.staffUI_blueprint.add_url_rule('/staff_control', 'staff_control', view_func=home_staff_control)

        def set_scenario() -> Any:
            """
            Set the hacking scenario of a controlled car.

            Redirect the client to the login page if client is not authenticated. Set the scenario for the requested car
            using the CyberSecurityManager.

            Returns
            -------
            Response
                Returns a Response object representing a redirect to the default staff ui page.
            """
            if not is_authenticated():
                self.logger.warning("Not authenticated")
                return login_redirect()
            selected_option = request.form.get('option')
            pattern = r"scenarioID_(\d+)-UUID_([A-Fa-f0-9:]+|Virtual Vehicle [0-9]+)>"
            match = re.search(pattern, selected_option)

            scenario_id = match.group(1)
            uuid = match.group(2)
            cybersecurity_mng.activate_hacking_scenario_for_vehicle(uuid, scenario_id)

            return redirect(url_for('staffUI_bp.staff_control'))

        def login_site() -> Any:
            """
            Load the login page.

            Redirect to default staff ui page if already authenticated. Check entered password.

            Returns
            -------
            Response
                Returns a Response object representing a redirect to the default staff ui page or back to login
                according to authentication status.
            """
            if is_authenticated():
                self.logger.info("Authenticated")
                return redirect(url_for('staffUI_bp.staff_control'))
            if request.method == 'GET':
                return render_template('staff_login.html')
            # a password was submitted via POST
            pwd = request.form.get('password')
            if pwd is not None and pwd == self.password:
                response = redirect(url_for('staffUI_bp.staff_control'))
                response.set_cookie('admin_token', self.admin_token)
                return response
            return render_template('staff_login.html', wrong_password=True)

        self.staffUI_blueprint.add_url_rule('/hacking_scenario', methods=['POST'], view_func=set_scenario)
        self.staffUI_blueprint.add_url_rule('/', methods=['GET', 'POST'], view_func=login_site)

        # We can't directly redirect via SocketIO so we just drop the requests
        # TODO: Log dropped events!

        @self.socketio.on('get_uuids')
        def update_uuids_staff_ui() -> None:
            """
            Handles the 'get_uuids' websocket event.

            This function checks if the client is authenticated. If not, it logs a warning and returns early. If the
            client is authenticated, requests update from EnvironmentManager.
            """
            if not is_authenticated():
                self.logger.warning("Not authenticated")
                return
            self.environment_mng.update_staff_ui()
            return

        @self.socketio.on('connect')
        def initiate_uuids() -> None:
            """
            Handles the 'connect' websocket event.

            This function checks if the client is authenticated. If not, it logs a warning and returns early. If the
            client is authenticated, it logs an info and requests an update from the EnvironmentManager.
            """
            if not is_authenticated():
                self.logger.warning("Not authenticated")
                return
            self.logger.debug("Client connected")
            self.environment_mng.update_staff_ui()
            return

        @self.socketio.on('search_cars')
        def search_cars() -> None:
            """
            Handles the 'search_cars' websocket event.

            This function checks if the client is authenticated. If not, it logs a warning and returns early. If the
            client is authenticated, it calls the function to search for unpaired Anki cars from the EnvironmentManager.
            Publishes the list of found cars via websocket. Logs the search and its result as an info.
            """
            if not is_authenticated():
                self.logger.warning("Not authenticated")
                return
            self.logger.info("Searching devices...")
            print("Searching devices")
            new_devices = environment_mng.find_unpaired_anki_cars()
            self.logger.info(f'Found devices: {new_devices}')
            self.socketio.emit('new_devices', new_devices)
            return

        @self.socketio.on('add_device')
        def handle_add_device(device: str) -> None:
            """
            Handles the 'add_device' websocket event.

            This function checks if the client is authenticated. If not, it logs a warning and returns early. If the
            client is authenticated, it calls the function to add a car from the EnvironmentManager providing the
            devices id, logs a debug for the added device and initiates the hacking scenario in the
            CyberSecurityManager.

            Parameters
            ----------
            device: str
                Id of the device to be added.
            """
            if not is_authenticated():
                self.logger.warning("Not authenticated")
                return
            environment_mng.add_vehicle(device)
            self.logger.debug("Device added %s", device)
            # TODO: exception if device is no longer available
            self.cybersecurity_mng._update_active_hacking_scenarios(device, '0')
            return

        @self.socketio.on('add_virtual_vehicle')
        def handle_add_virtual_vehicle() -> None:
            """
            Handles the 'add_virtual_vehicle' websocket event.

            This function checks if the client is authenticated. If not, it logs a warning and returns early. If the
            client is authenticated, it calls the function to add a virtual vehicle from the EnvironmentManager,
            initiate its hacking scenario and send the 'added_device' event.
            """
            if not is_authenticated():
                self.logger.warning("Not authenticated")
                return
            name = environment_mng.add_virtual_vehicle()
            self.socketio.emit('device_added', name)
            self.cybersecurity_mng._update_active_hacking_scenarios(name, '0')
            return

        @self.socketio.on('delete_player')
        def handle_delete_player(player: str) -> None:
            """
            Handles the 'delete_player' websocket event.

            This function checks if the client is authenticated. If not, it logs a warning and returns early. If the
            client is authenticated, it logs a debug for the removed player and calls the EnvironmentManager to remove
            the player from the vehicle as well as from the player queue.

            Parameters
            ----------
            player: str
                ID of the player to be removed.
            """
            if not is_authenticated():
                self.logger.warning("Not authenticated")
                return
            print(f'delete player {player}')
            environment_mng.remove_player_from_vehicle(player)
            environment_mng.remove_player_from_waitlist(player)
            self.logger.debug("Player deleted %s", player)
            return

        @self.socketio.on('delete_vehicle')
        def handle_delete_vehicle(vehicle_id: str) -> None:
            """
            Handles the 'delete_vehicle' websocket event.

            This function checks if the client is authenticated. If not, it logs a warning and returns early. If the
            client is authenticated, it logs a debug for the removed vehicle and calls the EnvironmentManager to remove
            the vehicle from the game.

            Parameters
            ----------
            vehicle_id: str
                ID of the vehicle to be removed.
            """
            if not is_authenticated():
                self.logger.warning("Not authenticated")
                return
            environment_mng.remove_vehicle(vehicle_id)
            self.logger.debug("Vehicle deleted %s", vehicle_id)
            return

        @self.socketio.on('get_update_hacking_scenarios')
        def update_hacking_scenarios() -> None:
            """
            Handles the 'get_update_hacking_scenarios' websocket event.

            This function checks if the client is authenticated. If not, it logs a warning and returns early. If the
            client is authenticated, it gets sorted lists of hacking scenarios and their description as well as the
            active scenario of each car. Logs an info and sends the information about the scenarios via the
            'update_hacking_scenarios' event.
            """
            if not is_authenticated():
                self.logger.warning("Not authenticated")
                return
            names, descriptions = self.sort_scenarios()
            active_scenarios = cybersecurity_mng.get_active_hacking_scenarios()
            data = {'activeScenarios': active_scenarios, 'uuids': self.environment_mng.get_controlled_cars_list(),
                    'names': names, 'descriptions': descriptions}
            self.logger.info("Updated hacking scenarios")
            self.socketio.emit('update_hacking_scenarios', data)
            return

        @self.staffUI_blueprint.route('/configuration/home')
        def config_home() -> Any:
            """
            Load configuration page.

            If client is not authenticated, client is redirected to the login page.

            Returns
            -------
            Response
                Returns a Response object representing the configuration page or a redirect to the login page, if not
                authenticated.
            """
            if not is_authenticated():
                self.logger.warning("Not authenticated")
                return login_redirect()
            return render_template('staff_config_home.html')

        @self.staffUI_blueprint.route('/configuration/config_update')
        def config_update() -> Any:
            """
            Load configuration page for SW-update.

            If client is not authenticated, client is redirected to the login page.

            Returns
            -------
            Response
                Returns a Response object representing the update page or a redirect to the login page, if not
                authenticated.
            """
            if not is_authenticated():
                self.logger.warning("Not authenticated")
                return login_redirect()
            return render_template('staff_config_update.html')

        @self.staffUI_blueprint.route('/configuration/config_system_control')
        def config_system_control() -> Any:
            """
            Load configuration page for system control.

            If client is not authenticated, client is redirected to the login page.

            Returns
            -------
            Response
                Returns a Response object representing the system control page or a redirect to the login page, if not
                authenticated.
            """
            if not is_authenticated():
                self.logger.warning("Not authenticated")
                return login_redirect()
            return render_template('staff_config_system_control.html')

        @self.staffUI_blueprint.route('/update_program', methods=['POST'])
        def update_application() -> Any:
            """
            Handles post request send by 'update' button.

            If client is not authenticated, client is redirected to the login page. If operating system is 'Linux' the
            'update' utility script is called. Otherwise, a warning is logged.

            Returns
            -------
            Response or Tuple
                If not authenticated, returns a Response object representing a redirect to the login page.
                If authenticated, Returns a Tuple[str, int] with the status about the request.
            """
            if not is_authenticated():
                self.logger.warning("Not authenticated")
                return jsonify({'redirect': url_for('staffUI_bp.staff_control')})

            if platform.system() == 'Linux':
                self.logger.info("Update triggered")
                subprocess.call('../update.sh')
                message = 'Update started. This will take a few moments. The system will restart afterwards.'
                return message, 200
            else:
                self.logger.warning("Update button pressed, but not running on Linux system")
                message = 'Error starting the update. Function only available on linux systems.'
                return message, 200

        @self.staffUI_blueprint.route('/restart_program', methods=['POST'])
        def restart_program() -> Any:
            """"
            Handles the post request send by the 'restart program' button.

            If client is not authenticated, client is redirected to the login page. If operating system is 'Linux' the
            'restart_IAV-Distortion' utility script is called. Otherwise, a warning is logged.

            Returns
            -------
            Response or Tuple
                If not authenticated, returns a Response object representing a redirect to the login page.
                If authenticated, Returns a Tuple[str, int] with the status about the request.
            """
            if not is_authenticated():
                self.logger.warning("Not authenticated")
                return jsonify({'redirect': url_for('staffUI_bp.staff_control')})

            if platform.system() == 'Linux':
                self.logger.info("Program restart triggered")
                subprocess.call('./restart_IAV-Distortion.sh')
                message = "The program will restart now. This will take a moment please wait and reload the page."
                return message, 200
            else:
                self.logger.warning("Program restart button pressed, but not running on Linux system")
                message = 'Error restarting IAV-Distortion. Function only available on linux systems.'
                return message, 200

        @self.staffUI_blueprint.route('/restart_system', methods=['POST'])
        def restart_system() -> Any:
            """"
            Handles the post request send by the 'restart system' button.

            If client is not authenticated, client is redirected to the login page. If operating system is 'Linux' the
            'restart_system' utility script is called. Otherwise, a warning is logged.

            Returns
            -------
            Response or Tuple
                If not authenticated, returns a Response object representing a redirect to the login page.
                If authenticated, Returns a Tuple[str, int] with the status about the request.
            """
            if not is_authenticated():
                self.logger.warning("Not authenticated")
                return jsonify({'redirect': url_for('staffUI_bp.staff_control')})

            if platform.system() == 'Linux':
                self.logger.info("System restart triggered")
                subprocess.call('./restart_system.sh')
                message = "The system will restart now. This will take a moment. Please wait and reload the page " \
                          "after the system rebooted"
                return message, 200
            else:
                self.logger.warning("System restart button pressed, but not running on Linux system")
                message = 'Error restarting the system. Function only available on linux systems.'
                return message, 200

        @self.staffUI_blueprint.route('/shutdown_system', methods=['POST'])
        def shutdown_system() -> Any:
            """"
            Handles the post request send by the 'shutdown sytem' button.

            If client is not authenticated, client is redirected to the login page. If operating system is 'Linux' the
            'shutdown_system' utility script is called. Otherwise, a warning is logged.

            Returns
            -------
            Response or Tuple
                If not authenticated, returns a Response object representing a redirect to the login page.
                If authenticated, Returns a Tuple[str, int] with the status about the request.
            """
            if not is_authenticated():
                self.logger.warning("Not authenticated")
                return jsonify({'redirect': url_for('staffUI_bp.staff_control')})

            if platform.system() == 'Linux':
                self.logger.info("System shutdown triggered")
                subprocess.call('./shutdown_system.sh')
                message = 'The system will be shut down now.'
                return message, 200
            else:
                self.logger.warning("System shutdown button pressed, but not running on Linux system")
                message = 'Error shutting down the system. Function only available on linux systems.'
                return message, 200

    def get_blueprint(self) -> Blueprint:
        """
        Get the Blueprint object associated with the instance.

        Returns
        -------
        Blueprint
            The Blueprint object associated with the instance.
        """
        return self.staffUI_blueprint

    def sort_scenarios(self) -> Tuple[dict, dict]:
        """
        Sort hacking scenario names and descriptions according to their id.

        Returns
        -------
        scenario_names: dict
            Dictionary of hacking scenario names according to the scenario IDs {'scenario_id': 'scenario_name'}
        scenario_descriptions: dict
            Dictionary of hacking scenario descriptions according to the scenario IDs
            {'scenario_id': 'scenario_description'}
        """
        scenario_names = {}
        scenario_descriptions = {}
        for scenario in self.scenarios:
            scenario_names.update({scenario['id']: scenario['name']})
            scenario_descriptions.update({scenario['id']: scenario['description']})
        return scenario_names, scenario_descriptions

    def publish_new_data(self, car_map, car_queue, player_queue) -> None:
        """
        Publish relevant data via 'update_uuids' websocket event.

        Gathers information about the cars associated with players, free cars and the player queue and publish them via
        websocket.

        Parameters
        ----------
        car_map: dict
            Player ID's assigned to vehicle ID's they are assigned to.
        car_queue: list
            Contains ID's of available and not by a player controlled vehicles.
        player_queue: list
            Contains ID's of players waiting in the queue.
        """
        self.socketio.emit('update_uuids', {"car_map": car_map, "car_queue": car_queue, "player_queue": player_queue})
        return

    def publish_removed_player(self, player: str) -> None:
        """
        Sends 'player_removed' event.

        Parameters
        ----------
        player: str
            ID of the player which has been removed.
        """
        self.socketio.emit('player_removed', player)
        return

    def publish_player_active(self, player: str) -> None:
        """
        Sends 'player_active' event.

        Parameters
        ----------
        player: str
            ID of the player, who switched from the queue to be an active player.
        """
        self.socketio.emit('player_active', player)
        return
