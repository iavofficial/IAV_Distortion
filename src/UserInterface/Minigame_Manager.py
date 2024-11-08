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

from EnvironmentManagement.ConfigurationHandler import ConfigurationHandler

from Minigames.Minigame import Minigame
from Minigames.Minigame_Test import Minigame_Test

logger = logging.getLogger(__name__)

minigames = {"Minigame_Test" : Minigame_Test}


class Minigame_Manager:

    def __init__(self, sio: AsyncServer, name=__name__) -> None:
        self.minigame_ui_blueprint: Blueprint = Blueprint(name='minigameUI_bp', import_name='minigameUI_bp')
        self._sio: AsyncServer = sio
        self.config_handler: ConfigurationHandler = ConfigurationHandler()
        self._connected_players = []
        
    
        try:
            self.__driver_heartbeat_timeout: int = int(self.config_handler.get_configuration()["driver"]
                                                       ["driver_heartbeat_timeout_s"])
        except KeyError:
            logger.warning("No valid value for driver: driver_heartbeat_timeout in config_file. Using default "
                           "value of 30 seconds")
            self.__driver_heartbeat_timeout = 30

        self.minigame_objects : dict = {}
        for minigame in minigames.keys():
            self.minigame_objects[minigame] = minigames[minigame](self._sio, self.minigame_ui_blueprint)

        async def home_minigame() -> str:
            player = request.cookies.get("player")
            if player is None:
                #TODO In this case, a player has connected to the minigame page without having connected as a driver before. They should probably notified that they need to drive first.
                return

            return await render_template(template_name_or_list='minigame_index.html', player=player, minigame = minigame, heartbeat_interval = self.__driver_heartbeat_timeout)
        
        self.minigame_ui_blueprint.add_url_rule('/', 'minigame', view_func = home_minigame)

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
            logger.debug(f"Driver {player} connected to the minigame.")
            print(data.keys())
            asyncio.create_task(self.send_description(data["minigame"]))
            return

        @self._sio.on('minigame_disconnected')
        def handle_disconnected(sid, data):
            player = data["player"]
            logger.debug(f"Driver {player} disconnected from the minigame!")
            self.__remove_player(player)
            return

        @self._sio.on('minigame_disconnect')
        def handle_clienet_disconnect(sid):
            logger.debug(f"Client {sid} disconnected from the minigame.")
            return

        Minigame_Manager.instance = self

    def getInstance() -> "Minigame_Manager":
        return Minigame_Manager.instance

    def get_blueprint(self) -> Blueprint:
        return self.minigame_ui_blueprint

    def __run_async_task(self, task):
        """
        Run a asyncio awaitable task
        task: awaitable task
        """
        asyncio.create_task(task)
        # TODO: Log error, if the coroutine doesn't end successfully

    def __remove_player(self, player: str) -> None:
        """
        Remove player from the minigame.

        Parameters
        ----------
        player: str
            ID of player to be removed.
        """
        self._connected_players.remove(player)
        return

    def get_minigame_object(self, minigame : str) -> Minigame:
        """
        Get the object/instance of the specified minigame

        Parameters:
        -----------
        minigame: str
            Name of the minigame (class name)
        """
        return self.minigame_objects.get(minigame)

    async def send_description(self, minigame : str):
        """
        Sends the description of the specified minigame via socketio
        
        Parameters:
        -----------
        minigame: str
            The name of the minigame (class name) which's description is to be sent
        """
        minigame_object : Minigame = self.get_minigame_object(minigame)
        if minigame_object is None:
            description = "This minigame could not be found."
        else:
            description = minigame_object.description()
        await self._sio.emit("send_description", {"minigame": minigame, "description": description})