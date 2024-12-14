import asyncio
import random

from VehicleMovementManagement.BehaviourController import BehaviourController


class Bot:
    def __init__(self, vehicle: str, _behaviour_ctrl: BehaviourController):
        self.vehicle = vehicle
        self._behaviour_ctrl = _behaviour_ctrl
        self.is_player_active = False
        asyncio.create_task(self._drive_automatically())

    def get_vehicle_id(self) -> str:
        return self.vehicle

    def set_vehicle(self, vehicle: str) -> None:
        self.vehicle = vehicle

    def set_is_player_active(self, is_player_active: bool) -> None:
        self.is_player_active = is_player_active
        if not self.is_player_active:
            self._behaviour_ctrl.request_speed_change_for(uuid=self.vehicle, value_perc=30.0)
        else:
            self._behaviour_ctrl.request_speed_change_for(uuid=self.vehicle, value_perc=50.0)

    async def _drive_automatically(self):
        self._behaviour_ctrl.request_speed_change_for(uuid=self.vehicle, value_perc=30.0)
        while True:
            await asyncio.sleep(1)
            if self.vehicle is None:
                break
            if self.is_player_active:
                random_move = random.randint(0, 10)
                random_speed = float(random.randint(20, 80))
                cases = {
                    1: lambda: self._behaviour_ctrl.request_speed_change_for(uuid=self.vehicle,
                                                                             value_perc=random_speed),
                    2: lambda: self._behaviour_ctrl.request_lane_change_for(uuid=self.vehicle,
                                                                            value="right"),
                    3: lambda: self._behaviour_ctrl.request_lane_change_for(uuid=self.vehicle,
                                                                            value="left"),
                    4: lambda: self._behaviour_ctrl.request_uturn_for(uuid=self.vehicle)
                    }
                action = cases.get(random_move)

                if action:
                    action()
