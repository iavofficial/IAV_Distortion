from unittest import TestCase
from unittest.mock import Mock

from DataModel.ModelCar import ModelCar
from VehicleManagement.AnkiController import AnkiController

dummy_uuid = "F1:76:08:08:C1:00" #rot


class ModelCarTest(TestCase):

    def setUp(self) -> None:
        self.anki_controller_mock = Mock(spec=AnkiController)
        self.anki_controller_mock.change_speed_to.return_value = True
        self.anki_controller_mock.change_lane_to.return_value = True
        self.mut: ModelCar = ModelCar(dummy_uuid, self.anki_controller_mock)

    def tearDown(self) -> None:
        del self.mut

    def test_new_instance(self):
        # Arrange

        # Act
        self.mut = ModelCar(dummy_uuid, self.anki_controller_mock)

        # Assert
        assert self.mut.vehicle_id == dummy_uuid
        assert isinstance(self.mut.get_typ_of_controller(), type(AnkiController))

    def test_calculate_speed(self):
        # Arrange

        # Act/Assert
        self.mut.speed_factor = 0.5
        assert self.mut.speed == 0

        self.mut.speed_request = 100
        assert self.mut.speed == 100 * 0.5

    def test_calculate_lane_change_from_center(self):
        # Arrange

        # Act/Assert
        self.mut.lane_change_request = 1
        assert self.mut.lane_change == 1

        self.mut.lane_change_request = 1
        assert self.mut.lane_change == 2

        self.mut.lane_change_request = 2
        assert self.mut.lane_change == 4

        self.mut.lane_change_request = -1
        assert self.mut.lane_change == 3

    def test_calculate_lane_change_from_left_side(self):
        # Arrange
        self.mut._offset_from_center = -65.0

        # Act/Assert
        self.mut.lane_change_request = 1
        assert self.mut.lane_change == 1

        self.mut.lane_change_request = 1
        assert self.mut.lane_change == 2

        self.mut.lane_change_request = 2
        assert self.mut.lane_change == 4

        self.mut.lane_change_request = -1
        assert self.mut.lane_change == 3