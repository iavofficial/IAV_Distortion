import asyncio
from bleak import BleakClient, BleakScanner


async def scan_for_cars():
    ble_devices = await BleakScanner.discover(return_adv=True)

    for d, a in ble_devices.values():
        if d.name is not None and "Drive" in d.name:
            print()
            print(d)
            print("-" * len(str(d)))
            print(a)
    filtered_anki_cars = [d for d in ble_devices.values() if d[0].name is not None and "Drive" in d[0].name]

    async with BleakClient(filtered_anki_cars[0][0].address) as anki_car:
        result = anki_car.is_connected
        await anki_car.disconnect()
        result = anki_car.is_connected
    return filtered_anki_cars


class VehicleController:
    def __init__(self):
        self.anki_vehicles = []
        return

    loop = asyncio.get_event_loop()
    loop.run_until_complete(scan_for_cars())
