import asyncio
from unittest.mock import MagicMock, patch, AsyncMock

import pytest

from BotManagement.Bot import Bot
from VehicleMovementManagement.BehaviourController import BehaviourController


class TestBotBehaviour:
    behaviour_ctrl_mock: MagicMock

    @pytest.fixture(autouse=True)
    def setup_mocks(self):
        self.behaviour_ctrl_mock = MagicMock(spec=BehaviourController)
        self.vehicle_id = "car1"

        with patch('asyncio.create_task') as create_task_mock:
            create_task_mock.return_value = MagicMock()

            self.bot = Bot(self.vehicle_id, self.behaviour_ctrl_mock)
            self.bot._behaviour_ctrl.request_lane_change_for = AsyncMock()
            self.bot._behaviour_ctrl.request_speed_change_for = AsyncMock()
            self.bot._behaviour_ctrl.request_uturn_for = AsyncMock()

    def test_is_player_active_true(self):
        self.bot.set_is_player_active(True)
        self.behaviour_ctrl_mock.request_speed_change_for.assert_called_with(uuid=self.vehicle_id, value_perc=50.0)

    def test_is_player_active_false(self):
        self.bot.set_is_player_active(False)
        self.behaviour_ctrl_mock.request_speed_change_for.assert_called_with(uuid=self.vehicle_id, value_perc=30.0)

    @pytest.mark.asyncio
    async def test_drive_automatically_vehicle_none(self):
        self.bot.vehicle = None

        await self.bot._drive_automatically()

        self.behaviour_ctrl_mock.request_speed_change_for.assert_called_with(uuid=self.bot.vehicle, value_perc=30.0)
        self.behaviour_ctrl_mock.request_lane_change_for.assert_not_called()
        self.behaviour_ctrl_mock.request_uturn_for.assert_not_called()

    @pytest.mark.asyncio
    async def test_drive_automatically_player_active_speed(self):
        self.bot.is_player_active = True
        self.bot.vehicle = self.vehicle_id

        random_values_mock = [1, 60] * 2

        with patch('random.randint', side_effect=random_values_mock):
            task = asyncio.create_task(self.bot._drive_automatically())
            await asyncio.sleep(2)
            self.bot.vehicle = None
            await task

        # Assert
        self.behaviour_ctrl_mock.request_speed_change_for.assert_any_call(uuid=self.vehicle_id, value_perc=60.0)

    @pytest.mark.asyncio
    async def test_drive_automatically_player_active_turn_right(self):
        self.bot.is_player_active = True
        self.bot.vehicle = self.vehicle_id

        random_values_mock = [2, 0] * 2

        with patch('random.randint', side_effect=random_values_mock):
            task = asyncio.create_task(self.bot._drive_automatically())
            await asyncio.sleep(2)
            self.bot.vehicle = None
            await task

        # Assert
        self.behaviour_ctrl_mock.request_lane_change_for.assert_any_call(uuid=self.vehicle_id, value='right')

    @pytest.mark.asyncio
    async def test_drive_automatically_player_active_turn_left(self):
        self.bot.is_player_active = True
        self.bot.vehicle = self.vehicle_id

        random_values_mock = [3, 0] * 2

        with patch('random.randint', side_effect=random_values_mock):
            task = asyncio.create_task(self.bot._drive_automatically())
            await asyncio.sleep(2)
            self.bot.vehicle = None
            await task

        # Assert
        self.behaviour_ctrl_mock.request_lane_change_for.assert_any_call(uuid=self.vehicle_id, value='left')

    @pytest.mark.asyncio
    async def test_drive_automatically_player_active_uturn(self):
        self.bot.is_player_active = True
        self.bot.vehicle = self.vehicle_id

        random_values_mock = [4, 0] * 2

        with patch('random.randint', side_effect=random_values_mock):
            task = asyncio.create_task(self.bot._drive_automatically())
            await asyncio.sleep(2)
            self.bot.vehicle = None
            await task

        # Assert
        self.behaviour_ctrl_mock.request_uturn_for.assert_any_call(uuid=self.vehicle_id)
