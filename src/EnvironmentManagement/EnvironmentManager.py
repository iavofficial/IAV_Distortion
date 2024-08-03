# Copyright 2024 IAV GmbH
#
# This file is part of the IAV-Distortion project an interactive
# and educational showcase designed to demonstrate the need
# of automotive cybersecurity in a playful, engaging manner.
# and is released under the "Apache 2.0". Please see the LICENSE
# file that should have been included as part of this package.
#
import logging
import asyncio
import re

from enum import Enum
from datetime import datetime, timedelta
from typing import List, Dict, Callable
from collections import deque
from deprecated import deprecated

from DataModel.PhysicalCar import PhysicalCar
from DataModel.Vehicle import Vehicle
from DataModel.VirtualCar import VirtualCar

from EnvironmentManagement.ConfigurationHandler import ConfigurationHandler

from VehicleManagement.AnkiController import AnkiController
from VehicleManagement.EmptyController import EmptyController
from VehicleManagement.FleetController import FleetController

from LocationService.LocationService import LocationService
from LocationService.TrackPieces import TrackBuilder, FullTrack
from LocationService.Track import TrackPieceType


class RemovalReason(Enum):
    NONE = 0
    PLAYING_TIME_IS_UP = 1
    NOT_REACHABLE = 2


class EnvironmentManager:

    def __init__(self, fleet_ctrl: FleetController,
                 configuration_handler: ConfigurationHandler = ConfigurationHandler()):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        console_handler = logging.StreamHandler()
        self.logger.addHandler(console_handler)

        self._fleet_ctrl = fleet_ctrl

        self._player_queue_list: deque[str] = deque()
        self._active_anki_cars: List[Vehicle] = []

        self.__update_staff_ui_callback: Callable[[Dict[str, str], List[str], List[str]], None] | None = None
        self.__publish_removed_player_callback: Callable[[str], None] | None = None
        self.__publish_player_active_callback: Callable[[str], None] | None = None

        # number used for naming virtual vehicles
        self._virtual_vehicle_num: int = 1

        self._remove_player_tasks: dict = {}

        self.__playing_time_checking_flag: bool = False
        self.config_handler: ConfigurationHandler = configuration_handler

        self._fleet_ctrl.set_add_anki_car_callback(self.connect_to_physical_car_by)

    # set Callbacks
    def set_staff_ui_update_callback(self,
                                     function_name: Callable[[Dict[str, str],
                                                              List[str],
                                                              List[str]],
                                                             None]) -> None:
        """
        Sets callback function for staff_ui_update.

        Parameters
        ----------
        function_name: Callable[[Dict[str, str], List[str], List[str]], None]
            Callback function that takes three parameters:
            1. A dictionary where keys and values are strings.
            2. A list of strings.
            3. Another list of strings.
            The function should not return anything (None).
        """
        self.__update_staff_ui_callback = function_name
        return

    def set_publish_removed_player_callback(self, function_name: Callable[[str], None]) -> None:
        """
        Sets callback function for publish_removed_player.

        Parameters
        ----------
        function_name: Callable[[str], None]
            Callback function that takes a string parameter.
        """
        self.__publish_removed_player_callback = function_name
        return

    def set_publish_player_active_callback(self, function_name: Callable[[str], None]) -> None:
        """
        Sets callback function for publish_player_active.

        Parameters
        ----------
        function_name: Callable[[str], None]
            Callback function that takes a string parameter.
        """
        self.__publish_player_active_callback = function_name
        return

    # Publish interface
    def update_staff_ui(self) -> None:
        """
        Sends an update of controlled cars, free cars and waiting players to the staff ui using a callback function.
        """
        if not callable(self.__update_staff_ui_callback):
            self.logger.critical('Missing update_staff_ui_callback!')
        else:
            self.__update_staff_ui_callback(self.get_mapped_cars(), self.get_free_car_list(),
                                            self.get_waiting_player_list())
        return

    def _publish_removed_player(self, player_id: str, reason: RemovalReason = RemovalReason.NONE) -> bool:
        """
        Sends which player has been removed from the game to the staff ui using a callback function.

        Parameters
        ----------
        player_id: str
            ID of player to update queue with.
        reason: RemovalReason
            This enum encodes the reason for deletion

        Returns
        -------
        bool
            is True if player was removed from queue or vehicle
            is False if player could not be removed
        """

        if not isinstance(reason, RemovalReason):
            return False

        message: str = ""
        if reason is RemovalReason.NONE:
            message = "Your player has been removed from the game."
        elif reason is RemovalReason.NOT_REACHABLE:
            message = "Your player was removed from the game, because you were no longer reachable."
        elif reason is RemovalReason.PLAYING_TIME_IS_UP:
            message = "Your player was removed from the game, because your playing time is over."

        if not callable(self.__publish_removed_player_callback):
            self.logger.critical('Missing publish_removed_player_callback!')
            return False
        else:
            self.__publish_removed_player_callback(player=player_id, reason=message)
            return True

    def _publish_player_active(self, player: str) -> None:
        """
        Sends which player changed from waiting in the queue to be an active player in the game.

        Parameters
        ----------
        player: str
            ID of player who became active.
        """
        if not callable(self.__publish_player_active_callback):
            self.logger.critical('Missing publish_player_active_callback!')
        else:
            self.__publish_player_active_callback(player)
        return

    # Player management
    def _add_player_to_queue(self, player_id: str) -> bool:
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
        if not isinstance(player_id, str) :
            return False

        striped_player_id = player_id.strip()
        if not striped_player_id or re.fullmatch(r'\W+', striped_player_id):
            return False

        if striped_player_id in self._player_queue_list:
            return False
        else:
            self._player_queue_list.append(striped_player_id)
            self.update_staff_ui()
            return True

    def _add_new_player(self, player_id: str) -> bool:
        """
        Adds a player to the queue, if it's appropriate.

        Player is added to the queue if the player isn't controlling a vehicle already and the player also isn't in the
        queue already.
        If player is already in the queue or assigned to a vehicle a potential task to remove the player is canceled.

        Parameters
        ----------
        player_id: str
            ID of player to be added to the queue if appropriate.
        """
        for v in self._active_anki_cars:
            if v.get_player_id() == player_id:
                self.__cancel_remove_player_task(player_id)
                return False
        for p in self._player_queue_list:
            if p == player_id:
                self.__cancel_remove_player_task(player_id)
                return False

        result = self._add_player_to_queue(player_id)
        return result

    def put_player_on_next_free_spot(self, player_id: str) -> bool:
        """
        Updates the player queue and
        if applicable, allows players in the queue to move up or get a free vehicle.

        Parameters
        ----------
        player_id: str
            ID of player to update queue with.

        Returns
        -------
        bool
            Is true, if a player could be assigned to a free vehicle.
            Is False, if no player could be assigned to a free vehicle.
        """
        _ = self._add_new_player(player_id)
        result = self._assign_players_to_vehicles()
        self.update_staff_ui()
        return result

    def _assign_players_to_vehicles(self) -> bool:
        """
        Assigns as many waiting players to vehicles as possible

        Returns
        -------
        bool
            Is true, if a player could be assigned to a free vehicle.
            Is False, if no player could be assigned to a free vehicle.
        """
        for vehicle in self._active_anki_cars:
            if vehicle.is_free():
                if len(self._player_queue_list) == 0:
                    self.update_staff_ui()
                    return False
                else:
                    next_player = self._player_queue_list.popleft()
                    self._publish_player_active(player=next_player)

                    vehicle.set_player(next_player)

                    timeout_interval = int(self.config_handler.get_configuration()["game_config"]
                                           ["game_cfg_playing_time_limit_min"])
                    if self.__playing_time_checking_flag is False and timeout_interval != 0:
                        self.logger.debug('Playtime checker is activated.')
                        self.start_playing_time_checker()
                    else:
                        self.logger.debug('Playtime checker is not needed.')
                    self.update_staff_ui()
                    return True
        return False

    def _manage_removal_from_game_for(self, player_id: str, reason: RemovalReason) -> bool:
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
        player_was_removed = (self._remove_player_from_waitlist(player_id) or
                              self._remove_player_from_vehicle(player_id))

        if player_was_removed:
            self._publish_removed_player(player_id=player_id, reason=reason)
            self.update_staff_ui()
            return True
        else:
            return False

    def _remove_player_from_waitlist(self, player_id: str) -> bool:
        """
        Remove a player from the waiting queue

        Returns
        -------
        bool
            is True, if player was removed from queue
            is False, if player could not be removed
        """
        if player_id in self._player_queue_list:
            self._player_queue_list.remove(player_id)
            return True
        else:
            return False

    def _remove_player_from_vehicle(self, player_id: str) -> bool:
        """
        removes a player from the vehicle they are controlling

        Returns
        -------
        bool
            is True, if player was removed from vehicle
            is False, if player could not be removed
        """
        for v in self._active_anki_cars:
            if v.get_player_id() == player_id:
                self.logger.info(f"Removing player with UUID {player_id} from vehicle")
                v.remove_player()
                self._assign_players_to_vehicles()
                return True
        return False

    def get_waiting_player_list(self) -> List[str]:
        """
        Gets a list of all player that are waiting for a vehicle
        """
        tmp = []
        for p in self._player_queue_list:
            tmp.append(p)
        return tmp

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

            timeout_interval = int(self.config_handler.get_configuration()["game_config"]
                                   ["game_cfg_playing_time_limit_min"])

            active_players = [v for v in self._active_anki_cars if v.player is not None]
            for player in active_players:
                time_difference: timedelta = datetime.now() - player.game_start
                if time_difference >= timedelta(minutes=timeout_interval):
                    self.logger.debug(f'playtime of {time_difference} for player {player.player} is over')
                    self._manage_removal_from_game_for(player_id=player.player,
                                                       reason=RemovalReason.PLAYING_TIME_IS_UP)

        self.logger.debug('Playtime checker is deactivated.')

    # player removal
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
            self.logger.debug(f'Scheduling player removal task for player: {player}')
            self._remove_player_tasks[player] = asyncio.create_task(self.__remove_player_after_grace_period
                                                                    (player, grace_period))
        else:
            self.logger.debug(f'Player removal task already scheduled for {player}')
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
            self._manage_removal_from_game_for(player_id=player,
                                               reason=RemovalReason.NOT_REACHABLE)
        except asyncio.CancelledError:
            logging.debug(f"Player {player} reconnected. Removing player aborted.")
        return

    # Vehicle Management
    @deprecated(reason="Diese Methode ist veraltet."
                       "Bitte verwende 'find_unpaired_anki_cars'"
                       "in Verbindung mit 'connect_to_physical_car_by'.")
    async def connect_all_anki_cars(self) -> list[Vehicle]:
        found_anki_cars = await self.find_unpaired_anki_cars()
        for vehicle_uuid in found_anki_cars:
            self.logger.info(f'Connecting to vehicle {vehicle_uuid}')
            await self.connect_to_physical_car_by(vehicle_uuid)
        return self.get_vehicle_list()

    async def find_unpaired_anki_cars(self) -> list[str]:
        self.logger.info("Searching for unpaired Anki cars")
        found_devices = await self._fleet_ctrl.scan_for_anki_cars()
        # remove already active uuids:

        connected_devices = []
        for v in self._active_anki_cars:
            connected_devices.append(v.get_vehicle_id())
        new_devices = [device for device in found_devices if device not in connected_devices]

        if new_devices:
            self.logger.info(f"Found new devices: {new_devices}")
        else:
            self.logger.info("No new devices found")

        return new_devices

    def remove_vehicle_by_id(self, uuid_to_remove: str) -> bool:
        """
        Remove both vehicle and the controlling player for a given vehicle.

        Parameters
        ----------
        uuid_to_remove: str
            ID of vehicle to be removed.
        """
        self.logger.info(f"Removing vehicle with UUID {uuid_to_remove}")

        found_vehicle = next((o for o in self._active_anki_cars if o.vehicle_id == uuid_to_remove), None)
        if found_vehicle is None:
            return False
        else:
            player_id = found_vehicle.get_player_id()
            if player_id is not None:
                found_vehicle.remove_player()
                self._publish_removed_player(player_id=player_id)

            self._active_anki_cars.remove(found_vehicle)
            found_vehicle.__del__()

            self._assign_players_to_vehicles()
            self.logger.debug("Updated list of active vehicles: %s", self._active_anki_cars)
            self.update_staff_ui()
            return True

    async def connect_to_physical_car_by(self, uuid: str) -> None:
        self.logger.debug(f"Adding physical vehicle with UUID {uuid}")

        anki_car_controller = AnkiController()
        location_service = LocationService(self.get_track(), start_immediately=True)
        new_vehicle = PhysicalCar(uuid, anki_car_controller, location_service)
        await new_vehicle.initiate_connection(uuid)
        # TODO: add a check if connection was successful 

        self._add_to_active_vehicle_list(new_vehicle)
        return

    def add_virtual_vehicle(self) -> None:
        # TODO: Add more better way of determining name numbers to allow reuse of already
        # used numbers
        name = f"Virtual Vehicle {self._virtual_vehicle_num}"
        self._virtual_vehicle_num += 1

        self.logger.debug(f"Adding virtual vehicle with name {name}")

        dummy_controller = EmptyController()
        location_service = LocationService(self.get_track(), start_immediately=True)
        new_vehicle = VirtualCar(name, dummy_controller, location_service)

        self._add_to_active_vehicle_list(new_vehicle)
        return

    def _add_to_active_vehicle_list(self, new_vehicle: Vehicle) -> None:
        self._active_anki_cars.append(new_vehicle)
        self._assign_players_to_vehicles()
        self.update_staff_ui()

        return

    # TODO check if all 4 return functions are needed:
    #   - get_vehicle_list
    #   - get_controlled_cars_list
    #   - get_free_car_list
    #   - get_mapped_cars
    def get_vehicle_list(self) -> list[Vehicle] | None:
        return self._active_anki_cars

    def get_controlled_cars_list(self) -> List[str]:
        """
        Returns a list of all vehicle names from vehicles that are
        controlled by a player
        """
        vehicle_list = []
        for vehicle in self._active_anki_cars:
            if vehicle.get_player_id() is not None:
                vehicle_list.append(vehicle.get_vehicle_id())
        return vehicle_list

    def get_free_car_list(self) -> List[str]:
        """
        Returns a list of all cars that have no player controlling them
        """
        vehicle_list = []
        for vehicle in self._active_anki_cars:
            if vehicle.get_player_id() is None:
                vehicle_list.append(vehicle.get_vehicle_id())
        return vehicle_list

    def get_mapped_cars(self) -> List[dict]:
        tmp = []
        for v in self._active_anki_cars:
            if v.get_player_id() is not None:
                tmp.append({
                    'player': v.get_player_id(),
                    'car': v.get_vehicle_id()
                })
        return tmp

    def get_vehicle_by_player_id(self, player: str) -> Vehicle | None:
        """
        Get the car that's controlled by a player or None, if the
        player doesn't control any car
        """
        for v in self._active_anki_cars:
            if v.get_player_id() == player:
                return v
        return None

    def get_car_color_map(self) -> Dict[str, List[str]]:
        colors = ["#F93822", "#DAA03D", "#E69A8D", "#42EADD", "#00203F", "#D6ED17", "#2C5F2D", "#101820"]
        full_map: Dict[str, List[str]] = {}
        num = 1
        for c in colors:
            for d in colors:
                # disallow same inner and outer color to preserve a contrast
                if c != d:
                    full_map.update({f"Virtual Vehicle {num}": [d, c]})
                    num += 1
        return full_map

    # racetrack management
    def get_track(self) -> FullTrack:
        """
        Get the used track in the simulation
        """
        track: FullTrack = TrackBuilder() \
            .append(TrackPieceType.STRAIGHT_WE) \
            .append(TrackPieceType.CURVE_WS) \
            .append(TrackPieceType.CURVE_NW) \
            .append(TrackPieceType.STRAIGHT_EW) \
            .append(TrackPieceType.CURVE_EN) \
            .append(TrackPieceType.CURVE_SE) \
            .build()

        return track
