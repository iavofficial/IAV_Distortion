# Copyright 2024 IAV GmbH
#
# This file is part of the IAV-Distortion project an interactive
# and educational showcase designed to demonstrate the need
# of automotive cybersecurity in a playful, engaging manner.
# and is released under the "Apache 2.0". Please see the LICENSE
# file that should have been included as part of this package.
#
import logging

from DataModel.ModelCar import ModelCar
from DataModel.Vehicle import Vehicle
from VehicleManagement.AnkiController import AnkiController
from VehicleManagement.FleetController import FleetController
from VehicleManagement.VehicleController import VehicleController


class EnvironmentManager:

    def __init__(self, fleet_ctrl: FleetController):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        console_handler = logging.StreamHandler()
        self.logger.addHandler(console_handler)

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

        if uuid in self._car_queue_list:
            self._car_queue_list.remove(uuid)
        if player_id in self._player_queue_list:
            self._player_queue_list.remove(player_id)

        self.logger.debug("Updated player UUID map: %s", self._player_uuid_map)
        print("added uuid")
        self._update_staff_ui()
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
        new_devices = [device for device in found_devices if device not in self._player_uuid_map.values()]

        if new_devices:
            self.logger.info(f"Found new devices: {new_devices}")
        else:
            self.logger.info("No new devices found")

        return new_devices

    def get_vehicle_list(self) -> list[Vehicle]:
        return self._active_anki_cars

    def remove_vehicle(self, uuid_to_remove: str):
        self.logger.info(f"Removing vehicle with UUID {uuid_to_remove}")
        player_to_remove = ''
        for player, uuid in self._player_uuid_map.items():
            if uuid == uuid_to_remove:
                player_to_remove = player

        if player_to_remove != '':
            del self._player_uuid_map[player_to_remove]
            self._update_staff_ui()

        self._active_anki_cars = [vehicle for vehicle in self._active_anki_cars if vehicle.vehicle_id != uuid_to_remove]
        self.logger.debug("Updated list of active vehicles: %s", self._active_anki_cars)

        found_vehicle = next((o for o in self._active_anki_cars if o.vehicle_id == uuid_to_remove), None)
        self._active_anki_cars.remove(found_vehicle)
        found_vehicle.__del__()

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
            print(self._player_queue_list)

        if len(self._car_queue_list) > 0:
            self.add_vehicle(uuid=self._car_queue_list.pop(0))
        else:
            self._update_staff_ui()

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

        self._update_staff_ui()

    def add_vehicle(self, uuid: str):
        self.logger.debug(f"Adding vehicle with UUID {uuid}")
        if uuid in self._player_uuid_map.values():
            print('UUID already exists!')
            return
        else:
            # if player queue is not empty, take first player id
            if len(self._player_queue_list) > 0:
                player = self._player_queue_list.pop(0)
            else:
                self._car_queue_list.append(uuid)
                self._update_staff_ui()
                return


            print(f'Player: {player}, UUID: {uuid}')
            anki_car_controller = AnkiController()
            temp_vehicle = ModelCar(uuid, anki_car_controller)
            temp_vehicle.initiate_connection(uuid)
            self.set_player_uuid_mapping(player_id=player, uuid=uuid)

            temp_vehicle.player = player
            self._active_anki_cars.append(temp_vehicle)

    def _update_staff_ui(self):
        if self.staff_ui is not None:
            self.staff_ui.update_map_of_uuids(self._player_uuid_map)
        else:
            print("staff_ui instance is not yet set!")
        return
