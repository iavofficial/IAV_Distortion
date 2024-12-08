import asyncio
import time
import asyncio
import time
import uuid
from unittest.mock import MagicMock, patch

import pytest

from socketio import AsyncServer

from EnvironmentManagement.EnvironmentManager import EnvironmentManager
from EnvironmentManagement.ConfigurationHandler import ConfigurationHandler
from LocationService.LocationService import LocationService
from Minigames.Minigame_Controller import Minigame_Controller
from UserInterface.DriverUI import DriverUI
from VehicleManagement.FleetController import FleetController
from DataModel.Vehicle import Vehicle
from VehicleMovementManagement.BehaviourController import BehaviourController


@pytest.fixture()
def initialise_dependencies():
    """
    Prepare a DriverUI, Environment Vehicle and Vehicle
    """
    configuration_handler_mock = MagicMock(spec=ConfigurationHandler)
    configuration_handler_mock.get_configuration.return_value = {
                        "virtual_cars_pics": {"AB:CD:EF:12:34:56": "ABCDEF123456.svg",
                                              "GH:IJ:KL:78:90:21": "GHIJKL789021.svg"},
                        "driver": {"key1": "value1", "key2": "value2"},
                        "game_config": {"game_cfg_playing_time_limit_min": 0}}

    socket = AsyncServer(async_mode='asgi')
    fleet_ctrl = FleetController()

    environment_manager = EnvironmentManager(fleet_ctrl, configuration_handler_mock)
    vehicles = environment_manager.get_vehicle_list()
    behaviour_ctrl = BehaviourController(vehicles)

    driver_ui = DriverUI(behaviour_ctrl=behaviour_ctrl, environment_mng=environment_manager, sio=socket)

    location_service_mock = MagicMock(spec=LocationService)


    vehicle: Vehicle = Vehicle('1234', location_service_mock, disable_item_removal=True)

    return driver_ui, environment_manager, vehicle


@pytest.mark.asyncio
async def test_driver_ui_template_data_player_exists(initialise_dependencies):
    """
    Test whether the player_exists boolean put into the HTML template is correct for 2 players and 1 vehicle
    """
    player_1 = str(uuid.uuid4())
    player_2 = str(uuid.uuid4())

    driver_ui, environment_manager, vehicle = initialise_dependencies
    environment_manager._add_to_active_vehicle_list(vehicle, is_physical_car=False)

    # player 1 has vehicle
    has_vehicle, _, _ = driver_ui._prepare_html_data(player_1)
    assert has_vehicle
    has_vehicle, _, _ = driver_ui._prepare_html_data(player_1)
    assert has_vehicle
    has_vehicle, _, _ = driver_ui._prepare_html_data(player_2)
    assert not has_vehicle
    has_vehicle, _, _ = driver_ui._prepare_html_data(player_1)
    assert has_vehicle
    has_vehicle, _, _ = driver_ui._prepare_html_data(player_2)
    assert not has_vehicle

        # Remove player 1 from the vehicle
        environment_manager.manage_removal_from_game_for(player_1)
        # Now player 2 has the car
        has_vehicle, _, _ = driver_ui._prepare_html_data(player_1)
        assert not has_vehicle
        has_vehicle, _, _ = driver_ui._prepare_html_data(player_1)
        assert not has_vehicle
        has_vehicle, _, _ = driver_ui._prepare_html_data(player_2)
        assert has_vehicle
        has_vehicle, _, _ = driver_ui._prepare_html_data(player_1)
        assert not has_vehicle
        has_vehicle, _, _ = driver_ui._prepare_html_data(player_2)
        assert has_vehicle


@pytest.mark.asyncio
async def test_proximity_timer_increment(initialise_dependencies):
    # Arrange
    player_1 = str(uuid.uuid4())
    player_2 = str(uuid.uuid4())

    driver_ui, env_manager, vehicle = initialise_dependencies

    vehicle2 = Vehicle("5678", location_service=MagicMock(spec=LocationService), disable_item_removal=False)
    vehicle2.set_player(player_2)
    vehicle.set_player(player_1)

    vehicle.vehicle_in_proximity = "5678"
    vehicle2.vehicle_in_proximity = "1234"
    vehicle.proximity_timer = time.time()

    env_manager._active_virtual_cars = ["1234", "5678"]
    env_manager.add_virtual_vehicle()

    # Act
    driver_ui._prepare_html_data(player_1)
    await asyncio.sleep(6)

    # Assert
    assert time.time() - vehicle.proximity_timer > 5
