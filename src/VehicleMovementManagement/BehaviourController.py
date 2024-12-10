# Copyright 2024 IAV GmbH
#
# This file is part of the IAV Distortion project an interactive
# and educational showcase designed to demonstrate the need
# of automotive cybersecurity in a playful, engaging manner.
# and is released under the "Apache 2.0". Please see the LICENSE
# file that should have been included as part of this package.
#

from EnvironmentManagement.EnvironmentManager import EnvironmentManager


class BehaviourController:

    def __init__(self, environment_manager: EnvironmentManager):
        self._env_mng: EnvironmentManager = environment_manager

    def on_vehicle_data_change(self, uuid: str) -> None:
        self._env_mng.get_vehicle_by_vehicle_id(uuid)
        return

    # Driver Controller
    def request_speed_change_for(self, uuid: str, value_perc: float) -> None:
        vehicle = self._env_mng.get_vehicle_by_vehicle_id(uuid)
        if vehicle is not None:
            vehicle.request_speed_percent(value_perc)

        print(f"Switch speed to {value_perc}. UUID: {uuid}")
        return

    def request_lane_change_for(self, uuid: str, value: str) -> None:
        vehicle = self._env_mng.get_vehicle_by_vehicle_id(uuid)

        if vehicle is not None:
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
        vehicle = self._env_mng.get_vehicle_by_vehicle_id(uuid)
        if vehicle is not None:
            vehicle.request_uturn()
            print(f"Make u-turn for ({uuid})")
        return

    # Security Controller
    def set_speed_factor(self, uuid: str, value: float) -> None:
        vehicle = self._env_mng.get_vehicle_by_vehicle_id(uuid)
        if vehicle is not None:
            vehicle.speed_factor = value
        return

    def block_lane_change(self, uuid: str) -> None:
        vehicle = self._env_mng.get_vehicle_by_vehicle_id(uuid)
        if vehicle is not None:
            vehicle.lange_change_blocked = True
        return

    def unblock_lane_change(self, uuid: str) -> None:
        vehicle = self._env_mng.get_vehicle_by_vehicle_id(uuid)
        if vehicle is not None:
            vehicle.lange_change_blocked = False
        return

    def block_turn(self, uuid: str) -> None:
        vehicle = self._env_mng.get_vehicle_by_vehicle_id(uuid)
        if vehicle is not None:
            vehicle.turn_blocked = True
        return

    def unblock_turn(self, uuid: str) -> None:
        vehicle = self._env_mng.get_vehicle_by_vehicle_id(uuid)
        if vehicle is not None:
            vehicle.turn_blocked = False
        return

    def set_hacking_scenario(self, uuid: str, value: str) -> None:
        vehicle = self._env_mng.get_vehicle_by_vehicle_id(uuid)
        if vehicle is not None:
            vehicle.hacking_scenario = value
        return
