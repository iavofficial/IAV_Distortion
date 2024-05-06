import unittest
from typing import List
from unittest.mock import Mock
import random

from DataModel.Vehicle import Vehicle
from CyberSecurityManager.CyberSecurityManager import BehaviourController


def generate_mac_address() -> str:

    # Generiere sechs zufällige Hexadezimalzahlen im Bereich von 0x00 bis 0xFF
    random_bytes = [random.randint(0x00, 0xFF) for _ in range(6)]

    # Konvertiere die Zahlen in Hexadezimalstrings und füge sie mit ':' zusammen
    mac_address = ":".join("{:02X}".format(byte) for byte in random_bytes)
    return mac_address

class BehaviourControllerTest(unittest.TestCase):
    number_of_vehicles = 3

    def setUp(self) -> None:
        self.dummy_vehicles = []


    def tearDown(self) -> None:
        del self.dummy_vehicles

    def test_get_vehicle_by_uuid(self):
        # Arrange
        uuid_ntk: str

        for _ in range(self.number_of_vehicles):
            vehicle_mock = Mock(spec=Vehicle)
            uuid_ntk = generate_mac_address()
            mock_id = id(vehicle_mock)

            vehicle_mock.vehicle_id = uuid_ntk
            self.dummy_vehicles.append(vehicle_mock)

        mut = BehaviourController(self.dummy_vehicles)

        # Act
        returned_vehicle = mut.get_vehicle_by_uuid(uuid_ntk)

        # Assert
        assert id(returned_vehicle) == mock_id
