from time import sleep
from unittest.mock import Mock

from DataModel.Vehicle import Vehicle
from VehicleManagement.VehicleController import VehicleController
from VehicleManagement.FleetController import FleetController

dummy_uuid = "FA:14:67:0F:39:FE"


def test_get_location():
    vctrl = VehicleController()
    fleet_ctrl = FleetController()

    found_vehicles = fleet_ctrl.scan_for_anki_cars()
    mut = Vehicle(found_vehicles[0], vctrl)

    mut.speed_request = 80.0

    sleep(5)

    mut.speed_request = 0.0

    assert mut


def test_get_driving_data() -> None:
    # Arrange
    vehicle_controller_mock = Mock()
    vehicle_controller_mock.connect_to_vehicle.return_value = False
    mut = Vehicle(dummy_uuid, vehicle_controller_mock)
    mut.player = "Player 1"
    mut._speed_actual = 333
    mut.hacking_scenario = "test_scenario"

    # Act
    driving_data = mut.get_driving_data()

    # Assert
    assert driving_data


def test_on_driving_data_change() -> None:
    # Arrange
    vehicle_controller_mock = Mock()
    vehicle_controller_mock.connect_to_vehicle.return_value = False
    mut = Vehicle(dummy_uuid, vehicle_controller_mock)
    mut.player = "Player 1"
    mut._speed_actual = 333

    receive_callback_mock = Mock()
    mut.set_driving_data_callback(receive_callback_mock)

    # Act
    mut.hacking_scenario = "test_scenario"

    # Assert
    receive_callback_mock.assert_called_once()