# Copyright 2024 IAV GmbH
#
# This file is part of the IAV-Distortion project an interactive
# and educational showcase designed to demonstrate the need
# of automotive cybersecurity in a playful, engaging manner.
# and is released under the "Apache 2.0". Please see the LICENSE
# file that should have been included as part of this package.
#
import asyncio
from asyncio import Task
import struct
import logging
from typing import Callable
from VehicleManagement.VehicleController import VehicleController, Turns, TurnTrigger
from bleak import BleakClient, BleakGATTCharacteristic, BleakError


class AnkiController(VehicleController):
    """
    Controller class for the BLE interface for the Anki cars
    """
    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        console_handler = logging.StreamHandler()
        self.logger.addHandler(console_handler)

        super().__init__()
        self.task_in_progress: bool = False

        self.__MAX_ANKI_SPEED = 1200  # mm/s
        self.__MAX_ANKI_ACCELERATION = 2500  # mm/s^2
        self.__LANE_OFFSET = 22.25

        self.__location_callback = None
        self.__transition_callback = None
        self.__offset_callback = None
        self.__version_callback = None
        self.__battery_callback = None
        self.__ble_not_reachable_callback: Callable[[], None] | None = None

        self.__latest_command: bytes | None = None
        self.__command_in_progress: bool = False

        return

    def __del__(self) -> None:
        asyncio.create_task(self.__disconnect_from_vehicle())

    def __run_async_task(self, task: Task) -> None:
        """
        Run a asyncio awaitable task

        Parameters
        ----------
        task: Task
            awaitable task
        """
        asyncio.create_task(task)
        # TODO: Log error, if the coroutine doesn't end successfully

    async def __process_latest_command(self) -> None:
        """
        Process the most recent command.

        As long as new commands are received while another command is processed the most recent command will be
        precessed next.
        """
        while self.__latest_command is not None:
            current_command = self.__latest_command
            self.__latest_command = None
            task = asyncio.create_task(self.__send_command_task(current_command))
            await task
        self.__command_in_progress = False
        return

    def set_callbacks(self,
                      location_callback: Callable,
                      transition_callback: Callable,
                      offset_callback: Callable,
                      version_callback: Callable,
                      battery_callback: Callable) -> None:
        """
        Sets callback functions.

        Parameters
        ----------
        location_callback: Callable
            Callback function executed on location event.
        transition_callback: Callable
            Callback function executed on transition event.
        offset_callback: Callable
            Callback function executed on offset event.
        version_callback: Callable
            Callback function executed on version event.
        battery_callback: Callable
            Callback function executed on battery event.
        car_not_reachable_callback: Callable
            Callback function executed on car not reachable event.
        """
        self.__location_callback = location_callback
        self.__transition_callback = transition_callback
        self.__offset_callback = offset_callback
        self.__version_callback = version_callback
        self.__battery_callback = battery_callback
        return

    def set_ble_not_reachable_callback(self, ble_not_reachable_callback: Callable[[], None]):
        """
        Sets a callback that should be executed when the car is not reachable
        """
        self.__ble_not_reachable_callback = ble_not_reachable_callback

    async def connect_to_vehicle(self, ble_client: BleakClient, start_notification: bool = True) -> bool:
        """
        Establishes BLE connection to Anki car.

        Parameters
        ----------
        ble_client: BleakClient
            Client to connect to.
        start_notification: bool
            Flag to start clients notification service.

        Returns
        -------
        bool:
            True, if connection established successfully.
            False, if connection failed.
        """
        if ble_client is None or not isinstance(ble_client, BleakClient):
            self.logger.debug("Invalid client.")
            return False

        try:
            await ble_client.connect()

            if ble_client.is_connected:
                self._connected_car = ble_client
                await self._setup_car(start_notification)
                self.logger.info("Car connected")
                return True
            else:
                self.logger.info("Not connected")
                return False
        except BleakError as e:
            self.logger.debug(f"Bleak Error: {e}")
            return False

    def __send_command(self, command: bytes) -> None:
        """
        Constructs coroutine that will be created as async task.

        Parameters
        ----------
        command: bytes
            Command to be sent to the client.
        """
        self.__run_async_task(self.__send_command_task(command))
        return

    def __send_latest_command(self, command: bytes) -> None:
        """
        Stores most recent command and starts loop to run most recent task if loop is not running.

        Parameters
        ----------
        command: bytes
            Command to be sent to the client.
        """
        self.__latest_command = command
        if not self.__command_in_progress:
            self.__command_in_progress = True
            self.__run_async_task(self.__process_latest_command())
        return

    async def __send_command_task(self, command: bytes) -> bool:
        """
        Sends BLE command asynchronously.

        Constructs final BLE command. Sends BLE command if no other task is still being progressed. If another task is
        in progress, the current command is dropped.

        Parameters
        ----------
        command: bytes
            Command to be sent via bluetooth.

        Returns
        -------
        success: bool
            True, if sending the command was successful.
            False, if sending the command failed.
        """
        success = False

        if self.task_in_progress:
            return success
        else:
            self.task_in_progress = True
            final_command = struct.pack("B", len(command)) + command

            try:
                await self._connected_car.write_gatt_char("BE15BEE1-6186-407E-8381-0BD89C4D8DF4", final_command, None)
                success = True
                self.task_in_progress = False
            except (BleakError, OSError):
                success = False
                self.task_in_progress = False
                if self.__ble_not_reachable_callback is not None:
                    self.__ble_not_reachable_callback()

            return success

    async def __start_notifications_now(self) -> bool:
        """
        Constructs and sends BLE command to start the clients notification service.

        Returns
        -------
        bool
            True, if sending the command was successful.
            False, if sending the command failed.
        """
        try:
            await self._connected_car.start_notify("BE15BEE0-6186-407E-8381-0BD89C4D8DF4",
                                                   self.__on_receive_data)
            return True
        except BleakError:
            if self.__ble_not_reachable_callback is not None:
                self.__ble_not_reachable_callback()
            else:
                return False

    async def __stop_notifications_now(self) -> bool:
        """
        Constructs and sends BLE command to stop the clients notification service.

        Returns
        -------
        bool
            True, if sending the command was successful.
            False, if sending the command failed.
        """
        try:
            await self._connected_car.stop_notify("BE15BEE0-6186-407E-8381-0BD89C4D8DF4")
            return True
        except BleakError:
            if self.__ble_not_reachable_callback is not None:
                self.__ble_not_reachable_callback()
            else:
                return False

    def change_speed_to(self, velocity: int, acceleration: int = 1000, respect_speed_limit: bool = True) -> bool:
        """
        Calculates target speed value, constructs and send BLE command to request this speed value.

        Parameters
        ----------
        velocity: int
            Target velocity.
        acceleration: int
            Acceleration to get to the target speed.
        respect_speed_limit: bool
            Flag to activate or deactivate the track speed limit.

        Returns
        -------
        bool
            True
        """
        limit_int = int(respect_speed_limit)
        speed_int = int(self.__MAX_ANKI_SPEED * velocity / 100)
        accel_int = acceleration

        command = struct.pack("<BHHH", 0x24, speed_int, accel_int, limit_int)
        self.logger.debug("Changed speed to %i", speed_int)
        self.__send_latest_command(command)
        return True

    def change_lane_to(self, change_direction: int, velocity: int, acceleration: int = 1000) -> bool:
        """
        Calculates, constructs and sends the command to do a requested lane change.

        Parameters
        ----------
        change_direction: int
            -1: lane change to the left.
            1: lane change to the right.
        velocity: int
            Velocity during lane change.
        acceleration: int
            Acceleration during lane change.

        Returns
        -------
        bool
            True
        """
        speed_int = int(self.__MAX_ANKI_SPEED * velocity / 100)
        lane_direction = self.__LANE_OFFSET * change_direction
        command = struct.pack("<BHHf", 0x25, speed_int, acceleration, lane_direction)
        self.logger.debug("Changed lane direction %i", lane_direction)
        self.__send_command(command)
        return True

    def do_turn_with(self, direction: Turns,
                     turntrigger: TurnTrigger = TurnTrigger.VEHICLE_TURN_TRIGGER_IMMEDIATE) -> bool:
        """
        Constructs and sends the command to do a u-turn.

        Parameters
        ----------
        direction: Turns
            Direction for the turn.
        turntrigger: TurnTrigger
            Trigger for the u-turn.

        Returns
        -------
        bool
            True
        """
        command = struct.pack("<BHH", 0x32, direction.value[0], turntrigger.value[0])
        self.__send_command(command)
        return True

    def request_version(self) -> bool:
        """
        Constructs and sends command to request Anki cars SW version.

        Returns
        -------
        bool
            True
        """
        command = struct.pack("<B", 0x18)
        self.__send_command(command)
        return True

    def request_battery(self) -> bool:
        """
        Constructs and sends the command to request the Anki cars battery status.

        Returns
        -------
        bool
            True
        """
        command = struct.pack("<B", 0x1a)
        self.__send_command(command)
        return True

    async def _setup_car(self, start_notification: bool) -> bool:
        """
        Sets sdk mode and initilizes road_offset for the Anki car, optionally starts notification service.

        Parameters
        ----------
        start_notification: bool
            If True, starts notification service.

        Returns
        -------
        bool
            True
        """
        if start_notification:
            await self.__start_notifications_now()

        self.__set_sdk_mode_to(True)
        self.__set_road_offset_on(0.0)
        return True

    def __set_sdk_mode_to(self, value: bool) -> bool:
        """
        Constructs and sends command to set the sdk mode.

        Parameters
        ----------
        value: bool
            If True, activates sdk mode.
            If False, deactivate sdk mode.

        Returns
        -------
        bool
            True
        """
        command_parameter: int
        if value:
            command_parameter = 0x01
        else:
            command_parameter = 0x00
        command = struct.pack("<BBB", 0x90, 0x01, command_parameter)
        self.__send_command(command)
        return True

    def __set_road_offset_on(self, value: float = 0.0) -> bool:
        """
        Constructs and sends command to set the road offset value.

        Parameters
        ----------
        value: float
            Value to set road offset to.

        Returns
        -------
        bool
            True
        """
        command = struct.pack("<Bf", 0x2c, value)
        self.__send_command(command)
        return True

    def _update_road_offset(self) -> bool:
        """
        Constructs and sends command to update the road offset value.

        Returns
        -------
        bool
            True
        """
        command = struct.pack("<B", 0x2d)
        self.__send_command(command)
        return True

    async def __disconnect_from_vehicle(self) -> bool:
        """
        Constructs and sends command to disconnect from the Anki car after stopping the notification service.

        Returns
        -------
        bool
            True
        """
        await self.__stop_notifications_now()

        command = struct.pack("<B", 0xd)
        self.__send_command(command)
        return True

    def __on_receive_data(self, sender: BleakGATTCharacteristic, data: bytearray) -> None:
        """
        Processes received data and runs regarding callback functions according to data type.

        Parameters
        ----------
        sender: BleakGATTCharacteristic
            Sender of the received data.
        data: bytearray
            Received data payload.
        """
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
            _ = data.hex(" ", 1)

        return

    def on_send_new_event(self, value_tuple: tuple, callback: classmethod) -> None:
        """
        Generic function to run a callback function.

        Parameters
        ----------
        value_tuple: tuple
            Arguments for callback function.
        callback: classmethod
            Callback function to be executed.
        """
        if callback is not None:
            callback(value_tuple)
        return
