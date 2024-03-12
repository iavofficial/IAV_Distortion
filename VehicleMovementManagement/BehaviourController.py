from DriveController import DriverController
from SecurityController import SecurityController


class BehaviourController:

    def __init__(self, vehicles):
        self.vehicles = vehicles

    def get_driver_controller(self):
        return DriverController()

    def get_security_controller(self):
        return SecurityController()
