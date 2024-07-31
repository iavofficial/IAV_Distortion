from unittest import TestCase
from time import sleep

from bleak import BleakClient
from VehicleManagement.AnkiController import AnkiController
from VehicleManagement.FleetController import FleetController


class AnkiControllerIntegrationTest(TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        fleet_ctrl = FleetController()
        cls.ankiCarMacs = fleet_ctrl.scan_for_anki_cars()

    def setUp(self) -> None:
        self.mut: AnkiController = AnkiController()

    def tearDown(self) -> None:
        del self.mut

    def dummy_callback(self):
        return

    def test_vehicle_disconnect_event(self):
        # Arrange
        self.mut.set_callbacks(None, None, None, None, None, self.dummy_callback)
        # Act
        if not self.mut.connect_to_vehicle(BleakClient(self.ankiCarMacs[0])):
            assert False

        self.mut.request_version()

        # Assert
        assert True

    def test_connect_to_vehicle(self):
        # Arrange

        # Act
        if not self.mut.connect_to_vehicle(BleakClient(self.ankiCarMacs[0])):
            assert False

        self. mut.change_speed_to(100)
        sleep(2)
        self.mut.change_speed_to(90)
        sleep(2)
        self.mut.change_speed_to(110)
        sleep(2)
        self.mut.change_speed_to(0)

        # Assert