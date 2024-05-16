import asyncio
import struct
from threading import Thread

from VehicleManagement.VehicleController import VehicleController, Turns, TurnTrigger
from bleak import BleakClient, BleakGATTCharacteristic, BleakError


class AnkiController(VehicleController):
    def __init__(self) -> None:
        super().__init__()
        self.task_in_progress: bool = False

        self._notification_thread: Thread = Thread(target=self.__on_receive_data,
                                                   name="notification_thread",
                                                   args=(BleakGATTCharacteristic, bytearray))

        self.__loop = asyncio.new_event_loop()

        self.__MAX_ANKI_SPEED = 1200  # mm/s
        self.__MAX_ANKI_ACCELERATION = 2500  # mm/s^2
        self.__LANE_OFFSET = 22.25

        self.__location_callback = None
        self.__transition_callback = None
        self.__offset_callback = None
        self.__version_callback = None
        self.__battery_callback = None
        self.__car_not_reachable_callback = None

        return

    def __del__(self) -> None:
        self.__disconnect_from_vehicle()

    def __run_async_task(self, task):
        """
        Run a asyncio awaitable task
        task: awaitable task
        """
        asyncio.run_coroutine_threadsafe(task, self.__loop).result()
        # TODO: Log error, if the coroutine doesn't end successfully

    def set_callbacks(self,
                      location_callback,
                      transition_callback,
                      offset_callback,
                      version_callback,
                      battery_callback,
                      car_not_reachable_callback) -> None:
        self.__location_callback = location_callback
        self.__transition_callback = transition_callback
        self.__offset_callback = offset_callback
        self.__version_callback = version_callback
        self.__battery_callback = battery_callback
        self.__car_not_reachable_callback = car_not_reachable_callback
        return

    def connect_to_vehicle(self, ble_client: BleakClient, start_notification: bool = True) -> bool:
        if ble_client is None or not isinstance(ble_client, BleakClient):
            return False

        try:
            Thread(target=self.__loop.run_forever).start()
            self.__run_async_task(ble_client.connect())

            if ble_client.is_connected:
                self._connected_car = ble_client
                self._setup_car(start_notification)
                return True
            else:
                return False
        except BleakError:
            return False

    def __send_command(self, command: bytes) -> bool:
        success = False

        if self.task_in_progress:
            return success
        else:
            self.task_in_progress = True
            final_command = struct.pack("B", len(command)) + command

            try:
                self.__run_async_task(
                    self._connected_car.write_gatt_char("BE15BEE1-6186-407E-8381-0BD89C4D8DF4", final_command,
                                                        None))
                success = True
                self.task_in_progress = False
            except BleakError:
                success = False
                self.task_in_progress = False
                if self.__car_not_reachable_callback is not None:
                    self.__car_not_reachable_callback("Anki car is not reachable. Can not send command.")

            return success

    def __start_notifications_now(self) -> bool:
        try:
            self._notification_thread.start()
            self.__run_async_task(self._connected_car.start_notify("BE15BEE0-6186-407E-8381-0BD89C4D8DF4",
                                                                   self.__on_receive_data))
            return True
        except BleakError:
            if self.__car_not_reachable_callback is not None:
                self.__car_not_reachable_callback("Anki car is not reachable. Can not start notification.")
            else:
                return False

    def __stop_notifications_now(self) -> bool:
        try:
            self.__run_async_task(self._connected_car.stop_notify("BE15BEE0-6186-407E-8381-0BD89C4D8DF4"))
            return True
        except BleakError:
            if self.__car_not_reachable_callback is not None:
                self.__car_not_reachable_callback("Anki car is not reachable. Can not stop notification.")
            else:
                return False

    def change_speed_to(self, velocity: int, acceleration: int = 1000, respect_speed_limit: bool = True) -> bool:
        limit_int = int(respect_speed_limit)
        speed_int = int(self.__MAX_ANKI_SPEED * velocity / 100)
        accel_int = acceleration

        command = struct.pack("<BHHH", 0x24, speed_int, accel_int, limit_int)
        self.__send_command(command)
        return True

    def change_lane_to(self, change_direction: int, velocity: int, acceleration: int = 1000) -> bool:
        speed_int = int(self.__MAX_ANKI_SPEED * velocity / 100)
        lane_direction = self.__LANE_OFFSET * change_direction
        command = struct.pack("<BHHf", 0x25, speed_int, acceleration, lane_direction)
        self.__send_command(command)
        return True

    def do_turn_with(self, direction: Turns,
                     turntrigger: TurnTrigger = TurnTrigger.VEHICLE_TURN_TRIGGER_IMMEDIATE) -> bool:
        command = struct.pack("<BHH", 0x32, direction.value[0], turntrigger.value[0])
        self.__send_command(command)
        return True

    def request_version(self) -> bool:
        command = struct.pack("<B", 0x18)
        self.__send_command(command)
        return True

    def request_battery(self) -> bool:
        command = struct.pack("<B", 0x1a)
        self.__send_command(command)
        return True

    def _setup_car(self, start_notification: bool) -> bool:
        if start_notification:
            self.__start_notifications_now()

        self.__set_sdk_mode_to(True)
        self.__set_road_offset_on(0.0)
        return True

    def __set_sdk_mode_to(self, value: bool) -> bool:
        command_parameter: int
        if value:
            command_parameter = 0x01
        else:
            command_parameter = 0x00
        command = struct.pack("<BBB", 0x90, 0x01, command_parameter)
        self.__send_command(command)
        return True

    def __set_road_offset_on(self, value: float = 0.0) -> bool:
        command = struct.pack("<Bf", 0x2c, value)
        self.__send_command(command)
        return True

    def _update_road_offset(self) -> bool:
        command = struct.pack("<B", 0x2d)
        self.__send_command(command)
        return True

    def __disconnect_from_vehicle(self) -> bool:
        self.__stop_notifications_now()

        command = struct.pack("<B", 0xd)
        self.__send_command(command)
        return True

    def __on_receive_data(self, sender: BleakGATTCharacteristic, data: bytearray) -> None:
        command_id = hex(data[1])

        # Version
        if command_id == "0x19":
            version_tuple = struct.unpack_from("<BB", data, 2)
            # new_data = data.hex(" ", 1)
            # version_tuple = tuple(new_data[6:11])
            self.on_send_new_event(version_tuple, self.__version_callback)

        # Battery
        elif command_id == "0x1b":
            battery_tuple = struct.unpack_from("<H", data, 2)
            # new_data = data.hex(" ", 1)
            # battery_tuple = tuple(new_data[6:12])
            self.on_send_new_event(battery_tuple, self.__battery_callback)

        elif command_id == "0x27":
            location_tuple = struct.unpack_from("<BBfHB", data, 2)
            self.on_send_new_event(location_tuple, self.__location_callback)

        elif command_id == "0x29":
            transition_tuple = struct.unpack_from("<BBfB", data, 2)
            self.on_send_new_event(transition_tuple, self.__transition_callback)

        elif command_id == "0x2d":
            offset_tuple = struct.unpack_from("<f", data, 2)
            self.on_send_new_event(offset_tuple, self.__offset_callback)

        else:
            new_data = data.hex(" ", 1)
            # print(f"{command_id} / {new_data[2:]}")
        return

    def on_send_new_event(self, value_tuple: tuple, callback: classmethod) -> None:
        if callback is not None:
            callback(value_tuple)
        return
