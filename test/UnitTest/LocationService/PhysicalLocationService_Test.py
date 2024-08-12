import math

import pytest

from LocationService.PhysicalLocationService import PhysicalLocationService
from LocationService.Track import FullTrack, TrackPieceType
from LocationService.TrackPieces import TrackBuilder

STRAIGHT_PIECE_LENGTH_MIDDLE = TrackBuilder().STRAIGHT_PIECE_LENGTH
CURVE_LENGTH_MIDDLE = (TrackBuilder().CURVE_PIECE_SIZE / 2) * math.pi / 2


@pytest.fixture
def get_physical_location_service() -> PhysicalLocationService:
    track: FullTrack = TrackBuilder() \
        .append(TrackPieceType.STRAIGHT_WE, 40) \
        .append(TrackPieceType.CURVE_WS, 18) \
        .append(TrackPieceType.CURVE_NW, 23) \
        .append(TrackPieceType.STRAIGHT_EW, 39) \
        .append(TrackPieceType.CURVE_EN, 17) \
        .append(TrackPieceType.CURVE_SE, 20) \
        .build()

    service: PhysicalLocationService = PhysicalLocationService(track, simulation_ticks_per_second=1)
    return service


def test_length_calculation_same_piece(get_physical_location_service):
    """
    This test tests whether the distance calculation on the same piece is correct for both driving directions
    """
    service = get_physical_location_service
    service._progress_on_current_piece = 30
    # if this fails we changed the track piece which we shouldn't since we only travel 10mm/s
    assert service._current_piece_index == 0

    real_start_distance = service._progress_on_current_piece

    same_piece_distance = service._calculate_distance_on_same_piece(real_start_distance + 10)
    assert pytest.approx(10) == same_piece_distance

    same_piece_distance = service._calculate_distance_on_same_piece(real_start_distance - 10)
    assert pytest.approx(-10) == same_piece_distance

    # change direction manually
    service._direction_mult *= -1

    # The results should be the other way around here
    same_piece_distance = service._calculate_distance_on_same_piece(real_start_distance + 10)
    assert pytest.approx(-10) == same_piece_distance

    same_piece_distance = service._calculate_distance_on_same_piece(real_start_distance - 10)
    assert pytest.approx(10) == same_piece_distance


def test_forward_backward_calculation(get_physical_location_service):
    """
    This tests whether both the forward and backward calculations are correct for both driving directions
    """
    service = get_physical_location_service
    service._progress_on_current_piece = 400

    other_index = 2
    other_progress = 350

    real_forward_distance = STRAIGHT_PIECE_LENGTH_MIDDLE - 400 + CURVE_LENGTH_MIDDLE + 350
    real_backward_distance = CURVE_LENGTH_MIDDLE - 350 + STRAIGHT_PIECE_LENGTH_MIDDLE + 2 * CURVE_LENGTH_MIDDLE + 400
    real_backward_distance *= -1

    assert pytest.approx(real_forward_distance) == service._calculate_distance_to_position_forward(other_index,
                                                                                                   other_progress)

    assert pytest.approx(real_backward_distance) == service._calculate_distance_to_position_backward(other_index,
                                                                                                     other_progress)

    # change direction manually
    service._direction_mult *= -1

    # since the driving direction changed these 2 should have swapped results since the direction changed
    # and their sign should be the opposite
    assert pytest.approx(real_backward_distance * -1) == service._calculate_distance_to_position_forward(other_index,
                                                                                                         other_progress)

    assert pytest.approx(real_forward_distance * -1) == service._calculate_distance_to_position_backward(other_index,
                                                                                                         other_progress)


def test_calculation_brings_right_tesult(get_physical_location_service):
    """
    This tests whether the general `_calculate_distance_to_position` function returns the results from the correct
    specific function
    """
    service = get_physical_location_service
    service._progress_on_current_piece = 20

    same_piece_result = service._calculate_distance_on_same_piece(30)
    automatically_chosen = service._calculate_distance_to_position(service._current_piece_index, 30)
    assert pytest.approx(same_piece_result) == automatically_chosen

    forward_results = service._calculate_distance_to_position_forward(1, 300)
    automatically_chosen = service._calculate_distance_to_position(1, 300)
    assert pytest.approx(forward_results) == automatically_chosen

    backward_result = service._calculate_distance_to_position_backward(5, 300)
    automatically_chosen = service._calculate_distance_to_position(5, 300)
    assert pytest.approx(backward_result) == automatically_chosen

    service._direction_mult *= -1

    same_piece_result = service._calculate_distance_on_same_piece(30)
    automatically_chosen = service._calculate_distance_to_position(service._current_piece_index, 30)
    assert pytest.approx(same_piece_result) == automatically_chosen

    forward_results = service._calculate_distance_to_position_forward(5, 300)
    automatically_chosen = service._calculate_distance_to_position(5, 300)
    assert pytest.approx(forward_results) == automatically_chosen

    backward_result = service._calculate_distance_to_position_backward(1, 300)
    automatically_chosen = service._calculate_distance_to_position(1, 300)
    assert pytest.approx(backward_result) == automatically_chosen
