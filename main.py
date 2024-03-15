from VehicleMovementManagement.BehaviourController import BehaviourController
from EnvironmentManagement.EnvironmentManager import EnvironmentManager
from UserInterface.DriverUI import DriverUI
from UserInterface.StaffUI import StaffUI
from flask import Flask


class Main:
    def __init__(self):
        environment_mng = EnvironmentManager()
        vehicles = environment_mng.get_vehicle_list()
        player_uuid_map = environment_mng.get_player_uuid_mapping()

        behaviour_ctrl = BehaviourController(vehicles)
        driver_ctrl = behaviour_ctrl.get_driver_controller()
        security_ctrl = behaviour_ctrl.get_security_controller()

        driver_ui = DriverUI(map_of_uuids=player_uuid_map, drive_ctrl=driver_ctrl)
        driver_ui_blueprint = driver_ui.get_blueprint()
        staff_ui = StaffUI(map_of_uuids=player_uuid_map)
        staff_ui_blueprint = staff_ui.get_blueprint()

        app = Flask('IAV_Distortion', template_folder='Userinterface/templates', static_folder='Userinterface/static')
        app.register_blueprint(driver_ui_blueprint, url_prefix='/driver')
        app.register_blueprint(staff_ui_blueprint, url_prefix='/staff')
        app.run(debug=True, host='0.0.0.0')


if __name__ == '__main__':
    iav_distortuion = Main()