import asyncio
import struct
from asyncio import sleep

from bleak import BleakScanner, BleakClient

async def scan_for_cars():
    anki_cars = []
    ble_devices = await BleakScanner.discover(return_adv=True)

    for d, a in ble_devices.values():
        if d.name is not None and "Drive" in d.name:
            print()
            print(d)
            print("-" * len(str(d)))
            print(a)
    filtered_anki_cars = [d for d in ble_devices.values() if d[0].name is not None and "Drive" in d[0].name]
    try:
        for one_car in filtered_anki_cars:
            temp_car = BleakClient(one_car[0].address)
            await temp_car.connect()
            anki_cars.append(temp_car)

        # SDK Mode Active
        command = struct.pack("<BBB", 0x90, 0x01, 0x01)
        final_command = struct.pack("B", len(command)) + command
        await anki_cars[0].write_gatt_char("BE15BEE1-6186-407E-8381-0BD89C4D8DF4", final_command, None)
        await anki_cars[1].write_gatt_char("BE15BEE1-6186-407E-8381-0BD89C4D8DF4", final_command, None)

        sleep(1)

        # Set Speed
        command = struct.pack("<BHHB", 0x24, 800, 1000, 0x01)
        final_command = struct.pack("B", len(command)) + command
        await anki_cars[0].write_gatt_char("BE15BEE1-6186-407E-8381-0BD89C4D8DF4", final_command, None)
        await anki_cars[1].write_gatt_char("BE15BEE1-6186-407E-8381-0BD89C4D8DF4", final_command, None)

        sleep(5)

        # Change Lane
        command = struct.pack("<BHHf", 0x25, 800, 1000, -44.5)
        final_command = struct.pack("B", len(command)) + command
        await anki_cars[0].write_gatt_char("BE15BEE1-6186-407E-8381-0BD89C4D8DF4", final_command, None)

        sleep(5)

        # Turn 180
        command = struct.pack("<BHH", 0x32, 0x03, 0x00)
        final_command = struct.pack("B", len(command)) + command
        await anki_cars[0].write_gatt_char("BE15BEE1-6186-407E-8381-0BD89C4D8DF4", final_command, None)

        sleep(5)

    finally:
        # Dissconect
        command = struct.pack("<B", 0xd)
        final_command = struct.pack("B", len(command)) + command
        await anki_cars[0].write_gatt_char("BE15BEE1-6186-407E-8381-0BD89C4D8DF4", final_command, None)
        await anki_cars[1].write_gatt_char("BE15BEE1-6186-407E-8381-0BD89C4D8DF4", final_command, None)

    # characteristic = await anki_car.read_gatt_char('be15bee0-6186-407e-8381-0bd89c4d8df4')

    return filtered_anki_cars


loop = asyncio.get_event_loop()
loop.run_until_complete(scan_for_cars())
