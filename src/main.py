from VehicleManagement.VehicleController import VehicleController
from VehicleManagement.FleetController import FleetController
from VehicleMovementManagement.BehaviourController import BehaviourController
from EnvironmentManagement.EnvironmentManager import EnvironmentManager
from CyberSecurityManager.CyberSecurityManager import CyberSecurityManager
from UserInterface.DriverUI import DriverUI
from UserInterface.StaffUI import StaffUI
from flask import Flask
from flask_socketio import SocketIO

import os

class Main:
    def __init__(self, admin_password: str):
        fleet_ctrl = FleetController()
        environment_mng = EnvironmentManager(fleet_ctrl)

        vehicles = environment_mng.get_vehicle_list()
        player_uuid_map = environment_mng.get_player_uuid_mapping()

        behaviour_ctrl = BehaviourController(vehicles)
        cybersecurity_mng = CyberSecurityManager(behaviour_ctrl, player_uuid_map)

        app = Flask('IAV_Distortion', template_folder='UserInterface/templates', static_folder='UserInterface/static')
        socketio = SocketIO(app, cors_allowed_origins="*", async_mode=None)

        driver_ui = DriverUI(vehicles=vehicles, map_of_uuids=player_uuid_map, behaviour_ctrl=behaviour_ctrl, socketio=socketio)
        driver_ui_blueprint = driver_ui.get_blueprint()
        staff_ui = StaffUI(map_of_uuids=player_uuid_map, cybersecurity_mng=cybersecurity_mng, socketio=socketio, environment_mng=environment_mng, password=admin_password)
        staff_ui_blueprint = staff_ui.get_blueprint()

        app.register_blueprint(driver_ui_blueprint, url_prefix='/driver')
        app.register_blueprint(staff_ui_blueprint, url_prefix='/staff')
        socketio.run(app, debug=True, host='0.0.0.0', allow_unsafe_werkzeug=True)


if __name__ == '__main__':
    admin_pwd = os.environ.get('ADMIN_PASSWORD')
    if admin_pwd is None:
        print("WARNING!!! No admin password supplied via Environement variable. Using '123' as default password!")
        admin_pwd = '123'
    iav_distortion = Main(admin_pwd)
