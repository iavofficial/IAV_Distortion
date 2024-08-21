from unittest import TestCase

from time import sleep

import pytest

from VehicleManagement.FleetController import FleetController
from VehicleManagement.VehicleController import VehicleController
from bleak import BleakClient


@pytest.mark.skip_ci
class VehicleControllerIntegrationTest(TestCase):
    def test_connect_to_anki_car(self):
        mut = VehicleController()

        fleet_ctrl = FleetController()
        found_vehicles = fleet_ctrl.scan_for_anki_cars()
        is_connected = mut.connect_to_vehicle(BleakClient(found_vehicles[0]))
        mut.set_callbacks(self.location_callback_dummy,
                          self.location_callback_dummy,
                          self.location_callback_dummy,
                          self.location_callback_dummy,
                          self.location_callback_dummy)

        mut.change_speed_to(60)
        sleep(2)
        mut.__del__()

        assert is_connected

    def location_callback_dummy(self, value_tuple):
        print(f"{value_tuple}")

    def test_change_speed(self):
        mut = VehicleController()

        fleet_ctrl = FleetController()
        found_vehicles = fleet_ctrl.scan_for_anki_cars()
        mut.connect_to_vehicle(BleakClient(found_vehicles[0]))
        mut.set_callbacks(self.location_callback_dummy,
                          self.location_callback_dummy,
                          self.location_callback_dummy,
                          self.location_callback_dummy,
                          self.location_callback_dummy)

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

    def test_change_lane_from_left_to_right(self):
        mut = VehicleController()

        fleet_ctrl = FleetController()
        found_vehicles = fleet_ctrl.scan_for_anki_cars()
        mut.connect_to_vehicle(BleakClient(found_vehicles[0]))
        mut.set_callbacks(self.location_callback_dummy,
                          self.location_callback_dummy,
                          self.location_callback_dummy,
                          self.location_callback_dummy,
                          self.location_callback_dummy)

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
