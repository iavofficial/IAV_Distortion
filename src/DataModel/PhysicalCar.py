from bleak import BleakClient
from DataModel.ModelCar import ModelCar
from LocationService.Track import FullTrack
from VehicleManagement.AnkiController import AnkiController


class PhysicalCar(ModelCar):
    def __init__(self, vehicle_id: str, controller: AnkiController, track: FullTrack) -> None:
        super().__init__(vehicle_id, controller, track)
        self._controller: AnkiController = controller

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
