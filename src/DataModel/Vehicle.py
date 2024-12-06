# Copyright 2024 IAV GmbH
#
# This file is part of the IAV Distortion project an interactive
# and educational showcase designed to demonstrate the need
# of automotive cybersecurity in a playful, engaging manner.
# and is released under the "Apache 2.0". Please see the LICENSE
# file that should have been included as part of this package.
#
import asyncio
from datetime import datetime
from typing import Callable, Any

import Constants
from DataModel.Effects.VehicleEffect import VehicleEffect
from Items.Item import Item
from LocationService.LocationService import LocationService
from LocationService.Track import FullTrack
from LocationService.Trigo import Position, Angle
import logging

logger = logging.getLogger(__name__)


class Vehicle:
    def __init__(self, vehicle_id: str,
                 location_service: LocationService,
                 disable_item_removal: bool = False) -> None:

        self.vehicle_id: str = vehicle_id
        self.player: str = ""
        self.game_start: datetime | None = None

        self._active_hacking_scenario: str = "0"
        self._driving_data_callback: Callable[[dict[str, Any]], None] | None = None

        self._effects: list[VehicleEffect] = []
        self._item_data_callback: Callable[[dict[str, str]], None] | None = None

        self._location_service: LocationService = location_service

        if not disable_item_removal:
            self._effect_removal_task = asyncio.create_task(self._check_effect_removal())

        self._requested_speed: float = 0
        self._speed_factor: float = 1.0
        self._speed_offset: float = 0
        self._current_driving_speed: int = 0

        self.__lane_change: int = 0
        self.__lange_change_blocked: bool = False
        self.__lane_change_inverted: bool = False

        self.__turn_blocked: bool = False

        self._is_safemode_on: bool = True

        self._virtual_location_update_callback: Callable[[str, dict[str, float], float], None] | None = None

    def __del__(self):
        pass

    def notify_new_track(self, new_track: FullTrack) -> None:
        self._location_service.notify_new_track(new_track)

    def set_player(self, key: str) -> None:
        """
        Sets the owner of the vehicle
        """
        if key != "":
            self.player = key
            self.game_start = datetime.now()
        return

    def remove_player(self) -> None:
        """
        Removes the player occupation and marks the vehicle as free
        """
        self.player = ""
        self.game_start = None
        return

    def is_free(self) -> bool:
        """
        Returns whether the vehicle is free (has no active driver)
        """
        return self.player == ""

    def get_player_id(self) -> str:
        """
        Returns the player that is controlling they vehicle or None
        """
        return self.player

    def get_vehicle_id(self) -> str:
        """
        Returns the name (for real vehicles UUID) of the vehicle
        """
        return self.vehicle_id

    def get_speed_with_effects_applied(self, requested_speed: float) -> int:
        """
        Calculates the speed after applying the speed factor and other effects
        """
        speed_calculated = requested_speed * self._speed_factor + self._speed_offset
        if speed_calculated > Constants.MINIMUM_SPEED_PERCENT:
            return int(speed_calculated)

        self._current_driving_speed = 0
        self._on_driving_data_change()
        return 0

    def set_driving_data_callback(self, function_name: Callable[[dict[str, Any]], None]) -> None:
        self._driving_data_callback = function_name
        return

    def _on_driving_data_change(self) -> None:
        if self._driving_data_callback is not None and callable(self._driving_data_callback):
            self._driving_data_callback(self.get_driving_data())
        return

    # --------------------------
    # Methods to request actions
    # --------------------------
    def request_speed_percent(self, requested_speed: float):
        """
        Method that gets called when a speed is requested. The value range for it is 0-100
        """
        self._requested_speed = requested_speed
        self._new_speed_calculated(self.get_speed_with_effects_applied(requested_speed))

    def request_lanechange(self, direction: int):
        """
        Method that requests a lanechange
        """
        self.__calculate_lane_change(direction)
        self._new_offset_calculated(self.__lane_change)

    def request_uturn(self):
        self.__calculate_turn()

    # ----------------------------------------------
    # Methods that get called when a change occurred
    # ----------------------------------------------
    def _new_speed_calculated(self, new_speed: int) -> None:
        """
        Gets called when the speed calculation changes (e.g. due to a new speed factor or due to a speed request)
        """
        asyncio.create_task(self._location_service.set_speed_percent(new_speed))

    def _new_offset_calculated(self, current_lane: int) -> None:
        """
        Gets called when a new offset was just calculated
        """
        asyncio.create_task(self._location_service.set_offset_int(current_lane))
        asyncio.create_task(self._location_service.set_speed_percent(
            self.get_speed_with_effects_applied(self._requested_speed)))

    def _uturn_starting(self):
        """
        Gets called when a U-Turn is executed
        """
        asyncio.create_task(self._location_service.do_uturn())

    # ---------------------------
    # Generic getters and setters
    # ---------------------------
    @property
    def hacking_scenario(self) -> str:
        return self._active_hacking_scenario

    @hacking_scenario.setter
    def hacking_scenario(self, value: str) -> None:
        self._active_hacking_scenario = value
        self._on_driving_data_change()

    def remove_hacking_scenario(self) -> None:
        self._active_hacking_scenario = "0"

    @property
    def speed_factor(self) -> float:
        return self._speed_factor

    @speed_factor.setter
    def speed_factor(self, value: float) -> None:
        if not value == self._speed_factor:
            self._speed_factor = value
            self._new_speed_calculated(self.get_speed_with_effects_applied(self._requested_speed))
        return

    @property
    def speed_offset(self) -> float:
        return self._speed_offset

    @speed_offset.setter
    def speed_offset(self, value: float) -> None:
        if not value == self._speed_offset:
            self._speed_offset = value
            self._new_speed_calculated(self.get_speed_with_effects_applied(self._requested_speed))

    @property
    def lange_change_blocked(self) -> bool:
        return self.__lange_change_blocked

    @lange_change_blocked.setter
    def lange_change_blocked(self, value: bool) -> None:
        self.__lange_change_blocked = value

    @property
    def lange_change_inverted(self) -> bool:
        return self.__lane_change_inverted

    @lange_change_inverted.setter
    def lange_change_inverted(self, value: bool) -> None:
        self.__lane_change_inverted = value

    @property
    def lane_change(self) -> int:
        return self.__lane_change

    @property
    def turn_blocked(self) -> bool:
        return self.__turn_blocked

    @turn_blocked.setter
    def turn_blocked(self, value: bool) -> None:
        self.__turn_blocked = value

    # ---------------------
    # Miscellaneous methods
    # ---------------------
    def __update_own_lane_change(self) -> None:
        """
        Updates the own current lane on the track. Needed to ensure
        a lane change will go to the right offset
        """
        if self._offset_from_center > 55.625:
            self.__lane_change = 3
        elif self._offset_from_center > 33.375:
            self.__lane_change = 2
        elif self._offset_from_center > 11.125:
            self.__lane_change = 1
        elif self._offset_from_center > -11.125:
            self.__lane_change = 0
        elif self._offset_from_center > -33.375:
            self.__lane_change = -1
        elif self._offset_from_center > -55.625:
            self.__lane_change = -2
        else:
            self.__lane_change = -3

    def __calculate_lane_change(self, change_request: int) -> None:
        if self.__lange_change_blocked:
            return
        if self.__lane_change_inverted:
            change_request *= -1

        self.__update_own_lane_change()
        self.__lane_change += change_request

        if self.__lane_change < -3:
            self.__lane_change = -3
        elif self.__lane_change > 3:
            self.__lane_change = 3

    def __calculate_turn(self) -> None:
        if self.__turn_blocked:
            return

        self._uturn_starting()

    def set_safemode(self, value: bool) -> None:
        self._is_safemode_on = value

    def get_driving_data(self) -> dict[str, Any]:
        driving_info_dic = {
            'vehicle_id': self.vehicle_id,
            'player': self.player,
            'speed_request': self._requested_speed,
            'lane_change_blocked': self.__lange_change_blocked,
            'lane_change_inverted': self.__lane_change_inverted,
            'is_safemode_on': self._is_safemode_on,
            'active_hacking_scenario': self._active_hacking_scenario,
            'speed_actual': self._current_driving_speed}
        return driving_info_dic

    def _receive_transition(self, value_tuple: tuple[int, int, float, int]) -> None:
        piece, piece_prev, offset, direction = value_tuple
        self._road_piece = piece
        self._prev_road_piece = piece_prev
        self._offset_from_center = offset
        self._direction = direction
        return

    def _receive_offset_update(self, value_tuple: tuple[float]) -> None:
        offset = value_tuple[0]
        self._offset_from_center = offset
        return

    def _receive_version(self, value_tuple: tuple[int, int]) -> None:
        self._version = str(value_tuple)
        return

    def _receive_battery(self, value_tuple: tuple[Any]) -> None:
        self._battery = str(value_tuple)

        self._on_driving_data_change()
        return

    # -----------------------------
    # Location Service related code
    # -----------------------------
    def set_virtual_location_update_callback(self,
                                             function_name: Callable[[str, dict[str, float], float], None]) -> None:
        self._virtual_location_update_callback = function_name
        return

    def _on_virtual_location_update(self, pos: Position, angle: Angle, _: dict[str, float]) -> None:
        if self._virtual_location_update_callback is not None and callable(self._virtual_location_update_callback):
            self._virtual_location_update_callback(self.vehicle_id, pos.to_dict(), angle.get_deg())
        return

    def _location_service_update(self, pos: Position, rot: Angle, data: dict[Any, Any]) -> None:
        """
        Default callback to be called when the location service has a new calculated vehicle position.
        It invokes the virtual location update which publishes the driving data via socketio
        """
        self._on_virtual_location_update(pos, rot, {})

    # -----------------
    # Item related code
    # -----------------
    def notify_item_collected(self, item: Item):
        self.apply_effect(item.get_effect())

    def get_active_effects(self):
        return self._effects

    def apply_effect(self, new_effect: VehicleEffect) -> None:
        for effect in self._effects:
            if effect.identify() == new_effect.identify() or effect.identify() in new_effect.conflicts_with():
                return

        if new_effect.can_be_applied(self):
            self.hacking_scenario = str(new_effect.identify())
            self._effects.append(new_effect)
            logger.info("Car %s now has the effect %s", self.vehicle_id, str(new_effect.identify()))
            if new_effect.on_start(self) is True:
                self._on_item_data_change('hacking_protection')

        return

    def remove_effect(self, effect: VehicleEffect):
        if effect.on_end(self) is True:
            self.hacking_scenario = "0"
            self._effects.remove(effect)

    async def _check_effect_removal(self):
        while True:
            for effect in self._effects:
                if effect.effect_should_end(self):
                    self._effects.remove(effect)
                    self._on_item_data_change('None')
                    logger.info("Car %s doesn't have the effect %s anymore", self.vehicle_id, str(effect.identify()))
            await asyncio.sleep(1)

    def set_item_data_callback(self, function_name: Callable[[dict[str, str]], None]) -> None:
        self._item_data_callback = function_name
        return

    def _on_item_data_change(self, item_active: str) -> None:
        item_dict = {'player_id': self.player,
                     'vehicle_id': self.vehicle_id,
                     'item_stash': 'None',
                     'item_active': item_active}

        if self._item_data_callback is not None and callable(self._item_data_callback):
            self._item_data_callback(item_dict)
        return
