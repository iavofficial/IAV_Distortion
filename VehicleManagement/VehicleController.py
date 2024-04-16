import asyncio
import struct
from enum import Enum

from bleak import BleakClient, BleakGATTCharacteristic


class Turns(Enum):
    NOT = 0,
    TO_LEFT = 1,
    TO_RIGHT = 2,
    A_UTURN = 3,
    A_UTURN_JUMP = 4


class TurnTrigger(Enum):
    VEHICLE_TURN_TRIGGER_IMMEDIATE = 0,
    VEHICLE_TURN_TRIGGER_INTERSECTION = 1


class VehicleController:
    def __init__(self):
        self._connected_car = None
        self.loop = asyncio.new_event_loop()
        self.task_in_progress: bool = False

        self.__MAX_ANKI_SPEED = 1200  # mm/s
        self.__MAX_ANKI_ACCELERATION = 2500  # mm/s^2
        self.__LANE_OFFSET = 22.25

        self.__location_callback = None
        self.__transition_callback = None
        self.__offset_callback = None
        self.__version_callback = None
        self.__battery_callback = None

        return

    def __del__(self):
        self.__disconnect_from_vehicle()
        del self._connected_car

    def __str__(self):
        return "Connected Car" + str(self._connected_car)

    def __repr__(self):
        return self.__str__()

    def set_callbacks(self,
                      location_callback,
                      transition_callback,
                      offset_callback,
                      version_callback,
                      battery_callback):
        self.__location_callback = location_callback
        self.__transition_callback = transition_callback
        self.__offset_callback = offset_callback
        self.__version_callback = version_callback
        self.__battery_callback = battery_callback

    def connect_to_vehicle(self, ble_client: BleakClient, start_notification: bool = True) -> bool:
        if ble_client is None or not isinstance(ble_client, BleakClient):
            return False

        try:
            connected_car = ble_client
            self.loop.run_until_complete(connected_car.connect())
            if connected_car.is_connected:
                self._connected_car = connected_car
                self._initiate_car(start_notification)
                return True
            else:
                return False
        except IOError:
            return False

    def change_speed_to(self, velocity: int, acceleration: int = 1000, respect_speed_limit: bool = True):
        limit_int = int(respect_speed_limit)
        speed_int = int(self.__MAX_ANKI_SPEED * velocity / 100)
        accel_int = acceleration

        command = struct.pack("<BHHH", 0x24, speed_int, accel_int, limit_int)
        self.__send_command(command)

    def change_lane_to(self, change_direction: int, velocity: int, acceleration: int = 1000):
        speed_int = int(self.__MAX_ANKI_SPEED * velocity / 100)
        lane_direction = self.__LANE_OFFSET * change_direction
        print(f"change direction: {change_direction} and calculated offset: {lane_direction}")
        command = struct.pack("<BHHf", 0x25, speed_int, acceleration, lane_direction)
        # print(f"{command}")
        self.__send_command(command)

    def do_turn_with(self, direction: Turns,
                     turntrigger: TurnTrigger = TurnTrigger.VEHICLE_TURN_TRIGGER_IMMEDIATE):
        command = struct.pack("<BHH", 0x32, direction, turntrigger)
        self.__send_command(command)

    def request_version(self):
        command = struct.pack("<B", 0x18)
        self.__send_command(command)

    def request_battery(self):
        command = struct.pack("<B", 0x1a)
        self.__send_command(command)

    def _initiate_car(self, start_notification: bool) -> bool:
        if start_notification:
            self.__start_notifications_now()

        self.__set_sdk_mode_to(True)
        self.__set_road_offset_on(0.0)

        return True

    def __set_sdk_mode_to(self, value: bool):
        command_parameter: int
        if value:
            command_parameter = 0x01
        else:
            command_parameter = 0x00
        command = struct.pack("<BBB", 0x90, 0x01, command_parameter)
        self.__send_command(command)

    def __set_road_offset_on(self, value: float = 0.0):
        command = struct.pack("<Bf", 0x2c, value)
        self.__send_command(command)

    def _update_road_offset(self):
        command = struct.pack("<B", 0x2d)
        self.__send_command(command)

    def __disconnect_from_vehicle(self):
        self.__stop_notifications_now()

        command = struct.pack("<B", 0xd)
        self.__send_command(command)


    def __send_command(self, command: bytes) -> bool:
        success = False

        if self.task_in_progress:
            return success
        else:
            self.task_in_progress = True
            final_command = struct.pack("B", len(command)) + command

            self.loop.run_until_complete(self._connected_car.write_gatt_char("BE15BEE1-6186-407E-8381"
                                                                             "-0BD89C4D8DF4",
                                                                             final_command, None))
            success = True
            # print(f"sending command not possible. uuid {self.uuid} is unknown.")
            # success = False

            self.task_in_progress = False
            return success

    def __start_notifications_now(self):
        self.loop.run_until_complete(
            self._connected_car.start_notify("BE15BEE0-6186-407E-8381-0BD89C4D8DF4", self.__on_receive_data))

    def __stop_notifications_now(self):
        self.loop.run_until_complete(self._connected_car.stop_notify("BE15BEE0-6186-407E-8381-0BD89C4D8DF4"))

    def __on_receive_data(self, sender: BleakGATTCharacteristic, data: bytearray):
        command_id = hex(data[1])

        if command_id == "0x19":
            new_data = data.hex(" ", 1)
            version_tuple = tuple(new_data[6:11])
            self.new_event(version_tuple, self.__version_callback)

        elif command_id == "0x1b":
            new_data = data.hex(" ", 1)
            version_tuple = tuple(new_data[6:12])
            self.new_event(version_tuple, self.__battery_callback)

        elif command_id == "0x27":
            location_tuple = struct.unpack_from("<BBfHB", data, 2)
            self.new_event(location_tuple, self.__location_callback)

        elif command_id == "0x29":
            transition_tuple = struct.unpack_from("<BBfB", data, 2)
            self.new_event(transition_tuple, self.__transition_callback)

        elif command_id == "0x2d":
            offset_tuple = struct.unpack_from("<f", data, 2)
            self.new_event(offset_tuple, self.__offset_callback)

        else:
            new_data = data.hex(" ", 1)
            # print(f"{command_id} / {new_data[2:]}")

    def new_event(self, value_tuple: tuple, callback: classmethod):
        callback(value_tuple)
