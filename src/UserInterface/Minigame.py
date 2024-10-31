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

from EnvironmentManagement.EnvironmentManager import EnvironmentManager
from EnvironmentManagement.ConfigurationHandler import ConfigurationHandler

logger = logging.getLogger(__name__)


class Minigame:

    def __init__(self, sio: AsyncServer, name=__name__) -> None:
        self.minigame_ui_blueprint: Blueprint = Blueprint(name='minigameUI_bp', import_name='minigameUI_bp')
        self._sio: AsyncServer = sio

        async def home_minigame() -> str:
            """
            Load the minigame ui page.

            Gets the clients cookie for identification, provides GUI for minigames.

            Returns
            -------
                Returns a Response object representing a redirect to the minigame ui page.
            """
            player = request.cookies.get("player")
            if player is None:
                player = str(uuid.uuid4())

            return await render_template(template_name_or_list='minigame_index.html', player=player)
            
        self.minigame_ui_blueprint.add_url_rule('/', 'minigame', view_func=home_minigame)

        async def exit_minigame() -> str:
            player_id = request.args.get(key='player_id', type=str)
            reason = request.args.get(key='reason', default="The minigame has been cancelled.", type=str)

            return await render_template(template_name_or_list='driver_exit.html', player=player_id, message=reason)

        self.minigame_ui_blueprint.add_url_rule('/exit', 'exit_driver', view_func=exit_minigame)

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
            return

        @self._sio.on('disconnected')
        def handle_disconnected(sid, data):
            player = data["player"]
            logger.debug(f"Driver {player} disconnected!")
            self.__remove_player(player)
            return

        @self._sio.on('disconnect')
        def handle_clienet_disconnect(sid):
            logger.debug(f"Client {sid} disconnected.")
            return

    def update_driving_data(self, driving_data: dict) -> None:
        self.__run_async_task(self.__emit_driving_data(driving_data))
        return

    def get_blueprint(self) -> Blueprint:
        return self.minigame_ui_blueprint

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
                    logger.info(f'Player {player} timed out. Removing player from the game...')
                    self.__remove_player(player)

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
