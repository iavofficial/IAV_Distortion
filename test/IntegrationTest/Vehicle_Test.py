from time import sleep
from unittest.mock import Mock

import sys
import os
sys.path.append(os.path.abspath('../../src'))

from DataModel.Vehicle import Vehicle
from VehicleManagement.VehicleController import VehicleController


dummy_uuid = "FA:14:67:0F:39:FE"


def test_on_driving_data_change() -> None:
    print('1')
    # Arrange
    vehicle_controller = VehicleController()
    mut = Vehicle(dummy_uuid, vehicle_controller)
    mut.player = "1"

    mut.set_driving_data_callback(return_driving_data)

    # Act
    mut.hacking_scenario = "test_scenario"
    mut.speed_request = 200
    sleep(5)
    mut.speed_request = 250
    sleep(2)
    mut.speed_request = 0
    del mut


def return_driving_data(data: dict) -> None:
    print(f"return_driving_data: {data}")
    return


test_on_driving_data_change()