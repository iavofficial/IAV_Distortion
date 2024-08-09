import asyncio
from unittest.mock import Mock

import pytest

from DataModel.Vehicle import Vehicle
from EnvironmentManagement.ConfigurationHandler import ConfigurationHandler
from EnvironmentManagement.EnvironmentManager import EnvironmentManager
from VehicleManagement.FleetController import FleetController


@pytest.fixture()
def initialise_dependencies():
    config = ConfigurationHandler()

    fleet_ctrl = FleetController()

    environment_manager = EnvironmentManager(fleet_ctrl, config)
    return environment_manager


@pytest.mark.manual
@pytest.mark.one_anki_car_needed
@pytest.mark.asyncio
async def test_physical_vehicle_publishes_location(initialise_dependencies, mac_address: str = 'FE:9A:8F:15:50:8F'):
    """
    Test that the PhysicalCar sends some it's position (from the LocationService) via the callback
    """
    environment_manager: EnvironmentManager
    environment_manager = initialise_dependencies
    await environment_manager.connect_to_physical_car_by(mac_address)

    vehicles: list[Vehicle] = environment_manager.get_vehicle_list()
    assert len(vehicles) == 1

    car = vehicles[0]
    virtual_location_update_callback_mock = Mock()
    car.set_virtual_location_update_callback(virtual_location_update_callback_mock)
    await asyncio.sleep(1)
    virtual_location_update_callback_mock.assert_called()
    assert virtual_location_update_callback_mock.call_count > 3
