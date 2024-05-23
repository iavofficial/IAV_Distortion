# Copyright 2024 IAV GmbH
#
# This file is part of the IAV-Distortion project an interactive
# and educational showcase designed to demonstrate the need
# of automotive cybersecurity in a playful, engaging manner.
# and is released under the "Apache 2.0". Please see the LICENSE
# file that should have been included as part of this package.
#
from DataModel.PhysicalCar import PhysicalCar
from DataModel.Vehicle import Vehicle
from VehicleManagement.AnkiController import AnkiController
from VehicleManagement.FleetController import FleetController

from LocationService.TrackPieces import TrackBuilder, FullTrack
from LocationService.Track import TrackPieceType

class EnvironmentManager:

    def __init__(self, fleet_ctrl: FleetController):
        self._fleet_ctrl = fleet_ctrl
        self._player_uuid_map = {}
        self._active_anki_cars = []
        self.staff_ui = None

        # self.find_unpaired_anki_cars()

    def set_staff_ui(self, staff_ui):
        self.staff_ui = staff_ui
        return

    def get_player_uuid_mapping(self):
        return self._player_uuid_map

    def set_player_uuid_mapping(self, player_id: str, uuid: str):
        self._player_uuid_map.update({player_id: uuid})
        print("added uuid")
        self._update_staff_ui()
        return

    def connect_all_anki_cars(self) -> list[Vehicle]:
        found_anki_cars = self.find_unpaired_anki_cars()
        for vehicle_uuid in found_anki_cars:
            self.add_vehicle(vehicle_uuid)
        return self.get_vehicle_list()

    def find_unpaired_anki_cars(self) -> list[str]:
        found_devices = self._fleet_ctrl.scan_for_anki_cars()
        # remove already active uuids:
        new_devices = []
        new_devices = [device for device in found_devices if device not in self._player_uuid_map.values()]

        return new_devices

    def get_vehicle_list(self) -> list[Vehicle]:
        return self._active_anki_cars

    def remove_vehicle(self, uuid_to_remove: str):
        player_to_remove = ''
        for player, uuid in self._player_uuid_map.items():
            if uuid == uuid_to_remove:
                player_to_remove = player

        if player_to_remove != '':
            del self._player_uuid_map[player_to_remove]
            self._update_staff_ui()

        found_vehicle = next((o for o in self._active_anki_cars if o.vehicle_id == uuid_to_remove), None)
        self._active_anki_cars.remove(found_vehicle)
        found_vehicle.__del__()
        return

    def add_vehicle(self, uuid: str):
        if uuid in self._player_uuid_map.values():
            print('UUID already exists!')
            return
        else:
            players_as_ints = [int(player) for player in self._player_uuid_map.keys()]
            if not players_as_ints:
                max_player = 0
                smallest_available_num = '1'
            else:
                max_player = max(players_as_ints)

            # find smallest available player
            for i in range(1, max_player+1):
                if i not in players_as_ints:
                    smallest_available_num = str(i)
                    break
                else:
                    smallest_available_num = str(max_player + 1)

            # print(f'Player: {smallest_available_num}, UUID: {uuid}')

            anki_car_controller = AnkiController()
            temp_vehicle = PhysicalCar(uuid, anki_car_controller, self.get_track())
            temp_vehicle.initiate_connection(uuid)
            if temp_vehicle:
                self.set_player_uuid_mapping(player_id=smallest_available_num, uuid=uuid)

                temp_vehicle.player = smallest_available_num
                self._active_anki_cars.append(temp_vehicle)
            return

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
            self.staff_ui.update_map_of_uuids(self._player_uuid_map)
        else:
            print("staff_ui instance is not yet set!")
        return
