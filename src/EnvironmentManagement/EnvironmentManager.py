# Copyright 2024 IAV GmbH
#
# This file is part of the IAV-Distortion project an interactive
# and educational showcase designed to demonstrate the need
# of automotive cybersecurity in a playful, engaging manner.
# and is released under the "Apache 2.0". Please see the LICENSE
# file that should have been included as part of this package.
#
import logging
from typing import List
from collections import deque
from flask_socketio import SocketIO

from DataModel.Vehicle import Vehicle
from DataModel.VirtualCar import VirtualCar
from DataModel.PhysicalCar import PhysicalCar
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
        self._player_queue_list: deque[str] = deque()
        self._active_anki_cars: List[Vehicle] = []
        self.staff_ui = None

        # self.find_unpaired_anki_cars()

        # number used for naming virtual vehicles
        self._virtual_vehicle_num: int = 1

        self._socketio: SocketIO = socketio

    def set_staff_ui(self, staff_ui):
        self.staff_ui = staff_ui
        return


    def connect_all_anki_cars(self) -> list[Vehicle]:
        found_anki_cars = self.find_unpaired_anki_cars()
        for vehicle_uuid in found_anki_cars:
            self.logger.info(f'Connecting to vehicle {vehicle_uuid}')
            self.add_physical_vehicle(vehicle_uuid)
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

    def remove_player_from_vehicles_and_waitlist(self, player: str):
        """
        Kicks a player out of the current car/queue
        """
        self.logger.info(f"Removing player with UUID {player}")
        for v in self._active_anki_cars:
            if v.get_player() == player:
                v.remove_player()
        self._assign_players_to_vehicles()
        self.logger.debug("Updated list of active vehicles: %s", self._active_anki_cars)
        self._update_staff_ui()

    def remove_vehicle(self, vehicle_id: str):
        self.logger.info("Removing vehicle with id %s", vehicle_id)
        vehicle = next((v for v in self._active_anki_cars if v.get_vehicle_id() == vehicle_id), None)
        if vehicle is None:
            self.logger.error("Attempted to remove vehicle %s which doesn't exist!", vehicle_id)
            return
        self._active_anki_cars.remove(vehicle)
        vehicle.__del__()
        self._update_staff_ui()


    def update_queues_and_get_vehicle(self, player_id: str) -> Vehicle | None:
        self._add_player_to_queue_if_appropiate(player_id)
        self._assign_players_to_vehicles()
        for v in self._active_anki_cars:
            if v.get_player() == player_id:
                return v
        self._update_staff_ui()
        return None

    def _add_player_to_queue_if_appropiate(self, player_id: str):
        for v in self._active_anki_cars:
            if v.get_player() == player_id:
                return
        for p in self._player_queue_list:
            if p == player_id:
                return
        self._player_queue_list.append(player_id)

    def _assign_players_to_vehicles(self):
        for v in self._active_anki_cars:
            if v.is_free():
                if len(self._player_queue_list) == 0:
                    return
                p = self._player_queue_list.popleft()
                v.set_player(p)

    def add_player(self, player_id: str):
        """
        Add a player to the waiting queue.
        """
        if player_id in self._player_queue_list:
            print(f'Player {player_id} is already in the queue!')
            return
        else:
            self._player_queue_list.append(player_id)
            print(self._player_queue_list)
        # TODO: Implememnt
        self._update_staff_ui()


    def remove_player(self, player_id: str):
        """
        Remove a player from the waiting queue and the car they are active in
        """
        for v in self._active_anki_cars:
            if v.get_player() == player_id:
                v.remove_player()
        self._player_queue_list.remove(player_id)
        self._update_staff_ui()

    def add_physical_vehicle(self, uuid: str):
        self.logger.debug(f"Adding vehicle with UUID {uuid}")

        anki_car_controller = AnkiController()
        temp_vehicle = PhysicalCar(uuid, anki_car_controller, self.get_track(), self._socketio)
        temp_vehicle.initiate_connection(uuid)
        self._active_anki_cars.append(temp_vehicle)
        self._assign_players_to_vehicles()

    def add_virtual_vehicle(self):
        name = f"Virtual Vehicle {self._virtual_vehicle_num}"
        self._virtual_vehicle_num += 1
        vehicle = VirtualCar(name, self.get_track(), self._socketio)
        self._active_anki_cars.append(vehicle)
        self._assign_players_to_vehicles()

    def get_track(self) -> FullTrack:
        track: FullTrack = TrackBuilder()\
            .append(TrackPieceType.STRAIGHT_WE)\
            .append(TrackPieceType.CURVE_WS)\
            .append(TrackPieceType.CURVE_NW)\
            .append(TrackPieceType.STRAIGHT_EW)\
            .append(TrackPieceType.CURVE_EN)\
            .append(TrackPieceType.CURVE_SE)\
            .build()

        return track

    def _update_staff_ui(self):
        if self.staff_ui is not None:
            self.staff_ui.publish_new_data()
        else:
            print("staff_ui instance is not yet set!")
        return

    def get_uuid_list(self):
        l = []
        for v in self._active_anki_cars:
            if v.get_player() is not None:
                l.append(v.get_vehicle_id())
        return l

    def get_free_car_list(self):
        l = []
        for v in self._active_anki_cars:
            if v.get_player() is None:
                l.append(v.get_vehicle_id())
        return l

    def get_waiting_player_list(self):
        tmp = []
        for p in self._player_queue_list:
            tmp.append(p)
        return tmp

    def get_car_from_player(self, player: str) -> Vehicle:
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
