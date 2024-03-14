from flask import Flask, render_template, request, redirect, url_for


class StaffUI:

    def __init__(self, map_of_uuids, name=__name__):
        self.app = Flask(name)
        self.uuids = map_of_uuids
        return

    def run(self):
        def home_staff_control():
            return render_template('staff_control.html')
        self.app.add_url_rule('/staff_control', 'staff_control', view_func=home_staff_control)

        def set_szenario(player):
            selected_option = request.form.get('option')
            print(f"Senario {selected_option} wurde aktiviert für Player {player}")
            return redirect(url_for('home_staff_control'))
        self.app.add_url_rule('/hacking_szenario_car1', methods=['POST'], view_func=set_szenario)

        self.app.run(debug=True, host='0.0.0.0', port=5001)
