from unittest import TestCase
from unittest.mock import Mock

from VehicleManagement.AnkiController import AnkiController


class AnkiControllerTest(TestCase):

    def setUp(self) -> None:
        self.mut: AnkiController = AnkiController()
