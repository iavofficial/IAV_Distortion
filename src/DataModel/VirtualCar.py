import logging
from DataModel.Vehicle import Vehicle
from LocationService.LocationService import LocationService
from LocationService.Trigo import Angle, Position

logger = logging.getLogger(__name__)


class VirtualCar(Vehicle):
    def __init__(self, vehicle_id: str,
                 location_service: LocationService,
                 disable_item_removal=False) -> None:
        super().__init__(vehicle_id, location_service, disable_item_removal=disable_item_removal)
        self._location_service.add_on_update_callback(self._location_service_update)

        return

    def __del__(self):
        self._location_service.__del__()
        super().__del__()

    def _location_service_update(self, pos: Position, rot: Angle, data: dict) -> None:
        speed: float | None = data.get('speed')
        if speed is None:
            logger.error("Location service callback didn't include speed!")
        else:
            self._current_driving_speed = int(speed)

        offset: float | None = data.get('offset')
        if offset is None:
            logger.error("Location service callback didn't include offset!")
        else:
            self._offset_from_center = offset
        self._on_driving_data_change()
        super()._location_service_update(pos, rot, data)

        return
