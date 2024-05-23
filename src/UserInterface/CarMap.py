from flask import Blueprint, render_template
from EnvironmentManagement.EnvironmentManager import EnvironmentManager

class CarMap:
    def __init__(self, environment_manager: EnvironmentManager):
        self.carMap_blueprint: Blueprint = Blueprint(name='carMap_bp', import_name='carMap_bp')
        self._environment_manager = environment_manager

        def home_car_map():
            # TODO: Add track into template and render it
            return render_template("car_map.html")
        self.carMap_blueprint.add_url_rule("", "home_car_map", view_func=home_car_map)

    def get_blueprint(self) -> Blueprint:
        return self.carMap_blueprint
