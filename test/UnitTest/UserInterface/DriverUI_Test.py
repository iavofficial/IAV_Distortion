import uuid
from unittest.mock import MagicMock

import pytest

from socketio import AsyncServer

from EnvironmentManagement.EnvironmentManager import EnvironmentManager
from EnvironmentManagement.ConfigurationHandler import ConfigurationHandler
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
    configuration_handler_mock.get_configuration.return_value = \
        {"game_config": {"game_cfg_playing_time_limit_min": 0}}

    socket = AsyncServer(async_mode='asgi')
    fleet_ctrl = FleetController()

    environment_manager = EnvironmentManager(fleet_ctrl, configuration_handler_mock)
    vehicles = environment_manager.get_vehicle_list()
    behaviour_ctrl = BehaviourController(vehicles)

    driver_ui = DriverUI(behaviour_ctrl=behaviour_ctrl, environment_mng=environment_manager, sio=socket)

    vehicle: Vehicle = Vehicle('1234', disable_item_removal=True)

    return driver_ui, environment_manager, vehicle


@pytest.mark.asyncio
async def test_driver_ui_template_data_player_exists(initialise_dependencies):
    """
    Test whether the player_exists boolean put into the HTML template is correct for 2 players and 1 vehicle
    """
    player_1 = str(uuid.uuid4())
    player_2 = str(uuid.uuid4())

    driver_ui, environment_manager, vehicle = initialise_dependencies
    environment_manager._add_to_active_vehicle_list(vehicle)

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
