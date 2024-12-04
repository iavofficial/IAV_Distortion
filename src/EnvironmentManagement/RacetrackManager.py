from DataModel.InitializationCar import InitializationCar

from EnvironmentManagement.ConfigurationHandler import ConfigurationHandler
from EnvironmentManagement.EnvironmentManager import logger

from LocationService.TrackPieces import FullTrack
from LocationService.TrackSerialization \
    import PieceDecodingException, parse_list_of_dicts_to_full_track

from VehicleManagement.AnkiController import AnkiController


class RacetrackManager:
    def __init__(self,
                 configuration_handler: ConfigurationHandler = ConfigurationHandler()) -> None:
        self.config_handler = configuration_handler
        return

    def get_fulltrack(self) -> FullTrack | None:
        """
        Get the used track in the simulation
        """
        track = self.config_handler.get_configuration().get('track')
        if track is None:
            return None
        try:
            full_track = parse_list_of_dicts_to_full_track(track)
            return full_track
        except PieceDecodingException as e:
            logger.error("Couldn't parse track from config: %s", e)
        return None

    async def scan_track(self, controller: AnkiController) -> FullTrack | None:
        """
        Scans a track and notifies when the scanning finished.
        Returns
        -------
        A error message, if the scanning isn't possible (e.g. the car isn't available) or None in case of success
        """
        init_car = InitializationCar(controller)
        track_list = await init_car.run()
        if track_list is not None:
            new_track = FullTrack(track_list)
        return new_track
