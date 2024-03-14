from VehicleMovementManagement.BehaviourController import BehaviourController


class SecurityController:

    def __init__(self, behaviour_ctrl: BehaviourController):
        self._behaviour_ctrl = behaviour_ctrl
        return

    def set_speed_factor(self, uuid: str, value):
        vehicle = self._behaviour_ctrl.get_vehicle_by_uuid(uuid)
        vehicle.speed_factor = value

        return

    def block_lane_change(self, uuid: str):
        vehicle = self._behaviour_ctrl.get_vehicle_by_uuid(uuid)
        vehicle.lange_change_blocked = True

        return

    def unblock_lane_change(self, uuid):
        vehicle = self._behaviour_ctrl.get_vehicle_by_uuid(uuid)
        vehicle.lange_change_blocked = False

        return

    def invert_light_switch(self, uuid, value):
        vehicle = self._behaviour_ctrl.get_vehicle_by_uuid(uuid)
        vehicle.isLightInverted = value

        return

    def turn_safemode_off(self, uuid):
        vehicle = self._behaviour_ctrl.get_vehicle_by_uuid(uuid)
        vehicle.isSafeModeOn = False

        return

    def turn_safemode_on(self, uuid):
        vehicle = self._behaviour_ctrl.get_vehicle_by_uuid(uuid)
        vehicle.isSafeModeOn = True

        return
