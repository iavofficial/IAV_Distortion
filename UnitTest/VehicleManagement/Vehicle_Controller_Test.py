from time import sleep
from VehicleManagement.FleetController import FleetController
from VehicleManagement.VehicleController import VehicleController
from bleak import BleakClient


def test_connect_to_anki_car():
    mut = VehicleController()

    fleet_ctrl = FleetController()
    found_vehicles = fleet_ctrl.scan_for_anki_cars()
    is_connected = mut.connect_to_vehicle(BleakClient(found_vehicles[0]))
    mut.set_callbacks(location_callback_dummy,
                      location_callback_dummy,
                      location_callback_dummy,
                      location_callback_dummy,
                      location_callback_dummy)

    mut.change_speed_to(60)
    sleep(2)
    mut.__del__()

    assert is_connected == True


def location_callback_dummy(value_tuple):
    print(f"{value_tuple}")


def test_change_speed():
    mut = VehicleController()

    fleet_ctrl = FleetController()
    found_vehicles = fleet_ctrl.scan_for_anki_cars()
    is_connected = mut.connect_to_vehicle(BleakClient(found_vehicles[0]))
    mut.set_callbacks(location_callback_dummy,
                      location_callback_dummy,
                      location_callback_dummy,
                      location_callback_dummy,
                      location_callback_dummy)

    mut.change_speed_to(60)
    sleep(2)
    mut.change_lane_to(-1, 60)
    mut.change_lane_to(1, 40)
    sleep(2)
    mut._update_road_offset()
    mut._update_road_offset()

    sleep(4)
    mut.change_speed_to(0)
    mut.change_speed_to(0)

    del mut


def test_change_lane_from_left_to_right():
    mut = VehicleController()

    fleet_ctrl = FleetController()
    found_vehicles = fleet_ctrl.scan_for_anki_cars()
    is_connected = mut.connect_to_vehicle(BleakClient(found_vehicles[0]))
    mut.set_callbacks(location_callback_dummy,
                      location_callback_dummy,
                      location_callback_dummy,
                      location_callback_dummy,
                      location_callback_dummy)

    mut.change_speed_to(60)
    sleep(2)

    mut.change_lane_to(-1, 60)
    sleep(2)
    mut.change_lane_to(1, 60)
    sleep(2)
    mut.change_lane_to(2, 60)
    sleep(2)
    mut.change_lane_to(-1, 60)
    sleep(2)
    mut.change_lane_to(1, 60)
    sleep(2)
    mut.change_lane_to(2, 60)
    sleep(3)

    mut.change_speed_to(0)

    del mut
