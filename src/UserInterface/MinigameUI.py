# Copyright 2024 IAV GmbH
#
# This file is part of the IAV-Distortion project an interactive
# and educational showcase designed to demonstrate the need
# of automotive cybersecurity in a playful, engaging manner.
# and is released under the "Apache 2.0". Please see the LICENSE
# file that should have been included as part of this package.
#

from quart import Blueprint, render_template, request, redirect, url_for
import logging
import asyncio
from asyncio import Task

from socketio import AsyncServer

from EnvironmentManagement.ConfigurationHandler import ConfigurationHandler
from EnvironmentManagement.EnvironmentManager import EnvironmentManager
from VehicleMovementManagement.BehaviourController import BehaviourController

from Minigames.Minigame_Controller import Minigame_Controller
from Minigames.Minigame import Minigame

logger = logging.getLogger(__name__)


class Minigame_UI:

    def __init__(self, sio: AsyncServer, environment_mng: EnvironmentManager, behaviour_ctrl: BehaviourController,
                 name=__name__) -> None:
        self.minigame_ui_blueprint: Blueprint = Blueprint(name='minigameUI_bp', import_name='minigameUI_bp')
        self._sio: AsyncServer = sio
        self._environment_mng: EnvironmentManager = environment_mng
        self._behaviour_ctrl = behaviour_ctrl
        self.config_handler: ConfigurationHandler = ConfigurationHandler()
        self._minigame_controller: Minigame_Controller =\
            Minigame_Controller.get_instance(sio=self._sio, minigame_ui_blueprint=self.minigame_ui_blueprint)
        self._minigame_controller.set_minigame_start_callback(self._minigame_started_callback)
        try:
            self._driving_speed_while_playing =\
                self.config_handler.get_configuration()['minigame']['driving_speed_while_playing']
        except KeyError:
            logger.warning("No valid value for minigame: driving_speed_while_playing in config_file. \
                Using default value of 30")
            self._driving_speed_while_playing = 30

        try:
            self.__driver_heartbeat_timeout: int = int(self.config_handler.get_configuration()["driver"]
                                                       ["driver_heartbeat_timeout_s"])
        except KeyError:
            logger.warning("No valid value for driver: driver_heartbeat_timeout in config_file. Using default "
                           "value of 30 seconds")
            self.__driver_heartbeat_timeout = 30

        async def home_minigame() -> str:
            player = request.cookies.get("player")
            if player is None or self._minigame_controller.get_minigame_name_by_player_id(player) is None:
                return redirect(url_for("driverUI_bp.home_driver"))

            return await render_template(template_name_or_list='minigame_index.html',
                                         player=player,
                                         minigame=self._minigame_controller.get_minigame_name_by_player_id(player),
                                         heartbeat_interval=self.__driver_heartbeat_timeout)

        self.minigame_ui_blueprint.add_url_rule('/', 'minigame', view_func=home_minigame)

        async def exit_minigame() -> str:
            player_id = request.args.get(key='player_id', type=str)
            reason = request.args.get(key='reason', default="The minigame has been cancelled.", type=str)

            return await render_template(template_name_or_list='driver_index.html', player=player_id, message=reason)

        self.minigame_ui_blueprint.add_url_rule('/exit', 'exit_driver', view_func=exit_minigame)

        @self._sio.on('minigame_handle_connect')
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
            logger.debug(f"Driver {player} connected to the minigame lobby.")
            asyncio.create_task(self._send_description(data["minigame"]))
            asyncio.create_task(self._sio.enter_room(sid, player))
            return

        @self._sio.on('minigame_disconnected')
        def handle_disconnected(sid, data):
            player = data["player"]
            logger.debug(f"Driver {player} disconnected from the minigame lobby!")
            minigame_name = self._minigame_controller.get_minigame_name_by_player_id(player)
            if minigame_name is None or minigame_name not in self._minigame_controller.get_minigame_name_list():
                return

            self._minigame_controller.get_minigame_object(minigame_name).cancel()
            return

        @self._sio.on('minigame_player_accept')
        def on_minigame_player_accept(sid, data):
            player = data['player']
            minigame_name = data['minigame']
            self._minigame_controller.set_player_ready(player, minigame_name)

    def get_blueprint(self) -> Blueprint:
        return self.minigame_ui_blueprint

    async def _send_description(self, minigame: str) -> None:
        """
        Sends the description of the specified minigame via the SocketIO event 'send_description'

        Parameters:
        -----------
        minigame: str
            Name of the minigame

        Returns:
        --------
        Nothing
        """
        description = self._minigame_controller.get_description(minigame)
        if description is None:
            description = f"A description for the minigame {minigame} could not be found."
        await self._sio.emit('send_description', {"minigame": minigame, "description": description})

    def _minigame_started_callback(self, minigame_task: Task, minigame_object: Minigame) -> None:
        """
        Function to be executed once a new minigame has started.
        Will redirect the minigame's players to the minigame ui
        and back to the driver ui once the minigame is done/cancelled.

        Parameters:
        -----------
        minigame_object: Minigame
            Object/Instance of the minigame that has just started
        """

        if minigame_task is None:
            logger.warning("MinigameUI: No minigame task was provided.")
            return None
        if minigame_object is None:
            logger.warning("MinigameUI: No minigame object was provided.")
            return None

        async def manage_players():
            await asyncio.sleep(1)

            actually_playing = minigame_object.get_players()
            owner_of_physical_vehicle_at_start = None
            for player in actually_playing:
                if "Virtual" not in self._environment_mng.get_vehicle_by_player_id(player).get_vehicle_id():
                    owner_of_physical_vehicle_at_start = player
                    break

            await self.redirect_to_minigame_ui(*actually_playing)

            self.make_vehicles_drive_continuously(*actually_playing)

            while not minigame_task.done() and not minigame_task.cancelled():
                await asyncio.sleep(1)

            if minigame_task.cancelled():
                winner = None
            else:
                winner = await minigame_task

            winner = await minigame_task

            await self._sio.emit('minigame_winner',
                                 {'minigame': minigame_object.get_name(),
                                  'winner': winner,
                                  'owner_of_physical_vehicle_at_start': owner_of_physical_vehicle_at_start})

            await asyncio.sleep(5)
            await self.redirect_to_driver_ui(*actually_playing)

        asyncio.create_task(manage_players())

    async def redirect_to_minigame_ui(self, *players: str) -> None:
        """
        Redirects the specified players from the driver UI to the minigame UI.
        """
        for room in players:
            await self._sio.emit("redirect_to_minigame_ui", to=room)

    async def redirect_to_driver_ui(self, *players: str) -> None:
        """
        Redirects the specified players from the minigame UI to the driver UI.
        """
        data = {}
        for i, player in enumerate(players):
            data[f"player{i}"] = player
        await self._sio.emit("redirect_to_driver_ui", data=data)

    def make_vehicles_drive_continuously(self, *players: str) -> None:
        """
        Makes the vehicles of the given players drive at the same speed.
        """
        for player in players:
            vehicle = self._environment_mng.get_vehicle_by_player_id(player)
            if vehicle is None:
                logger.warning("Minigame_Manager.make_vehicles_drive_continuously: No vehicle was found for player %s. "
                               "Ignoring the request", player)
                continue
            vehicle_id = vehicle.get_vehicle_id()
            if vehicle_id is None:
                logger.warning("Minigame_Manager.make_vehicles_drive_continuously: \
                    No vehicle_id was found for vehicle %s of player %s. "
                               "Ignoring the request", vehicle.__str__(), player)
                continue
            self._behaviour_ctrl.request_speed_change_for(uuid=vehicle_id, value_perc=self._driving_speed_while_playing)
