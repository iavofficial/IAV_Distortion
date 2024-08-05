from DataModel.ModelCar import ModelCar
from LocationService.LocationService import LocationService
from LocationService.Trigo import Angle, Position
from VehicleManagement.EmptyController import EmptyController


class VirtualCar(ModelCar):
    def __init__(self, vehicle_id: str,
                 controller: EmptyController,
                 location_service: LocationService) -> None:
        super().__init__(vehicle_id)
        self._controller: EmptyController = controller
        self._location_service: LocationService = location_service
        self._location_service.set_on_update_callback(self._location_service_update)

    def __del__(self):
        self._controller.__del__()
        self._location_service.__del__()
        super().__del__()

    def _location_service_update(self, pos: Position, rot: Angle, data: dict):
        self._on_driving_data_change()
        super()._location_service_update(pos, rot, data)
