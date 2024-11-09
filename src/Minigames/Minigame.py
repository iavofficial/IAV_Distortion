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
        self.name = name
        if "." in name:
            self.name = name.split(".")[-1]
        self._players : list[str] = []

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

            return await render_template(template_name_or_list=self.name + '.html', player = player)
            
        self.minigame_ui_blueprint.add_url_rule(f'/{self.name}', self.name, view_func=home_minigame)

    @abstractmethod
    async def play(self, *players : str) -> str:
        """
        Starts the minigame with the given player ids. When done returns the winner of the game.
        Should redirect the players from the driver UI to the minigame UI and back to the driver UI once the minigame is finished.
        If more players are required for the minigame than are given, the rest will be replaced by bots.
        If less players are required for the minigame than are given, only the first will be picked.

        Parameters
        ----------
        *players: The ID of the first player

        Returns
        ----------
        ID of the victor
        """

    @abstractmethod
    def cancel(self) -> None:
        """
        Immediately Cancels the game without winner or loser.
        """

    @abstractmethod
    def description(self) -> str:
        """
        Returns a very short description of the game / how to play it.
        """

    @abstractmethod
    def get_players(self) -> list[str]:
        """
        Returns a list of the IDs of the players that were selected for this minigame
        """