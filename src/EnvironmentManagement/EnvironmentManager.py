# Copyright 2024 IAV GmbH
#
# This file is part of the IAV-Distortion project an interactive
# and educational showcase designed to demonstrate the need
# of automotive cybersecurity in a playful, engaging manner.
# and is released under the "Apache 2.0". Please see the LICENSE
# file that should have been included as part of this package.
#
from DataModel.ModelCar import ModelCar
from DataModel.Vehicle import Vehicle
from VehicleManagement.AnkiController import AnkiController
from VehicleManagement.FleetController import FleetController
from VehicleManagement.VehicleController import VehicleController


class EnvironmentManager:

    def __init__(self, fleet_ctrl: FleetController):
        self._fleet_ctrl = fleet_ctrl
        self._player_queue_list = []
        self._car_queue_list = []
        self._player_uuid_map = {}
        self._active_anki_cars = []
        self.staff_ui = None

        # self.find_unpaired_anki_cars()

    def set_staff_ui(self, staff_ui):
        self.staff_ui = staff_ui
        return

    def get_player_uuid_mapping(self):
        return self._player_uuid_map

    def get_player_queue(self):
        return self._player_queue_list

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
        # Funktion zum Fahrzeuge Suchen und Verbinden
        # BLE device suchen
        # mit Device verbinden, wenn bekannt, sonst via web interface

        # vehicle initialisieren
        found_devices = self._fleet_ctrl.scan_for_anki_cars()
        # remove already active uuids:
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

        self._active_anki_cars = [vehicle for vehicle in self._active_anki_cars if vehicle.vehicle_id != uuid_to_remove]
        return



    def add_player(self, player_id: str):
        """
        Add a player to the waiting queue.
        """
        if player_id in self._player_queue_list:
            print(f'Player {player_id} is already in the queue!')
            return
        else:
            self._player_queue_list.append(player_id)
        if self._car_queue_list:
            self.add_vehicle(uuid=self._car_queue_list.pop(0))

    def remove_player(self, player_id: str):
        """
        Remove a player from the waiting queue and add them to the active list.
        """
        if player_id  in self._player_queue_list:
            self._player_queue_list.remove(player_id)
        if player_id in self._player_uuid_map:
            uuid = self._player_uuid_map[player_id]
            del self._player_uuid_map[player_id]
            # Assuming a car has become available and the player is added to the active list
            self.add_vehicle(uuid=uuid)

    def add_vehicle(self, uuid: str):
        if uuid in self._player_uuid_map.values():
            print('UUID already exists!')
            return
        else:
            # if player queue is not empty, take first player id
            if len(self._player_queue_list) > 0:
                player = self._player_queue_list.pop(0)
                self.set_player_uuid_mapping(player_id=player, uuid=uuid)
            else:
                self._car_queue_list.append(uuid)
                return


            print(f'Player: {player}, UUID: {uuid}')
            anki_car_controller = AnkiController()
            temp_vehicle = ModelCar(uuid, anki_car_controller)
        # Einkommentieren, um mit echten Geräten zu testen
         #   temp_vehicle.initiate_connection(uuid)
            if temp_vehicle:
                self.set_player_uuid_mapping(player_id=player, uuid=uuid)

                temp_vehicle.player = player
                self._active_anki_cars.append(temp_vehicle)
            return

    def _update_staff_ui(self):
        if self.staff_ui is not None:
            self.staff_ui.update_map_of_uuids(self._player_uuid_map)
        else:
            print("staff_ui instance is not yet set!")
        return
