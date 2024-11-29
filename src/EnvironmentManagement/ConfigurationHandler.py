# Copyright 2024 IAV GmbH
#
# This file is part of the IAV Distortion project an interactive
# and educational showcase designed to demonstrate the need
# of automotive cybersecurity in a playful, engaging manner.
# and is released under the "Apache 2.0". Please see the LICENSE
# file that should have been included as part of this package.
#
import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


class Singleton(type):
    """
    Metaclass to define a class as singleton.
    Checks if instance of class already exists and returns it.
    """
    _instances: dict[Any, Any] = {}

    def __call__(cls, *args: tuple[Any], **kwargs: dict[str, Any]) -> 'ConfigurationHandler':
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class ConfigurationHandler(metaclass=Singleton):
    """
    Coordinates access to the configuration file.

    Implemented as singleton to ensure globally consistent configuration data.
    """

    def __init__(self, config_file: str = "config_file.json") -> None:
        self.config_file: str = config_file
        self.__config_tup: tuple[dict[str, Any]] = self.__read_configuration()
        return

    def __read_configuration(self) -> tuple[dict[str, Any]]:
        """
        Read the configuration file and return it as a tuple.

        Returns
        -------
        Tuple [Any]
            Configuration data in a tuple.

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
            with open(self.config_file, 'r') as file:
                configuration = json.load(file)
                return configuration,

        except FileNotFoundError:
            logger.critical("Configuration file not found.")
        except json.JSONDecodeError:
            logger.critical("JSON decoding error in the configuration file.")
        except PermissionError:
            logger.critical("No permission to read configuration file.")
        except Exception as e:
            logger.critical(f"An unexpected error occurred trying to read the configuration file: {e}")
        return {},

    def write_configuration(self, new_config: dict[str, dict[str, Any]]) -> None:
        """
        Writes the current configuration into a configuration file

        Parameters
        ----------
        new_config: dict
            dictionary containing the new configuration parameter
        """
        current_config = self.__config_tup[0]
        # Merge the new configuration with the current configuration
        for key, value in new_config.items():
            if isinstance(value, dict):
                # Recursively handle nested dictionaries
                if key in current_config:
                    self.__merge_dict(current_config[key], value)
                else:
                    current_config[key] = value
            else:
                current_config[key] = value

        # Write the merged configuration back to the file
        try:
            with open(self.config_file, 'w') as file:
                json.dump(current_config, file, indent='\t')
        except PermissionError:
            logger.critical("No permission to write to configuration file.")
        except Exception as e:
            logger.critical(f"An unexpected error occured trying to write to the configuration file: {e}")

        self.__config_tup = self.__read_configuration()
        return

    def __merge_dict(self, target: dict[str, dict[str, Any]], source: dict[str, dict[str, Any]]) -> None:
        """
        Recursively merges the source dictionary into the target dictionary.
        """
        for key, value in source.items():
            if isinstance(value, dict):
                # If the key does not exist in the target, add it
                if key not in target:
                    target[key] = {}
                # Recursively merge the nested dictionaries
                self.__merge_dict(target[key], value)
            else:
                target[key] = value
        return

    def get_configuration(self) -> dict[str, Any]:
        """
        Returns the internal saved configuration data as a dictionary.

        Returns
        -------
        configuration: dict
            Dictionary containing all configuration data.

        Raises
        ------
        TypeError
            If the configuration is not of type dict.
        """
        if not isinstance(self.__config_tup[0], dict):
            logger.critical("Expected the configuration to be of type dict")
            raise TypeError("Expected the configuration to be of type dict")
        for key, value in self.__config_tup[0].items():
            if not isinstance(key, str) or not isinstance(value, (int, float, str, list, dict)):
                logger.critical("Expected configuration keys to be strings and values to be of certain types")
                raise TypeError("Expected configuration keys to be strings and values to be of certain types")
        else:
            return self.__config_tup[0]
