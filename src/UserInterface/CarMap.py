from quart import Blueprint, render_template
import socketio
import asyncio

from EnvironmentManagement.EnvironmentManager import EnvironmentManager
from EnvironmentManagement.ConfigurationHandler import ConfigurationHandler

from DataModel.Vehicle import Vehicle
from DataModel.ModelCar import ModelCar

class CarMap:
    """
        Provides the visualization of the virtual race track.

        Parameters
        ----------
        environment_manager: EnvironmentManager
            Access to the EnvironmentManager to exchange information about queues and add or remove players and vehicles.
        """
    def __init__(self, environment_manager: EnvironmentManager, sio: socketio):
        self.carMap_blueprint: Blueprint = Blueprint(name='carMap_bp', import_name='carMap_bp')
        self._environment_manager = environment_manager
        self._vehicles: list[Vehicle] | None = self._environment_manager.get_vehicle_list()
        self.config_handler: ConfigurationHandler = ConfigurationHandler()

        self._sio: socketio = sio


        async def home_car_map():
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
            if self._vehicles is not None:
                for vehicle in self._vehicles:
                    vehicle.set_virtual_location_update_callback(self.update_virtual_location)

            car_pictures = self.config_handler.get_configuration()["virtual_cars_pics"]
            return await render_template("car_map.html", track=track, car_pictures=car_pictures,
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

    def update_virtual_location(self, vehicle_id: str, position: dict, angle: float) -> None:
        data = {'car': vehicle_id, 'position': position, 'angle': angle}
        self.__run_async_task(self.send_car_position(data))
        return

    async def send_car_position(self, data):
        await self._sio.emit('car_positions', data)
        return

    def __run_async_task(self, task):
        """
        Run a asyncio awaitable task
        task: awaitable task
        """
        asyncio.create_task(task)
        # TODO: Log error, if the coroutine doesn't end successfully