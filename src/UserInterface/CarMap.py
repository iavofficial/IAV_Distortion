from flask import Blueprint, render_template
from EnvironmentManagement.EnvironmentManager import EnvironmentManager
from EnvironmentManagement.ConfigurationHandler import ConfigurationHandler


class CarMap:
    """
    Provides the visualization of the virtual race track.

    Parameters
    ----------
    environment_manager: EnvironmentManager
        Access to the EnvironmentManager to exchange information about queues and add or remove players and vehicles.
    """
    def __init__(self, environment_manager: EnvironmentManager):
        self.carMap_blueprint: Blueprint = Blueprint(name='carMap_bp', import_name='carMap_bp')
        self._environment_manager: EnvironmentManager = environment_manager
        self.config_handler = ConfigurationHandler()

        def home_car_map():
            """
            Load car map page.

            Gets the track from the EnvironmentManager, loads configured vehicle pictures from config file and gets the
            color map from the EnvironmentManager used to visualize virtual cars exceeding the amount of car pictures.

            Returns
            -------
            Response
                Returns a Response object representing the car map page.
            """
            track = environment_manager.get_track().get_as_list()
            car_pictures = self.config_handler.get_configuration()["virtual_cars_pics"]
            return render_template("car_map.html", track=track, car_pictures=car_pictures,
                                   color_map=environment_manager.get_car_color_map())

        self.carMap_blueprint.add_url_rule("", "home_car_map", view_func=home_car_map)

    def get_blueprint(self) -> Blueprint:
        """
        Get the Blueprint object associated with the instance.

        Returns
        -------
        Blueprint
            The Blueprint object associated with the instance.
        """
        return self.carMap_blueprint
