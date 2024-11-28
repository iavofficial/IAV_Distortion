import asyncio
import time

import pytest
from unittest.mock import Mock, MagicMock, patch

from DataModel.PhysicalCar import PhysicalCar
from DataModel.VirtualCar import VirtualCar
from EnvironmentManagement.EnvironmentManager import EnvironmentManager, RemovalReason
from EnvironmentManagement.ConfigurationHandler import ConfigurationHandler
from LocationService.LocationService import LocationService
from LocationService.Track import TrackPieceType, FullTrack
from LocationService.TrackPieces import TrackBuilder
from Minigames.Minigame_Controller import Minigame_Controller
from VehicleManagement.FleetController import FleetController
from DataModel.Vehicle import Vehicle
from VehicleMovementManagement.BehaviourController import BehaviourController


@pytest.fixture(scope="module")
def initialise_dependencies():
    fleet_ctrl_mock = Mock(spec=FleetController)
    configuration_handler_mock = Mock(spec=ConfigurationHandler)

    return fleet_ctrl_mock, configuration_handler_mock


@pytest.fixture(scope="module")
def get_mut_with_one_minute_playing_time(initialise_dependencies) -> EnvironmentManager:
    fleet_ctrl_mock, configuration_handler_mock = initialise_dependencies
    configuration_handler_mock.get_configuration.return_value = \
        {"game_config": {"game_cfg_playing_time_limit_min": 1},
         "virtual_cars_pics": {}}

    mut: EnvironmentManager = EnvironmentManager(fleet_ctrl_mock,
                                                 configuration_handler_mock)
    return mut


@pytest.fixture
def get_mut_with_endless_playing_time(initialise_dependencies) -> EnvironmentManager:
    fleet_ctrl_mock, configuration_handler_mock = initialise_dependencies
    configuration_handler_mock.get_configuration.return_value = \
        {"game_config": {"game_cfg_playing_time_limit_min": 0},
         "virtual_cars_pics": {}}

    mut: EnvironmentManager = EnvironmentManager(fleet_ctrl_mock,
                                                 configuration_handler_mock)
    return mut


@pytest.fixture(scope="module")
def get_two_dummy_vehicles() -> list[Vehicle]:
    location_service_mock = MagicMock(spec=LocationService)
    vehicle1: Vehicle = Vehicle("123", location_service_mock, disable_item_removal=True)
    vehicle2: Vehicle = Vehicle("456", location_service_mock, disable_item_removal=True)
    output: list[Vehicle] = [vehicle1, vehicle2]
    return output


@pytest.fixture(scope="module")
def get_four_dummy_vehicles() -> list[Vehicle]:
    location_service_mock = MagicMock(spec=LocationService)
    vehicle1: Vehicle = Vehicle("123", location_service_mock, disable_item_removal=True)
    vehicle2: Vehicle = Vehicle("456", location_service_mock, disable_item_removal=True)
    vehicle3: Vehicle = Vehicle("789", location_service_mock, disable_item_removal=True)
    vehicle4: Vehicle = Vehicle("012", location_service_mock, disable_item_removal=True)
    output: list[Vehicle] = [vehicle1, vehicle2, vehicle3, vehicle4]
    return output


@pytest.fixture(scope="module")
def get_two_dummy_player() -> list[str]:
    dummy1: str = "DummyPlayer1"
    dummy2: str = "DummyPlayer2"
    output: list[str] = [dummy1, dummy2]

    return output


@pytest.fixture(scope="module")
def get_four_dummy_players() -> list[str]:
    dummy1: str = "DummyPlayer1"
    dummy2: str = "DummyPlayer2"
    dummy3: str = "DummyPlayer3"
    dummy4: str = "DummyPlayer4"
    output: list[str] = [dummy1, dummy2, dummy3, dummy4]

    return output


@pytest.fixture
def get_one_dummy_vehicle() -> Vehicle:
    location_service_mock = MagicMock(spec=LocationService)
    vehicle: Vehicle = Vehicle("123", location_service_mock, disable_item_removal=True)

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
        location_service_mock = MagicMock(spec=LocationService)
        dummy_vehicle = Vehicle("vehicle1", location_service_mock, disable_item_removal=True)
        dummy_vehicle.set_player(self.dummy_player1)
        mut._add_to_active_vehicle_list(dummy_vehicle, is_physical_car=False)

        # Act / Assert
        added = mut._add_new_player(self.dummy_player1)
        assert added is False


class TestPutPlayerOnNextFreeSpot:
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_with_playing_time_check(self, get_mut_with_one_minute_playing_time, get_one_dummy_vehicle):
        # Arrange
        vehicle1: Vehicle = get_one_dummy_vehicle
        mut: EnvironmentManager = get_mut_with_one_minute_playing_time

        mut._add_to_active_vehicle_list(vehicle1, is_physical_car=False)
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
    @pytest.mark.slow
    async def test_without_playing_time_check(self, get_mut_with_endless_playing_time, get_one_dummy_vehicle):
        # Arrange
        vehicle1: Vehicle = get_one_dummy_vehicle
        mut: EnvironmentManager = get_mut_with_endless_playing_time

        mut._add_to_active_vehicle_list(vehicle1, is_physical_car=False)
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
            mut._add_to_active_vehicle_list(vehicle, is_physical_car=False)

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
            mut._add_to_active_vehicle_list(vehicle, is_physical_car=False)
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
        with patch('Minigames.Minigame_Controller.Minigame_Controller.__init__', return_value=None):
            minigame_controller_mock = MagicMock()
            minigame_controller_mock._minigame_objects = {}
            Minigame_Controller.instance = minigame_controller_mock
            Minigame_Controller.get_instance = MagicMock(return_value=MagicMock())

            vehicle1: Vehicle = get_one_dummy_vehicle
            mut: EnvironmentManager = get_mut_with_endless_playing_time

            mut._add_to_active_vehicle_list(vehicle1, is_physical_car=False)
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
        with patch('Minigames.Minigame_Controller.Minigame_Controller.__init__', return_value=None):
            minigame_controller_mock = MagicMock()
            minigame_controller_mock._minigame_objects = {}
            Minigame_Controller.instance = minigame_controller_mock
            Minigame_Controller.get_instance = MagicMock(return_value=MagicMock())

            vehicle1: Vehicle = get_one_dummy_vehicle
            mut: EnvironmentManager = get_mut_with_endless_playing_time

            mut._add_to_active_vehicle_list(vehicle1, is_physical_car=False)
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
                              (RemovalReason.PLAYER_NOT_REACHABLE, "Your player was removed from the game, "
                                                                   "because you were no longer reachable.")])
    def test_with_valid_data(self, get_mut_with_endless_playing_time, reason_parameter, expected):
        # Arrange
        with patch('Minigames.Minigame_Controller.Minigame_Controller.__init__', return_value=None):
            minigame_controller_mock = MagicMock()
            minigame_controller_mock._minigame_objects = {}
            Minigame_Controller.instance = minigame_controller_mock
            Minigame_Controller.get_instance = MagicMock(return_value=MagicMock())

            remove_player_callback_mock = Mock()
            mut: EnvironmentManager = get_mut_with_endless_playing_time
            mut.set_publish_removed_player_callback(remove_player_callback_mock)

            # Act
            result = mut._publish_removed_player("dummyplayer1", reason_parameter)

            # Assert
            assert result
            remove_player_callback_mock.assert_called_with("dummyplayer1", expected)

    def test_with_invalid_string_reason(self, get_mut_with_endless_playing_time):
        # Arrange
        with patch('Minigames.Minigame_Controller.Minigame_Controller.__init__', return_value=None):
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


def test_get_track_returns_from_config(initialise_dependencies):
    """
    This tests that the EnvironmentManager returns the track it gets from the config or None, if it's not parsable
    """
    fleet_ctrl_mock, configuration_handler_mock = initialise_dependencies
    env = EnvironmentManager(fleet_ctrl_mock, configuration_handler_mock)
    configuration_handler_mock.get_configuration.return_value = {}
    assert env.get_track() is None

    configuration_handler_mock.get_configuration.return_value = {
        'track': [
            {
                "type": "Nonexistent",
                "rotation": 90,
                "physical_id": 33,
                "length": 210,
                "diameter": 184,
                "start_line_width": 21
            }
        ]
    }
    assert env.get_track() is None

    configuration_handler_mock.get_configuration.return_value = {
        'track': [
            {
                "type": "LocationService.TrackPieces.StartPieceAfterLine",
                "rotation": 90,
                "physical_id": 33,
                "length": 210,
                "diameter": 184,
                "start_line_width": 21
            }
        ]
    }
    assert env.get_track() is not None


def test_track_notify():
    """
    Tests that the location services get notified when a new track is there due to e.g. scanning
    """
    config_mock = MagicMock()
    fleet_ctrl_mock = MagicMock(spec=FleetController)
    env_manager = EnvironmentManager(fleet_ctrl_mock, configuration_handler=config_mock)
    new_track: FullTrack = TrackBuilder() \
        .append(TrackPieceType.START_PIECE_AFTER_LINE_WE) \
        .append(TrackPieceType.CURVE_WS).build()

    # Virtual Vehicle
    virtual_location_service = MagicMock()
    virtual_vehicle = VirtualCar('Virtual Car 1', virtual_location_service, disable_item_removal=True)
    env_manager._active_anki_cars.append(virtual_vehicle)

    # "Real" Vehicle
    physical_location_service = MagicMock()
    physical_car = PhysicalCar('AA:AA:AA:AA:AA:AA', MagicMock(), physical_location_service, disable_item_removal=True)
    env_manager._active_anki_cars.append(physical_car)

    item_generator = MagicMock()
    env_manager.add_item_generator(item_generator)

    env_manager.notify_new_track(new_track)

    virtual_location_service.notify_new_track.assert_called()
    physical_location_service.notify_new_track.assert_called()
    item_generator.notify_new_track.assert_called()


@pytest.mark.skip_ci
@pytest.mark.slow
@pytest.mark.manual
@pytest.mark.one_anki_car_needed
@pytest.mark.asyncio
async def test_vehicle_removal_on_non_reachable(car_uuid: str = 'DF:8B:DC:02:2C:23'):
    """
    Tests that a vehicle gets removed when sending data doesn't succeed.
    *HOW TO RUN:* To use this test you need to start an Anki Car and let it connect. After it's connected you need to
    manually turn it off so the BLE messages don't reach the car anymore and it disconnects. If the car connection
    loss isn't encountered within 10 seconds the test will fail.
    """
    with patch('EnvironmentManagement.ConfigurationHandler.ConfigurationHandler.get_configuration',
               return_value={"virtual_cars_pics": {}}):
        fleet_ctrl = FleetController()
        config = ConfigurationHandler()
        env_manager = EnvironmentManager(fleet_ctrl, configuration_handler=config)
        behavior_controller = BehaviourController(env_manager.get_vehicle_list())
        await env_manager.connect_to_physical_car_by(car_uuid)
        for _ in range(0, 20):
            car_list = env_manager.get_vehicle_list()
            if len(car_list) == 0:
                assert True
                return
            else:
                behavior_controller.request_lane_change_for(car_uuid, 'right')
            await asyncio.sleep(0.5)
        assert False


def test_vehicle_cant_be_added_twice(get_two_dummy_vehicles):
    """
    This tests that vehicles with the same ID can only be added once
    """
    fleet_mock = MagicMock(spec=FleetController)
    config_mock = MagicMock(spec=ConfigurationHandler)
    env_manager = EnvironmentManager(fleet_mock, configuration_handler=config_mock)
    vehicle1, vehicle2 = get_two_dummy_vehicles
    location_service_mock = MagicMock(spec=LocationService)
    new_vehicle_1 = Vehicle(vehicle1.get_vehicle_id(), location_service_mock, disable_item_removal=True)
    new_vehicle_2 = Vehicle(vehicle2.get_vehicle_id(), location_service_mock, disable_item_removal=True)

    env_manager._add_to_active_vehicle_list(vehicle1, is_physical_car=False)
    env_manager._add_to_active_vehicle_list(vehicle1, is_physical_car=False)
    env_manager._add_to_active_vehicle_list(new_vehicle_1, is_physical_car=False)
    env_manager._add_to_active_vehicle_list(new_vehicle_1, is_physical_car=False)
    assert len(env_manager._active_anki_cars) == 1

    env_manager._add_to_active_vehicle_list(vehicle2, is_physical_car=False)
    env_manager._add_to_active_vehicle_list(vehicle2, is_physical_car=False)
    env_manager._add_to_active_vehicle_list(new_vehicle_2, is_physical_car=False)
    env_manager._add_to_active_vehicle_list(new_vehicle_2, is_physical_car=False)
    assert len(env_manager._active_anki_cars) == 2


class TestSwitchCars:

    def test_manage_car_switch(self, get_two_dummy_player, get_two_dummy_vehicles, initialise_dependencies):
        # Arrange
        fleet_mock = MagicMock(spec=FleetController)
        config_mock = MagicMock(spec=ConfigurationHandler)
        env_manager = EnvironmentManager(fleet_mock, configuration_handler=config_mock)

        dummy_player1, dummy_player2 = get_two_dummy_player
        dummy_vehicle1, dummy_vehicle2 = get_two_dummy_vehicles

        env_manager._add_to_active_vehicle_list(dummy_vehicle1, False)
        env_manager._add_to_active_vehicle_list(dummy_vehicle2, True)

        dummy_vehicle1.set_player(dummy_player1)
        dummy_vehicle2.set_player(dummy_player2)

        # Act
        env_manager.manage_car_switch_for(dummy_player1, dummy_vehicle2.get_vehicle_id())

        # Assert
        new_vehicle = env_manager.get_vehicle_by_player_id(dummy_player1)
        assert new_vehicle == dummy_vehicle2
        new_vehicle = env_manager.get_vehicle_by_player_id(dummy_player2)
        assert new_vehicle == dummy_vehicle1

    def test_car_switch_lower_300ms(self, get_two_dummy_player, get_two_dummy_vehicles, initialise_dependencies):
        # Arrange
        fleet_mock = MagicMock(spec=FleetController)
        config_mock = MagicMock(spec=ConfigurationHandler)
        env_manager = EnvironmentManager(fleet_mock, configuration_handler=config_mock)

        dummy_player1, dummy_player2 = get_two_dummy_player
        dummy_vehicle1, dummy_vehicle2 = get_two_dummy_vehicles

        env_manager._add_to_active_vehicle_list(dummy_vehicle1, False)
        env_manager._add_to_active_vehicle_list(dummy_vehicle2, True)

        dummy_vehicle1.set_player(dummy_player1)
        dummy_vehicle2.set_player(dummy_player2)

        # Act
        start_time = time.time()
        env_manager.manage_car_switch_for(dummy_player1, dummy_vehicle2.get_vehicle_id())
        end_time = time.time()
        duration = (end_time - start_time)
        print(f"\nTime in seconds: {duration}")

        # Assert
        assert duration <= 0.3

    def test_manage_multiple_car_switch(self, get_four_dummy_players, get_four_dummy_vehicles, initialise_dependencies):
        # Arrange
        fleet_mock = MagicMock(spec=FleetController)
        config_mock = MagicMock(spec=ConfigurationHandler)
        env_manager = EnvironmentManager(fleet_mock, configuration_handler=config_mock)

        dummy_player1, dummy_player2, dummy_player3, dummy_player4 = get_four_dummy_players
        dummy_vehicle1, dummy_vehicle2, dummy_vehicle3, dummy_vehicle4 = get_four_dummy_vehicles

        env_manager._add_to_active_vehicle_list(dummy_vehicle1, False)
        env_manager._add_to_active_vehicle_list(dummy_vehicle2, True)
        env_manager._add_to_active_vehicle_list(dummy_vehicle3, False)
        env_manager._add_to_active_vehicle_list(dummy_vehicle4, True)

        dummy_vehicle1.set_player(dummy_player1)
        dummy_vehicle2.set_player(dummy_player2)
        dummy_vehicle3.set_player(dummy_player3)
        dummy_vehicle4.set_player(dummy_player4)

        # Act
        env_manager.manage_car_switch_for(dummy_player1, dummy_vehicle2.get_vehicle_id())
        env_manager.manage_car_switch_for(dummy_player3, dummy_vehicle4.get_vehicle_id())

        # Assert
        vehicle1 = env_manager.get_vehicle_by_vehicle_id(dummy_player1)
        assert not vehicle1 == dummy_vehicle1
        vehicle3 = env_manager.get_vehicle_by_vehicle_id(dummy_player3)
        assert not vehicle3 == dummy_vehicle3


class TestProximityBasedTimer:
    def test_(self):
        pass
