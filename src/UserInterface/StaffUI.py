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
from typing import Any, Dict, Tuple, List


class StaffUI:

    def __init__(self, map_of_uuids: dict, cybersecurity_mng, socketio, environment_mng):
        self.staffUI_blueprint: Blueprint = Blueprint(name='staffUI_bp', import_name='staffUI_bp')
        self.uuids: dict = map_of_uuids  # {'player': 'uuid'}
        self.scenarios: List[dict] = cybersecurity_mng.get_all_hacking_scenarios()
        self.socketio: Any = socketio
        self.environment_mng = environment_mng
        self.devices: list = []

        self.environment_mng.set_staff_ui(self)

        def home_staff_control() -> Any:
            names, descriptions = self.sort_scenarios()
            active_scenarios = cybersecurity_mng.get_active_hacking_scenarios()  # {'UUID': 'scenarioID'}
            # TODO: Show selection of choose hacking scenarios always sorted by player number
            return render_template('staff_control.html', activeScenarios=active_scenarios, uuids=self.uuids,
                                   names=names, descriptions=descriptions)
        self.staffUI_blueprint.add_url_rule('/staff_control', 'staff_control', view_func=home_staff_control)

        def set_scenario() -> Any:
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
        def update_uuids_staff_ui() -> None:
            self.update_map_of_uuids(self.uuids)
            return

        @self.socketio.on('connect')
        def initiate_uuids() -> None:
            print('Client connected')
            self.socketio.emit('update_uuids', self.uuids)
            return

        @self.socketio.on('search_cars')
        def search_cars() -> None:
            print("Searching devices")
            new_devices = environment_mng.find_unpaired_anki_cars()
            self.socketio.emit('new_devices', new_devices)
            return

        @self.socketio.on('add_device')
        def handle_add_device(device: str) -> None:
            environment_mng.add_vehicle(device)
            # TODO: exception if device is no longer available
            # TODO: remove added device from new_devices list
            self.socketio.emit('device_added', device)
            return

        @self.socketio.on('delete_device')
        def handle_delete_player(device: str) -> None:
            print(f'delete player {device}')
            environment_mng.remove_vehicle(device)
            pass

        @self.socketio.on('get_update_hacking_scenarios')
        def update_hacking_scenarios() -> None:
            names, descriptions = self.sort_scenarios()
            active_scenarios = cybersecurity_mng.get_active_hacking_scenarios()
            data = {'activeScenarios': active_scenarios, 'uuids': self.uuids, 'names': names,
                    'descriptions': descriptions}
            self.socketio.emit('update_hacking_scenarios', data)
            return

    def get_blueprint(self) -> Blueprint:
        return self.staffUI_blueprint

    def sort_scenarios(self) -> Tuple[dict, dict]:
        scenario_names = {}
        scenario_descriptions = {}
        for scenario in self.scenarios:
            scenario_names.update({scenario['id']: scenario['name']})
            scenario_descriptions.update({scenario['id']: scenario['description']})
        return scenario_names, scenario_descriptions

    def update_map_of_uuids(self, map_of_uuids: dict) -> None:
        self.uuids = map_of_uuids
        self.socketio.emit('update_uuids', self.uuids)
        return
