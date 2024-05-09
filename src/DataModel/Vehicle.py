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
    def __init__(self, uuid: str, controller: VehicleController) -> None:
        self.vehicle_id: str = uuid
        self.player: str = ""

        self._controller: VehicleController = controller
        self._active_hacking_scenario: str = ""
        self._driving_data_callback = None

        return

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

    def set_driving_data_callback(self, function_name) -> None:
        self._driving_data_callback = function_name
        return

    def _on_driving_data_change(self) -> None:
        if self._driving_data_callback is not None:
            self._driving_data_callback(self.get_driving_data())
        return

    def get_typ_of_controller(self):
        return type(self._controller)
