# Copyright 2024 IAV GmbH
#
# This file is part of the IAV-Distortion project an interactive
# and educational showcase designed to demonstrate the need
# of automotive cybersecurity in a playful, engaging manner.
# and is released under the "Apache 2.0". Please see the LICENSE
# file that should have been included as part of this package.
#
import asyncio
from typing import Callable, Coroutine

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

        self._virtual_position_data_callback: Callable[[Position, Angle, dict], None] | None = None
        return

    def __del__(self) -> None:
        pass

    def __run_coroutine_as_async_task(self, coro: Coroutine) -> None:
        """
        Run a asyncio awaitable task

        Parameters
        ----------
        coro: Coroutine
            awaitable task
        """
        asyncio.create_task(coro)
        # TODO: Log error, if the coroutine doesn't end successfully

    def set_callback(self, virtual_pos_callback: Callable) -> None:
        self._virtual_position_data_callback = virtual_pos_callback
        return

    def connect_to(self, location_service: LocationService) -> bool:

        if not isinstance(location_service, LocationService):
            return False

        self._location_service: LocationService = location_service
        self._location_service.set_on_update_callback(self.__on_receive_data)

        return True

    def __on_receive_data(self, pos: Position, rot: Angle, data: dict) -> None:
        self._pos = pos
        self._rot = rot
        self._data = data
        return

    def __convert_speed_percent_to_absolute(self, velocity_percent: int) -> float:
        return float(self.__MAX_ANKI_SPEED * velocity_percent / 100)

    def change_speed_to(self, velocity: int, acceleration: int = 1000, respect_speed_limit: bool = True) -> bool:
        if velocity < 0:
            return False

        speed: float = self.__convert_speed_percent_to_absolute(velocity)

        self.logger.debug("Changed speed to %i", speed)
        self.__run_coroutine_as_async_task(self._location_service.set_speed_absolute(speed))
        return True

    def change_lane_to(self, change_direction: int, velocity: int, acceleration: int = 1000) -> bool:
        speed: float = self.__convert_speed_percent_to_absolute(velocity)
        self.__run_coroutine_as_async_task(self._location_service.set_offset_int(change_direction))
        self.__run_coroutine_as_async_task(self._location_service.set_speed_absolute(speed))
        return True

    def do_turn_with(self, direction: Turns,
                     turntrigger: TurnTrigger = TurnTrigger.VEHICLE_TURN_TRIGGER_IMMEDIATE) -> bool:
        self.__run_coroutine_as_async_task(self._location_service.do_uturn())
        return True
