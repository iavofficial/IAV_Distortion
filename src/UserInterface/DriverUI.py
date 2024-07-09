# Copyright 2024 IAV GmbH
#
# This file is part of the IAV-Distortion project an interactive
# and educational showcase designed to demonstrate the need
# of automotive cybersecurity in a playful, engaging manner.
# and is released under the "Apache 2.0". Please see the LICENSE
# file that should have been included as part of this package.
#

from quart import Blueprint, render_template, request
import socketio
import uuid
import logging
from logging import Logger
import asyncio
import time

from EnvironmentManagement.EnvironmentManager import EnvironmentManager
from EnvironmentManagement.ConfigurationHandler import ConfigurationHandler


class DriverUI:

    def __init__(self, behaviour_ctrl, environment_mng, sio: socketio, name=__name__) -> None:
        self.driverUI_blueprint: Blueprint = Blueprint(name='driverUI_bp', import_name='driverUI_bp')
        self.vehicles: list = environment_mng.get_vehicle_list()
        self.behaviour_ctrl = behaviour_ctrl
        self._sio: socketio = sio
        self.environment_mng: EnvironmentManager = environment_mng
        self.config_handler: ConfigurationHandler = ConfigurationHandler()

        self.logger: Logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        console_handler = logging.StreamHandler()
        self.logger.addHandler(console_handler)

        self.__latest_driver_heartbeats: dict = {}
        self.__checking_heartbeats_flag: bool = False

        try:
            self.__driver_heartbeat_timeout: int = int(self.config_handler.get_configuration()["driver"]["driver_heartbeat_timeout_s"])
        except:
            self.logger.warning("No valid value for driver: driver_heartbeat_timeout in config_file. Using default "
                                "value of 30 seconds")
            self.__driver_heartbeat_timeout = 30

        async def home_driver() -> str:
            """
            Load the driver ui page.

            Gets the clients cookie for identification, provides driving data and car image information to the client.

            Returns
            -------
                Returns a Response object representing a redirect to the driver ui page.
            """
            player = request.cookies.get("player")
            print(f"Driver {player} connected!")
            if player is None:
                player = str(uuid.uuid4())
                self.__latest_driver_heartbeats[player] = time.time()
            if not self.__checking_heartbeats_flag:
                self.__run_async_task(self.__check_driver_heartbeat_timeout())
                self.__checking_heartbeats_flag = True

            config = self.config_handler.get_configuration()
            vehicle = self.environment_mng.update_queues_and_get_vehicle(player)
            player_exists = False
            picture = ''  # default picture can be added here
            vehicle_information = {
                'active_hacking_scenario': '0',
                'speed_request': '0'
            }

            if vehicle is not None:
                player_exists = True
                picture = vehicle.vehicle_id
                if vehicle.vehicle_id.startswith("Virtual Vehicle"):
                    try:
                        picture = 'Virtual_Vehicles/' + config["virtual_cars_pics"][vehicle.vehicle_id]
                    except KeyError:
                        self.logger.warning(f'No image configured for {vehicle.vehicle_id}.')
                else:
                    picture = 'Real_Vehicles/' + picture.replace(":", "") + ".webp"
                vehicle.set_driving_data_callback(self.update_driving_data)
                vehicle_information = vehicle.get_driving_data()
                self.logger.debug(f'Callback set for {player}')

            return await render_template('driver_index.html', player=player, player_exists=player_exists,
                                         picture=picture,
                                         vehicle_information=vehicle_information,
                                         heartbeat_interval=config["driver"]["driver_heartbeat_interval_ms"],
                                         background_grace_period=config["driver"]["driver_background_grace_period_s"])

        self.driverUI_blueprint.add_url_rule('/', 'home_driver', view_func=home_driver)

        @self._sio.on('handle_connect')
        def handle_connected(sid: str, data: dict) -> None:
            """
            Calls environment manager function to update queues and vehicles.

            Custom event triggered on connection of a client to the driver ui. Event needed to handle reloads of
            driver ui properly. Receives the player id from client which is used by the environment manager to abort
            removing of player if reconnected in a certain time (e.g. when reloading the page).

            Parameters
            ----------
            sid: str
                ID of websocket client
            data: dict
                Data received with websocket event.
            """
            player = data["player"]
            self.environment_mng.update_queues_and_get_vehicle(player)
            return

        @self._sio.on('disconnected')
        def handle_disconnected(sid, data):
            player = data["player"]
            self.logger.debug(f"Driver {player} disconnected!")
            self.remove_player(player)
            return

        @self._sio.on('disconnect')
        def handle_clienet_disconnect(sid):
            self.logger.debug(f"Client {sid} disconnected.")
            return

        @self._sio.on('slider_changed')
        def handle_slider_change(sid, data) -> None:
            player = data['player']
            value = float(data['value'])
            car_id = self.environment_mng.get_car_from_player(player).get_vehicle_id()
            # TODO: add check for car_id not None
            self.behaviour_ctrl.request_speed_change_for(uuid=car_id, value_perc=value)
            return

        @self._sio.on('lane_change')
        def change_lane(sid, data: dict) -> None:
            player = data['player']
            direction = data['direction']
            car_id = self.environment_mng.get_car_from_player(player).get_vehicle_id()
            self.behaviour_ctrl.request_lane_change_for(uuid=car_id, value=direction)
            return

        @self._sio.on('make_uturn')
        def make_uturn(sid, data: dict) -> None:
            player = data['player']
            car_id = self.environment_mng.get_car_from_player(player).get_vehicle_id()
            self.behaviour_ctrl.request_uturn_for(uuid=car_id)
            return

        @self._sio.on('get_driving_data')
        def get_driving_data(sid, player: str) -> None:
            vehicle = self.get_vehicle_by_player(player=player)
            driving_data = vehicle.get_driving_data()
            self.update_driving_data(driving_data)
            return

        @self._sio.on('driver_heartbeat')
        def update_last_heartbeat(sid, data: dict) -> None:
            """
            Updates timestamp of latest received heartbeat for the players.
            """
            player = data["player"]
            self.__latest_driver_heartbeats[player] = time.time()
            return

        @self._sio.on('driver_inactive')
        def client_inactive(sid, data: dict) -> None:
            player = data["player"]
            grace_period = self.config_handler.get_configuration()["driver"]["driver_background_grace_period_s"]
            self.logger.debug(f"Player {player} send the application to the background and will be removed in "
                              f"{grace_period} seconds.")
            self.environment_mng.schedule_remove_player_task(player=player, grace_period=grace_period)
            return

        @self._sio.on('driver_active')
        def client_active(sid, data: dict) -> None:
            player = data["player"]
            self.logger.debug(f"Player {player} is back in the application. Removal will be canceled or player will be "
                              f"added to the queue again.")
            self.environment_mng.update_queues_and_get_vehicle(player)
            return

    def update_driving_data(self, driving_data: dict) -> None:
        self.__run_async_task(self.__emit_driving_data(driving_data))
        return

    def get_blueprint(self) -> Blueprint:
        return self.driverUI_blueprint

    def get_vehicle_by_player(self, player: str):
        temp_vehicle = [vehicle for vehicle in self.vehicles if vehicle.player == player]
        if len(temp_vehicle) == 1:
            return temp_vehicle[0]
        elif len(temp_vehicle) < 1:
            return None
        else:
            # Todo: define error reaction if same player is assigned to different vehicles
            return None

    def __run_async_task(self, task):
        """
        Run a asyncio awaitable task
        task: awaitable task
        """
        asyncio.create_task(task)
        # TODO: Log error, if the coroutine doesn't end successfully

    async def __emit_driving_data(self, driving_data: dict) -> None:
        await self._sio.emit('update_driving_data', driving_data)
        return

    async def __check_driver_heartbeat_timeout(self):
        """
        Continuously checks driver heartbeats for timeouts.
        """
        while True:
            await asyncio.sleep(1)
            players = list(self.__latest_driver_heartbeats.keys())
            for player in players:
                if time.time() - self.__latest_driver_heartbeats.get(player, 0) > self.__driver_heartbeat_timeout:
                    self.logger.info(f'Player {player} timed out. Removing player from the game...')
                    self.remove_player(player)

    def remove_player(self, player: str) -> None:
        """
        Remove player from the game.

        Parameters
        ----------
        player: str
            ID of player to be removed.
        """
        if player in self.__latest_driver_heartbeats:
            del self.__latest_driver_heartbeats[player]
        grace_period = self.config_handler.get_configuration()["driver"]["driver_reconnect_grace_period_s"]
        self.environment_mng.schedule_remove_player_task(player=player, grace_period=grace_period)
        return
