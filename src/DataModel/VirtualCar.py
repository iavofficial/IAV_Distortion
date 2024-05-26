from flask_socketio import SocketIO

from DataModel.ModelCar import ModelCar
from LocationService.LocationService import LocationService
from LocationService.Track import FullTrack
from LocationService.Trigo import Angle, Position
from VehicleManagement.EmptyController import EmptyController


class VirtualCar(ModelCar):
    def __init__(self, vehicle_id: str, track: FullTrack, socketio: SocketIO) -> None:
        super().__init__(vehicle_id, EmptyController(), track, socketio)
        self._location_service: LocationService = LocationService(track, self.__location_service_update, start_immeaditly=True)

    def __location_service_update(self, pos: Position, rot: Angle, data: dict):
        speed: float | None = data.get('speed')
        if speed is None:
            # TODO: Log via real logger
            print("Error: Location service callback didn't include the speed!")
        else:
            self._speed_actual = int(speed)

        self._on_driving_data_change()
        self._send_location_via_socketio(pos, rot)
