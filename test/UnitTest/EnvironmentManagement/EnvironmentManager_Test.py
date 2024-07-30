import asyncio
import pytest
from unittest import TestCase
from unittest.mock import Mock

from EnvironmentManagement.EnvironmentManager import EnvironmentManager, RemovalReason
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
    if any(vehicle.get_player_id() is not None for vehicle in mut.get_vehicle_list()):
        pytest.fail("preconditions in vehicle list not correct.")

    # Act
    mut.put_player_on_next_free_spot("dummyplayer1")
    if not any(vehicle.get_player_id() == "1" for vehicle in mut.get_vehicle_list()):
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
    if any(vehicle.get_player_id() is not None for vehicle in mut.get_vehicle_list()):
        pytest.fail("preconditions in vehicle list not correct.")

    # Act
    mut.put_player_on_next_free_spot("dummyplayer1")
    if not any(vehicle.get_player_id() == "1" for vehicle in mut.get_vehicle_list()):
        pytest.fail("preconditions in vehicle list not correct.")

    # Assert
    await asyncio.sleep(59)
    used_cars = mut.get_mapped_cars()
    assert len(used_cars) == 1

    await asyncio.sleep(12)
    used_cars = mut.get_mapped_cars()
    assert len(used_cars) == 1


# TODO vehicle was found, with and without a player; vehicle wasn't found
@pytest.mark.asyncio
def test_manage_removal_from_game_for_valid_player_id_and_reason(get_mut_with_endless_playing_time,
                                                                 get_one_dummy_vehicle):
    # Arrange
    vehicle1: Vehicle = get_one_dummy_vehicle
    mut: EnvironmentManager = get_mut_with_endless_playing_time

    mut._add_to_active_vehicle_list(vehicle1)
    if any(vehicle.get_player_id() is not None for vehicle in mut.get_vehicle_list()):
        pytest.fail("preconditions in vehicle list not correct.")

    mut.put_player_on_next_free_spot("dummyplayer1")
    mut.put_player_on_next_free_spot("dummyplayer2")
    if not sum(vehicle.get_player_id() == "dummyplayer1"
               for vehicle in mut.get_vehicle_list()) == 1:
        pytest.fail("preconditions in vehicle list not correct.")

    if not any(player == "dummyplayer2"
               for player in mut.get_waiting_player_list()):
        pytest.fail("preconditions in vehicle list not correct.")

    # Act / Assert
    assert len(mut.get_waiting_player_list()) == 1
    result = mut._manage_removal_from_game_for("dummyplayer2", RemovalReason.NONE)
    assert result
    assert len(mut.get_waiting_player_list()) == 0

    result = mut._manage_removal_from_game_for("dummyplayer1", RemovalReason.NONE)
    assert result
    assert all(vehicle.get_player_id() is None
               for vehicle in mut.get_vehicle_list())


@pytest.mark.asyncio
def test_manage_removal_from_game_for_invalid_player_id_and_reason(get_mut_with_endless_playing_time,
                                                                   get_one_dummy_vehicle):
    # Arrange
    vehicle1: Vehicle = get_one_dummy_vehicle
    mut: EnvironmentManager = get_mut_with_endless_playing_time

    mut._add_to_active_vehicle_list(vehicle1)
    if any(vehicle.get_player_id() is not None for vehicle in mut.get_vehicle_list()):
        pytest.fail("preconditions in vehicle list not correct.")

    mut.put_player_on_next_free_spot("dummyplayer1")
    mut.put_player_on_next_free_spot("dummyplayer2")
    if not any(vehicle.get_player_id() == "dummyplayer1" for vehicle in mut.get_vehicle_list()):
        pytest.fail("preconditions in vehicle list not correct.")
    if not any(player == "dummyplayer2" for player in mut.get_waiting_player_list()):
        pytest.fail("preconditions in vehicle list not correct.")

    # Act / Assert
    assert len(mut.get_waiting_player_list()) == 1
    result = mut._manage_removal_from_game_for("invalid_player_id", RemovalReason.NONE)
    assert not result
    assert len(mut.get_waiting_player_list()) == 1

    result = mut._manage_removal_from_game_for("dummyplayer2", RemovalReason.NONE)
    assert result
    result = mut._manage_removal_from_game_for("invalid_player_id", RemovalReason.NONE)
    assert not result
    assert sum(vehicle.get_player_id() == "dummyplayer1"
               for vehicle in mut.get_vehicle_list()) == 1


@pytest.mark.parametrize("reason_parameter , expected",
                         [(RemovalReason.NONE, "Your player has been removed from the game."),
                          (RemovalReason.PLAYING_TIME_IS_UP, "Your player was removed from the game, "
                                                             "because your playing time is over."),
                          (RemovalReason.NOT_REACHABLE, "Your player was removed from the game, "
                                                        "because you were no longer reachable.")])
def test_publish_removed_player(get_mut_with_endless_playing_time, reason_parameter, expected):
    # Arrange
    remove_player_callback_mock = Mock()
    mut: EnvironmentManager = get_mut_with_endless_playing_time
    mut.set_publish_removed_player_callback(remove_player_callback_mock)

    # Act
    result = mut._publish_removed_player("dummyplayer1", reason_parameter)

    # Assert
    assert result
    remove_player_callback_mock.assert_called_with(player="dummyplayer1", reason=expected)
