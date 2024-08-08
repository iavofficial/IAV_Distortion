from unittest.mock import Mock

import pytest

from VehicleManagement.LocationServiceController import LocationServiceController
from LocationService.LocationService import LocationService


@pytest.fixture()
def get_valid_mut():
    return LocationServiceController()


@pytest.fixture()
def get_valid_location_service_mock():
    return Mock(spec=LocationService)

class TestConnectTo:
    def test_get_valid_location_service(self, get_valid_mut, get_valid_location_service_mock):
        # Arrange
        mut = get_valid_mut
        location_service_mock = get_valid_location_service_mock

        # Act
        result = mut.connect_to(location_service_mock)

        # Assert
        assert result is True

    def test_get_none_as_location_service(self, get_valid_mut):
        # Arrange
        mut = get_valid_mut

        # Act
        result = mut.connect_to(None)

        # Assert
        assert result is False