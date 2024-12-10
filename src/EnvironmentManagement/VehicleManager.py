import logging

from typing import Any, Callable

from .RacetrackManager import RacetrackManager
from .ConfigurationHandler import ConfigurationHandler
from .RemovalReason import RemovalReason

from DataModel.Vehicle import Vehicle
from DataModel.PhysicalCar import PhysicalCar
from DataModel.VirtualCar import VirtualCar

from VehicleManagement.AnkiController import AnkiController
from VehicleManagement.FleetController import FleetController

from Items.ItemCollisionDetection import ItemCollisionDetector

from LocationService.LocationService import LocationService
from LocationService.PhysicalLocationService import PhysicalLocationService

logger = logging.getLogger(__name__)


class VehicleManager:
    def __init__(self,
                 fleet_controller: FleetController,
                 track_manager: RacetrackManager,
                 item_collision_detector: ItemCollisionDetector,
                 configuration_handler: ConfigurationHandler = ConfigurationHandler()) -> None:

        self._active_anki_cars: list[Vehicle] = []
        self._fleet_ctrl = fleet_controller
        self._track_mng = track_manager
        self._coll_detector = item_collision_detector
        self._config_handler = configuration_handler

        self._virtual_vehicle_dict: dict[str, str] = self._config_handler.get_configuration()["virtual_cars_pics"]
        self._virtual_vehicle_list: list[str] = [key for key in self._virtual_vehicle_dict.keys()
                                                 if key.startswith("Virtual Vehicle")]

        self.__on_added_vehicle_callbacks: list[Callable[[str], Any]] = []
        self.__on_removed_vehicle_callback: list[Callable[[str, str | None, RemovalReason], Any]] = []
        return

    # callbacks
    def __on_added_vehicle(self, vehicle_id: str) -> None:
        for callback in self.__on_added_vehicle_callbacks:
            callback(vehicle_id)
        return

    def subscribe_on_added_vehicle(self, callbackfunction: Callable[[str], Any]) -> bool:
        if isinstance(callbackfunction, Callable):
            self.__on_added_vehicle_callbacks.append(callbackfunction)
            return True
        else:
            return False

    def __on_removed_vehicle(self, vehicle_id: str, player_id: str | None, reason: RemovalReason) -> None:
        for callback in self.__on_removed_vehicle_callback:
            callback(vehicle_id, player_id, reason)
        return

    def subscribe_on_removed_vehicle(self, callbackfunction: Callable[[str, str | None, RemovalReason], Any]) -> bool:
        if isinstance(callbackfunction, Callable):
            self.__on_removed_vehicle_callback.append(callbackfunction)
            return True
        else:
            return False

    # vehicle getter
    # TODO check if all 4 return functions are needed:
    #   - get_active_vehicles
    #   - get_controlled_cars_list
    #   - get_free_car_list
    #   - get_mapped_cars
    def get_active_vehicles(self) -> list[Vehicle]:
        return self._active_anki_cars

    def get_controlled_vehicles(self) -> list[Vehicle]:
        """
        Returns a list of all vehicle names from vehicles that are
        controlled by a player
        """
        controlled_vehicles: list[Vehicle] = []
        for vehicle in self._active_anki_cars:
            if vehicle.get_player_id() is not None:
                controlled_vehicles.append(vehicle)
        return controlled_vehicles

    def get_free_vehicles(self) -> list[Vehicle]:
        """
        Returns a list of all cars that have no player controlling them
        """
        vehicle_list: list[Vehicle] = []
        for vehicle in self._active_anki_cars:
            if vehicle.get_player_id() is None:
                vehicle_list.append(vehicle)
        return vehicle_list

    def get_mapped_cars(self) -> list[dict[str, str]]:
        tmp: list[dict[str, str]] = []
        for v in self._active_anki_cars:
            if v.get_player_id() is not None:
                tmp.append({
                    'player': v.get_player_id(),
                    'car': v.get_vehicle_id()})
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

    def get_vehicle_by_vehicle_id(self, vehicle_id: str) -> Vehicle | None:
        """
        Get the car based on it's name (e.g. a Bluetooth MAC address).
        Returns None if the vehicle isn't found
        """
        if vehicle_id == "":
            return None

        for v in self._active_anki_cars:
            if v.vehicle_id == vehicle_id:
                return v
        return None

    def get_next_free_vehicle(self) -> Vehicle | None:
        for vehicle in self._active_anki_cars:
            if vehicle.is_free() is True:
                return vehicle

        return None

    # vehicle management
    def add_to_active_vehicle_list(self, new_vehicle: Vehicle) -> None:
        vehicle_already_exists = self.get_vehicle_by_vehicle_id(new_vehicle.get_vehicle_id()) is not None
        if vehicle_already_exists:
            logger.warning("Tried to add a vehicle that already exists. Ignoring the request")
            return
        self._active_anki_cars.append(new_vehicle)
        self.__on_added_vehicle(new_vehicle.vehicle_id)
        return

    def __remove_vehicle_by_id(self,
                               uuid_to_remove: str,
                               reason: RemovalReason = RemovalReason.NONE) -> bool:
        """
        Remove both vehicle and the controlling player for a given vehicle.

        Parameters
        ----------
        uuid_to_remove: str
            ID of vehicle to be removed.
        """
        logger.info(f"Removing vehicle with UUID {uuid_to_remove}")

        found_vehicle = next((o for o in self._active_anki_cars if o.vehicle_id == uuid_to_remove), None)
        if found_vehicle is None:
            return False
        else:
            player_id = found_vehicle.get_player_id()
            if player_id is not None:
                found_vehicle.remove_player()
            self._active_anki_cars.remove(found_vehicle)
            found_vehicle.__del__()

            self.__on_removed_vehicle(uuid_to_remove, player_id, reason)
            return True

    def remove_non_reachable_vehicle(self, vehicle_id: str) -> bool:
        """
        Removes the specific vehicle, if this vehicle isn't reachable anymore
        """
        return self.__remove_vehicle_by_id(vehicle_id, RemovalReason.CAR_DISCONNECTED)

    def remove_unused_vehicle(self, vehicle_id: str) -> bool:
        """
        Removes the specific vehicle, if this vehicle isn't needed anymore
        """
        return self.__remove_vehicle_by_id(vehicle_id, RemovalReason.CAR_MANUALLY_REMOVED)

    def remove_player_from_vehicle(self, player_id: str) -> bool:
        """
        removes a player from the vehicle they are controlling

        Returns
        -------
        bool
            is True, if player was removed from vehicle
            is False, if player could not be removed
        """
        for vehicle in self._active_anki_cars:
            if vehicle.get_player_id() == player_id:
                logger.info(f"Removing player with UUID {player_id} from vehicle")
                vehicle.remove_player()
                return True
        return False

    async def find_unpaired_anki_cars(self) -> list[str]:
        logger.info("Searching for unpaired Anki cars")
        found_devices = await self._fleet_ctrl.scan_for_anki_cars()
        # remove already active uuids:

        connected_devices = []
        for v in self._active_anki_cars:
            connected_devices.append(v.get_vehicle_id())
        new_devices = [device for device in found_devices if device not in connected_devices]

        if new_devices:
            logger.info(f"Found new devices: {new_devices}")
        else:
            logger.info("No new devices found")

        return new_devices

    async def connect_to_physical_car(self, uuid: str) -> bool:
        logger.debug(f"Adding physical vehicle with UUID {uuid}")

        anki_car_controller = AnkiController()
        location_service = PhysicalLocationService(self._track_mng.get_fulltrack(), start_immediately=True)
        new_vehicle = PhysicalCar(uuid, anki_car_controller, location_service)

        def item_collision(pos, rot, _): self._coll_detector.notify_new_vehicle_position(new_vehicle,
                                                                                         pos,
                                                                                         rot)
        location_service.add_on_update_callback(item_collision)
        new_vehicle.set_vehicle_not_reachable_callback(self.remove_non_reachable_vehicle)

        if await new_vehicle.initiate_connection(uuid):
            self.add_to_active_vehicle_list(new_vehicle)
            return True
        else:
            return False

    def add_virtual_vehicle(self) -> str:
        """
        Adds a virtual vehicle to the game.

        This function iterates through the list of virtual vehicles and checks if any of them are not currently in use.
        If a vehicle is found that is not in use, it is selected and added to the game.

        Returns
        -------
        name: str
            The name of the virtual vehicle added to the game or 'undefined' if no vehicle could be added.
        """
        name = None
        for vehicle in self._virtual_vehicle_list:
            if not any(vehicle == active_car.vehicle_id for active_car in self._active_anki_cars):
                name = vehicle
                break

        if name is None:
            logger.warning("No virtual vehicle available to add to the game")
            name = "undefined"
            return name

        logger.debug(f"Adding virtual vehicle with name {name}")

        location_service = LocationService(self._track_mng.get_fulltrack(), start_immediately=True)
        new_vehicle = VirtualCar(name, location_service)

        def item_collision(pos, rot, _): self._coll_detector.notify_new_vehicle_position(new_vehicle,
                                                                                         pos,
                                                                                         rot)
        location_service.add_on_update_callback(item_collision)

        self.add_to_active_vehicle_list(new_vehicle)
        return name
