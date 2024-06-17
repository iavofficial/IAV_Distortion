from flask import Blueprint, render_template
from flask_socketio import SocketIO

from EnvironmentManagement.EnvironmentManager import EnvironmentManager
from DataModel.Vehicle import Vehicle
from DataModel.ModelCar import ModelCar

class CarMap:
    def __init__(self, environment_manager: EnvironmentManager, socketio: SocketIO):
        self.carMap_blueprint: Blueprint = Blueprint(name='carMap_bp', import_name='carMap_bp')
        self._environment_manager = environment_manager
        self._vehicles: list[Vehicle] | None = self._environment_manager.get_vehicle_list()

        self._socketio: SocketIO = socketio

        def home_car_map():
            track = environment_manager.get_track().get_as_list()
            if self._vehicles is not None:
                for vehicle in self._vehicles:
                    vehicle.set_virtual_location_update_callback(self.update_virtual_location)

            return render_template("car_map.html", track=track, color_map=environment_manager.get_car_color_map())
        self.carMap_blueprint.add_url_rule("", "home_car_map", view_func=home_car_map)

    def get_blueprint(self) -> Blueprint:
        return self.carMap_blueprint

    def update_virtual_location(self, vehicle_id: str, position: dict, angle: float) -> None:
        data = {'car': vehicle_id, 'position': position, 'angle': angle}
        self._socketio.emit("car_positions", data)
        return
