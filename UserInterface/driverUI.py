from flask import Flask, render_template, request, redirect, url_for
from flask.views import View
from VehicleMovementManagement import DriverController


class DriverUI:

    def __init__(self, mapOfUuids, name=__name__):
        self.app = Flask(name)
        self.uuids = mapOfUuids
        return

    def run(self):
        def home_driver(player):
            return render_template('driver_index.html', my_var=player)
        self.app.add_url_rule('/driver/<player>', 'home_driver', view_func=home_driver)

        def slider_driver(player):
            value = request.form['value']
            #print(f"Driver{player} : Slider value: {value}")
            request_speed_change()
            return '', 204
        self.app.add_url_rule('/slider/<player>', 'slider_driver', methods=['POST'], view_func=slider_driver)

        # @self.app.route('/changeLane_left', methods=['POST'])
        def change_lane_left(player):
            #uuid = self.uuids{player}
            print(f"Driver{player}: Button << pressed!")
            #request_speed_change(uuid, 'left')
            # Hier können Sie Ihren Python-Code hinzufügen, der ausgeführt werden soll, wenn der Button 1 gedrückt wird.
            return redirect(url_for('home_driver', player=player))
        self.app.add_url_rule('/change_lane_left/<player>', 'change_lane_left', methods=['POST'], view_func=change_lane_left)

        # @self.app.route('/changeLane_right', methods=['POST'])
        def change_lane_right(player):
            print(f"Driver{player}: Button >> pressed!")
            # Hier können Sie Ihren Python-Code hinzufügen, der ausgeführt werden soll, wenn der Button 2 gedrückt wird.
            return redirect(url_for('home_driver', player=player))
        self.app.add_url_rule('/changeLane_right/<player>', 'change_lane_right', methods=['POST'], view_func=change_lane_right)

        self.app.run(debug=True, host='0.0.0.0')
