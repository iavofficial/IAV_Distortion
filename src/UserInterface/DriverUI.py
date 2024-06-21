# Copyright 2024 IAV GmbH
#
# This file is part of the IAV-Distortion project an interactive
# and educational showcase designed to demonstrate the need
# of automotive cybersecurity in a playful, engaging manner.
# and is released under the "Apache 2.0". Please see the LICENSE
# file that should have been included as part of this package.
#

from quart import Blueprint, render_template, request
import socketio
import uuid
from logging import Logger, getLogger
import asyncio

from EnvironmentManagement.EnvironmentManager import EnvironmentManager
from EnvironmentManagement.ConfigurationHandler import ConfigurationHandler

class DriverUI:

    def __init__(self, behaviour_ctrl, environment_mng, sio: socketio, name=__name__) -> None:
        self.driverUI_blueprint: Blueprint = Blueprint(name='driverUI_bp', import_name='driverUI_bp')
        self.vehicles: list = environment_mng.get_vehicle_list()
        self.behaviour_ctrl = behaviour_ctrl
        self._sio: socketio = sio
        self.environment_mng: EnvironmentManager = environment_mng
        self.config_handler: ConfigurationHandler = ConfigurationHandler()
        self.logger: Logger = getLogger(__name__)

        async def home_driver() -> str:
            player = request.cookies.get("player")
            print(f"Driver {player} connected!")
            if player is None:
                player = str(uuid.uuid4())

            config = self.config_handler.get_configuration()
            vehicle = self.environment_mng.update_queues_and_get_vehicle(player)
            player_exists = False
            picture = ''  # default picture can be added here
            vehicle_information = {
                'active_hacking_scenario': '0',
                'speed_request': '0'
            }

            if vehicle is not None:
                player_exists = True
                picture = vehicle.vehicle_id
                if vehicle.vehicle_id.startswith("Virtual Vehicle"):
                    try:
                        picture = 'Virtual_Vehicles/' + config["virtual_cars_pics"][vehicle.vehicle_id]
                    except KeyError:
                        self.logger.warning(f'No image configured for {vehicle.vehicle_id}.')
                else:
                    picture = 'Real_Vehicles/' + picture.replace(":", "") + ".png"
                vehicle.set_driving_data_callback(self.update_driving_data)
                vehicle_information = vehicle.get_driving_data()
                self.logger.debug(f'Callback set for {player}')

            return await render_template('driver_index.html', player=player, player_exists=player_exists, picture=picture,
                                   vehicle_information=vehicle_information)

        self.driverUI_blueprint.add_url_rule('/', 'home_driver', view_func=home_driver)

        @self._sio.on('handle_connect')
        def handle_connected(sid, data):
            player = data["player"]
            vehicle = self.get_vehicle_by_player(player=player)
            print(f"Driver {player} connected with vehicle {vehicle}!")
            if vehicle is None:
                # add to queue
                self.environment_mng.add_player(player)
                print(f'added {player} to queue')
            return
        
        @self._sio.on('disconnected')
        def handle_disconnected(sid, data):
            player=data["player"]
            print(f"Driver {player} disconnected!")
            self.environment_mng.remove_player_from_waitlist(player)
            # TODO: check what happens to disconnected players assigned to a car
            return

        @self._sio.on('slider_changed')
        def handle_slider_change(sid, data) -> None:
            player = data['player']
            value = float(data['value'])
            car_id = self.environment_mng.get_car_from_player(player).get_vehicle_id()
            # TODO: add check for car_id not None
            self.behaviour_ctrl.request_speed_change_for(uuid=car_id, value_perc=value)
            return

        @self._sio.on('lane_change')
        def change_lane(sid, data: dict) -> None:
            player = data['player']
            direction = data['direction']
            car_id = self.environment_mng.get_car_from_player(player).get_vehicle_id()
            self.behaviour_ctrl.request_lane_change_for(uuid=car_id, value=direction)
            return

        @self._sio.on('make_uturn')
        def make_uturn(sid, data: dict) -> None:
            player = data['player']
            car_id = self.environment_mng.get_car_from_player(player).get_vehicle_id()
            self.behaviour_ctrl.request_uturn_for(uuid=car_id)
            return

        @self._sio.on('get_driving_data')
        def get_driving_data(sid, player: str) -> None:
            vehicle = self.get_vehicle_by_player(player=player)
            driving_data = vehicle.get_driving_data()
            self.update_driving_data(driving_data)
            return

    def update_driving_data(self, driving_data: dict) -> None:
        self.__run_async_task(self.__emit_driving_data(driving_data))
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

