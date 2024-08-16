# Copyright 2024 IAV GmbH
#
# This file is part of the IAV-Distortion project an interactive
# and educational showcase designed to demonstrate the need
# of automotive cybersecurity in a playful, engaging manner.
# and is released under the "Apache 2.0". Please see the LICENSE
# file that should have been included as part of this package.
#
import logging

from VehicleManagement.VehicleController import VehicleController
from VehicleManagement.FleetController import FleetController
from VehicleMovementManagement.BehaviourController import BehaviourController
from EnvironmentManagement.EnvironmentManager import EnvironmentManager
from EnvironmentManagement.ConfigurationHandler import ConfigurationHandler
from CyberSecurityManager.CyberSecurityManager import CyberSecurityManager
from UserInterface.DriverUI import DriverUI
from UserInterface.StaffUI import StaffUI
from UserInterface.CarMap import CarMap

from quart import Quart
from socketio import AsyncServer, ASGIApp
from hypercorn.config import Config
from hypercorn.asyncio import serve
import asyncio

import os


def create_app(admin_password: str):
    socket = AsyncServer(async_mode='asgi')
    quart_app = Quart('IAV_Distortion', template_folder='UserInterface/templates', static_folder='UserInterface/static')

    config_handler = ConfigurationHandler()
    fleet_ctrl = FleetController()
    environment_mng = EnvironmentManager(fleet_ctrl)

    @quart_app.before_serving
    async def app_start_up():
        """
        App initialization.
        Function executed once during application start up.
        """
        if config_handler.get_configuration()["environment"]["env_auto_discover_anki_cars"]:
            quart_app.add_background_task(fleet_ctrl.start_auto_discover_anki_cars)

    vehicles = environment_mng.get_vehicle_list()
    behaviour_ctrl = BehaviourController(vehicles)
    cybersecurity_mng = CyberSecurityManager(behaviour_ctrl)

    driver_ui = DriverUI(behaviour_ctrl=behaviour_ctrl, environment_mng=environment_mng, sio=socket)
    driver_ui_blueprint = driver_ui.get_blueprint()
    staff_ui = StaffUI(cybersecurity_mng=cybersecurity_mng, sio=socket, environment_mng=environment_mng,
                       password=admin_password)
    staff_ui_blueprint = staff_ui.get_blueprint()

    if environment_mng.get_track() is not None:
        car_map = CarMap(environment_manager=environment_mng, sio=socket)
        car_map_blueprint = car_map.get_blueprint()
        quart_app.register_blueprint(car_map_blueprint, url_prefix='/car_map')

    quart_app.register_blueprint(driver_ui_blueprint, url_prefix='/driver')
    quart_app.register_blueprint(staff_ui_blueprint, url_prefix='/staff')

    return quart_app, socket


if __name__ == '__main__':
    # TODO: work with hashed password, passwords should not be stored in clear text
    admin_pwd = os.environ.get('ADMIN_PASSWORD')
    if admin_pwd is None:
        print("WARNING!!! No admin password supplied via Environment variable. Using '0000' as default password. "
              "Please change the password!")
        admin_pwd = '0000'

    app, sio = create_app(admin_pwd)
    app_asgi = ASGIApp(socketio_server=sio, other_asgi_app=app)

    config = Config()
    config.bind = ["0.0.0.0:5000"]
    asyncio.run(serve(app_asgi, config))
