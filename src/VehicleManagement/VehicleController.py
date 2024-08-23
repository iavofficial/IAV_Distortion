# Copyright 2024 IAV GmbH
#
# This file is part of the IAV-Distortion project an interactive
# and educational showcase designed to demonstrate the need
# of automotive cybersecurity in a playful, engaging manner.
# and is released under the "Apache 2.0". Please see the LICENSE
# file that should have been included as part of this package.
#

from enum import Enum
import abc


class Turns(Enum):
    NOT = 0,
    TO_LEFT = 1,
    TO_RIGHT = 2,
    A_UTURN = 3,
    A_UTURN_JUMP = 4


class TurnTrigger(Enum):
    VEHICLE_TURN_TRIGGER_IMMEDIATE = 0,
    VEHICLE_TURN_TRIGGER_INTERSECTION = 1


class VehicleController:
    def __init__(self) -> None:
        self._connected_car = None
        return

    def __del__(self) -> None:
        self.loop.stop()

    def __str__(self) -> str:
        return "Connected Car" + str(self._connected_car)

    def __repr__(self) -> str:
        return self.__str__()

    @abc.abstractmethod
    def change_speed_to(self, velocity: int, acceleration: int = 1000, respect_speed_limit: bool = True) -> bool:
        pass

    @abc.abstractmethod
    def change_lane_to(self, change_direction: int, velocity: int, acceleration: int = 1000) -> bool:
        pass

    @abc.abstractmethod
    def do_turn_with(self, direction: Turns,
                     turntrigger: TurnTrigger = TurnTrigger.VEHICLE_TURN_TRIGGER_IMMEDIATE) -> bool:
        pass
