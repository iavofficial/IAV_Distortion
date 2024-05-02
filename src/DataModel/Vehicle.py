# Copyright 2024 IAV GmbH
#
# This file is part of the IAV-Distortion project an interactive
# and educational showcase designed to demonstrate the need
# of automotive cybersecurity in a playful, engaging manner.
# and is released under the "Apache 2.0". Please see the LICENSE
# file that should have been included as part of this package.
#

from VehicleManagement.VehicleController import VehicleController
from bleak import BleakClient
import abc


class Vehicle:
    def __init__(self, uuid: str, controller: VehicleController) -> None:
        self.vehicle_id: str = uuid
        self.player: str = ""
        self.__controller: VehicleController = controller

        self.__active_hacking_scenario: str = ""

        self.__driving_data_callback = None

        return

    @property
    def hacking_scenario(self) -> str:
        return self.__active_hacking_scenario

    @hacking_scenario.setter
    def hacking_scenario(self, value: str) -> None:
        self.__active_hacking_scenario = value
        self.__on_driving_data_change()

    @abc.abstractmethod
    def get_driving_data(self) -> dict:

    def set_driving_data_callback(self, function_name) -> None:
        self.__driving_data_callback = function_name
        return

    def __on_driving_data_change(self) -> None:
        if self.__driving_data_callback is not None:
            self.__driving_data_callback(self.get_driving_data())
        return