from VehicleMovementManagement.BehaviourController import BehaviourController
from EnvironmentManagement.EnvironmentManager import EnvironmentManager
from UserInterface.DriverUI import DriverUI


class Main:
    def __init__(self):
        environment_mng = EnvironmentManager()
        vehicles = environment_mng.get_vehicle_list()
        player_uuid_map = environment_mng.get_player_uuid_mapping()

        behaviour_ctrl = BehaviourController(vehicles)
        driver_ctrl = behaviour_ctrl.get_driver_controller()
        security_ctrl = behaviour_ctrl.get_security_controller()

        driver_ui = DriverUI(map_of_uuids=player_uuid_map, drive_ctrl=driver_ctrl)
        driver_ui.run()


if __name__ == '__main__':
    iav_distortion = Main()
