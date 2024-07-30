import asyncio
import pytest
from unittest import TestCase
from unittest.mock import Mock

from EnvironmentManagement.EnvironmentManager import EnvironmentManager
from EnvironmentManagement.ConfigurationHandler import ConfigurationHandler
from VehicleManagement.FleetController import FleetController
from DataModel.Vehicle import Vehicle


@pytest.fixture()
def initialise_dependencies():
    fleet_ctrl_mock = Mock(spec=FleetController)
    configuration_handler_mock = Mock(spec=ConfigurationHandler)

    return fleet_ctrl_mock, configuration_handler_mock


@pytest.fixture()
def get_mut_with_one_minute_playing_time(initialise_dependencies) -> EnvironmentManager:
    fleet_ctrl_mock,  configuration_handler_mock = initialise_dependencies
    configuration_handler_mock.get_configuration.return_value = \
        {"game_config": {"game_cfg_playing_time_limit_min": 1}}

    mut: EnvironmentManager = EnvironmentManager(fleet_ctrl_mock,
                                                 configuration_handler_mock)
    return mut


@pytest.fixture()
def get_mut_with_endless_playing_time(initialise_dependencies) -> EnvironmentManager:
    fleet_ctrl_mock, configuration_handler_mock = initialise_dependencies
    configuration_handler_mock.get_configuration.return_value = \
        {"game_config": {"game_cfg_playing_time_limit_min": 0}}

    mut: EnvironmentManager = EnvironmentManager(fleet_ctrl_mock,
                                                 configuration_handler_mock)
    return mut


@pytest.fixture()
def get_two_dummy_vehicles():
    vehicle1: Vehicle = Vehicle("123")
    vehicle2: Vehicle = Vehicle("456")

    return vehicle1, vehicle2


@pytest.fixture
def get_one_dummy_vehicle() -> Vehicle:
    vehicle: Vehicle = Vehicle("123")

    return vehicle


@pytest.mark.asyncio
async def test_put_player_on_next_free_spot_with_playing_time_check(get_mut_with_one_minute_playing_time, get_one_dummy_vehicle):
    # Arrange
    vehicle1: Vehicle = get_one_dummy_vehicle
    mut: EnvironmentManager = get_mut_with_one_minute_playing_time

    mut._add_to_active_vehicle_list(vehicle1)
    if any(vehicle.get_player() is not None for vehicle in mut.get_vehicle_list()):
        pytest.fail("preconditions in vehicle list not correct.")

    # Act
    mut.put_player_on_next_free_spot("1")
    if not any(vehicle.get_player() == "1" for vehicle in mut.get_vehicle_list()):
        pytest.fail("preconditions in vehicle list not correct.")

    # Assert
    await asyncio.sleep(59)
    used_cars = mut.get_mapped_cars()
    assert len(used_cars) == 1

    await asyncio.sleep(12)
    used_cars = mut.get_mapped_cars()
    assert len(used_cars) == 0


@pytest.mark.asyncio
async def test_put_player_on_next_free_spot_without_playing_time_check(get_mut_with_endless_playing_time, get_one_dummy_vehicle):
    # Arrange
    vehicle1: Vehicle = get_one_dummy_vehicle
    mut: EnvironmentManager = get_mut_with_endless_playing_time

    mut._add_to_active_vehicle_list(vehicle1)
    if any(vehicle.get_player() is not None for vehicle in mut.get_vehicle_list()):
        pytest.fail("preconditions in vehicle list not correct.")

    # Act
    mut.put_player_on_next_free_spot("1")
    if not any(vehicle.get_player() == "1" for vehicle in mut.get_vehicle_list()):
        pytest.fail("preconditions in vehicle list not correct.")

    # Assert
    await asyncio.sleep(59)
    used_cars = mut.get_mapped_cars()
    assert len(used_cars) == 1

    await asyncio.sleep(12)
    used_cars = mut.get_mapped_cars()
    assert len(used_cars) == 1
