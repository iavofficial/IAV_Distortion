# Copyright 2024 IAV GmbH
#
# This file is part of the IAV-Distortion project an interactive
# and educational showcase designed to demonstrate the need
# of automotive cybersecurity in a playful, engaging manner.
# and is released under the "Apache 2.0". Please see the LICENSE
# file that should have been included as part of this package.
#
from gevent import monkey
monkey.patch_all()

import logging

from VehicleManagement.VehicleController import VehicleController
from VehicleManagement.FleetController import FleetController
from VehicleMovementManagement.BehaviourController import BehaviourController
from EnvironmentManagement.EnvironmentManager import EnvironmentManager
from CyberSecurityManager.CyberSecurityManager import CyberSecurityManager
from UserInterface.DriverUI import DriverUI
from UserInterface.StaffUI import StaffUI
from UserInterface.CarMap import CarMap
from flask import Flask
from flask_socketio import SocketIO

import os
import asyncio

def main(admin_password: str, debug: bool):
    app = Flask('IAV_Distortion', template_folder='UserInterface/templates', static_folder='UserInterface/static')
    socketio = SocketIO(app, cors_allowed_origins="*", async_mode='gevent')
    # Todo: using async_mode='threading' makes flask use the development server instead of the eventlet server.
    #  change to use some production server

    fleet_ctrl = FleetController()
    environment_mng = EnvironmentManager(fleet_ctrl, socketio)

    vehicles = environment_mng.get_vehicle_list()

    behaviour_ctrl = BehaviourController(vehicles)
    cybersecurity_mng = CyberSecurityManager(behaviour_ctrl)


   # driver_ui = DriverUI(vehicles=vehicles, map_of_uuids=player_uuid_map, behaviour_ctrl=behaviour_ctrl,
   #                      socketio=socketio)

    driver_ui = DriverUI(behaviour_ctrl=behaviour_ctrl, environment_mng = environment_mng,socketio=socketio)
    driver_ui_blueprint = driver_ui.get_blueprint()
   # staff_ui = StaffUI(map_of_uuids=player_uuid_map, cybersecurity_mng=cybersecurity_mng, socketio=socketio,
    #                   environment_mng=environment_mng, password=admin_password)
    staff_ui = StaffUI(cybersecurity_mng=cybersecurity_mng, socketio=socketio, environment_mng=environment_mng, password=admin_password)
    staff_ui_blueprint = staff_ui.get_blueprint()
    car_map = CarMap(environment_manager=environment_mng)
    car_map_blueprint = car_map.get_blueprint()

    app.register_blueprint(driver_ui_blueprint, url_prefix='/driver')
    app.register_blueprint(staff_ui_blueprint, url_prefix='/staff')
    app.register_blueprint(car_map_blueprint, url_prefix='/car_map')
    socketio.run(app, debug=debug, host='0.0.0.0', allow_unsafe_werkzeug=debug)


if __name__ == '__main__':
    # TODO: work with hashed password, passwords should not be stored in clear text
    admin_pwd = os.environ.get('ADMIN_PASSWORD')
    debug = False
    if admin_pwd is None:
        print("WARNING!!! No admin password supplied via Environment variable. Using '0000' as default password"
              " and starting in debug mode. Please change the password!")
        admin_pwd = '0000'
        debug = True
        
    main(admin_pwd, debug)

