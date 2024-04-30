# Copyright 2024 IAV GmbH
#
# This file is part of the IAV-Distortion project an interactive
# and educational showcase designed to demonstrate the need
# of automotive cybersecurity in a playful, engaging manner.
# and is released under the "Apache 2.0". Please see the LICENSE
# file that should have been included as part of this package.
#

from flask import Blueprint, render_template, request, redirect, url_for
import re
import secrets


class StaffUI:

    def __init__(self, map_of_uuids: dict, cybersecurity_mng, socketio, environment_mng, password: str):
        self.password = password
        self.admin_token = secrets.token_urlsafe(12)
        self.staffUI_blueprint = Blueprint(name='staffUI_bp', import_name='staffUI_bp')
        self.uuids = map_of_uuids  # {'player': 'uuid'}
        self.scenarios = cybersecurity_mng.get_all_hacking_scenarios()
        self.socketio = socketio
        self.environment_mng = environment_mng
        self.devices = []

        self.environment_mng.set_staff_ui(self)

        def is_authentificated() -> bool:
            request_token = request.cookies.get('admin_token')
            return request_token is not None and request_token == self.admin_token

        def login_redirect():
            return redirect(url_for("staffUI_bp.login_site"))

        def home_staff_control(): 
            if not is_authentificated():
                return login_redirect()
            names, descriptions = self.sort_scenarios()
            active_scenarios = cybersecurity_mng.get_active_hacking_scenarios()  # {'UUID': 'scenarioID'}
            # TODO: Show selection of choose hacking scenarios always sorted by player number
            return render_template('staff_control.html', activeScenarios=active_scenarios, uuids=self.uuids,
                                   names=names, descriptions=descriptions)
        self.staffUI_blueprint.add_url_rule('/staff_control', 'staff_control', view_func=home_staff_control)

        def set_scenario():
            if not is_authentificated():
                return login_redirect()
            selected_option = request.form.get('option')
            pattern = r"scenarioID_(\d+)-UUID_([\d:]+)"
            print(f"Scenario {selected_option} has been activated")
            match = re.search(pattern, selected_option)
            scenario_id = match.group(1)
            uuid = match.group(2)
            cybersecurity_mng.activate_hacking_scenario_for_vehicle(uuid, scenario_id)

            return redirect(url_for('staffUI_bp.staff_control'))

        def login_site():
            if is_authentificated():
                return redirect(url_for('staffUI_bp.staff_control'))
            if request.method == 'GET':
                return render_template('staff_login.html')
            # a password was submitted via POST
            pwd = request.form.get('password')
            if pwd is not None and pwd == self.password:
                response = redirect(url_for('staffUI_bp.staff_control'))
                response.set_cookie('admin_token', self.admin_token)
                return response
            return render_template('staff_login.html', wrong_password=True)

        self.staffUI_blueprint.add_url_rule('/hacking_scenario', methods=['POST'], view_func=set_scenario)
        self.staffUI_blueprint.add_url_rule('', methods=['GET', 'POST'], view_func=login_site)

        # We can't directly redirect via SocketIO so we just drop the requests
        # TODO: Log dropped events!
        @self.socketio.on('get_uuids')
        def update_uuids_staff_ui():
            if not is_authentificated():
                return
            self.update_map_of_uuids(self.uuids)
            return

        @self.socketio.on('connect')
        def initiate_uuids():
            if not is_authentificated():
                return
            print('Client connected')
            self.socketio.emit('update_uuids', self.uuids)
            return

        @self.socketio.on('search_cars')
        def search_cars():
            if not is_authentificated():
                return
            print("Searching devices")
            new_devices = environment_mng.find_unpaired_anki_cars()
            self.socketio.emit('new_devices', new_devices)
            return

        @self.socketio.on('add_device')
        def handle_add_device(device):
            if not is_authentificated():
                return
            environment_mng.add_vehicle(device)
            # TODO: exception if device is no longer available
            # TODO: remove added device from new_devices list
            self.socketio.emit('device_added', device)
            return

        @self.socketio.on('get_update_hacking_scenarios')
        def update_hacking_scenarios():
            if not is_authentificated():
                return
            names, descriptions = self.sort_scenarios()
            active_scenarios = cybersecurity_mng.get_active_hacking_scenarios()
            data = {'activeScenarios': active_scenarios, 'uuids': self.uuids, 'names': names,
                    'descriptions': descriptions}
            self.socketio.emit('update_hacking_scenarios', data)
            return

        def submit():
            if not is_authentificated():
                return login_redirect()
            # TODO: delete function, only for development and testing
            uuid = request.form['uuid']
            self.environment_mng.add_vehicle(uuid=uuid)
            return redirect(url_for('staffUI_bp.staff_control'))
        self.staffUI_blueprint.add_url_rule('/submit', methods=['POST'], view_func=submit)

    def get_blueprint(self):
        return self.staffUI_blueprint

    def sort_scenarios(self):
        scenario_names = {}
        scenario_descriptions = {}
        for scenario in self.scenarios:
            scenario_names.update({scenario['id']: scenario['name']})
            scenario_descriptions.update({scenario['id']: scenario['description']})
        return scenario_names, scenario_descriptions

    def update_map_of_uuids(self, map_of_uuids):
        self.uuids = map_of_uuids
        self.socketio.emit('update_uuids', self.uuids)
