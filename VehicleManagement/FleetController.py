import asyncio
import struct
from bleak import BleakScanner

class FleetController:

    def __init__(self):
        self._connected_cars = {} # BleakClients
        self.loop = asyncio.get_event_loop()

    def scan_for_anki_cars(self) -> list[str]:
        ble_devices = self.loop.run_until_complete(BleakScanner.discover(return_adv=True))
        _active_devices = [d[0].address for d in ble_devices.values() if d[0].name is not None and "Drive" in d[0].name]
        if _active_devices:
            return _active_devices
        else:
            return []
