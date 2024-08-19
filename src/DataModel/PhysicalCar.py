from bleak import BleakClient
from DataModel.ModelCar import ModelCar
from LocationService.LocationService import LocationService
from LocationService.PhysicalLocationService import PhysicalLocationService
from VehicleManagement.AnkiController import AnkiController


def clamp(val: float, minimum: float, maximum: float) -> float:
    """
    Restricts the value range of value to a minimum and maximum boundary
    """
    return min(maximum, max(minimum, val))


class PhysicalCar(ModelCar):
    def __init__(self,
                 vehicle_id: str,
                 controller: AnkiController,
                 location_service: PhysicalLocationService) -> None:
        super().__init__(vehicle_id)
        self._controller: AnkiController = controller
        self._location_service: PhysicalLocationService = location_service
        self._location_service.set_on_update_callback(self._location_service_update)

    def __del__(self):
        self._controller.__del__()
        self._location_service.__del__()
        super().__del__()

    async def initiate_connection(self, uuid: str) -> bool:
        if await self._controller.connect_to_vehicle(BleakClient(uuid), True):
            self._controller.set_ble_not_reachable_callback(self._on_model_car_not_reachable)
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

    def get_typ_of_controller(self) -> AnkiController:
        return type(self._controller)

    def get_typ_of_location_service(self) -> LocationService:
        return type(self._location_service)

    def _receive_location(self, value_tuple) -> None:
        super()._receive_location(value_tuple)
        location, piece, offset, _, _ = value_tuple
        offset = clamp(offset, -66.5, 66.5)
        self._location_service.notify_location_event(piece, location, offset, self._speed_actual)

    def _receive_transition(self, value_tuple) -> None:
        super()._receive_transition(value_tuple)
        _, _, offset, _ = value_tuple
        offset = clamp(offset, -66.5, 66.5)
        self._location_service.notify_transition_event(offset)
