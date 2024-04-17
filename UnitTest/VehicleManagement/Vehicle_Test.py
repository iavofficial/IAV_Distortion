from time import sleep
from DataModel.Vehicle import Vehicle
from VehicleManagement.VehicleController import VehicleController
from VehicleManagement.FleetController import FleetController


def test_get_location():
    vctrl = VehicleController()
    fleet_ctrl = FleetController()

    found_vehicles = fleet_ctrl.scan_for_anki_cars()
    mut = Vehicle(found_vehicles[0], vctrl)

    mut.speed_request = 80.0

    sleep(5)

    mut.speed_request = 0.0

    assert mut
