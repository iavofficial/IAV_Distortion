from flask import Blueprint, render_template, request, redirect, url_for


class StaffUI:

    def __init__(self, map_of_uuids, name=__name__):
        self.staffUI_blueprint = Blueprint(name='staffUI_bp', import_name='staffUI_bp')
        self.uuids = map_of_uuids

        def home_staff_control():
            return render_template('staff_control.html')
        self.staffUI_blueprint.add_url_rule('/staff_control', 'staff_control', view_func=home_staff_control)

        def set_szenario():
            selected_option = request.form.get('option')
            print(f"Szenario {selected_option} wurde aktiviert")
            return redirect(url_for('staffUI_bp.staff_control'))
        self.staffUI_blueprint.add_url_rule('/hacking_szenario', methods=['POST'], view_func=set_szenario)

    def get_blueprint(self):
        return self.staffUI_blueprint
