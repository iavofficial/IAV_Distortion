from quart import Blueprint, render_template, request
import uuid
import logging
import asyncio
import time

from socketio import AsyncServer
from abc import abstractmethod

class Minigame:

    def __init__(self, sio: AsyncServer, blueprint : Blueprint, name=__name__):
        self.minigame_ui_blueprint: Blueprint = blueprint
        self._sio: AsyncServer = sio
        if "." in name:
            name = name.split(".")[-1]

        async def home_minigame() -> str:
            """
            Load this minigame's ui page.

            Gets the clients cookie for identification, provides GUI for minigame.

            Returns
            -------
                Returns a Response object representing a redirect to the minigame ui page.
            """
            player = request.cookies.get("player")
            if player is None:
                player = str(uuid.uuid4())

            return await render_template(template_name_or_list=name + '.html', player = player)
            
        self.minigame_ui_blueprint.add_url_rule(f'/{name}', name, view_func=home_minigame)

    @abstractmethod
    async def play(player1 : str, player2 : str = None) -> str:
        """
        Starts the minigame with the given player ids. When done returns the winner of the game.

        Parameters
        ----------
        player1: The ID of the first player
        player2: The ID of the second player. None if the the second player should be a bot

        Returns
        ----------
        ID of the victor
        """

    @abstractmethod
    def cancel() -> None:
        """
        Immediately Cancels the game without winner or loser.
        """

    @abstractmethod
    def description() -> str:
        """
        Returns a very short description of the game / how to play it.
        """
