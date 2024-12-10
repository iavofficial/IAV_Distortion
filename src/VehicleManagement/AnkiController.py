# Copyright 2024 IAV GmbH
#
# This file is part of the IAV Distortion project an interactive
# and educational showcase designed to demonstrate the need
# of automotive cybersecurity in a playful, engaging manner.
# and is released under the "Apache 2.0". Please see the LICENSE
# file that should have been included as part of this package.
#
import asyncio
import struct
import logging
from typing import Callable, Coroutine, Any

import Constants
from VehicleManagement.VehicleController import VehicleController, Turns, TurnTrigger
from bleak import BleakClient
from bleak.exc import BleakError
from bleak.backends.characteristic import BleakGATTCharacteristic

logger = logging.getLogger(__name__)

ble_connection_logger = logging.getLogger('ble_connection_logging')
ble_connection_logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler('ble-connection-trace.log')
formatter = logging.Formatter('%(asctime)s: %(message)s')
file_handler.setFormatter(formatter)
ble_connection_logger.addHandler(file_handler)


class AnkiController(VehicleController):
    """
    Controller class for the BLE interface for the Anki cars
    """
    def __init__(self) -> None:

        super().__init__()
        self.task_in_progress: bool = False

        self.__location_callback: Callable[[tuple[int, int, float, int, int]], None] | None = None
        self.__transition_callback: Callable[[tuple[int, int, float, int]], None] | None = None
        self.__offset_callback: Callable[[tuple[float]], None] | None = None
        self.__version_callback: Callable[[tuple[int, int]], None] | None = None
        self.__battery_callback: Callable[[tuple[int]], None] | None = None
        self.__ble_not_reachable_callback: Callable[[], None] | None = None

        self.__latest_command: bytes | None = None
        self.__command_in_progress: bool = False

        return

    def __del__(self) -> None:
        asyncio.create_task(self.__disconnect_from_vehicle())

    def __run_async_task(self, task: Coroutine[Any, Any, Any]) -> None:
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

        As long as new commands are received while another command is
        processed the most recent command will be precessed next.
        """
        while self.__latest_command is not None:
            current_command = self.__latest_command
            self.__latest_command = None
            task = asyncio.create_task(self.__send_command_task(current_command))
            await task
        self.__command_in_progress = False
        return

    def set_callbacks(self,
                      location_callback: Callable[[tuple[int, int, float, int, int]], None] | None = None,
                      transition_callback: Callable[[tuple[int, int, float, int]], None] | None = None,
                      offset_callback: Callable[[tuple[float]], None] | None = None,
                      version_callback: Callable[[tuple[int, int]], None] | None = None,
                      battery_callback: Callable[[tuple[int]], None] | None = None) -> None:
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

    def set_ble_not_reachable_callback(self, ble_not_reachable_callback: Callable[[], None]) -> None:
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
            logger.debug("Invalid client.")
            return False

        try:
            ble_connection_logger.info('%s | Starting to connect', ble_client.address)
            await ble_client.connect()

            if ble_client.is_connected:
                self._connected_car = ble_client
                await self._setup_car(start_notification)
                logger.info("Car connected")
                ble_connection_logger.info('%s | Connection established successfully', ble_client.address)
                return True
            else:
                logger.info("Not connected")
                ble_connection_logger.info('%s | Connection was not established', ble_client.address)
                return False
        except (BleakError, OSError) as e:
            ble_connection_logger.error(f'{ble_client.address} | Error while trying to connect: "{e}"')
            logger.debug(f"Bleak Error: {e}")
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
                await self._connected_car.write_gatt_char("BE15BEE1-6186-407E-8381-0BD89C4D8DF4", final_command, True)
                success = True
                self.task_in_progress = False
            except (BleakError, OSError):
                success = False
                self.task_in_progress = False
                ble_connection_logger.warning('%s | Car isn\'t reachable anymore',
                                              self._connected_car.address)
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
                return False
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
                return False
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
        speed_int = int(Constants.MAX_ANKI_SPEED * velocity / 100)
        accel_int = acceleration

        command = struct.pack("<BHHH", 0x24, speed_int, accel_int, limit_int)
        logger.debug("Changed speed to %i", speed_int)
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
        speed_int = int(Constants.MAX_ANKI_SPEED * velocity / 100)
        lane_direction = Constants.TRACK_LANE_WIDTH * change_direction
        command = struct.pack("<BHHf", 0x25, speed_int, acceleration, lane_direction)
        logger.debug("Changed lane direction %i", lane_direction)
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
        command = struct.pack("<BHH", 0x32, direction, turntrigger)
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
        ble_connection_logger.debug('%s | Normally disconnecting', self._connected_car.address)
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
            if self.__version_callback is not None:
                self.__version_callback(version_tuple)

        # Battery
        elif command_id == "0x1b":
            battery_tuple = struct.unpack_from("<H", data, 2)
            # new_data = data.hex(" ", 1)
            # battery_tuple = tuple(new_data[6:12])
            if self.__battery_callback is not None:
                self.__battery_callback(battery_tuple)

        elif command_id == "0x27":
            location_tuple = struct.unpack_from("<BBfHB", data, 2)
            if self.__location_callback is not None:
                self.__location_callback(location_tuple)

        elif command_id == "0x29":
            transition_tuple = struct.unpack_from("<BBfB", data, 2)
            if self.__transition_callback is not None:
                self.__transition_callback(transition_tuple)

        elif command_id == "0x2d":
            offset_tuple = struct.unpack_from("<f", data, 2)
            if self.__offset_callback is not None:
                self.__offset_callback(offset_tuple)

        else:
            _ = data.hex(" ", 1)

        return
