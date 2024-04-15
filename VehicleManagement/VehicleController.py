import asyncio
import struct
from bleak import BleakClient, BleakGATTCharacteristic


class VehicleController:
    def __init__(self):
        self._connected_cars = {}  # BleakClients
        self.loop = asyncio.new_event_loop()

        self.__MAX_ANKI_SPEED = 1200  # mm/s
        self.__MAX_ANKI_ACCELERATION = 2500  # mm/s^2
        self.__LANE_OFFSET = 22.25

        self.__location_callback = None
        self.__transition_callback = None
        self.__version_callback = None
        self.__battery_callback = None

        return

    def __del__(self):
        all_car_keys = list(self._connected_cars.keys())
        for car_key in all_car_keys:
            self.__disconnect_from(car_key)

        del self._connected_cars

    def __str__(self):
        return "Connected Cars" + str(self._connected_cars)

    def __repr__(self):
        return self.__str__()

    def __len__(self):
        return len(self._connected_cars)

    def set_callbacks(self, location_callback, transition_callback, version_callback, battery_callback):
        self.__location_callback = location_callback
        self.__transition_callback = transition_callback
        self.__version_callback = version_callback
        self.__battery_callback = battery_callback

    # def scan_for_anki_cars(self) -> list[str]:
    #    ble_devices = self.loop.run_until_complete(BleakScanner.discover(return_adv=True))
    #    _active_devices = [d[0].address for d in ble_devices.values() if d[0].name is not None and "Drive" in d[0].name]
    #    if _active_devices:
    #        return _active_devices
    #    else:
    #        return []

    def connect_to_anki_cars(self, uuid: str, start_notification: bool = True) -> bool:
        if uuid is None or len(uuid) == 0:
            return False

        try:
            connected_car = BleakClient(uuid)
            self.loop.run_until_complete(connected_car.connect())
            if connected_car.is_connected:
                self._connected_cars[connected_car.address] = connected_car
                self._initiate_car_for(connected_car.address, start_notification)
                return True
            else:
                return False
        except IOError:
            return False

    def change_speed(self, uuid: str, velocity: int, acceleration: int = 1000, respect_speed_limit: bool = True):
        limit_int = int(respect_speed_limit)
        speed_int = int(self.__MAX_ANKI_SPEED * velocity / 100)
        accel_int = acceleration

        command = struct.pack("<BHHH", 0x24, speed_int, accel_int, limit_int)
        self.__send_command_to(uuid, command)

    def change_lane(self, uuid: str, change_direction: int, velocity: int, acceleration: int = 1000):
        speed_int = int(self.__MAX_ANKI_SPEED * velocity / 100)
        lane_direction = self.__LANE_OFFSET * change_direction
        # print(f"lane_direction: {lane_direction}")
        command = struct.pack("<BHHf", 0x25, speed_int, acceleration, lane_direction)
        # print(f"{command}")
        self.__send_command_to(uuid, command)

    def do_u_turn(self, uuid: str):
        command = struct.pack("<BHH", 0x32, 0x03, 0x00)
        self.__send_command_to(uuid, command)

    def request_version_of(self, uuid: str):
        command = struct.pack("<B", 0x18)
        self.__send_command_to(uuid, command)

    def request_battery_of(self, uuid: str):
        command = struct.pack("<B", 0x1a)
        self.__send_command_to(uuid, command)

    def _initiate_car_for(self, uuid: str, start_notification: bool) -> bool:
        if start_notification:
            self.__start_notifications_for(uuid)

        self.__set_sdk_mode_to(uuid, True)
        self.__set_road_offset_for(uuid, 0.0)

    def __set_sdk_mode_to(self, uuid: str, value: bool):
        command = struct.pack("<BBB", 0x90, 0x01, 0x01)
        self.__send_command_to(uuid, command)

    def __set_road_offset_for(self, uuid: str, value: float = 0.0):
        command = struct.pack("<Bf", 0x2c, value)
        self.__send_command_to(uuid, command)

    def _update_road_offset_for(self, uuid: str):
        command = struct.pack("<B", 0x2d)
        self.__send_command_to(uuid, command)

    def __disconnect_from(self, uuid: str):
        self.__stop_notifications_for(uuid)

        command = struct.pack("<B", 0xd)
        self.__send_command_to(uuid, command)

        del self._connected_cars[uuid]

    def __send_command_to(self, uuid: str, command: bytes):
        final_command = struct.pack("B", len(command)) + command

        if uuid in self._connected_cars:
            self.loop.run_until_complete(self._connected_cars[uuid].write_gatt_char("BE15BEE1-6186-407E-8381"
                                                                                    "-0BD89C4D8DF4",
                                                                                    final_command, None))
        else:
            print(f"uuid {uuid} is unknown.")
        'await self._connected_cars[uuid].write_gatt_char("BE15BEE1-6186-407E-8381-0BD89C4D8DF4", final_command, None)'

    def __start_notifications_for(self, uuid: str):
        self.loop.run_until_complete(
            self._connected_cars[uuid].start_notify("BE15BEE0-6186-407E-8381-0BD89C4D8DF4", self.__on_receive_data))

    def __stop_notifications_for(self, uuid: str):
        self.loop.run_until_complete(self._connected_cars[uuid].stop_notify("BE15BEE0-6186-407E-8381-0BD89C4D8DF4"))

    def __on_receive_data(self, sender: BleakGATTCharacteristic, data: bytearray):
        command_id = hex(data[1])

        if command_id == "0x19":
            #version_tuple = tuple(data.hex("", 1))
            new_data = data.hex(" ", 1)
            version_tuple = tuple(new_data[6:11])
            # print(f"{sender.uuid}: {command_id} - Version / {new_data[5:]}")
            self.new_event(version_tuple, self.__version_callback)

        elif command_id == "0x1b":
            #battery_tuple = tuple(data.hex("", 1))
            new_data = data.hex(" ", 1)
            version_tuple = tuple(new_data[6:12])
            # print(f"{sender.uuid}: {command_id} - Battery / {new_data[5:]}")
            self.new_event(version_tuple, self.__battery_callback)

        elif command_id == "0x27":
            location_tuple = struct.unpack_from("<BBfHB", data, 2)
            location, piece, offset, speed, clockwise = location_tuple
            # print(f"{sender.uuid}: {command_id} - Position / piece: {piece}, location: {location},
            # offset: {offset:.2f}, speed: {speed}, clockwise: {clockwise}")
            self.new_event(location_tuple, self.__location_callback)

        elif command_id == "0x29":
            transition_tuple = struct.unpack_from("<BBfB", data, 2)
            # piece, piecePrev, offset, direction = transition_tuple
            # print(f"{sender.uuid}: {command_id} - Transition / piece: {piece}, piecePrev: {piecePrev},
            # offset: {offset:.2f}, direction: {direction}")
            self.new_event(transition_tuple, self.__transition_callback)

        elif command_id == "0x2d":
            print(f"{command_id} - Offset Update")

        else:
            new_data = data.hex(" ", 1)
            # print(f"{command_id} / {new_data[2:]}")

    def new_event(self, value_tuple: tuple, callback: classmethod):
        callback(value_tuple)
