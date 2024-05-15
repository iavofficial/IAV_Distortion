from unittest import TestCase

from DataModel.ModelCar import ModelCar
from VehicleManagement.AnkiController import AnkiController
from VehicleManagement.FleetController import FleetController

dummy_vehicleID = "123456789"


def dummy_callback(vehicle_id: str, player: str, err_msg: str):
    print(f"Error occurred on {vehicle_id} from player {player}. {err_msg}")

class ModelCaIntegrationTest(TestCase):

    def setUp(self) -> None:
        self.dummy_uuid = FleetController().scan_for_anki_cars()[0]
        self.anki_controller: AnkiController = AnkiController()
        self.mut: ModelCar = ModelCar(dummy_vehicleID, self.anki_controller)
        self.mut.set_model_car_not_reachable_callback(dummy_callback)

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
