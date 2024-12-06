# Copyright 2024 IAV GmbH
#
# This file is part of the IAV Distortion project an interactive
# and educational showcase designed to demonstrate the need
# of automotive cybersecurity in a playful, engaging manner.
# and is released under the "Apache 2.0". Please see the LICENSE
# file that should have been included as part of this package.
#
import logging

from enum import Enum
from typing import Any, Callable

from .PlayerManager import PlayerManager
from .VehicleManager import VehicleManager
from .RacetrackManager import RacetrackManager
from .ConfigurationHandler import ConfigurationHandler

from DataModel.PhysicalCar import PhysicalCar
from DataModel.Vehicle import Vehicle

from Items.ItemCollisionDetection import ItemCollisionDetector
from Items.ItemGenerator import ItemGenerator

from VehicleManagement.AnkiController import AnkiController
from VehicleManagement.FleetController import FleetController

from LocationService.TrackPieces import FullTrack
from LocationService.TrackSerialization import full_track_to_list_of_dicts


logger = logging.getLogger(__name__)


class RemovalReason(Enum):
    NONE = 0
    PLAYING_TIME_IS_UP = 1
    PLAYER_NOT_REACHABLE = 2
    CAR_DISCONNECTED = 3
    CAR_MANUAL_REMOVED = 4


class EnvironmentManager:

    def __init__(self,
                 fleet_ctrl: FleetController,
                 configuration_handler: ConfigurationHandler = ConfigurationHandler()) -> None:

        self._item_collision_detector: ItemCollisionDetector = ItemCollisionDetector()
        self._item_generator: ItemGenerator | None = None

        self._fleet_ctrl: FleetController = fleet_ctrl
        self._track_mng: RacetrackManager = RacetrackManager()
        self._vehicle_mng: VehicleManager = VehicleManager(self._fleet_ctrl,
                                                           self._track_mng,
                                                           self._item_collision_detector)
        self._player_mng: PlayerManager = PlayerManager(self._vehicle_mng)

        # self._player_queue_list: deque[str] = deque()
        self._active_anki_cars: list[Vehicle] = []

        self.__update_staff_ui_callback: Callable[[list[dict[str, str]], list[str], list[str]], None] | None = None
        self.__publish_removed_player_callback: Callable[[str, str], Any] | None = None
        self.__publish_player_active_callback: Callable[[str], Any] | None = None
        self.__publish_vehicle_added_callback: Callable[[], Any] | None = None

        self.config_handler: ConfigurationHandler = configuration_handler

        # list of configured virtual vehicles
        self._virtual_vehicle_dict: dict[str, str] = self.config_handler.get_configuration()["virtual_cars_pics"]
        self._virtual_vehicle_list: list[str] = [key for key in self._virtual_vehicle_dict.keys()
                                                 if key.startswith("Virtual Vehicle")]

        self._fleet_ctrl.set_add_anki_car_callback(self._vehicle_mng.connect_to_physical_car)

        return

    def add_item_generator(self, item_generator: ItemGenerator) -> None:
        self._item_generator = item_generator
        return

    def get_item_collision_detector(self) -> ItemCollisionDetector:
        return self._item_collision_detector

    # set Callbacks
    def set_vehicle_added_callback(self, function_name: Callable[[], None]) -> None:
        self.__publish_vehicle_added_callback = function_name
        return

    def set_staff_ui_update_callback(self,
                                     function_name: Callable[[list[dict[str, str]],
                                                              list[str],
                                                              list[str]],
                                                             None]) -> None:
        """
        Sets callback function for staff_ui_update.

        Parameters
        ----------
        function_name: Callable[[dict[str, str], list[str], list[str]], None]
            Callback function that takes three parameters:
            1. A dictionary where keys and values are strings.
            2. A list of strings.
            3. Another list of strings.
            The function should not return anything (None).
        """
        self.__update_staff_ui_callback = function_name
        return

    def set_publish_removed_player_callback(self, function_name: Callable[[str, str], None]) -> None:
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
            logger.critical('Missing update_staff_ui_callback!')
        else:
            self.__update_staff_ui_callback(self._vehicle_mng.get_mapped_cars(),
                                            self.get_free_cars_list(),
                                            self._player_mng.get_all_waiting_players())
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
        elif reason is RemovalReason.PLAYER_NOT_REACHABLE:
            message = "Your player was removed from the game, because you were no longer reachable."
        elif reason is RemovalReason.PLAYING_TIME_IS_UP:
            message = "Your player was removed from the game, because your playing time is over."
        elif reason is RemovalReason.CAR_DISCONNECTED:
            message = "You were removed since your car wasn't reachable anymore"

        if not callable(self.__publish_removed_player_callback):
            logger.critical('Missing publish_removed_player_callback!')
            return False
        else:
            self.__publish_removed_player_callback(player_id, message)
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
            logger.critical('Missing publish_player_active_callback!')
        else:
            self.__publish_player_active_callback(player)
        return

    # Player management
    def put_player_on_next_free_vehicle(self, player_id: str) -> bool:
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
        if self._player_mng.add_player_to_queue(player_id) is False:
            return False
        result = self._player_mng.assign_players_to_vehicles()
        self.update_staff_ui()
        return result

    def remove_player_from_game_for(self,
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
        return self._player_mng.manage_removal_from_game_for(player_id, reason)

    def request_removal_of_player(self, player: str, grace_period: int = 5) -> None:
        """
        Schedules asynchronous task to remove player, only if no removal task exists for this player already.

        Parameters
        ----------
        player: str
            ID of player to be removed.
        grace_period: int
            Time to wait in seconds until player is removed, in case of reconnect.
        """
        self._player_mng.schedule_remove_player_task(player, grace_period)
        return

    # Vehicle Management
    def remove_vehicle(self, uuid_to_remove: str) -> bool:
        """
        Remove both vehicle and the controlling player for a given vehicle.

        Parameters
        ----------
        uuid_to_remove: str
            ID of vehicle to be removed.
        """
        logger.info(f"Removing vehicle with UUID {uuid_to_remove}")
        if self._vehicle_mng.remove_unused_vehicle(uuid_to_remove):
            self._player_mng.assign_players_to_vehicles()
            logger.debug("Updated list of active vehicles: %s", self._active_anki_cars)
            self.update_staff_ui()
            return True
        else:
            return False

    async def request_vehicle_connaction_to(self, uuid: str) -> bool:
        result: bool = await self._vehicle_mng.connect_to_physical_car(uuid)
        return result

    def request_virtual_vehicle(self) -> str:
        """
        Adds a virtual vehicle to the game.

        This function iterates through the list of virtual vehicles and checks if any of them are not currently in use.
        If a vehicle is found that is not in use, it is selected and added to the game.

        Returns
        -------
        name: str
            The name of the virtual vehicle added to the game or 'undefined' if no vehicle could be added.
        """
        return self._vehicle_mng.add_virtual_vehicle()

    async def get_unpaired_cars(self) -> list[str]:
        return await self._vehicle_mng.find_unpaired_anki_cars()

    def get_all_vehicles_list(self) -> list[str]:
        """
        Returns a list of all vehicles that are active
        """
        all_vehicles: list[Vehicle] = self._vehicle_mng.get_active_vehicles()
        if len(all_vehicles) == 0:
            return []
        else:
            all_vehicle_ids: list[str] = [vehicle.vehicle_id for vehicle in all_vehicles]
            return all_vehicle_ids

    def get_controlled_cars_list(self) -> list[str]:
        """
        Returns a list of all vehicle names from vehicles that are
        controlled by a player
        """
        controlled_vehicles: list[Vehicle] = self._vehicle_mng.get_controlled_vehicles()
        if len(controlled_vehicles) == 0:
            return []
        else:
            controlled_vehicle_ids: list[str] = [vehicle.vehicle_id for vehicle in controlled_vehicles]
            return controlled_vehicle_ids

    def get_free_cars_list(self) -> list[str]:
        free_vehicles: list[Vehicle] = self._vehicle_mng.get_free_vehicles()
        if len(free_vehicles) == 0:
            return []
        else:
            free_vehicle_ids: list[str] = [vehicle.vehicle_id for vehicle in free_vehicles]
            return free_vehicle_ids

    def get_vehicle_by_player_id(self, player: str) -> Vehicle | None:
        """
        Get the car that's controlled by a player or None, if the
        player doesn't control any car
        """
        return self._vehicle_mng.get_vehicle_by_vehicle_id(player)

    def get_car_color_map(self) -> dict[str, list[str]]:
        colors = ["#F93822", "#DAA03D", "#E69A8D", "#42EADD", "#00203F", "#D6ED17", "#2C5F2D", "#101820"]
        full_map: dict[str, list[str]] = {}
        num = 1
        for c in colors:
            for d in colors:
                # disallow same inner and outer color to preserve a contrast
                if c != d:
                    full_map.update({f"Virtual Vehicle {num}": [d, c]})
                    num += 1
        return full_map

    # racetrack management
    def notify_new_track(self, new_track: FullTrack) -> None:
        track_config = {'track': full_track_to_list_of_dicts(new_track)}
        self.config_handler.write_configuration(new_config=track_config)
        for car in self._vehicle_mng.get_active_vehicles():
            car.notify_new_track(new_track)
        if self._item_generator is None:
            logger.critical("EnvironmentManager has no Item Generator!")
            return
        self._item_generator.notify_new_track(new_track)
        return

    async def rescan_track_with(self, car: str) -> str | None:
        """
        Scans a track and notifies when the scanning finished.
        Returns
        -------
        A error message, if the scanning isn't possible (e.g. the car isn't available) or None in case of success
        """
        vehicle = self._vehicle_mng.get_vehicle_by_vehicle_id(car)
        if vehicle is None:
            logger.error("A client attempted to use a vehicle for track scanning that doesn't exist")
            return "Request didn't include a valid vehicle"
        if not isinstance(vehicle, PhysicalCar):
            return "This car isn't a real car. Please use a real car"
        extracted_controller: AnkiController | None = vehicle.extract_controller()
        if extracted_controller is None:
            return "The selected car can't be controlled currently. Please use another car"

        new_track: FullTrack | None = await self._track_mng.scan_track(extracted_controller)
        if new_track is not None:
            self.notify_new_track(new_track)

        vehicle.insert_controller(extracted_controller)

        return None
