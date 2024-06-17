# Copyright 2024 IAV GmbH
#
# This file is part of the IAV-Distortion project an interactive
# and educational showcase designed to demonstrate the need
# of automotive cybersecurity in a playful, engaging manner.
# and is released under the "Apache 2.0". Please see the LICENSE
# file that should have been included as part of this package.
#
import logging
from typing import List, Dict, Callable
from collections import deque
from flask_socketio import SocketIO

from DataModel.PhysicalCar import PhysicalCar
from DataModel.Vehicle import Vehicle
from DataModel.VirtualCar import VirtualCar
from VehicleManagement.AnkiController import AnkiController
from VehicleManagement.FleetController import FleetController
from VehicleManagement.VehicleController import VehicleController

from LocationService.TrackPieces import TrackBuilder, FullTrack
from LocationService.Track import TrackPieceType


class EnvironmentManager:

    def __init__(self, fleet_ctrl: FleetController, socketio: SocketIO):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        console_handler = logging.StreamHandler()
        self.logger.addHandler(console_handler)

        self._fleet_ctrl = fleet_ctrl
        self._socketio: SocketIO = socketio
        self._player_queue_list: deque[str] = deque()
        self._active_anki_cars: List[Vehicle] = []

        self.__update_staff_ui_callback: Callable[[Dict[str, str], List[str], List[str]], None] | None = None
        self.__publish_removed_player_callback: Callable[[str], None] | None = None
        self.__publish_player_active_callback: Callable[[str], None] | None = None

        # self.find_unpaired_anki_cars()

        # number used for naming virtual vehicles
        self._virtual_vehicle_num: int = 1

        self._socketio: SocketIO = socketio

    def set_staff_ui_update_callback(self, function_name: Callable[[Dict[str, str], List[str], List[str]], None]) \
            -> None:
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

    def _publish_removed_player(self, player: str) -> None:
        """
        Sends which player has been removed from the game to the staff ui using a callback function.

        Parameters
        ----------
        player: str
            ID of player that has been removed.
        """
        if not callable(self.__publish_removed_player_callback):
            self.logger.critical('Missing publish_removed_player_callback!')
        else:
            self.__publish_removed_player_callback(player)
        return

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

    def connect_all_anki_cars(self) -> list[Vehicle]:
        found_anki_cars = self.find_unpaired_anki_cars()
        for vehicle_uuid in found_anki_cars:
            self.logger.info(f'Connecting to vehicle {vehicle_uuid}')
            self.add_vehicle(vehicle_uuid)
        return self.get_vehicle_list()

    def find_unpaired_anki_cars(self) -> list[str]:
        self.logger.info("Searching for unpaired Anki cars")
        found_devices = self._fleet_ctrl.scan_for_anki_cars()
        # remove already active uuids:
        new_devices = []
        connected_devices = []
        for v in self._active_anki_cars:
            connected_devices.append(v.get_vehicle_id())
        new_devices = [device for device in found_devices if device not in connected_devices]

        if new_devices:
            self.logger.info(f"Found new devices: {new_devices}")
        else:
            self.logger.info("No new devices found")

        return new_devices

    def get_vehicle_list(self) -> list[Vehicle]:
        return self._active_anki_cars

    def remove_vehicle(self, uuid_to_remove: str):
        """
        Remove both vehicle and the controlling player for a given vehicle
        """
        self.logger.info(f"Removing vehicle with UUID {uuid_to_remove}")

        found_vehicle = next((o for o in self._active_anki_cars if o.vehicle_id == uuid_to_remove), None)
        if found_vehicle is not None:
            player = found_vehicle.get_player()
            if player is not None:
                self._publish_removed_player(player=player)
            found_vehicle.remove_player()
            self._active_anki_cars.remove(found_vehicle)
            found_vehicle.__del__()

        self._assign_players_to_vehicles()
        self.logger.debug("Updated list of active vehicles: %s", self._active_anki_cars)

        self.update_staff_ui()
        return

    def update_queues_and_get_vehicle(self, player_id: str) -> Vehicle | None:
        self._add_player_to_queue_if_appropiate(player_id)
        self._assign_players_to_vehicles()
        self.update_staff_ui()
        for v in self._active_anki_cars:
            if v.get_player() == player_id:
                return v
        self.update_staff_ui()
        return None

    def _add_player_to_queue_if_appropiate(self, player_id: str) -> None:
        """
        Adds a player to the queue, if it's appropriate (as in the
            player isn't controlling a vehicle already and the player
            also isn't in the queue already)
        """
        for v in self._active_anki_cars:
            if v.get_player() == player_id:
                return
        for p in self._player_queue_list:
            if p == player_id:
                return
        self._player_queue_list.append(player_id)
        return

    def _assign_players_to_vehicles(self) -> None:
        """
        Assigns as many waiting players to vehicles as possible
        """
        for v in self._active_anki_cars:
            if v.is_free():
                if len(self._player_queue_list) == 0:
                    self.update_staff_ui()
                    return
                p = self._player_queue_list.popleft()
                self._publish_player_active(player=p)
                v.set_player(p)
        self.update_staff_ui()
        return

    def add_player(self, player_id: str) -> None:
        """
        Add a player to the waiting queue.
        """
        if player_id in self._player_queue_list:
            print(f'Player {player_id} is already in the queue!')
            return
        else:
            self._player_queue_list.append(player_id)
            print(self._player_queue_list)
        self.update_staff_ui()
        return

    def remove_player_from_waitlist(self, player_id: str) -> None:
        """
        Remove a player from the waiting queue
        """
        if player_id in self._player_queue_list:
            self._player_queue_list.remove(player_id)
        # TODO: Show other page when the user gets removed from here
        self._publish_removed_player(player=player_id)
        self.update_staff_ui()
        return

    def remove_player_from_vehicle(self, player: str) -> None:
        """
        removes a player from the vehicle they are controlling
        """
        self.logger.info(f"Removing player with UUID {player} from vehicle")
        for v in self._active_anki_cars:
            if v.get_player() == player:
                v.remove_player()
                self._publish_removed_player(player=player)
                # TODO: define how to control vehicle without player
        self.update_staff_ui()
        return

    def add_vehicle(self, uuid: str) -> None:
        self.logger.debug(f"Adding vehicle with UUID {uuid}")

        anki_car_controller = AnkiController()
        temp_vehicle = PhysicalCar(uuid, anki_car_controller, self.get_track(), self._socketio)
        temp_vehicle.initiate_connection(uuid)
        # TODO: add a check if connection was successful 

        self._active_anki_cars.append(temp_vehicle)
        self._assign_players_to_vehicles()
        self.update_staff_ui()
        return

    def add_virtual_vehicle(self):
        # TODO: Add more better way of determining name numbers to allow reuse of already
        # used numbers
        name = f"Virtual Vehicle {self._virtual_vehicle_num}"
        self._virtual_vehicle_num += 1
        vehicle = VirtualCar(name, self.get_track(), self._socketio)
        self._active_anki_cars.append(vehicle)
        self._assign_players_to_vehicles()
        self.update_staff_ui()
        return

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

    def get_controlled_cars_list(self) -> List[str]:
        """
        Returns a list of all vehicle names from vehicles that are
        controlled by a player
        """
        l = []
        for v in self._active_anki_cars:
            if v.get_player() is not None:
                l.append(v.get_vehicle_id())
        return l

    def get_free_car_list(self) -> List[str]:
        """
        Returns a list of all cars that have no player controlling them
        """
        l = []
        for v in self._active_anki_cars:
            if v.get_player() is None:
                l.append(v.get_vehicle_id())
        return l

    def get_waiting_player_list(self) -> List[str]:
        """
        Gets a list of all player that are waiting for a vehicle
        """
        tmp = []
        for p in self._player_queue_list:
            tmp.append(p)
        return tmp

    def get_car_from_player(self, player: str) -> Vehicle | None:
        """
        Get the car that's controlled by a player or None, if the
        player doesn't control any car
        """
        for v in self._active_anki_cars:
            if v.get_player() == player:
                return v
        return None

    def get_mapped_cars(self) -> List[dict]:
        tmp = []
        for v in self._active_anki_cars:
            if v.get_player() is not None:
                tmp.append({
                    'player': v.get_player(),
                    'car': v.get_vehicle_id()
                })
        return tmp

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
