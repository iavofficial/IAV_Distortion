# Copyright 2024 IAV GmbH
#
# This file is part of the IAV-Distortion project an interactive
# and educational showcase designed to demonstrate the need
# of automotive cybersecurity in a playful, engaging manner.
# and is released under the "Apache 2.0". Please see the LICENSE
# file that should have been included as part of this package.
#
import asyncio
import pytest
from unittest import TestCase
from unittest.mock import patch, MagicMock
import struct
from VehicleManagement.AnkiController import AnkiController


@pytest.mark.skip_ci
class AnkiControllerUnitTests(TestCase):
    """
    Collection of AnkiController unit tests
    """
    @classmethod
    def setUpClass(cls) -> None:
        controller = AnkiController()
        return

    def setUp(self) -> None:
        self.commands_send = []
        return

    def tearDown(self) -> None:
        self.commands_send = []
        pass

    async def mock_send_command_task(self, command: bytes) -> None:
        """
        Mock sending BLE command to Anki car by asynchronously sleep for a short time.
        Save commands simulated to be sent into a list.

        Parameters
        ----------
        command: bytes
            Command to be sent to the client.
        """
        self.commands_send.append(command)  # append command to list of send commands
        await asyncio.sleep(0.05)  # mock sending BLE command
        return

    @pytest.mark.asyncio
    async def test_change_speed_to_multiple_inputs(self):
        """
        Test if AnkiController.__send_latest_command sends the first and latest received command, while commands in between
        can be dropped due to commands come in faster than they are processed.
        """
        # Arrange

        # Act
        controller = AnkiController()

        with patch.object(controller, "_AnkiController__send_command_task", new=self.mock_send_command_task):
            speed_requests = [2, 1, 0]
            speed_requests_commands = []
            for speed in speed_requests:
                controller.change_speed_to(speed, 1000, True)

                # convert speed request to command and save in list for comparison
                speed_int = int(controller._AnkiController__MAX_ANKI_SPEED * speed / 100)
                limit_int = int(True)
                speed_requests_commands.append(struct.pack("<BHHH", 0x24, speed_int, 1000, limit_int))

                await asyncio.sleep(0.01)  # time between commands << time to process command

            await asyncio.sleep(0.2)  # wait until all commands have been processed
            print("")
            print(f"speed_request_commands = {speed_requests_commands}")
            print(f"commands_send = {self.commands_send}")

        # Assert

        # test if __latest_command was cleared to None:
        assert controller._AnkiController__latest_command is None
        # test if first requested and send command is equal:
        assert self.commands_send[0] == speed_requests_commands[0]
        # test if commands_send is subset of speed_request_commands (expected that commands are dropped):
        assert self.commands_send < speed_requests_commands
        # test if last requested and send command is equal:
        assert self.commands_send.pop() == speed_requests_commands.pop()

