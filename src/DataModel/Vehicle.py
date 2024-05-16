# Copyright 2024 IAV GmbH
#
# This file is part of the IAV-Distortion project an interactive
# and educational showcase designed to demonstrate the need
# of automotive cybersecurity in a playful, engaging manner.
# and is released under the "Apache 2.0". Please see the LICENSE
# file that should have been included as part of this package.
#

from VehicleManagement.VehicleController import VehicleController
import abc


class Vehicle:
    def __init__(self, vehicle_id: str, controller: VehicleController = None) -> None:
        self.vehicle_id: str = vehicle_id
        self.player: str = ""

        self._controller: VehicleController = controller
        self._active_hacking_scenario: str = "0"
        self._driving_data_callback = None

        return

    @abc.abstractmethod
    def __del__(self) -> None:
        self._controller.__del__()
        return

    @abc.abstractmethod
    def get_typ_of_controller(self):
        pass

    def set_driving_data_callback(self, function_name) -> None:
        self._driving_data_callback = function_name
        return

    @abc.abstractmethod
    def _on_driving_data_change(self) -> None:
        pass

    @property
    def hacking_scenario(self) -> str:
        return self._active_hacking_scenario

    @hacking_scenario.setter
    def hacking_scenario(self, value: str) -> None:
        self._active_hacking_scenario = value
        self._on_driving_data_change()

    @abc.abstractmethod
    def get_driving_data(self) -> dict:
        pass

    @property
    @abc.abstractmethod
    def speed_request(self) -> float:
        pass

    @speed_request.setter
    @abc.abstractmethod
    def speed_request(self, value: float) -> None:
        pass

    @property
    @abc.abstractmethod
    def speed_factor(self) -> float:
        pass

    @speed_factor.setter
    @abc.abstractmethod
    def speed_factor(self, value: float) -> None:
        pass

    @property
    @abc.abstractmethod
    def speed(self) -> float:
        pass

    @property
    @abc.abstractmethod
    def lane_change_request(self) -> int:
        pass

    @lane_change_request.setter
    @abc.abstractmethod
    def lane_change_request(self, value: int) -> None:
        pass

    @property
    @abc.abstractmethod
    def lange_change_blocked(self) -> bool:
        pass

    @lange_change_blocked.setter
    @abc.abstractmethod
    def lange_change_blocked(self, value: bool) -> None:
        pass

    @property
    @abc.abstractmethod
    def lane_change(self) -> int:
        pass

    @property
    @abc.abstractmethod
    def turn_request(self) -> int:
        pass

    @turn_request.setter
    @abc.abstractmethod
    def turn_request(self, value: int) -> None:
        pass

    @property
    @abc.abstractmethod
    def turn_blocked(self) -> bool:
        pass

    @turn_blocked.setter
    @abc.abstractmethod
    def turn_blocked(self, value: bool) -> None:
        pass

    @property
    @abc.abstractmethod
    def turn(self):
        pass
