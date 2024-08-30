import logging
from typing import Callable

from bleak import BleakClient
from DataModel.Vehicle import Vehicle
from LocationService.PhysicalLocationService import PhysicalLocationService
from VehicleManagement.AnkiController import AnkiController
from VehicleManagement.VehicleController import Turns

logger = logging.getLogger(__name__)


def clamp(val: float, minimum: float, maximum: float) -> float:
    """
    Restricts the value range of value to a minimum and maximum boundary
    """
    return min(maximum, max(minimum, val))


class PhysicalCar(Vehicle):
    _location_service: PhysicalLocationService

    def __init__(self,
                 vehicle_id: str,
                 controller: AnkiController,
                 location_service: PhysicalLocationService,
                 disable_item_removal=False) -> None:
        super().__init__(vehicle_id, location_service, disable_item_removal)
        self._controller: AnkiController | None = controller
        self._location_service: PhysicalLocationService = location_service
        self._location_service.add_on_update_callback(self._location_service_update)
        self._car_not_reachable_callback: Callable[[str, str], None] | None = None

    def __del__(self) -> None:
        if self._controller is not None:
            self._controller.__del__()
        self._location_service.__del__()
        super().__del__()

    async def initiate_connection(self, uuid: str) -> bool:
        if self._controller is None:
            logger.error("Tried to connect to vehicle without active controller. Ignoring the request")
            return
        if await self._controller.connect_to_vehicle(BleakClient(uuid), True):
            self._controller.set_ble_not_reachable_callback(self._model_car_not_reachable_callback)
            self._controller.set_callbacks(self._receive_location,
                                           self._receive_transition,
                                           self._receive_offset_update,
                                           self._receive_version,
                                           self._receive_battery)
            self._controller.request_version()
            self._controller.request_battery()
            return True
        else:
            return False

    def _receive_location(self, value_tuple) -> None:
        location, piece, offset, speed, _ = value_tuple
        offset = clamp(offset, -66.5, 66.5)
        self._current_driving_speed = speed if self._requested_speed != 0 else 0
        self._offset_from_center = offset
        self._location_service.notify_location_event(piece, location, offset, self._current_driving_speed)
        self._on_driving_data_change()

    def _receive_transition(self, value_tuple) -> None:
        super()._receive_transition(value_tuple)
        _, _, offset, _ = value_tuple
        offset = clamp(offset, -66.5, 66.5)
        self._location_service.notify_transition_event(offset)

    def extract_controller(self):
        controller = self._controller
        self._controller = None
        return controller

    def insert_controller(self, controller: AnkiController):
        self._controller = controller
        self._controller.set_callbacks(self._receive_location,
                                       self._receive_transition,
                                       self._receive_offset_update,
                                       self._receive_version,
                                       self._receive_battery)
        self._controller.set_ble_not_reachable_callback(self._model_car_not_reachable_callback)
        self._controller.request_version()
        self._controller.request_battery()

    def set_vehicle_not_reachable_callback(self, function_name: Callable[[str, str], None]) -> None:
        self._car_not_reachable_callback = function_name
        return

    def _model_car_not_reachable_callback(self) -> None:
        if self._car_not_reachable_callback is not None:
            self._car_not_reachable_callback(self.vehicle_id, self.player)

    def _new_speed_calculated(self, new_speed: int) -> None:
        if self._controller is None:
            return
        super()._new_speed_calculated(new_speed)
        self._controller.change_speed_to(new_speed)

    def _new_offset_calculated(self, current_lane: int) -> None:
        if self._controller is None:
            return
        super()._new_offset_calculated(current_lane)
        self._controller.change_lane_to(current_lane, self.get_speed_with_effects_applied(self._requested_speed))

    def _uturn_starting(self):
        if self._controller is None:
            return
        super()._uturn_starting()
        self._controller.do_turn_with(Turns.A_UTURN)
