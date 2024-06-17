# Copyright 2024 IAV GmbH
#
# This file is part of the IAV-Distortion project an interactive
# and educational showcase designed to demonstrate the need
# of automotive cybersecurity in a playful, engaging manner.
# and is released under the "Apache 2.0". Please see the LICENSE
# file that should have been included as part of this package.
#
import json
from portalocker import RedisLock, LOCK_SH
from logging import Logger, getLogger, DEBUG, StreamHandler


class ConfigurationHandler:
    """
    Coordinates access to the configuration file.

    Prevents simultaneous writing access.
    """
    def __init__(self) -> None:
        self.lock: RedisLock = RedisLock('config_file')
        self.logger: Logger = getLogger(__name__)

        self.logger.setLevel(DEBUG)
        console_handler = StreamHandler()
        self.logger.addHandler(console_handler)
        return

    def get_configuration(self) -> dict:
        """
        Read the configuration file and return the configuration data.

        Using lock to safely access the file.

        Returns
        -------
        configuration: dict
            Dictionary containing all configuration data.

        Raises
        ------
        FileNotFoundError
            If the configuration file does not exist.
        json.JSONDecodeError
            If there is an error in JSON format in the configuration file.
        PermissionError
            If there is no permission to read the configuration file.
        Exception
            For any other unexpected errors that may occur.
        """
        try:
            # with self.lock:
            with open('config_file.json', 'r') as file:
                configuration = json.load(file)

                return configuration

        except FileNotFoundError:
            self.logger.critical("Configuration file not found.")
        except json.JSONDecodeError:
            self.logger.critical("JSON decoding error in the configuration file.")
        except PermissionError:
            self.logger.critical("No permission to read configuration file.")
        except Exception as e:
            self.logger.critical(f"An unexpected error occured trying to read the configuration file: {e}")
