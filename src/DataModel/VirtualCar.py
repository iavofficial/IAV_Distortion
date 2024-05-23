from DataModel.ModelCar import ModelCar
from LocationService.Track import FullTrack
from VehicleManagement.EmptyController import EmptyController


class VirtualCar(ModelCar):
    def __init__(self, vehicle_id: str, track: FullTrack) -> None:
        super().__init__(vehicle_id, EmptyController(), track)
        self._location_service.start()
