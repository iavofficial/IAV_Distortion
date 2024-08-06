# Copyright 2024 IAV GmbH
#
# This file is part of the IAV-Distortion project an interactive
# and educational showcase designed to demonstrate the need
# of automotive cybersecurity in a playful, engaging manner.
# and is released under the "Apache 2.0". Please see the LICENSE
# file that should have been included as part of this package.
#
import asyncio
from asyncio import Task
import struct
import logging
from typing import Callable

from VehicleManagement.VehicleController import VehicleController, Turns, TurnTrigger
from LocationService.LocationService import LocationService
from LocationService.Trigo import Angle, Position


class LocationServiceController(VehicleController):
    def __init__(self) -> None:
        super().__init__()

        self.__MAX_ANKI_SPEED = 1200  # mm/s
        self.__MAX_ANKI_ACCELERATION = 2500  # mm/s^2
        self.__LANE_OFFSET = 22.25

        self._location_service: LocationService | None = None
        return

    def __del__(self) -> None:
        pass

    def __run_async_task(self, task: Task) -> None:
        """
        Run a asyncio awaitable task

        Parameters
        ----------
        task: Task
            awaitable task
        """
        asyncio.create_task(task)
        # TODO: Log error, if the coroutine doesn't end successfully

    def connect_to(self, location_service: LocationService) -> bool:

        self._location_service: LocationService = location_service
        self._location_service.set_on_update_callback(self.__location_service_update)

        return True

    async def __location_service_update(self, pos: Position, rot: Angle, data: dict) -> None:
        return

    def __convert_speed_percent_to_absolute(self, velocity_percent: int) -> float:
        return float(self.__MAX_ANKI_SPEED * velocity_percent / 100)

    def change_speed_to(self, velocity: int, acceleration: int = 1000, respect_speed_limit: bool = True) -> bool:
        if velocity < 0:
            return False

        speed: float = self.__convert_speed_percent_to_absolut(velocity)

        self.logger.debug("Changed speed to %i", speed)
        self.__run_async_task(self._location_service.set_speed_absolute(speed))
        return True

    def change_lane_to(self, change_direction: int, velocity: int, acceleration: int = 1000) -> bool:
        speed: float = self.__convert_speed_percent_to_absolut(velocity)
        self.__run_async_task(self._location_service.set_offset_int(change_direction))
        self.__run_async_task(self._location_service.set_speed_absolute(speed))

    def do_turn_with(self, direction: Turns,
                     turntrigger: TurnTrigger = TurnTrigger.VEHICLE_TURN_TRIGGER_IMMEDIATE) -> bool:
        self.__run_async_task(self._location_service.do_uturn())