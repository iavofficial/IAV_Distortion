from flask import Blueprint, render_template, request, redirect, url_for
from flask_socketio import emit
from VehicleMovementManagement.DriveController import DriverController


class DriverUI:
    #socketio = None

    #@classmethod
    #def set_socketio(cls, socketio):
    #    cls.socketio = socketio

    def __init__(self, map_of_uuids, behaviour_ctrl, socketio, name=__name__):
        self.driverUI_blueprint = Blueprint(name='driverUI_bp', import_name='driverUI_bp')
        self.uuids = map_of_uuids
        self.behaviour_ctrl = behaviour_ctrl
        self.socketio = socketio

        def home_driver(player):
            # TODO: Display Error message if requested player is not in uuids
            return render_template('driver_index.html', my_var=player)
        self.driverUI_blueprint.add_url_rule('/<player>', 'home_driver', view_func=home_driver)

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

        @self.socketio.on('slider_changed')
        def handle_slider_change(data):
            player = data['player']
            value = data['value']
            # print(f"Slider {player} value: {value}")
            self.behaviour_ctrl.request_speed_change(uuid=self.uuids[player], value=value)

        @self.socketio.on('lane_change')
        def change_lane_left(data):
            player = data['player']
            direction = data['direction']
            # print(f"Driver{player}: Button << pressed!")
            self.behaviour_ctrl.request_lane_change(uuid=self.uuids[player], value=direction)
            #return redirect(url_for('driverUI_bp.home_driver', player=player))


    def get_blueprint(self):
        return self.driverUI_blueprint
