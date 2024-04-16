from time import sleep
from VehicleManagement.FleetController import FleetController
from VehicleManagement.VehicleController import VehicleController


def test_connect_to_anki_car():
    mut = VehicleController()
    is_connected = bool
    fleet_ctrl = FleetController()

    found_vehicles = fleet_ctrl.scan_for_anki_cars()

    is_connected = mut.connect_to_anki_cars(found_vehicles[0])
    mut.set_callbacks(location_callback_dummy,
                      location_callback_dummy,
                      location_callback_dummy,
                      location_callback_dummy)

    mut.change_speed(found_vehicles[0], 60)
    sleep(2)
    mut.__del__()

    assert is_connected == True


def location_callback_dummy(value_tuple):
    print(f"{value_tuple}")


def test_change_speed():
    mut = VehicleController()
    fleet_ctrl = FleetController()
    found_vehicles = fleet_ctrl.scan_for_anki_cars()

    for vehicle_address in found_vehicles:
        mut.connect_to_anki_cars(vehicle_address)

    mut.change_speed(found_vehicles[0], 60)
    mut.change_speed(found_vehicles[1], 40)
    sleep(2)
    mut.change_lane(found_vehicles[0], -1, 60)
    mut.change_lane(found_vehicles[1], 1, 40)
    sleep(2)
    mut._update_road_offset_for(found_vehicles[0])
    mut._update_road_offset_for(found_vehicles[1])

    sleep(4)
    mut.change_speed(found_vehicles[0], 0)
    mut.change_speed(found_vehicles[1], 0)

    del mut


def test_change_lane_from_left_to_right():
    mut = VehicleController()
    found_vehicles = mut.scan_for_anki_cars()

    for vehicle_address in found_vehicles:
        mut.connect_to_anki_cars(vehicle_address)

    mut.change_speed(found_vehicles[0], 60)
    sleep(2)

    mut.change_lane(found_vehicles[0], -1, 60)
    sleep(2)
    mut.change_lane(found_vehicles[0], 1, 60)
    sleep(2)
    mut.change_lane(found_vehicles[0], 2, 60)
    sleep(2)
    mut.change_lane(found_vehicles[0], -1, 60)
    sleep(2)
    mut.change_lane(found_vehicles[0], 1, 60)
    sleep(2)
    mut.change_lane(found_vehicles[0], 2, 60)
    sleep(3)

    mut.change_speed(found_vehicles[0], 0)

    del mut
