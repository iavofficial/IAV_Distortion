# Copyright 2024 IAV GmbH
#
# This file is part of the IAV-Distortion project an interactive
# and educational showcase designed to demonstrate the need
# of automotive cybersecurity in a playful, engaging manner.
# and is released under the "Apache 2.0". Please see the LICENSE
# file that should have been included as part of this package.
#
import logging
import asyncio
from asyncio import Task
from bleak import BleakScanner
from typing import Callable, Tuple
from EnvironmentManagement.ConfigurationHandler import ConfigurationHandler


class FleetController:

    def __init__(self, config_handler: ConfigurationHandler = None) -> None:
        self.config_handler: ConfigurationHandler = config_handler if config_handler else ConfigurationHandler()
        self.__add_anki_car_callback: Callable[[str], None] | None = None
        self.__auto_connect_anki_cars_task: Task | None = None

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
            _all_devices = [d for d in ble_devices.values() if d[0].name is not None and "Drive" in d[0].name]
            for device in _all_devices:
                local_name = device[1].local_name
                state = list(local_name.encode('utf-8'))[0]
                if state == 16:
                    _active_devices.append(device[0].address)
        else:
            _active_devices = [d[0].address for d in ble_devices.values() if
                               d[0].name is not None and "Drive" in d[0].name]
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
                        logging.warning('Missing callback to add vehicles. Auto discovery service will be deactivated.')
                        self.stop_auto_discover_anki_cars()
                    else:
                        await self.__add_anki_car_callback(uuid)

                await asyncio.sleep(5)
            except Exception as e:
                logging.warning(f'Error {e} occurred')

    def set_add_anki_car_callback(self, function_name: Callable[[str], None]) -> None:
        """
        Sets callback function to add Anki cars.

        Parameters
        ----------
        function_name: Callable
            Callback function.
        """
        if not callable(function_name):
            logging.warning("Tried to set non callable function as callback function.")
        else:
            self.__add_anki_car_callback = function_name
        return

    async def start_auto_discover_anki_cars(self) -> None:
        """
        Starts auto discover service for Anki cars if not already running.
        """
        if self.__auto_connect_anki_cars_task is None:
            self.__auto_connect_anki_cars_task = asyncio.create_task(self.auto_discover_anki_vehicles())
            logging.info("Auto discovery service for Anki cars activated.")
        return

    def stop_auto_discover_anki_cars(self) -> None:
        """
        Stops auto discover service for Anki cars.
        """
        if isinstance(self.__auto_connect_anki_cars_task, asyncio.Task):
            self.__auto_connect_anki_cars_task.cancel()
            self.__auto_connect_anki_cars_task = None
            logging.info("Auto discovery service for Anki cars deactivated.")
        return
