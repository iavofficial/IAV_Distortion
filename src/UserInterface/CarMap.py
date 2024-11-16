from quart import Blueprint, render_template
from typing import Any, Coroutine, List, Dict

import asyncio

from socketio import AsyncServer

from EnvironmentManagement.EnvironmentManager import EnvironmentManager
from EnvironmentManagement.ConfigurationHandler import ConfigurationHandler

from DataModel.Vehicle import Vehicle
from Items.Item import Item

from LocationService.Trigo import  Position


class CarMap:
    """
        Provides the visualization of the virtual race track.

        Parameters
        ----------
        environment_manager: EnvironmentManager
            Access to the EnvironmentManager to exchange information about queues and add or remove players and
            vehicles.
        """
    def __init__(self, environment_manager: EnvironmentManager, sio: AsyncServer):
        self.carMap_blueprint: Blueprint = Blueprint(name='carMap_bp', import_name='carMap_bp')
        self._environment_manager = environment_manager
        self._vehicles: list[Vehicle] | None = self._environment_manager.get_vehicle_list()
        self.config_handler: ConfigurationHandler = ConfigurationHandler()
        environment_manager.get_item_collision_detector().set_on_item_change_callback(self.update_item_positions)

        self._sio: AsyncServer = sio

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
            track = environment_manager.get_track()
            disp_settings = self.config_handler.get_configuration()["display_settings"]

            if track is None:
                return await render_template('car_map.html', track=None, disp_settings=disp_settings)
            serialized_track = track.get_as_list()
            if self._vehicles is not None:
                for vehicle in self._vehicles:
                    vehicle.set_virtual_location_update_callback(self.update_virtual_location)

            car_pictures = self.config_handler.get_configuration()["virtual_cars_pics"]
            items_as_dict = []
            for item in environment_manager.get_item_collision_detector().get_current_items():
                items_as_dict.append(item.to_html_dict())
            return await render_template(template_name_or_list="car_map.html",
                                         track=serialized_track,
                                         car_pictures=car_pictures,
                                         color_map=environment_manager.get_car_color_map(),
                                         used_space=environment_manager.get_track().get_used_space_as_dict(),
                                         items=items_as_dict,
                                         disp_settings=disp_settings)

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
        """
        Gathers the vehicle data and initiates sending it asynchronously.

        Parameters
        ----------
        vehicle_id: str
            ID of the vehicle belonging to the data.
        position: dict
            x and y coordinates, defining the vehicles position in the simulation.
        angle: float
            Angle of the vehicle, defining the direction the vehicle is facing in the simulation.
        """
        data = {'car': vehicle_id, 'position': position, 'angle': angle}
        self.__run_async_task(self.__emit_car_position(data))
        
        if self._vehicles is not None:
            self.check_vehicle_proximity(vehicle_id,position)             
        return

    def check_vehicle_proximity(self,vehicle_id: str, position: dict,) -> None:
        """
        Checks if the given vehicle (vehicle_id) is a virtual vehicle and, if so, performs a proximity check.

        Parameters
        ----------
        vehicle_id : str
            ID of the vehicle for which proximity is being checked.
        position : dict
            Dictionary containing the 'x' and 'y' coordinates of the vehicle's position in the simulation.
        """
        for v in self._environment_manager._active_virtual_cars:
            if v == vehicle_id:
                self.check_virtual_vehicle_proximity(vehicle_id, position)
        return

    def check_virtual_vehicle_proximity(self,vehicle_id: str, position: dict,) -> None:
        """
        Checks the proximity of a given vehicle to every other vehicle and updates
        its `vehicle_in_proximity` attribute if any vehicle is within a specified distance.

        Parameters
        ----------
        vehicle_id : str
            ID of the vehicle for which proximity is being checked.
        position : dict
            Dictionary containing the 'x' and 'y' coordinates of the vehicle's position in the simulation.
        """
        pos_self = Position(position['x'],position['y'])
        proximity_vehicle_id: str = self._environment_manager.get_vehicle_by_vehicle_id(vehicle_id).vehicle_in_proximity
        if proximity_vehicle_id != None:
            pos_proximity_vehicle = self._environment_manager.get_vehicle_by_vehicle_id(proximity_vehicle_id)._location_service._current_position
            if pos_proximity_vehicle.distance_to(pos_self) > 200:
                self._environment_manager.get_vehicle_by_vehicle_id(vehicle_id).vehicle_in_proximity = None
        else:
            for target_v_id in self._environment_manager._active_physical_cars:
                vehicle = self._environment_manager.get_vehicle_by_vehicle_id(target_v_id)
                pos_other = vehicle._location_service._current_position
                if pos_other.distance_to(pos_self) < 200:
                        self._environment_manager.get_vehicle_by_vehicle_id(vehicle_id).vehicle_in_proximity = target_v_id
                        return
        return

    async def __emit_car_position(self, data: dict) -> None:
        """
        Sends the 'car_positions' websocket event.

        Parameters
        ----------
        data: dict
            Vehicle data including the vehicle id, position and direction.
        """
        await self._sio.emit('car_positions', data)
        return

    def update_item_positions(self, items: List[Item]) -> None:
        dict_list: List[Dict[str, float | int]] = []
        for item in items:
            dict_list.append(item.to_html_dict())
        self.__run_async_task(self.__emit_item_position(dict_list))
        return

    async def __emit_item_position(self, data: List[Dict[str, float | int]]) -> None:

        await self._sio.emit('item_positions', data)
        return

    def __run_async_task(self, task: Coroutine[Any, Any, None]) -> None:
        """
        Runs an asyncio awaitable task.

        Parameters
        ----------
        task: Task
            Coroutine to be scheduled as an asynchronous task.
        """
        asyncio.create_task(task)
        # TODO: Log error, if the coroutine doesn't end successfully
        return
