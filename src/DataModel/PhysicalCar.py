from bleak import BleakClient
from DataModel.ModelCar import ModelCar
from LocationService.LocationService import LocationService
from VehicleManagement.AnkiController import AnkiController


class PhysicalCar(ModelCar):
    def __init__(self,
                 vehicle_id: str,
                 controller: AnkiController,
                 location_service: LocationService) -> None:
        super().__init__(vehicle_id)
        self._controller: AnkiController = controller
        self._location_service: LocationService = location_service
        self._location_service.set_on_update_callback(self._location_service_update)

    def __del__(self):
        self._controller.__del__()
        self._location_service.__del__()
        super().__del__()

    async def initiate_connection(self, uuid: str) -> bool:
        if await self._controller.connect_to_vehicle(BleakClient(uuid), True):
            self._controller.set_callbacks(self._receive_location,
                                           self._receive_transition,
                                           self._receive_offset_update,
                                           self._receive_version,
                                           self._receive_battery,
                                           self._on_model_car_not_reachable)
            self._controller.request_version()
            self._controller.request_battery()
            return True
        else:
            return False

    def get_typ_of_controller(self) -> AnkiController:
        return type(self._controller)

    def get_typ_of_location_service(self) -> LocationService:
        return type(self._location_service)
