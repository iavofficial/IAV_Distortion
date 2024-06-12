# Copyright 2024 IAV GmbH
#
# This file is part of the IAV-Distortion project an interactive
# and educational showcase designed to demonstrate the need
# of automotive cybersecurity in a playful, engaging manner.
# and is released under the "Apache 2.0". Please see the LICENSE
# file that should have been included as part of this package.
#

from flask import Blueprint, render_template, request, redirect, url_for
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

        self.environment_mng.set_staff_ui(self)

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
            pattern = r"scenarioID_(\d+)-UUID_([A-Fa-f0-9:]+)>"
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
            client is authenticated, it publishes new data using the `publish_new_data` method.
            """
            if not is_authenticated():
                self.logger.warning("Not authenticated")
                return
            self.publish_new_data()
            return

        @self.socketio.on('connect')
        def initiate_uuids() -> None:
            """
            Handles the 'connect' websocket event.

            This function checks if the client is authenticated. If not, it logs a warning and returns early. If the
            client is authenticated, it logs an info publishes new data using the `publish_new_data` method.
            """
            if not is_authenticated():
                self.logger.warning("Not authenticated")
                return
            self.logger.info("Client connected")
            print('Client connected')
            self.publish_new_data()
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
            if not is_authenticated():
                self.logger.warning("Not authenticated")
                return
            name = environment_mng.add_virtual_vehicle()
            self.socketio.emit('device_added', name)
            self.cybersecurity_mng._update_active_hacking_scenarios(name, '0')

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
            if not is_authenticated():
                self.logger.warning("Not authenticated")
                return login_redirect()
            return render_template('staff_config_home.html')

        @self.staffUI_blueprint.route('/configuration/config_update')
        def config_update() -> Any:
            if not is_authenticated():
                self.logger.warning("Not authenticated")
                return login_redirect()
            return render_template('staff_config_update.html')

        @self.staffUI_blueprint.route('/configuration/config_system_control')
        def config_system_control() -> Any:
            if not is_authenticated():
                self.logger.warning("Not authenticated")
                return login_redirect()
            return render_template('staff_config_system_control.html')

        @self.staffUI_blueprint.route('/configuration/update_application')
        def update_application() -> Any:
            if not is_authenticated():
                self.logger.warning("Not authenticated")
                return login_redirect()

            if platform.system() == 'Linux':
                self.logger.info("Update triggered")
                subprocess.call('./update.sh')
            else:
                self.logger.warning("Update button pressed, but not running on Linux system")
                print("Update button pressed. Function only available on Linux systems.")

            return ('', 204) # TODO: redirect to an info page or popup

        @self.staffUI_blueprint.route('/restart_program', methods=['POST'])
        def restart_program() -> Any:
            if not is_authenticated():
                self.logger.warning("Not authenticated")
                return login_redirect()

            if platform.system() == 'Linux':
                self.logger.info("Program restart triggered")
                subprocess.call('./restart_IAV-Distortion.sh')
            else:
                self.logger.warning("Program restart button pressed, but not running on Linux system")
                print("Restart program button pressed. Function only available on Linux systems.")

            return ('', 204) # TODO: redirect to an info page or popup

        @self.staffUI_blueprint.route('/restart_system', methods=['POST'])
        def restart_system() -> Any:
            if not is_authenticated():
                self.logger.warning("Not authenticated")
                return login_redirect()

            if platform.system() == 'Linux':
                self.logger.info("System restart triggered")
                subprocess.call('./restart_system.sh')
            else:
                self.logger.warning("System restart button pressed, but not running on Linux system")
                print("Restart system button pressed. Function only available on Linux systems.")

            return ('', 204)  # TODO: redirect to an info page or popup

        @self.staffUI_blueprint.route('/shutdown_system', methods=['POST'])
        def shutdown_system() -> Any:
            if not is_authenticated():
                self.logger.warning("Not authenticated")
                return login_redirect()

            if platform.system() == 'Linux':
                self.logger.info("System shutdown triggered")
                subprocess.call('./shutdown_system.sh')
            else:
                self.logger.warning("System shutdown button pressed, but not running on Linux system")
                print("Shutdown system button pressed. Function only available on Linux systems.")

            return ('', 204)  # TODO: redirect to an info page or popup

    def get_blueprint(self) -> Blueprint:
        return self.staffUI_blueprint

    def sort_scenarios(self) -> Tuple[dict, dict]:
        scenario_names = {}
        scenario_descriptions = {}
        for scenario in self.scenarios:
            scenario_names.update({scenario['id']: scenario['name']})
            scenario_descriptions.update({scenario['id']: scenario['description']})
        return scenario_names, scenario_descriptions

    def publish_new_data(self):
        self.socketio.emit('update_uuids', {"car_map": self.environment_mng.get_mapped_cars(), "car_queue": self.environment_mng.get_free_car_list(),
                                            "player_queue": self.environment_mng.get_waiting_player_list()})
        return

   # def update_uuids(self):
    #    self.socketio.emit('update_uuids', {"uuids": self.uuids, "car_queue": self.environment_mng._car_queue_list,
     #                                       "player_queue": self.environment_mng.get_player_queue()})
