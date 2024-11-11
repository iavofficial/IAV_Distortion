from quart import Blueprint
import asyncio
from asyncio import Task
import random

from socketio import AsyncServer
from typing import Callable

from EnvironmentManagement.ConfigurationHandler import ConfigurationHandler

from Minigames.Minigame import Minigame
from Minigames.Minigame_Test import Minigame_Test

class Minigame_Controller:

    instance : "Minigame_Controller" = None
    minigames : dict = {"Minigame_Test" : Minigame_Test}

    def __init__(self, sio: AsyncServer = None, minigame_ui_blueprint : Blueprint = None):
        """
        Behaves like a Singleton. If an instance has already been created, it will be returned. Otherwise the __init__ will be excecuted and the new instance returned

        Parameters:
        -----------
        minigame_ui_blueprint: Blueprint
            The blueprint of the minigame ui
        """
        if minigame_ui_blueprint is None:
            raise Exception("The minigame ui blueprint was not provided. Cancelling the Minigame_Controller.__init__.")
        if sio is None:
            raise Exception("No AsyncServer was provided. Cancelling the Minigame_Controller.__init__.")
        
        self._config_handler: ConfigurationHandler = ConfigurationHandler()
        try:
            self._driving_speed_while_playing = self._config_handler.get_configuration()['minigame']['driving_speed_while_playing']
        except KeyError:
            logger.warning("No valid value for minigame: driving_speed_while_playing in config_file. Using default value of 30")
            self._driving_speed_while_playing = 30
    
        try:
            self.__driver_heartbeat_timeout: int = int(self._config_handler.get_configuration()["driver"]
                                                       ["driver_heartbeat_timeout_s"])
        except KeyError:
            logger.warning("No valid value for driver: driver_heartbeat_timeout in config_file. Using default "
                           "value of 30 seconds")
            self.__driver_heartbeat_timeout = 30

        self._minigame_objects : dict = {}
        self._available_minigames : list[str] = []
        for minigame in Minigame_Controller.minigames.keys():
            self._minigame_objects[minigame] = Minigame_Controller.minigames[minigame](sio, minigame_ui_blueprint)
            self._available_minigames.append(minigame)

        Minigame_Controller.instance = self

    def set_minigame_start_callback(self, callback : Callable[Task, Minigame]) -> None:
        """
        Set a callback function to be called when a new minigame has started.

        Parameters:
        -----------
        callback: callable
            Callback function
        """
        self._minigame_start_callback = callback

    def _execute_minigame_start_callback(self, minigame_task : Task, minigame_object : Minigame) -> None:
        """
        Execute the minigame start callback function with info about the minigame and the players.

        Parameters:
        -----------
        minigame_object: Minigame
            Object/Instance of the minigame that has just started
        """
        self._minigame_start_callback(minigame_task, minigame_object)

    def get_instance(sio: AsyncServer = None, minigame_ui_blueprint : Blueprint = None) -> "Minigame_Controller":
        if Minigame_Controller.instance is None:
            Minigame_Controller.instance = Minigame_Controller(sio = sio, minigame_ui_blueprint = minigame_ui_blueprint)
        return Minigame_Controller.instance

    def handle_player_removed(self, player_id : str) -> None:
        """
        Handle the removal of the specified player from all minigames they are currently associated with.
        The associated minigames are cancelled.

        Parameters:
        -----------
        player_id: str
            UUID of the player to be removed
        """
        for minigame_object in self._minigame_objects.values():
            if player_id in minigame_object.get_players():
                minigame_object.cancel()

    def get_minigame_object(self, minigame : str) -> Minigame:
        """
        Get the object/instance of the specified minigame

        Parameters:
        -----------
        minigame: str
            Name of the minigame (class name)
        """
        return self._minigame_objects.get(minigame)

    def get_minigame_name_list(self) -> list[str]:
        """
        Get a list of the names of all minigames

        Returns:
        --------
        list[str]
            list of names of minigames
        """
        return self._minigame_objects.keys()

    def get_description(self, minigame : str) -> str | None:
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
        minigame_object : Minigame = self.get_minigame_object(minigame)
        if minigame_object is None:
            return None
        else:
            return minigame_object.description()

    def play_random_available_minigame(self, *players : str):
        """
        Play a random available minigame with the specified players. 

        Parameters:
        -----------
        *players : str
            IDs of the players that are supposed to play
        
        Returns:
        --------
        (asyncio.Task, Minigame): Task of the running game and object/instance of it. Will return the winner's uuid once finished or None if cancelled
        None: if the minigame could not be started for some reason
        """
        if len(self._available_minigames) == 0:
            raise Exception("No minigame is currently available.")
        minigame = random.choice(self._available_minigames)

        return self._play_minigame(minigame, *players)

    def _play_minigame(self, minigame : str, *players : str):
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
        (asyncio.Task, Minigame): Task of the running game and object/instance of it. Will return the winner's uuid once finished or None if cancelled
        None: if the minigame could not be started for some reason
        """
        minigame_object : Minigame = self._minigame_objects.get(minigame)

        if minigame_object is None:
            logger.warning("The selected minigame does not exist.")
            return None

        if minigame not in self._available_minigames:
            logger.warning("The selected minigame is not currently available.") 
            return None

        self._available_minigames.remove(minigame)

        running_game_task : asyncio.Task = asyncio.create_task(minigame_object.play(*players))
        running_game_task.add_done_callback(self._minigame_done_callback(minigame_object))

        self._minigame_start_callback(running_game_task, minigame_object)

        return running_game_task, minigame_object

    def _minigame_done_callback(self, minigame_object : Minigame) -> None:
        """
        Callback function to be executed once a minigame is done (completed or cancelled)

        Parameters:
        -----------
        minigame_object : Minigame
            The minigame object/instance that is done
        """
        self._available_minigames.append(minigame_object.get_name())

    def get_minigame_name_by_player_id(self, player_id : str) -> str | None:
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
        if player_id is None:
            return None

        for minigame_object in self._minigame_objects.values():
            if player_id in minigame_object.get_players():
                return minigame_object.get_name()
        return None