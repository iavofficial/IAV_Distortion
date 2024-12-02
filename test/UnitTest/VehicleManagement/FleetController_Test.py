# Copyright 2024 IAV GmbH
#
# This file is part of the IAV Distortion project an interactive
# and educational showcase designed to demonstrate the need
# of automotive cybersecurity in a playful, engaging manner.
# and is released under the "Apache 2.0". Please see the LICENSE
# file that should have been included as part of this package.
#
import asyncio
from unittest.mock import patch, AsyncMock

import pytest

from VehicleManagement.FleetController import FleetController
from EnvironmentManagement.ConfigurationHandler import ConfigurationHandler


@pytest.mark.skip_ci
@pytest.mark.slow
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


@pytest.mark.skip_ci
@pytest.mark.slow
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


@pytest.mark.skip_ci
@pytest.mark.slow
@pytest.mark.asyncio
async def test_auto_discover_anki_vehicles() -> None:
    """
    Test the auto discovery function.

    Preconditions:
    - no special preconditions required

    Expectation:
    - auto_discover_anki_vehicles function will be started
    - the mocked add_anki_car_callback will be called once with the mocked return_value of scan_for_anki_cars

    Note:
    - The following exception will appear during the test, because the event loop will be terminated with pending tasks.
      This can be ignored.
        AttributeError: 'NoneType' object has no attribute 'create_future' Task was destroyed but it is pending!
    """
    # Arrange
    test_config_handler = ConfigurationHandler('TestResources/test_config_files/env_auto_discover_anki_cars-true.json')
    fleet_controller = FleetController(test_config_handler)
    test_uuid = "uuid1"
    fleet_controller.scan_for_anki_cars = AsyncMock(return_value=[test_uuid])

    mock_callback = AsyncMock()
    fleet_controller.set_add_anki_car_callback(mock_callback)

    # Act
    await fleet_controller.start_auto_discover_anki_cars()
    await asyncio.sleep(2)  # wait some time to allow one BLE search
    fleet_controller.stop_auto_discover_anki_cars()

    # Assert
    mock_callback.assert_called_once_with(test_uuid)


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
    with patch('VehicleManagement.FleetController.FleetController.stop_auto_discover_anki_cars') as\
            mock_stop_auto_discover:
        fleet_controller = FleetController(test_config_handler)
        fleet_controller.set_add_anki_car_callback(None)
        test_uuid = "uuid1"
        fleet_controller.scan_for_anki_cars = AsyncMock(return_value=[test_uuid])

        # Act
        await fleet_controller.start_auto_discover_anki_cars()
        await asyncio.sleep(0.1)

        # Assert
        mock_stop_auto_discover.assert_called_once()


@pytest.mark.slow
@pytest.mark.asyncio
async def test_start_stop_auto_discover_anki_cars() -> None:
    """
    Test if FleetController.start_auto_discover_anki_cars() starts the auto discovery service AND if
    FleetController.stop_auto_discover_anki_cars() stops the auto discovery service.

    Precondition:
    - no special preconditions required

    Expectation:
    - after starting the auto_discover service the attribute __auto_connect_anki_cars_task is an asyncio.Task
    - after starting the auto_discover service the add_anki_car_callback is called at least once

    - after stopping the auto_discover service the add_anki_car_callback is not called anymore
    - after stopping the auto_discover service the attribute __auto_connect_anki_cars_task is reseted to None
    """
    # Arrange
    config_handler = ConfigurationHandler('../src/config_file.json')  # use default config_file

    fleet_ctrl = FleetController(config_handler=config_handler)
    mock_add_car_callback = AsyncMock()
    fleet_ctrl.set_add_anki_car_callback(mock_add_car_callback)
    fleet_ctrl.scan_for_anki_cars = AsyncMock(return_value=["uuid1"])

    # Act 1
    await fleet_ctrl.start_auto_discover_anki_cars()
    await asyncio.sleep(2)  # wait a short period to allow the auto discovery service run at least once

    # Assert 1
    assert isinstance(fleet_ctrl._FleetController__auto_connect_anki_cars_task, asyncio.Task)
    callback_count_before_stop = mock_add_car_callback.call_count
    mock_add_car_callback.assert_called()

    # Act 2
    fleet_ctrl.stop_auto_discover_anki_cars()
    await asyncio.sleep(7)  # wait for longer as the while loop will be performed to ensure it was not executed again
    callback_count_after_stop = mock_add_car_callback.call_count

    # Assert 2
    assert callback_count_after_stop == callback_count_before_stop
    assert fleet_ctrl._FleetController__auto_connect_anki_cars_task is None
