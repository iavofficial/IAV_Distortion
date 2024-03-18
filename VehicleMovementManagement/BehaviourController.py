from typing import List

from VehicleMovementManagement.DriveController import DriverController
from VehicleMovementManagement.SecurityController import SecurityController
from DataModel.Vehicle import Vehicle


class BehaviourController:

    def __init__(self, vehicles: List[Vehicle]):
        self.vehicles = vehicles

    def get_driver_controller(self):
        return DriverController(self)

    def get_security_controller(self):
        return SecurityController(self)

    def get_vehicle_by_uuid(self, uuid: str):
        found_vehicle = next((o for o in self.vehicles if o.uuid == uuid), None)
        return found_vehicle

    def on_vehicle_data_change(self, uuid):
        self.get_vehicle_by_uuid(uuid)

    # Driver Controller
    def request_speed_change(self, uuid: str, value):
        vehicle = self.get_vehicle_by_uuid(uuid)
        vehicle.speed_request = value

        print(f"Switch speed to {value}. UUID: {uuid}")
        return

    def request_lane_change(self, uuid: str, value):
        vehicle = self.get_vehicle_by_uuid(uuid)
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
        vehicle = self.get_vehicle_by_uuid(uuid)
        vehicle.isLightOn = True

        return

    def request_lights_off(self, uuid: str):
        vehicle = self.get_vehicle_by_uuid(uuid)
        vehicle.isLightOn = False

        return

    # Security Controller
    def set_speed_factor(self, uuid: str, value):
        vehicle = self.get_vehicle_by_uuid(uuid)
        vehicle.speed_factor = value

        return

    def block_lane_change(self, uuid: str):
        vehicle = self.get_vehicle_by_uuid(uuid)
        vehicle.lange_change_blocked = True

        return

    def unblock_lane_change(self, uuid):
        vehicle = self.get_vehicle_by_uuid(uuid)
        vehicle.lange_change_blocked = False

        return

    def invert_light_switch(self, uuid, value):
        vehicle = self.get_vehicle_by_uuid(uuid)
        vehicle.isLightInverted = value

        return

    def turn_safemode_off(self, uuid):
        vehicle = self.get_vehicle_by_uuid(uuid)
        vehicle.isSafeModeOn = False

        return

    def turn_safemode_on(self, uuid):
        vehicle = self.get_vehicle_by_uuid(uuid)
        vehicle.isSafeModeOn = True

        return
