from unittest import TestCase
from unittest.mock import Mock

from bleak import BleakClient

from VehicleManagement.AnkiController import AnkiController


class AnkiControllerTest(TestCase):

    def setUp(self) -> None:
        self.mut: AnkiController = AnkiController()

    def tearDown(self) -> None:
        del self.mut
    def test_vehicle_disconnect_event(self):
        # Arrange
        ble_client_mock = Mock(spec=BleakClient)
        self.mut.set_callbacks(None, None, None, None, None, self.test_callback)
        # Act
        if not self.mut.connect_to_vehicle(BleakClient("E8:7E:9F:34:CF:46")):
            assert False

        self.mut.request_version()

        # Assert
        assert True


    def test_callback(self):
        return
