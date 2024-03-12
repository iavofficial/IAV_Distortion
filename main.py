from VehicleMovementManagement.BehaviourController import BehaviourController
from EnvironmentManagement.EnvironmentManager import EnvironmentManager


class Main:
    def __init__(self):
        environment_mng = EnvironmentManager()
        vehicles = environment_mng.get_vehicle_list()
        behaviour_ctrl = BehaviourController(vehicles)
        driver_ctrl = behaviour_ctrl.get_driver_controller()
        security_ctrl = behaviour_ctrl.get_security_controller()
