from flask import Blueprint, render_template, request, redirect, url_for
from CyberSecurityManager.CyberSecurityManager import CyberSecurityManager


class StaffUI:

    def __init__(self, map_of_uuids: dict, cybersecurity_mng, name=__name__):
        self.staffUI_blueprint = Blueprint(name='staffUI_bp', import_name='staffUI_bp')
        self.uuids = map_of_uuids
        self.scenarios = cybersecurity_mng.get_all_hacking_scenario()

        def home_staff_control():
            names, descriptions = self.sort_scenarios()

            # activeScenario = get_activeScenario()  # TODO: function from Security or BehaviourControler
            activeScenario = "Scenario 1: Speed Limiter"  # example for development
            return render_template('staff_control.html', activeScenario_car1=activeScenario, uuids=self.uuids,
                                   names=names, descriptions=descriptions)
        self.staffUI_blueprint.add_url_rule('/staff_control', 'staff_control', view_func=home_staff_control)

        def set_szenario():
            selected_option = request.form.get('option')
            print(f"Szenario {selected_option} wurde aktiviert")
            # uuid = uuids[] # determine uuid of hacked vehicle from variable selected_option
            # activate_hacking_scenario_for_vehicle(uuid, scenario_id)
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

