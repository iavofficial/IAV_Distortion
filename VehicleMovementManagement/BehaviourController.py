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
