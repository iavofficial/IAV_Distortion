from unittest import TestCase
from unittest.mock import Mock

from LocationService.PhysicalLocationService import PhysicalLocationService
from TestingTools import generate_mac_address

from DataModel.PhysicalCar import PhysicalCar
from VehicleManagement.AnkiController import AnkiController


class ModelCarTest(TestCase):

    def setUp(self) -> None:
        self.anki_controller_mock = Mock(spec=AnkiController)
        self.anki_controller_mock.change_speed_to.return_value = True
        self.anki_controller_mock.change_lane_to.return_value = True
        self.physical_location_service_mock = Mock(spec=PhysicalLocationService)

        self.dummy_uuid = generate_mac_address()

    def tearDown(self) -> None:
        del self.mut

    def test_get_typ_of_controller(self):
        # Arrange

        # Act
        self.mut = PhysicalCar(self.dummy_uuid, self.anki_controller_mock, self.physical_location_service_mock)

        # Assert
        assert self.mut.vehicle_id == self.dummy_uuid
        assert isinstance(self.mut.get_typ_of_controller(), type(AnkiController))

    def test_calculate_speed(self):
        # Arrange
        self.mut: PhysicalCar = PhysicalCar(self.dummy_uuid, self.anki_controller_mock,
                                            self.physical_location_service_mock)

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
