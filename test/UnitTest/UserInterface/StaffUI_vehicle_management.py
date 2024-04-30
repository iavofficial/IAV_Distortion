from unittest.mock import MagicMock
from flask import Flask
from flask_socketio import SocketIO
from UserInterface.StaffUI import StaffUI

player_uuid_map = {
    '1': '12:34:56',
    '2': '78:90:87:65'
}

hacking_scenarios = [{
    "id": "0",
    "name": "normal",
    "description": "no hacking",
    "speed_factor": 1.0,
    "block_lane_change": False,
    "invert_light": False,
    "turn_safemode_off": False
}]

cybersecurity_mng_mock = MagicMock()
cybersecurity_mng_mock.get_all_hacking_scenarios.return_value = hacking_scenarios
cybersecurity_mng_mock.get_active_hacking_scenarios.return_value = {'12:34:56': '0',
                                                                    '78:90:87:65': '0'}

environment_mng_mock = MagicMock()
environment_mng_mock.set_staff_ui.return_value = None
environment_mng_mock.find_unpaired_anki_cars.return_value = ['11:22:33:44', '55:66:77:88']
environment_mng_mock.add_vehicle.return_value = None


def build_ui():
    app = Flask('IAV_Distortion', template_folder='../../../src/UserInterface/templates',
                static_folder='../../../src/UserInterface/static')
    socketio = SocketIO(app, cors_allowed_origins="*", async_mode=None)

    staff_ui = StaffUI(map_of_uuids=player_uuid_map, cybersecurity_mng=cybersecurity_mng_mock, socketio=socketio,
                       environment_mng=environment_mng_mock)
    staff_ui_blueprint = staff_ui.get_blueprint()

    app.register_blueprint(staff_ui_blueprint, url_prefix='/staff')
    socketio.run(app, debug=True, host='0.0.0.0', allow_unsafe_werkzeug=True)


build_ui()
