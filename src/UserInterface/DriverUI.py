# Copyright 2024 IAV GmbH
#
# This file is part of the IAV-Distortion project an interactive
# and educational showcase designed to demonstrate the need
# of automotive cybersecurity in a playful, engaging manner.
# and is released under the "Apache 2.0". Please see the LICENSE
# file that should have been included as part of this package.
#

from flask import Blueprint, render_template ,request
import uuid

class DriverUI:

    def __init__(self, behaviour_ctrl, environment_mng, socketio, name=__name__) -> None:
        self.driverUI_blueprint: Blueprint = Blueprint(name='driverUI_bp', import_name='driverUI_bp')
        self.vehicles: list = environment_mng.get_vehicle_list()
        self.uuids: dict = environment_mng.get_player_uuid_mapping()
        self.behaviour_ctrl = behaviour_ctrl
        self.socketio = socketio
        self.environment_mng = environment_mng

        def home_driver() -> str:
            player = request.cookies.get("player")
            print(f"Driver {player} connected!")
            if player is None:
                player = str(uuid.uuid4())

            vehicle = self.get_vehicle_by_player(player=player)
            player_exists = False
            picture = ''  # default picture can be added here
            vehicle_information = {}

            if vehicle is not None:
                player_exists = True
                picture = str(vehicle.vehicle_id)
                picture = picture.replace(":", "") + ".png"
                vehicle.set_driving_data_callback(self.update_driving_data)
                vehicle_information = vehicle.get_driving_data()
                print(f'set callback for {player}')

            return render_template('driver_index.html', player=player, player_exists=player_exists, picture=picture,
                                   vehicle_information=vehicle_information)

        self.driverUI_blueprint.add_url_rule('/', 'home_driver', view_func=home_driver)

        @self.socketio.on('connected')
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
            self.environment_mng.remove_player(player)

        @self.socketio.on('slider_changed')
        def handle_slider_change(data) -> None:
            player = data['player']
            value = float(data['value'])
            # print(f"Slider {player} value: {value}")
            if player in self.uuids:
              self.behaviour_ctrl.request_speed_change_for(uuid=self.uuids[player], value_proz=value)
            return

        @self.socketio.on('lane_change')
        def change_lane_left(data: dict) -> None:
            player = data['player']
            direction = data['direction']
            # print(f"Driver{player}: Button << pressed!")
            self.behaviour_ctrl.request_lane_change_for(uuid=self.uuids[player], value=direction)
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

