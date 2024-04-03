import asyncio
import struct
from bleak import BleakClient, BleakScanner


class VehicleController:
    def __init__(self):
        self._active_devices = []
        self._connected_cars = {}
        return

    def __del__(self):
        del self._active_devices
        del self._connected_cars

    def __str__(self):
        return "Connected Cars" + str(self._connected_cars)

    def __repr__(self):
        return self.__str__()

    def __len__(self):
        return len(self._connected_cars)

    async def scan_for_anki_cars(self):
        ble_devices = await BleakScanner.discover(return_adv=True)
        self._active_devices = [d for d in ble_devices.values() if d[0].name is not None and "Drive" in d[0].name]
        if self._active_devices:
            await self._connect_to_anki_cars()

    async def _connect_to_anki_cars(self):
        for anki_car in self._active_devices:
            connected_car = BleakClient(anki_car[0].address)
            await connected_car.connect()
            if connected_car.is_connected():
                self._connected_cars[connected_car.address] = connected_car

    def change_speed(self, uuid: str):
        command = struct.pack("<BHHB", 0x24, 800, 1000, 0x01)
        asyncio.create_task(self.__send_command(command, uuid))

    def change_lane(self, uuid: str):
        command = struct.pack("<BHHf", 0x25, 800, 1000, -44.5)
        asyncio.create_task(self.__send_command(command, uuid))

    def do_u_turn(self, uuid: str):
        command = struct.pack("<BHH", 0x32, 0x03, 0x00)
        asyncio.create_task(self.__send_command(command, uuid))

    def set_sdk_mode_to(self, uuid: str, value: bool):
        command = struct.pack("<BBB", 0x90, 0x01, 0x01)
        asyncio.create_task(self.__send_command(command, uuid))

    def __disconnect_from(self, uuid: str):
        command = struct.pack("<B", 0xd)
        asyncio.create_task(self.__send_command(command, uuid))
        del self._connected_cars[uuid]

    async def __send_command(self, command: bytes, uuid: str):
        final_command = struct.pack("B", len(command)) + command
        await self._connected_cars[uuid].write_gatt_char("BE15BEE1-6186-407E-8381-0BD89C4D8DF4", final_command, None)

    async def __receive_data(self, uuid: str):
        await self._connected_cars[uuid].read_gatt_char()