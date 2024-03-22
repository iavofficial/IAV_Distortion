from flask import Blueprint, render_template, request, redirect, url_for
from flask_socketio import emit
from VehicleMovementManagement.DriveController import DriverController


class DriverUI:

    def __init__(self, map_of_uuids, behaviour_ctrl, name=__name__):
        self.driverUI_blueprint = Blueprint(name='driverUI_bp', import_name='driverUI_bp')
        self.uuids = map_of_uuids
        self.behaviour_ctrl = behaviour_ctrl
        self.socketio = None

        def home_driver(player):
            # TODO: Display Error message if requested player is not in uuids
            return render_template('driver_index.html', my_var=player)
        self.driverUI_blueprint.add_url_rule('/<player>', 'home_driver', view_func=home_driver)

        def slider_driver(player):
            value = request.form['value']
            # print(f"Driver{player} : Slider value: {value}")
            self.behaviour_ctrl.request_speed_change(uuid=self.uuids[player], value=value)
            return '', 204
        self.driverUI_blueprint.add_url_rule('/slider/<player>', 'slider_driver', methods=['POST'],
                                             view_func=slider_driver)

        def change_lane_left(player):
            # print(f"Driver{player}: Button << pressed!")
            self.behaviour_ctrl.request_lane_change(uuid=self.uuids[player], value='left')
            return redirect(url_for('driverUI_bp.home_driver', player=player))
        self.driverUI_blueprint.add_url_rule('/change_lane_left/<player>', 'change_lane_left', methods=['POST'],
                                             view_func=change_lane_left)

        def change_lane_right(player):
            # print(f"Driver{player}: Button >> pressed!")
            self.behaviour_ctrl.request_lane_change(uuid=self.uuids[player], value='right')
            return redirect(url_for('driverUI_bp.home_driver', player=player))
        self.driverUI_blueprint.add_url_rule('/changeLane_right/<player>', 'change_lane_right', methods=['POST'],
                                             view_func=change_lane_right)

    def get_blueprint(self):
        return self.driverUI_blueprint

    def set_socketio(self, socketio):
        self.socketio = socketio

        @socketio.on('slider_changed')
        def handle_slider_change(data):
            player = data['player']
            value = data['value']
            self.behaviour_ctrl.request_speed_change(uuid=self.uuids[player], value=value)
