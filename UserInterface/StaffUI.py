from flask import Blueprint, render_template, request, redirect, url_for
import re


class StaffUI:

    def __init__(self, map_of_uuids: dict, cybersecurity_mng, socketio, environment_mng, name=__name__):
        self.staffUI_blueprint = Blueprint(name='staffUI_bp', import_name='staffUI_bp')
        self.uuids = map_of_uuids  # {'player': 'uuid'}
        self.scenarios = cybersecurity_mng.get_all_hacking_scenarios()
        self.socketio = socketio
        self.environment_mng = environment_mng
        self.devices = []

        self.environment_mng.set_staff_ui(self)

        def home_staff_control():
            names, descriptions = self.sort_scenarios()
            active_scenarios = cybersecurity_mng.get_active_hacking_scenarios()  # {'UUID': 'scenarioID'}
            # TODO: How to update display of choose hacking scenarios?
            # TODO: Show selection of choose hackink scenarios alwasy sorted by playernumber
            return render_template('staff_control.html', activeScenarios=active_scenarios, uuids=self.uuids,
                                   names=names, descriptions=descriptions)
        self.staffUI_blueprint.add_url_rule('/staff_control', 'staff_control', view_func=home_staff_control)

        def set_scenario():
            selected_option = request.form.get('option')
            pattern = r"scenarioID_(\d+)-UUID_([\d:]+)"
            print(f"Scenario {selected_option} has been activated")
            match = re.search(pattern, selected_option)
            scenario_id = match.group(1)
            uuid = match.group(2)
            cybersecurity_mng.activate_hacking_scenario_for_vehicle(uuid, scenario_id)

            return redirect(url_for('staffUI_bp.staff_control'))
        self.staffUI_blueprint.add_url_rule('/hacking_scenario', methods=['POST'], view_func=set_scenario)

        @self.socketio.on('get_uuids')
        def update_uuids_staff_ui():
            self.update_map_of_uuids(self.uuids)
            return

        @self.socketio.on('connect')
        def initiate_uuids():
            print('Client connected')
            self.socketio.emit('update_uuids', self.uuids)
            return

        @self.socketio.on('search_cars')
        def search_cars():
            new_devices = environment_mng.find_active_anki_cars()
            self.socketio.emit('new_devices', new_devices)
            return

        @self.socketio.on('add_device')
        def handle_add_device(device):
            environment_mng.add_vehicle(device)
            # TODO: exception if device is no longer available
            # TODO: remove added device from new_devices list
            self.socketio.emit('device_added', device)

        def submit():
            # TODO: delete function, only for development and testing
            player = request.form['player']
            uuid = request.form['uuid']
            self.environment_mng.set_player_uuid_mapping(player_id=player, uuid=uuid)
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
