from time import sleep
from unittest.mock import Mock

from DataModel.Vehicle import Vehicle
from VehicleManagement.VehicleController import VehicleController


dummy_uuid = "F1:76:08:08:C1:00" #rot


def test_on_driving_data_change() -> None:
    # Arrange
    vehicle_controller = VehicleController()
    mut = Vehicle(dummy_uuid, vehicle_controller)
    if mut.initiate_connection(dummy_uuid) is False:
        assert False

    mut.player = "1"
    mut.set_driving_data_callback(return_driving_data)

    # Act
    mut.hacking_scenario = "test_scenario"
    mut.speed_request = 100
    sleep(4)
    mut.speed_request = 75
    sleep(2)
    mut.speed_request = 0
    del mut


def return_driving_data(data: dict) -> None:
    print(f"return_driving_data: {data}")
    return