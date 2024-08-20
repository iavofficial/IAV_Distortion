import pytest

from LocationService.Trigo import Position

def test_direction_between_pieces():
    """
    Test the calculation of angles between 2 points
    """
    center = Position(0, 0)
    north = Position(0, -1)
    south = Position(0, 1)
    west = Position(-1, 0)
    east = Position(1, 0)
    assert pytest.approx(center.calculate_angle_to(north).get_deg()) == 0
    assert pytest.approx(center.calculate_angle_to(south).get_deg()) == 180
    assert pytest.approx(center.calculate_angle_to(west).get_deg()) == 270
    assert pytest.approx(center.calculate_angle_to(east).get_deg()) == 90
    assert pytest.approx(west.calculate_angle_to(east).get_deg()) == 90
    assert pytest.approx(north.calculate_angle_to(south).get_deg()) == 180
    assert pytest.approx(east.calculate_angle_to(west).get_deg()) == 270
    assert pytest.approx(south.calculate_angle_to(north).get_deg()) == 0
