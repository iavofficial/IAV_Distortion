import asyncio
import struct
from bleak import BleakClient, BleakScanner


class VehicleController:
    def __init__(self):
        self._connected_cars = {}
        self.loop = asyncio.get_event_loop()
        self.__MAX_ANKI_SPEED = 1200  # mm/s
        self.__MAX_ANKI_ACCELERATION = 2500  # mm/s^2
        self.__LANE_OFFSET = 22.25

        return

    def __del__(self):
        del self._connected_cars

    def __str__(self):
        return "Connected Cars" + str(self._connected_cars)

    def __repr__(self):
        return self.__str__()

    def __len__(self):
        return len(self._connected_cars)

    def scan_for_anki_cars(self) -> list[str]:
        ble_devices = self.loop.run_until_complete(BleakScanner.discover(return_adv=True))
        _active_devices = [d[0].address for d in ble_devices.values() if d[0].name is not None and "Drive" in d[0].name]
        if _active_devices:
            return _active_devices
        else:
            return []

    def connect_to_anki_cars(self, uuid: str) -> bool:
        connected_car = BleakClient(uuid)
        self.loop.run_until_complete(connected_car.connect())
        if connected_car.is_connected:
            self._connected_cars[connected_car.address] = connected_car
            self.set_sdk_mode_to(connected_car.address, True)
            return True
        else:
            return False

    def change_speed(self, uuid: str, velocity: int, acceleration: int = 1000, respect_speed_limit: bool = True):
        limit_int = int(respect_speed_limit)
        speed_int = int(self.__MAX_ANKI_SPEED * velocity / 100)
        accel_int = acceleration

        command = struct.pack("<BHHH", 0x24, speed_int, accel_int, limit_int)
        self.__send_command(command, uuid)

    def change_lane(self, uuid: str, change_direction: int, velocity: int, acceleration: int = 1000):
        speed_int = int(self.__MAX_ANKI_SPEED * velocity / 100)
        lane_direction = self.__LANE_OFFSET * change_direction
        print(f"lane_direction: {lane_direction}")
        command = struct.pack("<BHHf", 0x25, speed_int, acceleration, lane_direction)
        print(f"{command}")
        self.__send_command(command, uuid)

    def do_u_turn(self, uuid: str):
        command = struct.pack("<BHH", 0x32, 0x03, 0x00)
        self.__send_command(command, uuid)

    def set_sdk_mode_to(self, uuid: str, value: bool):
        command = struct.pack("<BBB", 0x90, 0x01, 0x01)
        self.__send_command(command, uuid)

    def __disconnect_from(self, uuid: str):
        command = struct.pack("<B", 0xd)
        self.__send_command(command, uuid)
        del self._connected_cars[uuid]

    def __send_command(self, command: bytes, uuid: str):
        final_command = struct.pack("B", len(command)) + command

        if uuid in self._connected_cars:
            self.loop.run_until_complete(self._connected_cars[uuid].write_gatt_char("BE15BEE1-6186-407E-8381"
                                                                                    "-0BD89C4D8DF4",
                                                                                    final_command, None))
        else:
            print(f"uuid {uuid} is unknown.")
        'await self._connected_cars[uuid].write_gatt_char("BE15BEE1-6186-407E-8381-0BD89C4D8DF4", final_command, None)'

    async def __receive_data(self, uuid: str):
        await self._connected_cars[uuid].read_gatt_char()
