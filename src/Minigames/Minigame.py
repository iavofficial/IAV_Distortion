from quart import Blueprint, render_template, request
import uuid
import asyncio
import logging

from socketio import AsyncServer
from abc import abstractmethod

from EnvironmentManagement.ConfigurationHandler import ConfigurationHandler

logger = logging.getLogger(__name__)


class Minigame:

    def __init__(self, sio: AsyncServer, blueprint: Blueprint | None = None, name=__name__):
        self._sio: AsyncServer = sio
        self._name = name
        if "." in name:
            self._name = name.split(".")[-1]
        if "_UI" in name:
            self._name = self._name.removesuffix("_UI")
        self._players: list[str] = []
        self._ready_players: list[str] = []
        self._task = None
        self._started = False
        self._config_handler = ConfigurationHandler()
        try:
            self._rule_acceptance_timeout = \
                int(self._config_handler.get_configuration()['minigame']['rule_acceptance_timeout'])
        except Exception:
            logger.warning("No valid value for minigame: rule_acceptance_timeout in config_file. \
            Using default value of 20")
            self._rule_acceptance_timeout = 20

        if blueprint is None:
            return

        self.minigame_lobby_ui_blueprint: Blueprint = blueprint

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

            return await render_template(template_name_or_list=self._name + '.html', player=player)

        self.minigame_lobby_ui_blueprint.add_url_rule(f'/{self._name}', self._name, view_func=home_minigame)

    def play(self, *players: str) -> asyncio.Task:
        """
        Starts the task of playing the minigame

        Parameters
        ----------
        *players: The ID of the first player

        Returns
        ----------
        ID of the victor
        """
        self._started = False
        asyncio.create_task(self._check_rule_acceptance_timeout())

        async def play_after_all_players_ready() -> str:
            actually_playing = self.set_players(*players)

            # Check if all players have accepted the rules
            all_ready = False
            while not all_ready:
                all_ready = True
                for player in actually_playing:
                    if player not in self._ready_players:
                        all_ready = False
                if all_ready:
                    self._started = True
                    player_data = {}
                    for i, player in enumerate(actually_playing):
                        player_data['player' + str(i)] = player
                    for i in range(3, -1, -1):
                        data = player_data.copy()
                        data['countdown'] = i
                        data['minigame'] = self._name
                        await self._sio.emit('all_ready', data)
                        if i > 0:
                            await asyncio.sleep(1)
                    break
                else:
                    await asyncio.sleep(.1)
            return await self._play()

        self._task = asyncio.create_task(play_after_all_players_ready())
        return self._task

    @abstractmethod
    async def _play(self) -> str:
        """
        Starts the minigame. When done returns the winner of the game.
        Should redirect the players from the driver UI to the minigame UI and
        back to the driver UI once the minigame is finished.

        Parameters
        ----------
        *players: The ID of the first player

        Returns
        ----------
        ID of the victor
        """

    @abstractmethod
    def set_players(self, *players: str) -> list[str]:
        """
        Sets the specified players as players associated with this game.
        If more players are required for the minigame than are given, the rest will be replaced by bots.
        If less players are required for the minigame than are given, only the first will be picked.

        Parameters:
        -----------
        *players: str
            UUIDs of the players

        Returns:
        --------
        list[str]: UUIDs of the players that have been accepted into the minigame
        """
        self._ready_players.clear()
        self._players.clear()

    def set_player_ready(self, player: str) -> None:
        """
        Appends the specified player to the ready players list.

        Parameters:
        -----------
        player: str
            UUID of the player
        """
        if player not in self.get_players():
            print(f"Minigame: The player {player} is not associated with the minigame {self.get_name()}. \
                Ignoring the request of accepting its rules.")
            return
        self._ready_players.append(player)

    def cancel(self) -> None:
        """
        Immediately Cancels the game without winner or loser.
        """
        print("MINIGAQME CANCELLED")
        self._players.clear()
        self._ready_players.clear()
        self._task.cancel()

    @abstractmethod
    def description(self) -> str:
        """
        Returns a very short description of the game / how to play it.
        """

    def get_players(self) -> list[str]:
        """
        Returns a list of the IDs of the players that were selected for this minigame
        """
        return self._players.copy()

    def get_name(self) -> str:
        return self._name

    async def _check_rule_acceptance_timeout(self) -> None:
        """
        Checks if the minigame has started after the rule acceptance timeout delay.
        Cancels minigame if the rules have not been accepted.
        """
        await asyncio.sleep(self._rule_acceptance_timeout)
        if self._started:
            # Minigame has already started -> rules have been accepted by everyone
            return

        self.cancel()
