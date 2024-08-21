from unittest import TestCase

import pytest

from EnvironmentManagement.EnvironmentManager import EnvironmentManager
from VehicleManagement.FleetController import FleetController


@pytest.mark.skip_ci
class EnvironmentManagerIntergrationTest(TestCase):

    def test_remove_vehicle(self):
        # Arrange
        mut = EnvironmentManager(FleetController())
        connected_cars = mut.connect_all_anki_cars()
        print(connected_cars)
        # Act
        mut.remove_vehicle_by_id(connected_cars[0].vehicle_id)
        print(connected_cars)

        # Assert
        assert True
