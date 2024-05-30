# Copyright 2024 IAV GmbH
#
# This file is part of the IAV-Distortion project an interactive
# and educational showcase designed to demonstrate the need
# of automotive cybersecurity in a playful, engaging manner.
# and is released under the "Apache 2.0". Please see the LICENSE
# file that should have been included as part of this package.
#

from bleak import BleakScanner

from Helpers import AsyncIoHelper


class FleetController:
    def __init__(self):
        self._connected_cars = {} # BleakClients

    def scan_for_anki_cars(self) -> list[str]:
        ble_devices = AsyncIoHelper.run_async_task(BleakScanner.discover(return_adv=True))
        _active_devices = [d[0].address for d in ble_devices.values() if d[0].name is not None and "Drive" in d[0].name]
        if _active_devices:
            return _active_devices
        else:
            return []
