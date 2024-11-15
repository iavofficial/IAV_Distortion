# Copyright 2024 IAV GmbH
#
# This file is part of the IAV-Distortion project an interactive
# and educational showcase designed to demonstrate the need
# of automotive cybersecurity in a playful, engaging manner.
# and is released under the "Apache 2.0". Please see the LICENSE
# file that should have been included as part of this package.
#

from typing import List
from DataModel.Vehicle import Vehicle


class BehaviourController:

    def __init__(self, vehicles: List[Vehicle]):
        if all(isinstance(v_item, Vehicle) for v_item in vehicles):
            self._vehicles = vehicles

    def get_vehicle_by_uuid(self, uuid: str) -> Vehicle:
        found_vehicle = next((o for o in self._vehicles if o.vehicle_id == uuid), None)
        return found_vehicle

    def on_vehicle_data_change(self, uuid):
        self.get_vehicle_by_uuid(uuid)

    # Driver Controller
    def request_speed_change_for(self, uuid: str, value_perc: float) -> None:
        vehicle = self.get_vehicle_by_uuid(uuid)
        vehicle.request_speed_percent(value_perc)

        print(f"Switch speed to {value_perc}. UUID: {uuid}")
        return

    def request_lane_change_for(self, uuid: str, value: str) -> None:
        vehicle = self.get_vehicle_by_uuid(uuid)
        if value == "right":
            vehicle.request_lanechange(1)
            print(f"Switch Lane to right (1) for {uuid}")

        elif value == "left":
            vehicle.request_lanechange(-1)
            print(f"Switch Lane to left (-1) for {uuid}")

        else:
            vehicle.request_lanechange(0)
            print(f"Stay in lane (0) for {uuid}")

        return

    def request_uturn_for(self, uuid: str) -> None:
        vehicle = self.get_vehicle_by_uuid(uuid)
        vehicle.request_uturn()
        print(f"Make u-turn for ({uuid})")
        return

    def request_lights_on(self, uuid: str) -> None:
        vehicle = self.get_vehicle_by_uuid(uuid)
        vehicle.isLightOn = True
        return

    def request_lights_off(self, uuid: str) -> None:
        vehicle = self.get_vehicle_by_uuid(uuid)
        vehicle.isLightOn = False
        return

    # Security Controller
    def set_speed_factor(self, uuid: str, value) -> None:
        vehicle = self.get_vehicle_by_uuid(uuid)
        vehicle.speed_factor = value
        return

    def block_lane_change(self, uuid: str) -> None:
        vehicle = self.get_vehicle_by_uuid(uuid)
        vehicle.lange_change_blocked = True
        return

    def unblock_lane_change(self, uuid) -> None:
        vehicle = self.get_vehicle_by_uuid(uuid)
        vehicle.lange_change_blocked = False
        return

    def block_turn(self, uuid: str) -> None:
        vehicle = self.get_vehicle_by_uuid(uuid)
        vehicle.turn_blocked = True
        return

    def unblock_turn(self, uuid) -> None:
        vehicle = self.get_vehicle_by_uuid(uuid)
        vehicle.turn_blocked = False
        return

    def invert_light_switch(self, uuid, value) -> None:
        vehicle = self.get_vehicle_by_uuid(uuid)
        vehicle.isLightInverted = value
        return

    def turn_safemode_off(self, uuid) -> None:
        vehicle = self.get_vehicle_by_uuid(uuid)
        vehicle.isSafeModeOn = False
        return

    def turn_safemode_on(self, uuid) -> None:
        vehicle = self.get_vehicle_by_uuid(uuid)
        vehicle.isSafeModeOn = True
        return

    def set_hacking_scenario(self, uuid, value) -> None:
        vehicle = self.get_vehicle_by_uuid(uuid)
        vehicle.hacking_scenario = value
        return
