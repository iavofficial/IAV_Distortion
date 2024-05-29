# Copyright 2024 IAV GmbH
#
# This file is part of the IAV-Distortion project an interactive
# and educational showcase designed to demonstrate the need
# of automotive cybersecurity in a playful, engaging manner.
# and is released under the "Apache 2.0". Please see the LICENSE
# file that should have been included as part of this package.
#

from flask import Blueprint, render_template ,request, url_for
import uuid

from EnvironmentManagement.EnvironmentManager import EnvironmentManager

class DriverUI:

    def __init__(self, behaviour_ctrl, environment_mng, socketio, name=__name__) -> None:
        self.driverUI_blueprint: Blueprint = Blueprint(name='driverUI_bp', import_name='driverUI_bp')
        self.vehicles: list = environment_mng.get_vehicle_list()
        self.behaviour_ctrl = behaviour_ctrl
        self.socketio = socketio
        self.environment_mng: EnvironmentManager = environment_mng

        def home_driver() -> str:
            player = request.cookies.get("player")
            print(f"Driver {player} connected!")
            if player is None:
                player = str(uuid.uuid4())

            vehicle = self.environment_mng.update_queues_and_get_vehicle(player)
            player_exists = False
            picture = ''  # default picture can be added here
            color = None
            vehicle_information = {
                'active_hacking_scenario': '0',
                'speed_request': '0'
            }

            if vehicle is not None:
                player_exists = True
                picture = vehicle.vehicle_id
                picture = picture.replace(":", "") + ".png"
                color = environment_mng.get_player_color(player)
                if color is not None and color[0] == "img":
                    color[1] = url_for('static', filename=f"images/{color[1]}")
                vehicle.set_driving_data_callback(self.update_driving_data)
                vehicle_information = vehicle.get_driving_data()
                print(f'set callback for {player}')

            return render_template('driver_index.html', player=player, player_exists=player_exists, picture=picture,
                                   vehicle_information=vehicle_information, has_color=(color is not None), color=color)

        self.driverUI_blueprint.add_url_rule('/', 'home_driver', view_func=home_driver)

        @self.socketio.on('handle_connect')
        def handle_connected(data):
            player = data["player"]
            vehicle = self.get_vehicle_by_player(player=player)
            print(f"Driver {player} connected with vehicle {vehicle}!")
            if vehicle is None:
                # add to queue
                self.environment_mng.add_player(player)
                print(f'added {player} to queue')
        @self.socketio.on('disconnected')
        def handle_disconnected(data):
            player=data["player"]
            print(f"Driver {player} disconnected!")
            self.environment_mng.remove_player_from_waitlist(player)
            self.environment_mng.remove_player_from_vehicle(player)

        @self.socketio.on('slider_changed')
        def handle_slider_change(data) -> None:
            player = data['player']
            value = float(data['value'])
            car_id = self.environment_mng.get_car_from_player(player).get_vehicle_id()
            self.behaviour_ctrl.request_speed_change_for(uuid=car_id, value_perc=value)
            return

        @self.socketio.on('lane_change')
        def change_lane(data: dict) -> None:
            player = data['player']
            direction = data['direction']
            car_id = self.environment_mng.get_car_from_player(player).get_vehicle_id()
            self.behaviour_ctrl.request_lane_change_for(uuid=car_id, value=direction)
            return

        @self.socketio.on('make_uturn')
        def make_uturn(data: dict) -> None:
            player = data['player']
            car_id = self.environment_mng.get_car_from_player(player).get_vehicle_id()
            self.behaviour_ctrl.request_uturn_for(uuid=car_id)
            return

        @self.socketio.on('get_driving_data')
        def get_driving_data(player: str) -> None:
            vehicle = self.get_vehicle_by_player(player=player)
            driving_data = vehicle.get_driving_data()
            self.update_driving_data(driving_data)
            return

    def update_driving_data(self, driving_data: dict) -> None:
        self.socketio.emit('update_driving_data', driving_data)
        return

    def get_blueprint(self) -> Blueprint:
        return self.driverUI_blueprint

    def get_vehicle_by_player(self, player: str):
        temp_vehicle = [vehicle for vehicle in self.vehicles if vehicle.player == player]
        if len(temp_vehicle) == 1:
            return temp_vehicle[0]
        elif len(temp_vehicle) < 1:
            return None
        else:
            # Todo: define error reaction if same player is assigned to different vehicles
            return None

