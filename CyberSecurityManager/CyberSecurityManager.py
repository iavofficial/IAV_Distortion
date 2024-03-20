from VehicleMovementManagement.BehaviourController import BehaviourController


def _set_scenarios():
    scenario0 = {"id": "0",
                 "name": "normal",
                 "description": "no hacking",
                 "speed_factor": 1.0,
                 "block_lane_change": False,
                 "invert_light": False,
                 "turn_safemode_off": False}

    scenario1 = {"id": "1",
                 "name": "slow_down",
                 "description": "drive with reduced speed",
                 "speed_factor": 0.3,
                 "block_lane_change": False,
                 "invert_light": False,
                 "turn_safemode_off": False}

    scenario3 = {"id": "3",
                 "name": "stop",
                 "description": "vehicle stops instantaneous",
                 "speed_factor": 0.0,
                 "block_lane_change": False,
                 "invert_light": False,
                 "turn_safemode_off": False}

    scenario4 = {"id": "4",
                 "name": "no safety",
                 "description": "the safemode module is deactivated",
                 "speed_factor": 1.5,
                 "block_lane_change": False,
                 "invert_light": False,
                 "turn_safemode_off": True}

    return [scenario0, scenario1, scenario3, scenario4]


class CyberSecurityManager:

    def __init__(self, behaviour_ctrl: BehaviourController):
        self._behaviour_ctrl = behaviour_ctrl
        self._hacking_scenarios = _set_scenarios()

        return

    def get_all_hacking_scenarios(self):
        return self._hacking_scenarios

    def activate_hacking_scenario_for_vehicle(self, uuid: str, scenario_id: str):
        scenario = next((sce for sce in self._hacking_scenarios if sce["id"] == scenario_id), None)

        self._behaviour_ctrl.set_speed_factor(uuid, scenario["speed_factor"])

        if scenario["block_lane_change"]:
            self._behaviour_ctrl.block_lane_change(uuid)
        else:
            self._behaviour_ctrl.unblock_lane_change(uuid)

        self._behaviour_ctrl.invert_light_switch(uuid, scenario["invert_light"])

        if scenario["turn_safemode_off"]:
            self._behaviour_ctrl.turn_safemode_off(uuid)
        else:
            self._behaviour_ctrl.turn_safemode_on(uuid)

        self._update_active_hacking_scenarios(uuid, scenario_id)

        return

    def get_active_hacking_scenarios(self):
        return self._active_scenarios

    def _update_active_hacking_scenarios(self, uuid: str, scenario_id: str):
        self._active_scenarios = {uuid: scenario_id}
