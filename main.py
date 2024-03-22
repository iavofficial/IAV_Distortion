from VehicleMovementManagement.BehaviourController import BehaviourController
from EnvironmentManagement.EnvironmentManager import EnvironmentManager
from CyberSecurityManager.CyberSecurityManager import CyberSecurityManager
from UserInterface.DriverUI import DriverUI
from UserInterface.StaffUI import StaffUI
from flask import Flask
from flask_socketio import SocketIO


class Main:
    def __init__(self):
        environment_mng = EnvironmentManager()
        vehicles = environment_mng.get_vehicle_list()
        for player_count in range(0, 2):
            environment_mng.set_player_uuid_mapping(player_id=str(player_count+1), uuid=vehicles[player_count].uuid)

        player_uuid_map = environment_mng.get_player_uuid_mapping()

        behaviour_ctrl = BehaviourController(vehicles)
        cybersecurity_mng = CyberSecurityManager(behaviour_ctrl, player_uuid_map)

        driver_ui = DriverUI(map_of_uuids=player_uuid_map, behaviour_ctrl=behaviour_ctrl)
        driver_ui_blueprint = driver_ui.get_blueprint()
        staff_ui = StaffUI(map_of_uuids=player_uuid_map, cybersecurity_mng=cybersecurity_mng)
        staff_ui_blueprint = staff_ui.get_blueprint()

        app = Flask('IAV_Distortion', template_folder='UserInterface/templates', static_folder='UserInterface/static')
        socketio = SocketIO(app)
        driver_ui.set_socketio(socketio)
        app.register_blueprint(driver_ui_blueprint, url_prefix='/driver')
        app.register_blueprint(staff_ui_blueprint, url_prefix='/staff')
        socketio.run(app, debug=True, host='0.0.0.0', allow_unsafe_werkzeug=True)


if __name__ == '__main__':
    iav_distortuion = Main()