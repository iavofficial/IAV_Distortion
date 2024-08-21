# Copyright 2024 IAV GmbH
#
# This file is part of the IAV-Distortion project an interactive
# and educational showcase designed to demonstrate the need
# of automotive cybersecurity in a playful, engaging manner.
# and is released under the "Apache 2.0". Please see the LICENSE
# file that should have been included as part of this package.
#
import asyncio
import pytest
from unittest.mock import patch
from bleak import BleakClient
from VehicleManagement.AnkiController import AnkiController


@pytest.mark.skip_ci
@pytest.mark.manual
@pytest.mark.one_anki_car_needed
@pytest.mark.asyncio
async def test_spam_connection_requests(mac_address: str = 'E8:7E:9F:34:CF:46', connection_requests: int = 2,
                                        change_speed: bool = False) -> None:
    """
    Test if multiple BLE connections can be established with one Anki Overdrive car.

    Expectation: It is possible to establish only ONE connection, further tries to connect to the vehicle fail.

    Parameters
    ----------
    mac_address: str
        MAC address of the Anki car used for the test.
    connection_requests: int
        Amount of connection requests/clients.
    change_speed: bool
        If True: Send speed requests from different clients to the Anki car.
    """
    clients = []
    controllers = []
    with patch.object(AnkiController, '__del__', lambda x: None):
        # patch AnkiController.__del__() to avoid errors due to asynchronous task in __del__ that is irrelevant for
        # the test
        for i in range(connection_requests):
            clients.append(BleakClient(mac_address))
            controllers.append(AnkiController())

    results = {}
    i = 0
    for controller in controllers:
        result = await controller.connect_to_vehicle(clients[i])
        results[controller] = result
        i += 1

    if change_speed:
        controllers[0].change_speed_to(60)
        await asyncio.sleep(2)
        controllers[1].change_speed_to(30)
        await asyncio.sleep(2)
        controllers[0].change_speed_to(0)
        await asyncio.sleep(2)

    # Assertions
    assert controllers[0]._connected_car.address == mac_address, \
        "First connection request should succeed. Check if correct mac address is used and if vehicle is turned on."
    for c in range(1, connection_requests):
        assert controllers[c]._connected_car is None, "Any other connection attempt should fail"
