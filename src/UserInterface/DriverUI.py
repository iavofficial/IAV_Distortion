# Copyright 2024 IAV GmbH
#
# This file is part of the IAV-Distortion project an interactive
# and educational showcase designed to demonstrate the need
# of automotive cybersecurity in a playful, engaging manner.
# and is released under the "Apache 2.0". Please see the LICENSE
# file that should have been included as part of this package.
#

from quart import Blueprint, render_template, request
import uuid
import logging
import asyncio
import time

from socketio import AsyncServer

from DataModel.Driver import Driver
from EnvironmentManagement.EnvironmentManager import EnvironmentManager
from EnvironmentManagement.ConfigurationHandler import ConfigurationHandler

from UserInterface.MinigameUI import Minigame_UI
from Minigames.Minigame_Controller import Minigame_Controller
from Minigames.Minigame import Minigame

logger = logging.getLogger(__name__)


class DriverUI:

    def __init__(self, behaviour_ctrl, environment_mng, sio: AsyncServer, name=__name__) -> None:
        self.driverUI_blueprint: Blueprint = Blueprint(name='driverUI_bp', import_name='driverUI_bp')
        self.vehicles: list = environment_mng.get_vehicle_list()
        self.behaviour_ctrl = behaviour_ctrl
        self._sio: AsyncServer = sio
        self.environment_mng: EnvironmentManager = environment_mng
        self.config_handler: ConfigurationHandler = ConfigurationHandler()

        self.__latest_driver_heartbeats: dict = {}
        self.__checking_heartbeats_flag: bool = False


        try:
            self.__driver_heartbeat_timeout: int = int(self.config_handler.get_configuration()["driver"]
                                                       ["driver_heartbeat_timeout_s"])
        except KeyError:
            logger.warning("No valid value for driver: driver_heartbeat_timeout in config_file. Using default "
                           "value of 30 seconds")
            self.__driver_heartbeat_timeout = 30

        try:
            self.__driver_proximity_timer: int = int(self.config_handler.get_configuration()["driver"]
                                                       ["driver_proximity_timer_s"])
        except KeyError:
            logger.warning("No valid value for driver: driver_proximity_timer in config_file. Using default "
                           "value of 5 seconds")
            self.__driver_proximity_timer = 5

        async def home_driver() -> str:
            """
            Load the driver ui page.

            Gets the clients cookie for identification, provides driving data and car image information to the client.

            Returns
            -------
                Returns a Response object representing a redirect to the driver ui page.
            """
            player = request.cookies.get("player")
            if player is None:
                player = str(uuid.uuid4())

            config = self.config_handler.get_configuration()

            heartbeat_interval = config["driver"]["driver_heartbeat_interval_ms"]
            background_grace_period = config["driver"]["driver_background_grace_period_s"]
            vehicle_scale = config["environment"]["env_vehicle_scale"]
            player_exists, picture, vehicle_information = self._prepare_html_data(player)

            return await render_template(template_name_or_list='driver_index.html', player=player,
                                         player_exists=player_exists,
                                         picture=picture,
                                         vehicle_information=vehicle_information,
                                         heartbeat_interval=heartbeat_interval,
                                         background_grace_period=background_grace_period,
                                         vehicle_scale=vehicle_scale,
                                         color_map=environment_mng.get_car_color_map())

        self.driverUI_blueprint.add_url_rule('/', 'home_driver', view_func=home_driver)

        async def exit_driver() -> str:
            player_id = request.args.get(key='player_id', type=str)
            reason = request.args.get(key='reason', default="You have been removed.", type=str)

            return await render_template(template_name_or_list='driver_exit.html', player=player_id, message=reason)

        self.driverUI_blueprint.add_url_rule('/exit', 'exit_driver', view_func=exit_driver)

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
            self.environment_mng.put_player_on_next_free_spot(player)
            self.__run_async_task(self._sio.enter_room(sid, player))
            return

        @self._sio.on('disconnected')
        def handle_disconnected(sid, data):
            player = data["player"]
            logger.debug(f"Driver {player} disconnected!")
            self.__remove_player(player)
            self.__run_async_task(self._sio.close_room(player))
            return

        @self._sio.on('disconnect')
        def handle_clienet_disconnect(sid):
            logger.debug(f"Client {sid} disconnected.")
            return

        @self._sio.on('slider_changed')
        def handle_slider_change(sid, data) -> None:
            player = data['player']
            value = float(data['value'])
            car = self.environment_mng.get_vehicle_by_player_id(player)
            if car is None:
                logger.warning("Player %s tried to change their own vehicle speed but they don't have a vehicle. "
                               "Ignoring the request", player)
                return
            car_id = car.get_vehicle_id()
            self.behaviour_ctrl.request_speed_change_for(uuid=car_id, value_perc=value)
            return

        @self._sio.on('lane_change')
        def change_lane(sid, data: dict) -> None:
            player = data['player']
            direction = data['direction']
            car = self.environment_mng.get_vehicle_by_player_id(player)
            if car is None:
                logger.warning("Player %s tried to change their lane but they don't have a vehicle. "
                               "Ignoring the request", player)
                return
            car_id = car.get_vehicle_id()
            self.behaviour_ctrl.request_lane_change_for(uuid=car_id, value=direction)
            return

        @self._sio.on('make_uturn')
        def make_uturn(sid, data: dict) -> None:
            player = data['player']
            car = self.environment_mng.get_vehicle_by_player_id(player)
            if car is None:
                logger.warning("Player %s tried to make a u-turn but they don't have a vehicle. "
                               "Ignoring the request", player)
                return
            car_id = car.get_vehicle_id()
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
            player = data.get("player")
            if player is None or not isinstance(player, str):
                logger.warning("Got invalid player data in driver_inactive message")
                return
            grace_period = self.config_handler.get_configuration()["driver"]["driver_background_grace_period_s"]
            logger.debug(f"Player {player} send the application to the background and will be removed in "
                         f"{grace_period} seconds.")
            self.environment_mng.schedule_remove_player_task(player=player, grace_period=grace_period)
            return

        @self._sio.on('driver_active')
        def client_active(sid, data: dict) -> None:
            player = data["player"]
            logger.debug(f"Player {player} is back in the application. Removal will be canceled or player will be "
                         f"added to the queue again.")
            self.environment_mng.put_player_on_next_free_spot(player)
            vehicle = self.get_vehicle_by_player(player=player)
            driver = self.environment_mng.get_driver_by_id(player_id=player)
            self.__run_async_task(self.__emit_driver_score(driver=driver))
            if vehicle is not None and driver.get_is_in_physical_vehicle() is not True:
                self.__run_async_task(self.__in_physical_vehicle(driver))
            return

        @self._sio.on('switch_cars')
        async def switch_cars(sid, data: dict) -> None:
            player = data["player"]
            vehicle = self.environment_mng.get_vehicle_by_player_id(player)
            if vehicle is None:
                logger.warn(f"Driver UI: No vehicle for player {player} could be found. Ignoring the switch request.")
                return
            target_vehicle_id = vehicle.vehicle_in_proximity
            if target_vehicle_id is None:
                logger.warn(f"Driver UI: No target vehicle id for player {player} driving {vehicle.get_vehicle_id()} could be found. Ignoring the switch request.")
                return
            target_vehicle = self.environment_mng.get_vehicle_by_vehicle_id(target_vehicle_id)
            if target_vehicle is None:
                logger.warn(f"Driver UI: No target vehicle for player {player} driving {vehicle.get_vehicle_id()} with target_vehicle_id {target_vehicle_id} could be found. Ignoring the switch request.")
                return
            target_player = target_vehicle.get_player_id()

            # Try to start Minigame
            minigame_task, minigame_object = Minigame_Controller.get_instance().play_random_available_minigame(player, target_player)
            
            if minigame_task is None or minigame_object is None:
                logger.warning(f"DriverUI: The minigame for player {player} and player {target_player} could not be started for some reason. Ignoring the request.")
                return
            winner = await minigame_task
            logger.debug(f"DriverUI: The player {player} has won a minigame that was initiated by a hack of vehicle {target_vehicle_id}.")
            if winner is None or winner == target_player:
                return
            
            self.environment_mng.manage_car_switch_for(player, target_vehicle_id)
            driver = self.environment_mng.get_driver_by_id(player_id=player)
            self.__run_async_task(self.__emit_driver_score(driver=driver))
            if vehicle is not None and driver.get_is_in_physical_vehicle() is not True:
                self.__run_async_task(self.__in_physical_vehicle(driver))
            return

    def update_driving_data(self, driving_data: dict) -> None:
        self.__run_async_task(self.__emit_driving_data(driving_data))
        return

    async def __emit_driving_data(self, driving_data: dict) -> None:
        await self._sio.emit('update_driving_data', driving_data)
        return

    def update_item_activity(self, item_data: dict) -> None:
        self.__run_async_task(self.__emit_item_data(item_data))
        return

    async def __emit_item_data(self, item_data: dict) -> None:
        await self._sio.emit('item_update', item_data)
        return

    def __run_async_task(self, task):
        """
        Run a asyncio awaitable task
        task: awaitable task
        """
        asyncio.create_task(task)
        # TODO: Log error, if the coroutine doesn't end successfully

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
    
    async def __emit_driver_score(self, driver: Driver) -> None:
        await self._sio.emit('update_player_score', {'score': driver.get_score(), 'player': driver.get_player_id()})
    
    async def __in_physical_vehicle(self, driver: Driver) -> None:
        driver.set_is_in_physical_vehicle(True)
        while self.get_vehicle_by_player(player=driver.get_player_id()) is not None and "Virtual" not in self.get_vehicle_by_player(player=driver.get_player_id()).get_vehicle_id():
            driver.increase_score(1)
            await self._sio.emit('update_player_score', {'score': driver.get_score(), 'player': driver.get_player_id()})
            await self._sio.sleep(1)
        driver.set_is_in_physical_vehicle(False)
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
                    logger.info(f'Player {player} timed out. Removing player from the game...')
                    self.__remove_player(player)

    async def __send_proximity_vehicle(self, player: str):
        """
        Continuously monitors a vehicle's proximity status and emits an update when its proximity status changes
        Parameters
        ----------
        player : str
            The identifier for the player whose vehicle proximity is being monitored
        """
        vehicle = self.get_vehicle_by_player(player=player)
        previous_vehicle_in_proximity = None
        previous_driver_getting_hacked = None
        if vehicle != None:
            while True:
                vehicle = self.get_vehicle_by_player(player=player)
                if vehicle is None:
                    return
                await asyncio.sleep(0.1)
                if previous_vehicle_in_proximity != vehicle.vehicle_in_proximity:
                    uuid = vehicle.vehicle_id
                    proximity_vehicle = self.environment_mng.get_vehicle_by_vehicle_id(vehicle.vehicle_in_proximity)
                    if proximity_vehicle is None:
                        driver_getting_hacked = None
                    else:
                        driver_getting_hacked = proximity_vehicle.get_player_id()
                        previous_driver_getting_hacked = driver_getting_hacked

                    # Emit message only to the hacking driver and the driver that is being hacked
                    for room in [player, driver_getting_hacked, previous_driver_getting_hacked]:
                        if room is None:
                            continue
                        self.__run_async_task(self._sio.emit('send_proximity_vehicle', {'hacker_vehicle_id': uuid, 'hacker_driver_id': player, 'getting_hacked_vehicle_id': vehicle.vehicle_in_proximity, 'getting_hacked_driver_id' : driver_getting_hacked, 'proximity_timer': self.__driver_proximity_timer}, to=room))
                   
                    previous_vehicle_in_proximity= vehicle.vehicle_in_proximity
                    vehicle.reset_proximity_timer()
                else:
                    if vehicle.vehicle_in_proximity != None:
                        self.__run_async_task(self.__check_driver_proximity_timer(player))

    async def __check_driver_proximity_timer(self, player: str):
        """
        Continuously monitors a vehicle's proximity timer and emits an update when its timer exceedes the limit
        Parameters
        ----------
        player : str
            The identifier for the player whose proximity timer is being monitored
        """
        vehicle = self.get_vehicle_by_player(player=player)
        if vehicle != None:
            if time.time() - vehicle.proximity_timer > self.__driver_proximity_timer:
                proximity_vehicle = self.environment_mng.get_vehicle_by_vehicle_id(vehicle.vehicle_in_proximity)
                if proximity_vehicle is None:
                    return
                driver_getting_hacked = proximity_vehicle.get_player_id()
                for room in [player, driver_getting_hacked]:
                    if room is None:
                        continue
                    await self._sio.emit('send_finished_proximity_timer', {'hacker_driver_id' : player, 'getting_hacked_driver_id' : driver_getting_hacked}, to=room)

                       
    def __remove_player(self, player: str) -> None:
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

    def _prepare_html_data(self, player: str) -> tuple[bool, str, dict[str, str]]:
        """
        Update queue and get all required data to render a template for a player

        Parameters
        ----------
        player: str
            ID of the player for which the site should be rendered

        Returns
        -------
            Tuple consisting of
                - boolean whether the player has a vehicle assigned
                - string of the picture path or empty string
                - vehicle driving information
        """
        print(f"Driver {player} connected!")

        self.__latest_driver_heartbeats[player] = time.time()
        self.__run_async_task(self.__send_proximity_vehicle(player))
        if not self.__checking_heartbeats_flag:
            self.__run_async_task(self.__check_driver_heartbeat_timeout())
            self.__checking_heartbeats_flag = True
        config = self.config_handler.get_configuration()

        picture = ''  # default picture can be added here
        vehicle_information = {
            'active_hacking_scenario': '0',
            'speed_request': '0'
        }
        self.environment_mng.put_player_on_next_free_spot(player)
        vehicle = self.environment_mng.get_vehicle_by_player_id(player)

        if vehicle is not None:
            picture = vehicle.vehicle_id
            if vehicle.vehicle_id.startswith("Virtual Vehicle"):
                try:
                    picture = 'Virtual_Vehicles/' + config["virtual_cars_pics"][vehicle.vehicle_id]
                except KeyError:
                    logger.warning(f'No image configured for {vehicle.vehicle_id}.')
            else:
                picture = 'Real_Vehicles/' + picture.replace(":", "") + ".webp"
            vehicle.set_driving_data_callback(self.update_driving_data)
            vehicle.set_item_data_callback(self.update_item_activity)
            vehicle_information = vehicle.get_driving_data()
            logger.debug(f'Callback set for {player}')
        return vehicle is not None, picture, vehicle_information
