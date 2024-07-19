from unittest import TestCase
from unittest.mock import Mock

from EnvironmentManagement.EnvironmentManager import EnvironmentManager
from VehicleManagement.FleetController import FleetController
from DataModel.Vehicle import Vehicle


class EnvironmentManagerTest(TestCase):
    def setUp(self):
        self.fleet_ctrl_Mock: FleetController = Mock(spec=FleetController)
        self.vehicle1: Vehicle = Vehicle("123")
        self.vehicle2: Vehicle = Vehicle("456")

    def tearDown(self):
        pass

    def test_assign_players_to_vehicles_no_playing_time_check(self):
        # Arrange
        mut: EnvironmentManager = EnvironmentManager(self.fleet_ctrl_Mock)
        mut._add_to_active_vehicle_list(self.vehicle1)
        mut._add_to_active_vehicle_list(self.vehicle2)

        # Act
        mut.add_player("1")
