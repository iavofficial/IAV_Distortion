from flask import Blueprint, render_template


class DriverUI:

    def __init__(self, map_of_uuids, behaviour_ctrl, socketio, name=__name__):
        self.driverUI_blueprint = Blueprint(name='driverUI_bp', import_name='driverUI_bp')
        self.uuids = map_of_uuids
        self.behaviour_ctrl = behaviour_ctrl
        self.socketio = socketio

        def home_driver(player):
            player_exists = False
            for key in self.uuids:
                if key == player:
                    player_exists = True

            if player_exists:
                picture = self.uuids[player]
                picture = picture.replace(":", "") + ".png"
            else:
                picture = "alternative.jpg"

            print(self.uuids)
            print(self.uuids[player])
            vehicle = behaviour_ctrl.get_vehicle_by_uuid(self.uuids[player])
            print(vehicle._speed_actual)
            print(vehicle.get_speed_request())

            return render_template('driver_index.html', my_var=player, player_exists=player_exists, picture=picture)
        self.driverUI_blueprint.add_url_rule('/<player>', 'home_driver', view_func=home_driver)

        @self.socketio.on('slider_changed')
        def handle_slider_change(data):
            player = data['player']
            value = float(data['value'])
            # print(f"Slider {player} value: {value}")
            self.behaviour_ctrl.request_speed_change_for(uuid=self.uuids[player], value_proz=value)
            return

        @self.socketio.on('lane_change')
        def change_lane_left(data):
            player = data['player']
            direction = data['direction']
            # print(f"Driver{player}: Button << pressed!")
            self.behaviour_ctrl.request_lane_change_for(uuid=self.uuids[player], value=direction)
            return

        @self.socketio.on('get_vehicle_status')
        def get_vehicle_status():
            pass

    def update_vehicle_status(self, vehicle_status):
        self.socketio.emit('update_vehicle_status', vehicle_status)

    def get_blueprint(self):
        return self.driverUI_blueprint
