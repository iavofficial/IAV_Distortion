from quart import Blueprint
import asyncio
from asyncio import Task
import random
import logging
import uuid

from socketio import AsyncServer
from typing import Callable

from EnvironmentManagement.ConfigurationHandler import ConfigurationHandler

from Minigames.Minigame import Minigame
from Minigames.Minigame_Test import Minigame_Test
from Minigames.Tapping_Contest_UI import Tapping_Contest_UI
from Minigames.Reaction_Contest_UI import Reaction_Contest_UI

logger = logging.getLogger(__name__)


class Minigame_Controller:

    instance: "Minigame_Controller" = None
    minigames: dict = {
        "Tapping_Contest": Tapping_Contest_UI,
        "Minigame_Test": Minigame_Test,
        "Reaction_Contest": Reaction_Contest_UI,
     }

    def __init__(self, sio: AsyncServer = None, minigame_ui_blueprint: Blueprint = None):
        """
        Behaves like a Singleton. If an instance has already been created, it will be returned.
        Otherwise the __init__ will be excecuted and the new instance returned

        Parameters:
        -----------
        minigame_ui_blueprint: Blueprint
            The blueprint of the minigame ui
        """
        if minigame_ui_blueprint is None:
            raise Exception("The minigame ui blueprint was not provided. Cancelling the Minigame_Controller.__init__.")
        if sio is None:
            raise Exception("No AsyncServer was provided. Cancelling the Minigame_Controller.__init__.")
        self._sio = sio
        self._config_handler: ConfigurationHandler = ConfigurationHandler()
        try:
            self._driving_speed_while_playing = \
                self._config_handler.get_configuration()['minigame']['driving_speed_while_playing']
        except KeyError:
            logger.warning("No valid value for minigame: driving_speed_while_playing in config_file. \
                Using default value of 30")
            self._driving_speed_while_playing = 30

        try:
            self.__driver_heartbeat_timeout: int = int(self._config_handler.get_configuration()["driver"]
                                                       ["driver_heartbeat_timeout_s"])
        except KeyError:
            logger.warning("No valid value for driver: driver_heartbeat_timeout in config_file. Using default "
                           "value of 30 seconds")
            self.__driver_heartbeat_timeout = 30

        self._minigame_uis: dict = {}
        self._available_minigames: list[str] = []
        self._minigame_instances: list[Minigame] = []
        for minigame in Minigame_Controller.minigames.keys():
            self._minigame_uis[minigame] = Minigame_Controller.minigames[minigame](sio=sio,
                                                                                   namespace=str(uuid.uuid4()),
                                                                                   blueprint=minigame_ui_blueprint)
            try:
                if self._config_handler.get_configuration()['minigame']['games'][minigame]:
                    self._available_minigames.append(minigame)
            except KeyError:
                logger.warning(f"No valid value for minigame: games: {minigame} in config_file. \
                    Using default value 0 ('not playable').")

        Minigame_Controller.instance = self

    def set_available_minigames(self, available_minigames: list[str]):
        self._available_minigames.clear()
        for minigame in available_minigames:
            if minigame in self._minigame_uis.keys():
                self._available_minigames.append(minigame)
            else:
                logger.warning(f"The given minigame {minigame} could not be added to the available minigames list \
                    because no instance of it exists.")
        print("New available minigame list:", self._available_minigames)

    def set_minigame_start_callback(self, callback: Callable[Task, Minigame]) -> None:
        """
        Set a callback function to be called when a new minigame has started.

        Parameters:
        -----------
        callback: callable
            Callback function
        """
        self._minigame_start_callback = callback

    def _execute_minigame_start_callback(self, minigame_task: Task, minigame_object: Minigame) -> None:
        """
        Execute the minigame start callback function with info about the minigame and the players.

        Parameters:
        -----------
        minigame_object: Minigame
            Object/Instance of the minigame that has just started
        """
        self._minigame_start_callback(minigame_task, minigame_object)

    @classmethod
    def get_instance(cls, sio: AsyncServer = None, minigame_ui_blueprint: Blueprint = None) -> "Minigame_Controller":
        if cls.instance is None:
            cls.instance = cls(sio=sio, minigame_ui_blueprint=minigame_ui_blueprint)
        return cls.instance

    def handle_player_removed(self, player_id: str) -> None:
        """
        Handle the removal of the specified player from all minigames they are currently associated with.
        The associated minigames are cancelled.

        Parameters:
        -----------
        player_id: str
            UUID of the player to be removed
        """
        minigame_instance: Minigame | None = self.get_minigame_instance_by_player_id(player_id)

        if minigame_instance is None:
            return

        minigame_instance.cancel()

    def get_minigame_name_list(self) -> list[str]:
        """
        Get a list of the names of all minigames

        Returns:
        --------
        list[str]
            list of names of minigames
        """
        return self._minigame_uis.keys()

    def get_description(self, minigame: str) -> str | None:
        """
        Returns the description of the specified minigame

        Parameters:
        -----------
        minigame: str
            The name of the minigame (class name) which's description is to be returned

        Returns:
        --------
        str: Description of the minigame as a String
        None: If the minigame could not be found None will be returned
        """
        minigame_object: Minigame = self._minigame_uis[minigame]
        if minigame_object is None:
            return None
        else:
            return minigame_object.description()

    def play_random_available_minigame(self, *players: str) -> tuple[asyncio.Task, Minigame] | tuple[None, None]:
        """
        Play a random available minigame with the specified players.

        Parameters:
        -----------
        *players : str
            IDs of the players that are supposed to play

        Returns:
        --------
        tuple[asyncio.Task, Minigame]: Task of the running game and object/instance of it. \
            Will return the winner's uuid once finished or None if cancelled
        tuple[None, None]: if the minigame could not be started for some reason
        """
        minigame = random.choice(self._available_minigames)

        return self._play_minigame(minigame, *players)

    def _play_minigame(self, minigame: str, *players: str) -> tuple[asyncio.Task, Minigame] | tuple[None, None]:
        """
        Create an asyncio of the minigame playing with the specified players.

        Parameters:
        -----------
        minigame: str
            Name of the minigame to play
        *players : str
            IDs of the players that are supposed to play

        Returns:
        --------
        tuple[asyncio.Task, Minigame]: Task of the running game and object/instance of it. \
            Will return the winner's uuid once finished or None if cancelled
        tuple[None, None]: if the minigame could not be started for some reason
        """
        players = list(set(players))
        for player in players:
            if self.get_minigame_instance_by_player_id(player) is not None:
                logger.warning(f"The player {player} is already participating in another minigame.\
                    A new minigame cannot be started with them.")
                return None, None

        minigame_instance: Minigame = Minigame_Controller.minigames[minigame](self._sio, str(uuid.uuid4()))
        self._minigame_instances.append(minigame_instance)

        if minigame_instance is None:
            logger.warning("The selected minigame does not exist.")
            return None, None

        if minigame not in self._available_minigames:
            logger.warning("The selected minigame is not currently available.")
            return None, None

        running_game_task: asyncio.Task = minigame_instance.play(*players)

        def minigame_done_callback(task) -> None:
            """
            Callback function to be executed once a minigame is done (completed or cancelled)

            Parameters:
            -----------
            minigame_object : Minigame
                The minigame object/instance that is done
            """
            self._minigame_instances.remove(minigame_instance)

        running_game_task.add_done_callback(minigame_done_callback)

        self._minigame_start_callback(running_game_task, minigame_instance)

        return running_game_task, minigame_instance

    def get_minigame_name_by_player_id(self, player_id: str) -> str | None:
        """
        Returns the name of the minigame that the specified player is currently associated with.

        Parameters:
        -----------
        player_id: str
            UUID of the player

        Returns:
        --------
        str: Name of the minigame the player is participating in
        None: If the player is not currently participating in any minigames
        """
        minigame_instance = self.get_minigame_instance_by_player_id(player_id)

        if minigame_instance is None:
            return None

        return minigame_instance.get_name()

    def get_minigame_instance_by_player_id(self, player_id: str) -> Minigame | None:
        """
        Returns the instance of the minigame the specified player is currently assigned to.

        Parameters:
        -----------
        player_id: str
            UUID of the player

        Returns:
        --------
        Minigame: Instance of the Minigame the player is participating in
        None: If the player is not currently participating in any minigame
        """
        if player_id is None:
            return None

        for minigame_instance in self._minigame_instances:
            if player_id in minigame_instance.get_players():
                return minigame_instance
        return None

    def set_player_ready(self, player_id: str) -> None:
        """
        The specified player has accepted the rules of the specified minigame.

        Parameters:
        -----------
        player : str
            UUID of the player
        minigame : str
            name of the minigame
        """

        minigame_instance = self.get_minigame_instance_by_player_id(player_id)
        if minigame_instance is None:
            logger.warning(f"MinigameController: The player {player_id} is not currently assigned to any minigame. \
                Ignoring the request of accepting minigame rules for this player.")
            return
        minigame_instance.set_player_ready(player_id)
        logger.info(f"PLAYER {player_id} is ready for minigame {minigame_instance.get_name()}")
