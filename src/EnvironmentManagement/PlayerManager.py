import logging
import re
import asyncio

from datetime import datetime, timedelta

from collections import deque
from typing import Any

from .ConfigurationHandler import ConfigurationHandler
from .VehicleManager import VehicleManager
from .EnvironmentManager import RemovalReason

from DataModel.Vehicle import Vehicle

logger = logging.getLogger(__name__)


class PlayerManager:
    def __init__(self,
                 vehhicle_manager: VehicleManager,
                 configuration_handler: ConfigurationHandler = ConfigurationHandler()) -> None:

        self.__config_handler:  ConfigurationHandler = configuration_handler
        self._vehicle_mng: VehicleManager = vehhicle_manager
        self._vehicle_mng.subscribe_on_added_vehicle(self.assign_players_to_vehicles)
        self._vehicle_mng.subscribe_on_removed_vehicle(self.handle_released_player)

        self.__player_queue_list: deque[str] = deque()
        self.__playing_time_checking_flag: bool = False
        self._remove_player_tasks: dict[str, asyncio.Task[Any]] = {}

        return

    def get_player_count(self) -> int:
        return len(self.__player_queue_list)

    def get_next_player(self) -> str:
        return self.__player_queue_list.popleft()

    def get_all_waiting_players(self) -> list[str]:
        """
        Gets a list of all player that are waiting for a vehicle
        """
        tmp: list[str] = []
        for p in self.__player_queue_list:
            tmp.append(p)
        return tmp

    def add_player_to_queue(self, player_id: str) -> bool:
        """
        Add a player to the waiting queue.

        Parameters
        ----------
        player_id: str
            ID of player to be added to the queue if appropriate.

        Returns
        -------
        bool
            Is true, if the player was added to the queue.
            Is False, if player was not added to the queue, because it is already in the queue or empty or no string.
        """
        if not isinstance(player_id, str) or player_id == "":
            return False

        striped_player_id = player_id.strip()
        if not striped_player_id or re.fullmatch(r'\W+', striped_player_id):
            return False

        for vehicle in self._vehicle_mng.get_controlled_vehicles():
            if vehicle.get_player_id() == striped_player_id:
                self.__cancel_remove_player_task(striped_player_id)
                return False
        if striped_player_id not in self.__player_queue_list:
            self.__player_queue_list.append(striped_player_id)

        return True

    def handle_released_player(self, vehicle_id: str, player_id: str | None, reason: RemovalReason) -> bool:
        if player_id is not None:
            return self.add_player_to_queue(player_id)
        else:
            return False

    def remove_player_from_queue(self, player_id: str) -> bool:
        """
        Remove a player from the waiting queue

        Returns
        -------
        bool
            is True, if player was removed from queue
            is False, if player could not be removed
        """
        if player_id in self.__player_queue_list:
            self.__player_queue_list.remove(player_id)
            return True
        else:
            return False

    def assign_players_to_vehicles(self, vehicle_id: str = "") -> bool:
        """
        Assigns as many waiting players to vehicles as possible

        Returns
        -------
        bool
            Is true, if a player could be assigned to a free vehicle.
            Is False, if no player could be assigned to a free vehicle.
        """
        if self.get_player_count() == 0:
            return False

        assigned_any_player: bool = False
        free_vehicle: Vehicle | None
        if vehicle_id == "":
            free_vehicle = self._vehicle_mng.get_next_free_vehicle()
        else:
            free_vehicle = self._vehicle_mng.get_vehicle_by_vehicle_id(vehicle_id)

        if free_vehicle is None:
            return False
        else:
            next_player = self.get_next_player()
            # self._publish_player_active(next_player)
            free_vehicle.set_player(next_player)
            assigned_any_player = True

            timeout_interval = int(self.__config_handler.get_configuration()["game_config"]
                                   ["game_cfg_playing_time_limit_min"])
            if self.__playing_time_checking_flag is False and timeout_interval != 0:
                logger.debug('Playtime checker is activated.')
                self.start_playing_time_checker()
            else:
                logger.debug('Playtime checker is not needed.')

            return assigned_any_player

    def start_playing_time_checker(self) -> bool:
        """
        starts the play time checker for all player, if not started yet

        Returns
        -------
        bool
            is True, if no play time checker has been started yet.
            is False, if a play time checker has been already been started.
        """
        if not self.__playing_time_checking_flag:
            asyncio.create_task(self.__check_playing_time_is_up())
            self.__playing_time_checking_flag = True
            return True
        else:
            return False

    def stop_running_playing_time_checker(self) -> bool:
        """
        stops the play time checker for all player, before the next execution

        Returns
        -------
        bool
            is always True
            is never False
        """
        self.__playing_time_checking_flag = False
        return True

    async def __check_playing_time_is_up(self) -> None:
        """
        Continuously checks playing time of each active player and
        removes player from vehicle as soon as the playing time is up
        """
        while self.__playing_time_checking_flag:
            await asyncio.sleep(10)

            timeout_interval = int(self.__config_handler.get_configuration()["game_config"]
                                   ["game_cfg_playing_time_limit_min"])

            controlled_vehicles: list[Vehicle] = self._vehicle_mng.get_controlled_vehicles()
            if len(controlled_vehicles) == 0:
                return
            else:
                for vehicle in controlled_vehicles:
                    if vehicle.game_start is None:
                        logger.error("A player without game start time exists")
                        return
                    time_difference: timedelta = datetime.now() - vehicle.game_start
                    if time_difference >= timedelta(minutes=timeout_interval):
                        logger.debug(f'playtime of {time_difference} for player {vehicle.player} is over')
                        if vehicle.player is None:
                            return
                        self.manage_removal_from_game_for(vehicle.player,
                                                          RemovalReason.PLAYING_TIME_IS_UP)

        logger.debug('Playtime checker is deactivated.')
        return

    def manage_removal_from_game_for(self,
                                     player_id: str,
                                     reason: RemovalReason = RemovalReason.NONE) -> bool:
        """
        This function organizes the deletion of the player ID, if necessary, from the waiting list
        or a vehicle object and triggers the deletion event.

        Parameters
        ----------
        player_id: str
            ID of player to update queue with.
        reason: RemovalReason
            This enum encodes the reason for deletion

        Returns
        -------
        bool
            is True, if player was removed from queue or vehicle
            is False, if player could not be removed
        """
        player_was_removed = (self.remove_player_from_queue(player_id) or
                              self._vehicle_mng.remove_player_from_vehicle(player_id))

        if player_was_removed:
            # self._publish_removed_player(player_id, reason)
            # self.update_staff_ui()
            self.assign_players_to_vehicles()
            return True
        else:
            return False

    def schedule_remove_player_task(self, player: str, grace_period: int = 5) -> None:
        """
        Schedules asynchronous task to remove player, only if no removal task exists for this player already.

        Parameters
        ----------
        player: str
            ID of player to be removed.
        grace_period: int
            Time to wait in seconds until player is removed, in case of reconnect.
        """
        if player not in self._remove_player_tasks:
            logger.debug(f'Scheduling player removal task for player: {player}')
            self._remove_player_tasks[player] = asyncio.create_task(self.__remove_player_after_grace_period
                                                                    (player, grace_period))
        else:
            logger.debug(f'Player removal task already scheduled for {player}')
        return

    def __cancel_remove_player_task(self, player: str) -> None:
        """
        Cancels remove_player_task.

        Parameters
        ----------
        player: str
            ID of player for which a potential existing remove_player_task shall be canceled.

        """
        if player in self._remove_player_tasks.keys():
            self._remove_player_tasks[player].cancel()
            del self._remove_player_tasks[player]
        return

    async def __remove_player_after_grace_period(self, player: str, grace_period: int = 5) -> None:
        """
        Wait for grace period then removes player.

        Parameters
        ----------
        player: str
            ID of player to be removed.
        grace_period: int
            Time to wait in seconds until player is removed, in case of reconnect.
        """
        try:
            await asyncio.sleep(grace_period)
            self.manage_removal_from_game_for(player_id=player,
                                              reason=RemovalReason.PLAYER_NOT_REACHABLE)
        except asyncio.CancelledError:
            logger.debug(f"Player {player} reconnected. Removing player aborted.")
        return
