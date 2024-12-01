from unittest.mock import MagicMock, patch

import pytest

import EnvironmentManagement
from DataModel.Vehicle import Vehicle
from LocationService.Trigo import Position
from UserInterface.CarMap import CarMap


class TestVehicleProximity:

    @pytest.fixture(autouse=True)
    def setup_mocks(self):
        self.env_manager_mock = MagicMock(spec=EnvironmentManagement)
        self.location_service_mock = MagicMock()

        with patch('asyncio.create_task') as create_task_mock:
            create_task_mock.return_value = MagicMock()

            self.vehicle1 = Vehicle(vehicle_id="car1", location_service=self.location_service_mock)
            self.vehicle2 = Vehicle(vehicle_id="car2", location_service=self.location_service_mock)

            self.vehicle1._location_service._current_position = Position(100, 100)
            self.vehicle2._location_service._current_position = Position(200, 200)

            def mock_get_vehicle_by_vehicle_id(vehicle_id):
                if vehicle_id == "car1":
                    return self.vehicle1
                elif vehicle_id == "car2":
                    return self.vehicle2
                return None

            self.env_manager_mock.get_vehicle_by_vehicle_id \
                = MagicMock(side_effect=mock_get_vehicle_by_vehicle_id)
            self.env_manager_mock.get_vehicle_list = MagicMock(return_value=[self.vehicle1, self.vehicle2])
            self.env_manager_mock.get_item_collision_detector = MagicMock(return_value=MagicMock())

            self.env_manager_mock._active_virtual_cars = ["car1"]
            self.env_manager_mock._active_physical_cars = ["car2"]

            self.car_map = CarMap(self.env_manager_mock, sio=MagicMock())

    def test_check_virtual_vehicle_proximity(self):
        # Act
        self.car_map.check_virtual_vehicle_proximity("car1", {"x": 100, "y": 100})

        # Assert
        assert self.vehicle1.vehicle_in_proximity == "car2"
        assert self.vehicle2.vehicle_in_proximity == "car1"

    def test_check_virtual_vehicle_leave_proximity(self):
        # Arrange
        self.car_map.check_virtual_vehicle_proximity("car1", {"x": 100, "y": 100})
        assert self.vehicle1.vehicle_in_proximity == "car2"

        # Act
        self.vehicle2._location_service._current_position = Position(250, 250)
        self.car_map.check_virtual_vehicle_proximity("car1", {"x": 100, "y": 100})

        # Assert
        assert not self.vehicle1.vehicle_in_proximity == "car2"
        assert not self.vehicle2.vehicle_in_proximity == "car1"
