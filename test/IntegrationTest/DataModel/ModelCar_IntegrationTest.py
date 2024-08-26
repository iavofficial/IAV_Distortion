from unittest import TestCase

import pytest

from DataModel.PhysicalCar import PhysicalCar
from VehicleManagement.AnkiController import AnkiController
from VehicleManagement.FleetController import FleetController

from LocationService.TrackPieces import TrackBuilder, FullTrack
from LocationService.Track import TrackPieceType

dummy_vehicleID = "123456789"

def get_dummy_track() -> FullTrack:
        track: FullTrack = TrackBuilder()\
            .append(TrackPieceType.STRAIGHT_WE)\
            .build()
        return track


def dummy_callback(vehicle_id: str, player: str, err_msg: str):
    print(f"Error occurred on {vehicle_id} from player {player}. {err_msg}")

@pytest.mark.skip_ci
class ModelCaIntegrationTest(TestCase):

    def setUp(self) -> None:
        self.dummy_uuid = FleetController().scan_for_anki_cars()[0]
        self.anki_controller: AnkiController = AnkiController()
        self.mut: PhysicalCar = PhysicalCar(dummy_vehicleID, self.anki_controller, get_dummy_track())
        self.mut.set_vehicle_not_reachable_callback(dummy_callback)

    def tearDown(self) -> None:
        del self.mut

    def test_on_model_car_not_reachable(self):
        # Arrange
        if not self.mut.initiate_connection(self.dummy_uuid):
            assert False

        # Act
        self.mut.speed_request = 1

        # Assert
        assert self.mut._battery != ""
        assert self.mut._version != ""
        return
