from flask import Blueprint, render_template, request, redirect, url_for
import re
from CyberSecurityManager.CyberSecurityManager import CyberSecurityManager


class StaffUI:

    def __init__(self, map_of_uuids: dict, cybersecurity_mng, name=__name__):
        self.staffUI_blueprint = Blueprint(name='staffUI_bp', import_name='staffUI_bp')
        self.uuids = map_of_uuids
        self.scenarios = cybersecurity_mng.get_all_hacking_scenarios()

        def home_staff_control():
            names, descriptions = self.sort_scenarios()

            activeScenarios = cybersecurity_mng.get_active_hacking_scenarios()  # {'UUID': 'scenarioID'}
            # activeScenarios = {'aa:bb:cc:dd': '1'}  # example for development
            return render_template('staff_control.html', activeScenarios=activeScenarios, uuids=self.uuids,
                                   names=names, descriptions=descriptions)
        self.staffUI_blueprint.add_url_rule('/staff_control', 'staff_control', view_func=home_staff_control)

        def set_szenario():
            selected_option = request.form.get('option')
            pattern = r"scenarioID_(\d+)-UUID_([\d:]+)"
            print(f"Szenario {selected_option} wurde aktiviert")
            match = re.search(pattern, selected_option)
            scenario_id = match.group(1)
            uuid = match.group(2)
            cybersecurity_mng.activate_hacking_scenario_for_vehicle(uuid, scenario_id)

            return redirect(url_for('staffUI_bp.staff_control'))
        self.staffUI_blueprint.add_url_rule('/hacking_szenario', methods=['POST'], view_func=set_szenario)

    def get_blueprint(self):
        return self.staffUI_blueprint

    def sort_scenarios(self):
        scenario_names = {}
        scenario_descriptions = {}
        for scenario in self.scenarios:
            scenario_names.update({scenario['id']: scenario['name']})
            scenario_descriptions.update({scenario['id']: scenario['description']})

        return scenario_names, scenario_descriptions

