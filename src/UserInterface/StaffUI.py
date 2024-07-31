# Copyright 2024 IAV GmbH
#
# This file is part of the IAV-Distortion project an interactive
# and educational showcase designed to demonstrate the need
# of automotive cybersecurity in a playful, engaging manner.
# and is released under the "Apache 2.0". Please see the LICENSE
# file that should have been included as part of this package.
#
import asyncio
from asyncio import Task

from quart import Blueprint, render_template, request, redirect, url_for, jsonify, Response
import socketio
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
    sio: socket
        socketio to enable websocket connection.
    environment_mng: EnvironmentManager
        Access to the EnvironmentManager to exchange information about queues and add or remove players and vehicles.
    password: str
        Configured password to log in to the staff ui.
    """

    def __init__(self, cybersecurity_mng: CyberSecurityManager, sio: socketio, environment_mng: EnvironmentManager,
                 password: str):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        console_handler = logging.StreamHandler()
        self.logger.addHandler(console_handler)

        self.cybersecurity_mng: CyberSecurityManager = cybersecurity_mng

        self.password = password
        self.admin_token = secrets.token_urlsafe(12)
        self.staffUI_blueprint: Blueprint = Blueprint(name='staffUI_bp', import_name='staffUI_bp')
        self.scenarios: List[dict] = cybersecurity_mng.get_all_hacking_scenarios()
        self._sio: socketio = sio
        self.environment_mng: EnvironmentManager = environment_mng
        self.devices: list = []

        self.environment_mng.set_staff_ui_update_callback(self.publish_new_data)
        self.environment_mng.set_publish_removed_player_callback(self.publish_removed_player)
        self.environment_mng.set_publish_player_active_callback(self.publish_player_active)

        @self.staffUI_blueprint.before_request
        def is_authenticated() -> Response | None:
            """
            Is executed before each request and checks if client is authenticated to access .../staff/... pages.

            If client is not authenticated, the client will be redirected to the login page.

            Returns
            -------
            Response or None
                If not authenticated, returns a Response object representing a redirect to the login page.
                If authenticated, returns None
            """
            if '/staff/' in request.path and request.path != '/staff/':
                request_token = request.cookies.get('admin_token')
                if request_token is None or request_token != self.admin_token:
                    return login_redirect() # redirect(url_for("staffUI_bp.login_site"))
                else:
                    return None

        def login_redirect() -> Any:
            """
            Redirect client to the login page.

            Returns
            -------
            Response
                Returns a Response object representing a redirect to the login page.
            """
            return redirect(url_for("staffUI_bp.login_site"))

        async def home_staff_control() -> Any:
            """
            Load the default page of the staff ui.

            Redirect the client to the login page if client is not authenticated. Gets information about hacking
            scenarios from CyberSecurityManager as well as the list of controlled cars from the EnvironmentManager to
            provide these to the staff ui.

            Returns
            -------
                Returns a Response object representing a redirect to the default staff ui page.
            """
            names, descriptions = self.sort_scenarios()
            active_scenarios = cybersecurity_mng.get_active_hacking_scenarios()  # {'UUID': 'scenarioID'}
            # TODO: Show selection of choose hacking scenarios always sorted by player number
            return await render_template('staff_control.html', activeScenarios=active_scenarios,
                                         uuids=environment_mng.get_controlled_cars_list(), names=names,
                                         descriptions=descriptions)

        self.staffUI_blueprint.add_url_rule('/staff_control', 'staff_control', view_func=home_staff_control)

        async def set_scenario() -> Any:
            """
            Set the hacking scenario of a controlled car.

            Redirect the client to the login page if client is not authenticated. Set the scenario for the requested car
            using the CyberSecurityManager.

            Returns
            -------
            Response
                Returns a Response object representing a redirect to the default staff ui page.
            """
            selected_option = (await request.form).get('option')
            pattern = r"scenarioID_(\d+)-UUID_([A-Fa-f0-9:]+|Virtual Vehicle [0-9]+)>"
            match = re.search(pattern, selected_option)

            scenario_id = match.group(1)
            uuid = match.group(2)
            cybersecurity_mng.activate_hacking_scenario_for_vehicle(uuid, scenario_id)

            return redirect(url_for('staffUI_bp.staff_control'))

        self.staffUI_blueprint.add_url_rule('/hacking_scenario', methods=['POST'], view_func=set_scenario)

        async def login_site() -> Any:
            """
            Load the login page.

            Redirect to default staff ui page if already authenticated. Check entered password.

            Returns
            -------
            Response
                Returns a Response object representing a redirect to the default staff ui page or back to login
                according to authentication status.
            """
            # if is_authenticated():
            #     self.logger.info("Authenticated")
            #     return redirect(url_for('staffUI_bp.staff_control'))
            if request.method == 'GET':
                return await render_template('staff_login.html')
            # a password was submitted via POST
            pwd = (await request.form).get('password')
            if pwd is not None and pwd == self.password:
                response = redirect(url_for('staffUI_bp.staff_control'))
                response.set_cookie('admin_token', self.admin_token)
                return response
            return await render_template('staff_login.html', wrong_password=True)

        self.staffUI_blueprint.add_url_rule('/', methods=['GET', 'POST'], view_func=login_site)

        # We can't directly redirect via SocketIO so we just drop the requests
        # TODO: Log dropped events!

        @self._sio.on('get_uuids')
        async def update_uuids_staff_ui(sid) -> None:
            """
            Handles the 'get_uuids' websocket event.

            This function checks if the client is authenticated. If not, it logs a warning and returns early. If the
            client is authenticated, requests update from EnvironmentManager.
            """
            # TODO: authentication check for websocket events
            self.environment_mng.update_staff_ui()
            return

        @self._sio.on('connect')
        async def initiate_uuids(sid, environ, auth) -> None:
            """
            Handles the 'connect' websocket event.

            This function checks if the client is authenticated. If not, it logs a warning and returns early. If the
            client is authenticated, it logs an info and requests an update from the EnvironmentManager.
            """
            # TODO: authentication check for websocket events
            self.logger.debug(f"Client {sid} connected")
            self.environment_mng.update_staff_ui()
            return

        @self._sio.on('search_cars')
        async def search_cars(sid) -> None:
            """
            Handles the 'search_cars' websocket event.

            This function checks if the client is authenticated. If not, it logs a warning and returns early. If the
            client is authenticated, it calls the function to search for unpaired Anki cars from the EnvironmentManager.
            Publishes the list of found cars via websocket. Logs the search and its result as an info.
            """
            # TODO: authentication check for websocket events
            self.logger.info("Searching devices...")
            new_devices = await environment_mng.find_unpaired_anki_cars()
            self.logger.info(f'Found devices: {new_devices}')
            await self._sio.emit('new_devices', new_devices)
            return

        @self._sio.on('add_device')
        async def handle_add_device(sid, device: str) -> None:
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
            # TODO: authentication check for websocket events
            await environment_mng.connect_to_physical_car_by(device)
            await self._sio.emit('device_added', device)
            self.logger.debug("Device added %s", device)
            # TODO: exception if device is no longer available
            self.cybersecurity_mng._update_active_hacking_scenarios(device, '0')
            return

        @self._sio.on('add_virtual_vehicle')
        async def handle_add_virtual_vehicle(sid) -> None:
            """
            Handles the 'add_virtual_vehicle' websocket event.

            This function checks if the client is authenticated. If not, it logs a warning and returns early. If the
            client is authenticated, it calls the function to add a virtual vehicle from the EnvironmentManager,
            initiate its hacking scenario and send the 'added_device' event.
            """
            # TODO: authentication check for websocket events
            name = environment_mng.add_virtual_vehicle()
            await self._sio.emit('device_added', name)
            self.cybersecurity_mng._update_active_hacking_scenarios(name, '0')
            return

        @self._sio.on('delete_player')
        async def handle_delete_player(sid, player: str) -> None:
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
            # TODO: authentication check for websocket events
            environment_mng._remove_player_from_vehicle(player)
            environment_mng._remove_player_from_waitlist(player)
            self.logger.debug("Player deleted %s", player)
            return

        @self._sio.on('delete_vehicle')
        async def handle_delete_vehicle(sid, vehicle_id: str) -> None:
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
            # TODO: authentication check for websocket events
            environment_mng.remove_vehicle_by_id(vehicle_id)
            await self._sio.emit('vehicle_removed', vehicle_id)
            self.logger.debug("Vehicle deleted %s", vehicle_id)
            return

        @self._sio.on('get_update_hacking_scenarios')
        async def update_hacking_scenarios(sid) -> None:
            """
            Handles the 'get_update_hacking_scenarios' websocket event.

            This function checks if the client is authenticated. If not, it logs a warning and returns early. If the
            client is authenticated, it gets sorted lists of hacking scenarios and their description as well as the
            active scenario of each car. Logs an info and sends the information about the scenarios via the
            'update_hacking_scenarios' event.
            """
            # TODO: authentication check for websocket events
            names, descriptions = self.sort_scenarios()
            active_scenarios = cybersecurity_mng.get_active_hacking_scenarios()
            data = {'activeScenarios': active_scenarios, 'uuids': self.environment_mng.get_controlled_cars_list(),
                    'names': names, 'descriptions': descriptions}
            self.logger.debug("Updated hacking scenarios")
            await self._sio.emit('update_hacking_scenarios', data)
            return

        @self.staffUI_blueprint.route('/configuration/home')
        async def config_home() -> Any:
            """
            Load configuration page.

            If client is not authenticated, client is redirected to the login page.

            Returns
            -------
            Response
                Returns a Response object representing the configuration page or a redirect to the login page, if not
                authenticated.
            """
            return await render_template('staff_config_home.html')

        @self.staffUI_blueprint.route('/configuration/config_update')
        async def config_update() -> Any:
            """
            Load configuration page for SW-update.

            If client is not authenticated, client is redirected to the login page.

            Returns
            -------
            Response
                Returns a Response object representing the update page or a redirect to the login page, if not
                authenticated.
            """
            return await render_template('staff_config_update.html')

        @self.staffUI_blueprint.route('/configuration/config_system_control')
        async def config_system_control() -> Any:
            """
            Load configuration page for system control.

            If client is not authenticated, client is redirected to the login page.

            Returns
            -------
            Response
                Returns a Response object representing the system control page or a redirect to the login page, if not
                authenticated.
            """
            return await render_template('staff_config_system_control.html')

        @self.staffUI_blueprint.route('/update_program', methods=['POST'])
        async def update_application() -> Any:
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
            if platform.system() == 'Linux':
                self.logger.info("Update triggered")
                process = subprocess.Popen(['bash', './update.sh'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                stdout, stderr = process.communicate()
                message = 'Update started. This will take a few moments. The system will restart afterwards.'
                return message, 200
            else:
                self.logger.warning("Update button pressed, but not running on Linux system")
                message = 'Error starting the update. Function only available on linux systems.'
                return message, 200

        @self.staffUI_blueprint.route('/restart_program', methods=['POST'])
        async def restart_program() -> Any:
            """
            Handles the post request send by the 'restart program' button.

            If client is not authenticated, client is redirected to the login page. If operating system is 'Linux' the
            'restart_IAV-Distortion' utility script is called. Otherwise, a warning is logged.

            Returns
            -------
            Response or Tuple
                If not authenticated, returns a Response object representing a redirect to the login page.
                If authenticated, Returns a Tuple[str, int] with the status about the request.
            """
            if platform.system() == 'Linux':
                self.logger.info("Program restart triggered")
                process = subprocess.Popen(['bash', './restart_IAV-Distortion.sh'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                stdout, stderr = process.communicate()
                message = "The program will restart now. This will take a moment please wait and reload the page."
                return message, 200
                
            else:
                self.logger.warning("Program restart button pressed, but not running on Linux system")
                message = 'Error restarting IAV-Distortion. Function only available on linux systems.'
                return message, 200

        @self.staffUI_blueprint.route('/restart_system', methods=['POST'])
        async def restart_system() -> Any:
            """
            Handles the post request send by the 'restart system' button.

            If client is not authenticated, client is redirected to the login page. If operating system is 'Linux' the
            'restart_system' utility script is called. Otherwise, a warning is logged.

            Returns
            -------
            Response or Tuple
                If not authenticated, returns a Response object representing a redirect to the login page.
                If authenticated, Returns a Tuple[str, int] with the status about the request.
            """
            if platform.system() == 'Linux':
                self.logger.info("System restart triggered")
                subprocess.run('./restart_system.sh')
                message = "The system will restart now. This will take a moment. Please wait and reload the page " \
                          "after the system rebooted"
                return message, 200
            else:
                self.logger.warning("System restart button pressed, but not running on Linux system")
                message = 'Error restarting the system. Function only available on linux systems.'
                return message, 200

        @self.staffUI_blueprint.route('/shutdown_system', methods=['POST'])
        async def shutdown_system() -> Any:
            """
            Handles the post request send by the 'shutdown sytem' button.

            If client is not authenticated, client is redirected to the login page. If operating system is 'Linux' the
            'shutdown_system' utility script is called. Otherwise, a warning is logged.

            Returns
            -------
            Response or Tuple
                If not authenticated, returns a Response object representing a redirect to the login page.
                If authenticated, Returns a Tuple[str, int] with the status about the request.
            """
            if platform.system() == 'Linux':
                self.logger.info("System shutdown triggered")
                subprocess.run('./shutdown_system.sh')
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
        data = {"car_map": car_map, "car_queue": car_queue, "player_queue": player_queue}
        self.__run_async_task(self.__emit_new_data(data))
        return

    def publish_removed_player(self, player: str, reason: str = "") -> None:
        """
        Sends 'player_removed' event.

        Parameters
        ----------
        player: str
            ID of the player which has been removed.
        reason: str
            removal reason shown in the UI
        """
        self.__run_async_task(self.__emit_player_removed(player, reason))
        return

    def publish_player_active(self, player: str) -> None:
        """
        Sends 'player_active' event.

        Parameters
        ----------
        player: str
            ID of the player, who switched from the queue to be an active player.
        """
        self.__run_async_task(self.__emit_player_active(player))
        return

    def __run_async_task(self, task: Task) -> None:
        """
        Run an asyncio awaitable task.

        Parameters
        ----------
        task: Task
            Coroutine to be scheduled as an asynchronous task.
        """
        asyncio.create_task(task)
        # TODO: Log error, if the coroutine doesn't end successfully
        return

    async def __emit_player_active(self, player: str) -> None:
        """
        Emits the 'player_active' websocket event.

        Parameters
        ----------
        player: str
            ID of player that changed from being queued to being active.
        """
        await self._sio.emit('player_active', player)
        return

    async def __emit_player_removed(self, player: str, reason: str = "") -> None:
        """
        Emits the 'player_removed' websocket event.

        Parameters
        ----------
        player: str
            ID of player that has been removed from the game.
                    reason: str
        reason: str
            removal reason shown in the UI
        """
        data = {
            "player_id": player,
            "message": reason
        }
        await self._sio.emit('player_removed', data)
        return

    async def __emit_new_data(self, data: dict) -> None:
        """
        Emits the 'update_uuids' websocket event.

        Parameters
        ----------
        data: dict
            Dictionary including the active player/cars mapping, player and vehicle queue.
        """
        await self._sio.emit('update_uuids', data)
        return

