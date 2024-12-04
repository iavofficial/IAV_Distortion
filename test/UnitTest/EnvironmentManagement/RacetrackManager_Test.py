import pytest
from unittest.mock import Mock

from EnvironmentManagement.RacetrackManager import RacetrackManager
from EnvironmentManagement.ConfigurationHandler import ConfigurationHandler


@pytest.fixture(scope="module")
def initialise_dependencies():
    configuration_handler_mock = Mock(spec=ConfigurationHandler)

    return configuration_handler_mock


@pytest.fixture(scope="module")
def get_mut_with_empty_or_invalid_config(initialise_dependencies):
    configuration_handler_mock = initialise_dependencies
    configuration_handler_mock.get_configuration.side_effect = [
        {},
        {'track': [{
                    "type": "Nonexistent",
                    "rotation": 90,
                    "physical_id": 33,
                    "length": 210,
                    "diameter": 184,
                    "start_line_width": 21}]},
        {'track': [{
                    "type": "LocationService.TrackPieces.StartPieceAfterLine",
                    "rotation": 90,
                    "physical_id": 33,
                    "length": 210,
                    "diameter": 184,
                    "start_line_width": 21}]}]
    mut: RacetrackManager = RacetrackManager(configuration_handler_mock)

    return mut


@pytest.fixture(scope="module")
def get_mut_with_valid_config(initialise_dependencies):
    configuration_handler_mock = initialise_dependencies
    configuration_handler_mock.get_configuration.return_value = {
        'track': [{
                    "type": "LocationService.TrackPieces.StartPieceAfterLine",
                    "rotation": 90,
                    "physical_id": 33,
                    "length": 210,
                    "diameter": 184,
                    "start_line_width": 21}]}
    mut: RacetrackManager = RacetrackManager(configuration_handler_mock)

    return mut


class TestGetFulltrack:
    def test_with_empty_or_invalid_config(self, get_mut_with_empty_or_invalid_config):
        """
        This tests that the EnvironmentManager returns the track it gets from the config or None, if it's not parsable
        """
        mut: RacetrackManager = get_mut_with_empty_or_invalid_config
        assert mut.get_fulltrack() is None
        assert mut.get_fulltrack() is None

    def test_with_valid_config(self, get_mut_with_valid_config):
        """
        This tests that the EnvironmentManager returns the track it gets from the config or None, if it's not parsable
        """
        mut: RacetrackManager = get_mut_with_valid_config
        assert mut.get_fulltrack() is not None


class TestScanTrack:
    @pytest.mark.skip_ci
    @pytest.mark.one_anki_car_needed
    @pytest.mark.slow
    @pytest.mark.manual
    def test_succsesful_Scan(self, get_mut_with_valid_config):
        pass
