from unittest import TestCase

from bleak import BleakClient

from VehicleManagement.AnkiController import AnkiController


class AnkiControllerIntegrationTest(TestCase):

    def setUp(self) -> None:
        self.mut: AnkiController = AnkiController()

    def tearDown(self) -> None:
        del self.mut

    def test_vehicle_disconnect_event(self):
        # Arrange
        self.mut.set_callbacks(None, None, None, None, None, self.dummy_callback)
        # Act
        if not self.mut.connect_to_vehicle(BleakClient("E8:7E:9F:34:CF:46")):
            assert False

        self.mut.request_version()

        # Assert
        assert True


    def dummy_callback(self):
        return
