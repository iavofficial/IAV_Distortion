# Copyright 2024 IAV GmbH
#
# This file is part of the IAV Distortion project an interactive
# and educational showcase designed to demonstrate the need
# of automotive cybersecurity in a playful, engaging manner.
# and is released under the "Apache 2.0". Please see the LICENSE
# file that should have been included as part of this package.
#
import logging
import asyncio
from asyncio import Task
from bleak import BleakScanner
from typing import Callable, Any, Coroutine
from EnvironmentManagement.ConfigurationHandler import ConfigurationHandler
from logging import FileHandler, Formatter

logger = logging.getLogger(__name__)


class FleetController:

    def __init__(self, configuration_handler: ConfigurationHandler = ConfigurationHandler()) -> None:
        self._connected_cars = {}  # BleakClients
        self.config_handler: ConfigurationHandler = configuration_handler
        self.__add_anki_car_callback: Callable[[str], Coroutine[Any, Any, Any]] | None = None
        self.__auto_connect_anki_cars_task: Task[Any] | None = None
        self.__ble_number_of_device_logging: Task[Any] | None = None

    async def scan_for_anki_cars(self, only_ready: bool = False) -> list[str]:
        """
        Scans for BLE devices matching Anki cars pattern.

        Parameters
        ----------
        only_ready: bool


        Returns
        -------
        list
            list uuids of found Anki cars.
        """
        ble_devices = await BleakScanner.discover(return_adv=True)
        _active_devices = []
        if only_ready:
            _all_devices = [d for d in ble_devices.values() if
                            'be15beef-6186-407e-8381-0bd89c4d8df4' in d[1].service_uuids]
            for device in _all_devices:
                local_name = device[1].local_name
                if local_name is None:
                    return []
                state = list(local_name.encode('utf-8'))[0]
                if state == 16:
                    _active_devices.append(device[0].address)
        else:
            _active_devices = [d[0].address for d in ble_devices.values() if
                               'be15beef-6186-407e-8381-0bd89c4d8df4' in d[1].service_uuids]
        return _active_devices

    async def auto_discover_anki_vehicles(self) -> None:
        """
        Periodically scan for Anki cars.
        """
        while True:
            try:
                anki_cars = await self.scan_for_anki_cars(only_ready=True)
                for uuid in anki_cars:
                    if not callable(self.__add_anki_car_callback):
                        logger.warning('Missing callback to add vehicles. Auto discovery service will be deactivated.')
                        self.stop_auto_discover_anki_cars()
                    else:
                        self.__add_anki_car_callback(uuid)

                await asyncio.sleep(5)
            except Exception as e:
                logger.warning(f'Error {e} occurred')

    async def log_number_of_ble_devices(self) -> None:
        ble_num_logger = logging.getLogger('ble_number_of_device_logger')
        ble_num_logger.setLevel(logging.DEBUG)
        file_handler = FileHandler('ble-number-of-devices.log')
        formatter = Formatter('%(asctime)s: %(message)s')
        file_handler.setFormatter(formatter)
        ble_num_logger.addHandler(file_handler)
        while True:
            try:
                all_devices = await BleakScanner.discover(return_adv=False)
                ble_num_logger.debug('%d BLE-Devices found', len(all_devices))
                await asyncio.sleep(60)
            except Exception as e:
                logger.warning(f'Error while scanning for all BLE devices in background: {e}')

    async def start_background_logging_for_ble_devices(self):
        if self.__ble_number_of_device_logging is not None:
            logger.warning("Tried to start Background logging for the number of BLE devices. Ignoring the request")
            return
        self.__ble_number_of_device_logging = asyncio.create_task(self.log_number_of_ble_devices())

    def set_add_anki_car_callback(self, function_name: Callable[[str], Coroutine[Any, Any, Any]]) -> None:
        """
        Sets callback function to add Anki cars.

        Parameters
        ----------
        function_name: Callable
            Callback function.
        """
        if not callable(function_name):
            logger.warning("Tried to set non callable function as callback function.")
        else:
            self.__add_anki_car_callback = function_name
        return

    async def start_auto_discover_anki_cars(self) -> None:
        """
        Starts auto discover service for Anki cars if not already running.
        """
        if self.__auto_connect_anki_cars_task is None:
            self.__auto_connect_anki_cars_task = asyncio.create_task(self.auto_discover_anki_vehicles())
            logger.info("Auto discovery service for Anki cars activated.")
        return

    def stop_auto_discover_anki_cars(self) -> None:
        """
        Stops auto discover service for Anki cars.
        """
        if isinstance(self.__auto_connect_anki_cars_task, asyncio.Task):
            self.__auto_connect_anki_cars_task.cancel()
            self.__auto_connect_anki_cars_task = None
            logger.info("Auto discovery service for Anki cars deactivated.")
        return
