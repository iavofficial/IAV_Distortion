import logging
from DataModel.Vehicle import Vehicle
from EnvironmentManagement.EnvironmentManager import EnvironmentManager


class SwitchCars:
    def switch(environmentManager: EnvironmentManager, vehicle: Vehicle):
        driver = vehicle.get_player_id()
        car = vehicle.get_vehicle_id()
        vehicle.remove_player()
        vehicles = environmentManager.get_vehicle_list()
        if len(vehicles) > 1:
            for v in vehicles:
                logging.info(v.get_vehicle_id())
                if v.get_vehicle_id() != car:
                    new_driver = v.get_player_id
                    v.remove_player
                    vehicle.set_player(new_driver)
                    v.set_player(driver)
                    break