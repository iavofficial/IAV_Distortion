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
from bleak import BleakClient, BleakError


@pytest.mark.asyncio
async def test_spam_connection_requests(mac_address: str = 'E8:7E:9F:34:CF:46', connection_requests: int = 2) -> None:
    client = BleakClient(mac_address)

    tasks = []
    results = []
    for i in range(connection_requests):
        task = asyncio.create_task(client.connect())
        tasks.append(task)

        try:
            result = await task
            results.append(result)
        except BleakError as e:
            # Assuming BleakError is raised for connection failures
            results.append(e)


    #for task in asyncio.as_completed(tasks):
    #    try:
    #        result = await task
    #        results.append(result)
    #    except BleakError as e:
    #        # Assuming BleakError is raised for connection failures
    #        results.append(e)

    print(results)
    # Assertions
    assert results[0] is True, "First connection request should succeed"
    assert isinstance(results[1], BleakError), "Second connection request should result in a BleakError"

    # Clean up by disconnecting if connected
    if client.is_connected:
        await client.disconnect()

# asyncio.run(test_spam_connection_requests(mac_address='E8:7E:9F:34:CF:46', connection_requests=10))
