# Copyright 2024 IAV GmbH
#
# This file is part of the IAV-Distortion project an interactive
# and educational showcase designed to demonstrate the need
# of automotive cybersecurity in a playful, engaging manner.
# and is released under the "Apache 2.0". Please see the LICENSE
# file that should have been included as part of this package.
#
import asyncio
from unittest import TestCase
from unittest.mock import patch, AsyncMock, Mock, MagicMock, call

import pytest

from VehicleManagement.FleetController import FleetController
from EnvironmentManagement.ConfigurationHandler import ConfigurationHandler


@pytest.mark.two_anki_cars_needed
@pytest.mark.asyncio
async def test_scan_for_anki_cars() -> None:
    """
    Scan for Anki cars. Check if two Anki cars were found. No matter if cars placed on charger or not.

    Precondition:
    - exact two Anki cars turned on
    - ready to connect (LED = green)

    Expected behaviour:
    - exact two devices are found
        - both Anki cars were found
        - all other bluetooth devices are filtered out
    """
    # Arrange
    test_config_handler = ConfigurationHandler('../src/config_file.json')  # use default config_file
    fleet_ctrl = FleetController(config_handler=test_config_handler)

    # Act
    found_devices = await fleet_ctrl.scan_for_anki_cars()
    print(f"Found devices: {found_devices}")

    # Assert
    assert len(found_devices) == 2


@pytest.mark.two_anki_cars_needed
@pytest.mark.anki_car_placed_on_charger
@pytest.mark.anki_car_removed_from_charger
@pytest.mark.asyncio
async def test_scan_for_ready_anki_cars() -> None:
    """
    Scan for ready Anki cars. Check if only one Anki car (one removed from the charger) was found.

    Precondition:
    - exact two Anki cars turned on
        - one car placed on the charger
        - one car removed from the charger
    - ready to connect (LED = green)

    Expected behaviour:
    - exact one device is found
        - Anki car that is removed from the charger is found
        - all other bluetooth devices are filtered out
    """
    # Arrange
    test_config_handler = ConfigurationHandler('../src/config_file.json')  # use default config_file
    fleet_ctrl = FleetController(config_handler=test_config_handler)

    # Act
    found_devices = await fleet_ctrl.scan_for_anki_cars(only_ready=True)
    print(f"Found devices: {found_devices}")

    # Assert
    assert len(found_devices) == 1


@pytest.mark.two_anki_cars_needed
@pytest.mark.anki_car_placed_on_charger
@pytest.mark.anki_car_removed_from_charger
@pytest.mark.asyncio
async def test_auto_discover_anki_vehicles() -> None:
    """
    Test the auto discovery function.

    Preconditions:
    - one Anki car placed NOT on the charger
    - one Anki car placed on the charger
    - both Anki cars turned on and ready to connect (LED green)

    Expectation:
    - auto_discover_anki_vehicles function will be started
    - the Anki car not placed on the charger will be discovered
    - the Anki car placed on the charger will not be discovered

    Note:
    - The following exception will appear during the test, because the event loop will be terminated with pending tasks.
      This can be ignored.
        AttributeError: 'NoneType' object has no attribute 'create_future' Task was destroyed but it is pending!
    """
    # Arrange
    test_config_handler = ConfigurationHandler('TestResources/test_config_files/env_auto_discover_anki_cars-true.json')
    fleet_controller = FleetController(test_config_handler)

    mock_callback = Mock()
    fleet_controller.set_add_anki_car_callback(mock_callback)

    # Act
    await fleet_controller.start_auto_discover_anki_cars()
    await asyncio.sleep(7)  # wait some time to allow one BLE search

    # Assert
    call_count = mock_callback.call_count
    print(f'Callback was called {call_count} times')
    assert call_count == 1


@pytest.mark.asyncio
async def test_auto_discover_anki_vehicles_invalid_callback() -> None:
    """
    Test if auto discovery service is terminated if invalid callback is used.

    Precondition:
    - no special preconditions required

    Expectation:
    - if no callable callback function is set, the stop_auto_discover_anki_cars is called to terminate the service
    """
    # Arrange
    test_config_handler = ConfigurationHandler('../src/config_file.json')  # use default config_file
    with patch('VehicleManagement.FleetController.FleetController.stop_auto_discover_anki_cars') as mock_stop_auto_discover:
        fleet_controller = FleetController(test_config_handler)
        fleet_controller.set_add_anki_car_callback(None)
        fleet_controller.scan_for_anki_cars = AsyncMock(return_value=["uuid1"])

        # Act
        await fleet_controller.start_auto_discover_anki_cars()
        await asyncio.sleep(1)

        # Assert
        mock_stop_auto_discover.assert_called_once()
