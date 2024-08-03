import asyncio
import pytest
from unittest.mock import Mock

from EnvironmentManagement.EnvironmentManager import EnvironmentManager, RemovalReason
from EnvironmentManagement.ConfigurationHandler import ConfigurationHandler
from VehicleManagement.FleetController import FleetController
from DataModel.Vehicle import Vehicle


@pytest.fixture(scope="module")
def initialise_dependencies():
    fleet_ctrl_mock = Mock(spec=FleetController)
    configuration_handler_mock = Mock(spec=ConfigurationHandler)

    return fleet_ctrl_mock, configuration_handler_mock


@pytest.fixture(scope="module")
def get_mut_with_one_minute_playing_time(initialise_dependencies) -> EnvironmentManager:
    fleet_ctrl_mock, configuration_handler_mock = initialise_dependencies
    configuration_handler_mock.get_configuration.return_value = \
        {"game_config": {"game_cfg_playing_time_limit_min": 1}}

    mut: EnvironmentManager = EnvironmentManager(fleet_ctrl_mock,
                                                 configuration_handler_mock)
    return mut


@pytest.fixture(scope="module")
def get_mut_with_endless_playing_time(initialise_dependencies) -> EnvironmentManager:
    fleet_ctrl_mock, configuration_handler_mock = initialise_dependencies
    configuration_handler_mock.get_configuration.return_value = \
        {"game_config": {"game_cfg_playing_time_limit_min": 0}}

    mut: EnvironmentManager = EnvironmentManager(fleet_ctrl_mock,
                                                 configuration_handler_mock)
    return mut


@pytest.fixture(scope="module")
def get_two_dummy_vehicles() -> list[Vehicle]:
    vehicle1: Vehicle = Vehicle("123")
    vehicle2: Vehicle = Vehicle("456")
    output: list[Vehicle] = [vehicle1, vehicle2]
    return output

@pytest.fixture(scope="module")
def get_two_dummy_player() -> list[str]:
    dummy1: str = "DummyPlayer1"
    dummy2: str = "DummyPlayer2"
    output: list[str] = [dummy1, dummy2]

    return output

@pytest.fixture(scope="module")
def get_one_dummy_vehicle() -> Vehicle:
    vehicle: Vehicle = Vehicle("123")

    return vehicle


@pytest.fixture
def create_inputs_with_expected_false(request):
    input_values = request.instance.invalid_player_ids
    testparameter: list[(str, bool)] = [(input_value, False) for input_value in input_values]

    return testparameter


def create_inputs(input_values: list[str] = None) -> list[(str, bool)]:
    if input_values is None:
        input_values = ["", "   ", "@#$%^&*()", 2, 3.5]
    testparameter: list[(str, bool)] = [(input_value, False) for input_value in input_values]

    return testparameter


class AddPlayerToQueueTest:
    @pytest.fixture(autouse=True)
    def value_init(self):
        self.dummy_player1 = "123"

    def test_by_adding_same_player_twice(self, get_mut_with_endless_playing_time):
        # Arrange
        mut: EnvironmentManager = get_mut_with_endless_playing_time

        # Act / Assert
        added = mut._add_player_to_queue(self.dummy_player1)
        assert added is True
        assert mut.get_waiting_player_list()[0] is self.dummy_player1

        added = mut._add_player_to_queue(self.dummy_player1)
        assert added is False

    @pytest.mark.parametrize("invalid_string, expected", create_inputs())
    def test_with_invalid_player_id(self, get_mut_with_endless_playing_time, invalid_string, expected):
        # Arrange
        mut: EnvironmentManager = get_mut_with_endless_playing_time

        # Act
        added = mut._add_player_to_queue(invalid_string)

        # Assert
        assert added == expected


