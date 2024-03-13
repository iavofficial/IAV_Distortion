from flask import Flask, render_template, request, redirect, url_for
from VehicleMovementManagement.DriveController import DriverController


class DriverUI:

    def __init__(self, map_of_uuids, drive_ctrl, name=__name__):
        self.app = Flask(name)
        self.uuids = map_of_uuids
        self.drive_ctrl = drive_ctrl
        return

    def run(self):
        def home_driver(player):
            return render_template('driver_index.html', my_var=player)
        self.app.add_url_rule('/driver/<player>', 'home_driver', view_func=home_driver)

        def slider_driver(player):
            value = request.form['value']
            # print(f"Driver{player} : Slider value: {value}")
            self.drive_ctrl.request_speed_change(uuid=self.uuids[player], value=value)
            return '', 204
        self.app.add_url_rule('/slider/<player>', 'slider_driver', methods=['POST'], view_func=slider_driver)

        def change_lane_left(player):
            # print(f"Driver{player}: Button << pressed!")
            self.drive_ctrl.request_lane_change(uuid=self.uuids[player], value='left')
            return redirect(url_for('home_driver', player=player))
        self.app.add_url_rule('/change_lane_left/<player>', 'change_lane_left', methods=['POST'],
                              view_func=change_lane_left)

        def change_lane_right(player):
            # print(f"Driver{player}: Button >> pressed!")
            self.drive_ctrl.request_lane_change(uuid=self.uuids[player], value='right')
            return redirect(url_for('home_driver', player=player))
        self.app.add_url_rule('/changeLane_right/<player>', 'change_lane_right', methods=['POST'],
                              view_func=change_lane_right)

        self.app.run(debug=True, host='0.0.0.0')
