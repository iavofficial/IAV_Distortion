# Copyright 2024 IAV GmbH
#
# This file is part of the IAV-Distortion project an interactive
# and educational showcase designed to demonstrate the need
# of automotive cybersecurity in a playful, engaging manner.
# and is released under the "Apache 2.0". Please see the LICENSE
# file that should have been included as part of this package.
#

from quart import Blueprint, render_template, request, Quart
import uuid
import logging
import asyncio
import time

from socketio import AsyncServer

from EnvironmentManagement.EnvironmentManager import EnvironmentManager
from EnvironmentManagement.ConfigurationHandler import ConfigurationHandler

from Minigames import Minigame_Test

logger = logging.getLogger(__name__)

minigames = {"Minigame_Test" : Minigame_Test.Minigame_Test}


class Minigame_Manager:

    def __init__(self, sio: AsyncServer, quart_app : Quart, name=__name__) -> None:
        self.minigame_ui_blueprint: Blueprint = Blueprint(name='minigameUI_bp', import_name='minigameUI_bp')
        self._sio: AsyncServer = sio
        self.quart_app = quart_app
        self._connected_players = []


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

    def set_minigame(self, minigame : str) -> None:
        """
        Set the Minigame that is to be played next with this Manager.

        Parameters
        ----------
        minigame: str
            Name of the minigame (class name)
        """
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
                #TODO In this case, a player has connected to the minigame page without having connected as a driver before. They should probably notified that they need to drive first.
                return

            return await render_template(template_name_or_list='minigame_index.html', player=player, minigame = minigame)
        
        self.minigame_ui_blueprint.add_url_rule('/', 'minigame', view_func = home_minigame)
        minigame_object = minigames[minigame](self._sio, self.minigame_ui_blueprint)

        self.quart_app.register_blueprint(self.minigame_ui_blueprint, url_prefix = "/minigame")