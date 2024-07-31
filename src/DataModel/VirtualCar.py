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
        self._location_service.set_on_update_callback(self.__location_service_update)

    def __del__(self):
        self._controller.__del__()
        self._location_service.__del__()
        super().__del__()

    def __location_service_update(self, pos: Position, rot: Angle, data: dict):
        speed: float | None = data.get('speed')
        if speed is None:
            # TODO: Log via real logger
            print("Error: Location service callback didn't include the speed!")
        else:
            self._speed_actual = int(speed)

        offset: float | None = data.get('offset')
        if offset is None:
            print("Error: Location service callback didn't include the offset!")
        else:
            self._offset_from_center = offset

        self._on_driving_data_change()
        self._on_virtual_location_update(pos, rot, {})
