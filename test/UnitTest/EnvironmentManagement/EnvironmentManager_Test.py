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


class TestAddPlayerToQueue:
    @pytest.fixture(autouse=True)
    def value_init(self):
        self.dummy_player1 = "123"

    def test_by_adding_same_player_twice(self, get_mut_with_endless_playing_time):
        # Arrange
        mut: EnvironmentManager = get_mut_with_endless_playing_time

        # Act / Assert
        added = mut._add_player_to_queue(self.dummy_player1)
        assert added is True
        assert mut.get_waiting_players()[0] is self.dummy_player1

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


class TestAddNewPlayer:
    @pytest.fixture(autouse=True)
    def value_init(self):
        self.dummy_player1 = "123"

    def test_by_adding_same_new_player_twice(self, get_mut_with_endless_playing_time):
        # Arrange
        mut: EnvironmentManager = get_mut_with_endless_playing_time

        # Act / Assert
        added = mut._add_new_player(self.dummy_player1)
        assert added is True

        added = mut._add_new_player(self.dummy_player1)
        assert added is False

    def test_by_adding_same_player_as_in_vehicle(self, get_mut_with_endless_playing_time):
        # Arrange
        mut: EnvironmentManager = get_mut_with_endless_playing_time
        dummy_vehicle = Vehicle("vehicle1")
        dummy_vehicle.set_player(self.dummy_player1)
        mut._add_to_active_vehicle_list(dummy_vehicle)

        # Act / Assert
        added = mut._add_new_player(self.dummy_player1)
        assert added is False


class TestPutPlayerOnNextFreeSpot:
    @pytest.mark.asyncio
    async def test_with_playing_time_check(self, get_mut_with_one_minute_playing_time, get_one_dummy_vehicle):
        # Arrange
        vehicle1: Vehicle = get_one_dummy_vehicle
        mut: EnvironmentManager = get_mut_with_one_minute_playing_time

        mut._add_to_active_vehicle_list(vehicle1)
        if any(vehicle.get_player_id() is not None for vehicle in mut.get_vehicle_list()):
            pytest.fail("preconditions in vehicle list not correct.")

        # Act
        mut.put_player_on_next_free_spot("dummyplayer1")
        if not any(vehicle.get_player_id() == "dummyplayer1" for vehicle in mut.get_vehicle_list()):
            pytest.fail("preconditions in vehicle list not correct.")

        # Assert
        await asyncio.sleep(59)
        used_cars = mut.get_mapped_cars()
        assert len(used_cars) == 1
        assert used_cars[0]["player"] == "dummyplayer1"
        assert used_cars[0]["car"] == vehicle1.get_vehicle_id()

        await asyncio.sleep(12)  # greater than playing time checking interval is 10 s
        used_cars = mut.get_mapped_cars()
        assert len(used_cars) == 0

    @pytest.mark.asyncio
    async def test_without_playing_time_check(self, get_mut_with_endless_playing_time, get_one_dummy_vehicle):
        # Arrange
        vehicle1: Vehicle = get_one_dummy_vehicle
        mut: EnvironmentManager = get_mut_with_endless_playing_time

        mut._add_to_active_vehicle_list(vehicle1)
        if any(vehicle.get_player_id() is not None for vehicle in mut.get_vehicle_list()):
            pytest.fail("preconditions in vehicle list not correct.")

        # Act
        mut.put_player_on_next_free_spot("dummyplayer1")
        if not any(vehicle.get_player_id() == "dummyplayer1" for vehicle in mut.get_vehicle_list()):
            pytest.fail("preconditions in vehicle list not correct.")

        # Assert
        await asyncio.sleep(59)
        used_cars = mut.get_mapped_cars()
        assert len(used_cars) == 1
        assert used_cars[0]["player"] == "dummyplayer1"
        assert used_cars[0]["car"] == vehicle1.get_vehicle_id()

        await asyncio.sleep(12)  # greater than playing time checking interval is 10 s
        used_cars = mut.get_mapped_cars()
        assert len(used_cars) == 1
        assert used_cars[0]["player"] == "dummyplayer1"
        assert used_cars[0]["car"] == vehicle1.get_vehicle_id()


class TestAssignPlayersToVehicles:
    def test_two_players_on_free_vehicles(self,
                                          get_mut_with_endless_playing_time,
                                          get_two_dummy_vehicles,
                                          get_two_dummy_player):
        # Arrange
        mut: EnvironmentManager = get_mut_with_endless_playing_time
        dummy_vehicles: list[Vehicle] = get_two_dummy_vehicles
        dummy_players: list[str] = get_two_dummy_player

        for vehicle in dummy_vehicles:
            vehicle.remove_player()
            mut._add_to_active_vehicle_list(vehicle)

        for dummy_player in dummy_players:
            mut._add_new_player(dummy_player)

        # Act
        result = mut._assign_players_to_vehicles()

        # Assert
        assert result is True
        for vehicle in mut.get_vehicle_list():
            temp_result: bool = any(vehicle.get_player_id() == player_id for player_id in dummy_players)
            assert temp_result is True

    def test_two_players_on_taken_vehicles(self,
                                           get_mut_with_endless_playing_time,
                                           get_two_dummy_vehicles,
                                           get_two_dummy_player):
        # Arrange
        mut: EnvironmentManager = get_mut_with_endless_playing_time
        dummy_vehicles: list[Vehicle] = get_two_dummy_vehicles
        dummy_players: list[str] = get_two_dummy_player

        i: int = 3
        for vehicle in dummy_vehicles:
            vehicle.set_player("Player"+str(i))
            mut._add_to_active_vehicle_list(vehicle)
            i += 1

        for dummy_player in dummy_players:
            mut._add_new_player(dummy_player)

        # Act
        result = mut._assign_players_to_vehicles()

        # Assert
        assert result is False
        for vehicle in mut.get_vehicle_list():
            temp_result: bool = any(vehicle.get_player_id() == player_id for player_id in dummy_players)
            assert temp_result is False


class TestStartPlayingTimeChecker:
    pass


class TestStopRunningPlayingTimeChecker:
    pass


class TestManageRemovalFromGame:
    @pytest.mark.asyncio
    def test_for_valid_player_id_and_reason(self, get_mut_with_endless_playing_time,
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
                   for player in mut.get_waiting_players()):
            pytest.fail("preconditions in vehicle list not correct.")

        # Act / Assert
        assert len(mut.get_waiting_players()) == 1
        result = mut.manage_removal_from_game_for("dummyplayer2", RemovalReason.NONE)
        assert result
        assert len(mut.get_waiting_players()) == 0

        result = mut.manage_removal_from_game_for("dummyplayer1", RemovalReason.NONE)
        assert result
        assert all(vehicle.get_player_id() is None
                   for vehicle in mut.get_vehicle_list())

    @pytest.mark.asyncio
    def test_for_invalid_player_id_and_reason(self, get_mut_with_endless_playing_time,
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
        if not any(player == "dummyplayer2" for player in mut.get_waiting_players()):
            pytest.fail("preconditions in vehicle list not correct.")

        # Act / Assert
        assert len(mut.get_waiting_players()) == 1
        assert sum(vehicle.get_player_id() == "dummyplayer1"
                   for vehicle in mut.get_vehicle_list()) == 1
        result = mut.manage_removal_from_game_for("invalid_player_id", RemovalReason.NONE)
        assert not result
        assert len(mut.get_waiting_players()) == 1
        assert sum(vehicle.get_player_id() == "dummyplayer1"
                   for vehicle in mut.get_vehicle_list()) == 1


class TestPublishRemovedPlayer:
    @pytest.mark.parametrize("reason_parameter , expected",
                             [(RemovalReason.NONE, "Your player has been removed from the game."),
                              (RemovalReason.PLAYING_TIME_IS_UP, "Your player was removed from the game, "
                                                                 "because your playing time is over."),
                              (RemovalReason.NOT_REACHABLE, "Your player was removed from the game, "
                                                            "because you were no longer reachable.")])
    def test_with_valid_data(self, get_mut_with_endless_playing_time, reason_parameter, expected):
        # Arrange
        remove_player_callback_mock = Mock()
        mut: EnvironmentManager = get_mut_with_endless_playing_time
        mut.set_publish_removed_player_callback(remove_player_callback_mock)

        # Act
        result = mut._publish_removed_player("dummyplayer1", reason_parameter)

        # Assert
        assert result
        remove_player_callback_mock.assert_called_with(player="dummyplayer1", reason=expected)

    def test_with_invalid_string_reason(self, get_mut_with_endless_playing_time):
        # Arrange
        remove_player_callback_mock = Mock()
        mut: EnvironmentManager = get_mut_with_endless_playing_time
        mut.set_publish_removed_player_callback(remove_player_callback_mock)

        # Act
        result = mut._publish_removed_player("dummyplayer1", "invalid_reason")

        # Assert
        assert not result

    def test_with_invalid_int_reason(self, get_mut_with_endless_playing_time):
        # Arrange
        remove_player_callback_mock = Mock()
        mut: EnvironmentManager = get_mut_with_endless_playing_time
        mut.set_publish_removed_player_callback(remove_player_callback_mock)

        # Act
        result = mut._publish_removed_player("dummyplayer1", 10)

        # Assert
        assert not result