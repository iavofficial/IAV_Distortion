# Copyright 2024 IAV GmbH
#
# This file is part of the IAV-Distortion project an interactive
# and educational showcase designed to demonstrate the need
# of automotive cybersecurity in a playful, engaging manner.
# and is released under the "Apache 2.0". Please see the LICENSE
# file that should have been included as part of this package.
#
from typing import Callable

from flask_socketio import SocketIO

from VehicleManagement.VehicleController import VehicleController
import abc


class Vehicle:
    def __init__(self, vehicle_id: str,
                 socketio: SocketIO,
                 controller: VehicleController = None) -> None:
        self.vehicle_id: str = vehicle_id
        self.player: str | None = None

        self._controller: VehicleController = controller
        self._active_hacking_scenario: str = "0"
        self._driving_data_callback: Callable[[dict], None] | None = None

        self._socketio = socketio

        return

    def set_player(self, key: str) -> None:
        """
        Sets the owner of the vehicle
        """
        self.player = key

    def remove_player(self) -> None:
        """
        Removes the player occupation and marks the vehicle as free
        """
        self.player = None

    def is_free(self) -> bool:
        """
        Returns whether the vehicle is free (has no active driver)
        """
        return self.player == None

    def get_player(self) -> str | None:
        """
        Returns the player that is controlling they vehicle or None
        """
        return self.player

    def get_vehicle_id(self) -> str | None:
        """
        Returns the name (for real vehicles UUID) of the vehicle
        """
        return self.vehicle_id


    @abc.abstractmethod
    def __del__(self) -> None:
        self._controller.__del__()
        return

    @abc.abstractmethod
    def get_typ_of_controller(self):
        pass

    @abc.abstractmethod
    def set_driving_data_callback(self, function_name: Callable[[dict], None]) -> None:
        pass

    @abc.abstractmethod
    def set_vehicle_not_reachable_callback(self, function_name: Callable[[str, str, str], None]) -> None:
        pass

    @abc.abstractmethod
    def set_virtual_location_update_callback(self, function_name: Callable[[str, dict, float], None]) -> None:
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
