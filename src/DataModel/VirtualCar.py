from DataModel.ModelCar import ModelCar
from LocationService.LocationService import LocationService
from LocationService.Track import FullTrack
from LocationService.Trigo import Angle, Position
from VehicleManagement.EmptyController import EmptyController


class VirtualCar(ModelCar):
    def __init__(self, vehicle_id: str,
                 controller: EmptyController,
                 location_service: LocationService,
                 disable_item_removal=False) -> None:
        super().__init__(vehicle_id, disable_item_removal=disable_item_removal)
        self._controller: EmptyController = controller
        self._location_service: LocationService = location_service
        self._location_service.add_on_update_callback(self._location_service_update)

        return

    def __del__(self):
        self._controller.__del__()
        self._location_service.__del__()
        super().__del__()

    def _location_service_update(self, pos: Position, rot: Angle, data: dict) -> None:
        self._on_driving_data_change()
        super()._location_service_update(pos, rot, data)

        return

    def notify_new_track(self, new_track: FullTrack) -> None:
        self._location_service.notify_new_track(new_track)

        return
