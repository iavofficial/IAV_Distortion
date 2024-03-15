class DriverController:
    """
    def __init__(self, behaviour_ctrl: BehaviourController):
        self._behaviour_ctrl = behaviour_ctrl
        return

    def request_speed_change(self, uuid: str, value):
        vehicle = self._behaviour_ctrl.get_vehicle_by_uuid(uuid)
        vehicle.speed_request = value

        print(f"Switch speed to {value}. UUID: {uuid}")
        return

    def request_lane_change(self, uuid: str, value):
        vehicle = self._behaviour_ctrl.get_vehicle_by_uuid(uuid)
        if value == "left":
            vehicle.lane_request = 1

            print(f"Switch Lane left. UUID: {uuid}")

        elif value == "right":
            vehicle.lane_request = -1

            print(f"Switch Lane right. UUID: {uuid}")

        else:
            vehicle.lane_request = 0
        return

    def request_lights_on(self, uuid: str):
        vehicle = self._behaviour_ctrl.get_vehicle_by_uuid(uuid)
        vehicle.isLightOn = True

        return

    def request_lights_off(self, uuid: str):
        vehicle = self._behaviour_ctrl.get_vehicle_by_uuid(uuid)
        vehicle.isLightOn = False

        return
    """