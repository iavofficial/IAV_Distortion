# Copyright 2024 IAV GmbH
#
# This file is part of the IAV-Distortion project an interactive
# and educational showcase designed to demonstrate the need
# of automotive cybersecurity in a playful, engaging manner.
# and is released under the "Apache 2.0". Please see the LICENSE
# file that should have been included as part of this package.
#
import asyncio
from datetime import datetime
from typing import Callable, List

from abc import abstractmethod

from DataModel.Effects.VehicleEffect import VehicleEffect
from Items.Item import Item
from LocationService import LocationService
from LocationService.Track import FullTrack
from VehicleManagement.VehicleController import VehicleController
import logging

logger = logging.getLogger(__name__)


class Vehicle:
    def __init__(self, vehicle_id: str, disable_item_removal=False) -> None:
        self.vehicle_id: str = vehicle_id
        self.player: str | None = None
        self.game_start: datetime | None = None

        self._active_hacking_scenario: str = "0"
        self._driving_data_callback: Callable[[dict], None] | None = None
        self._effects: List[VehicleEffect] = []

        if not disable_item_removal:
            self._effect_removal_task = asyncio.create_task(self._test_effect_removal_task())
        return

    @abstractmethod
    def notify_new_track(self, new_track: FullTrack) -> None:
        pass

    def extract_controller(self) -> VehicleController | None:
        pass

    def insert_controller(self) -> None:
        pass

    def set_player(self, key: str) -> None:
        """
        Sets the owner of the vehicle
        """
        self.player = key
        self.game_start = datetime.now()

    def remove_player(self) -> None:
        """
        Removes the player occupation and marks the vehicle as free
        """
        self.player = None
        self.game_start = None

    def is_free(self) -> bool:
        """
        Returns whether the vehicle is free (has no active driver)
        """
        return self.player is None

    def get_player_id(self) -> str | None:
        """
        Returns the player that is controlling they vehicle or None
        """
        return self.player

    def get_vehicle_id(self) -> str | None:
        """
        Returns the name (for real vehicles UUID) of the vehicle
        """
        return self.vehicle_id

    @abstractmethod
    def __del__(self) -> None:
        return

    @abstractmethod
    def get_typ_of_controller(self) -> VehicleController:
        pass

    @abstractmethod
    def get_typ_of_location_service(self) -> LocationService:
        pass

    @abstractmethod
    def set_driving_data_callback(self, function_name: Callable[[dict], None]) -> None:
        pass

    @abstractmethod
    def set_vehicle_not_reachable_callback(self, function_name: Callable[[str, str, str], None]) -> None:
        pass

    @abstractmethod
    def set_virtual_location_update_callback(self, function_name: Callable[[str, dict, float], None]) -> None:
        pass

    @property
    def hacking_scenario(self) -> str:
        return self._active_hacking_scenario

    @hacking_scenario.setter
    def hacking_scenario(self, value: str) -> None:
        self._active_hacking_scenario = value
        # TODO resolve warning
        self._on_driving_data_change()

        return

    @abstractmethod
    def get_driving_data(self) -> dict[str, str | bool | int | float]:
        pass

    @property
    @abstractmethod
    def speed_request(self) -> float:
        pass

    @speed_request.setter
    @abstractmethod
    def speed_request(self, value: float) -> None:
        pass

    @property
    @abstractmethod
    def speed_factor(self) -> float:
        pass

    @speed_factor.setter
    @abstractmethod
    def speed_factor(self, value: float) -> None:
        pass

    @property
    @abstractmethod
    def speed(self) -> float:
        pass

    @property
    @abstractmethod
    def lane_change_request(self) -> int:
        pass

    @lane_change_request.setter
    @abstractmethod
    def lane_change_request(self, value: int) -> None:
        pass

    @property
    @abstractmethod
    def lange_change_blocked(self) -> bool:
        pass

    @lange_change_blocked.setter
    @abstractmethod
    def lange_change_blocked(self, value: bool) -> None:
        pass

    @property
    @abstractmethod
    def lane_change(self) -> int:
        pass

    @property
    @abstractmethod
    def turn_request(self) -> int:
        pass

    @turn_request.setter
    @abstractmethod
    def turn_request(self, value: int) -> None:
        pass

    @property
    @abstractmethod
    def turn_blocked(self) -> bool:
        pass

    @turn_blocked.setter
    @abstractmethod
    def turn_blocked(self, value: bool) -> None:
        pass

    @property
    @abstractmethod
    def turn(self) -> None:
        pass

    def notify_item_collected(self, item: Item):
        self.apply_effect(item.get_effect())

    def get_active_effects(self):
        return self._effects

    def apply_effect(self, new_effect: VehicleEffect):
        for effect in self._effects:
            if effect.identify() == new_effect.identify() or effect.identify() in new_effect.conflicts_with():
                return

        if not new_effect.can_be_applied(self):
            return
        logger.info("Car %s now has the effect %s", self.vehicle_id, str(new_effect.identify()))
        self._effects.append(new_effect)
        new_effect.on_start(self)

    def remove_effect(self, effect: VehicleEffect):
        effect.on_end(self)
        self._effects.remove(effect)

    async def _test_effect_removal_task(self):
        while True:
            for effect in self._effects:
                if effect.effect_should_end(self):
                    self._effects.remove(effect)
                    logger.info("Car %s doesn't have the effect %s anymore", self.vehicle_id, str(effect.identify()))
            await asyncio.sleep(1)
