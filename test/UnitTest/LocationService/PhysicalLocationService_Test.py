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


@pytest.fixture
def get_physical_location_service_duplicate_ids() -> PhysicalLocationService:
    track: FullTrack = TrackBuilder() \
        .append(TrackPieceType.STRAIGHT_WE, 40) \
        .append(TrackPieceType.CURVE_WS, 18) \
        .append(TrackPieceType.CURVE_NW, 18) \
        .append(TrackPieceType.STRAIGHT_EW, 40) \
        .append(TrackPieceType.CURVE_EN, 18) \
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


def test_unknown_piece_results_in_early_return(get_physical_location_service):
    """
    Test that the _physical_piece variable isn't overwritten when wrong data is sent by the car
    """
    service = get_physical_location_service
    service.notify_location_event(99, 10, 20, 99)
    assert service._physical_piece is None


@pytest.mark.asyncio
async def test_adjust_speed_override_for_special_cases(get_physical_location_service):
    """
    Test that the overwritten method only manipulates the speed when there is no special case
    """
    service = get_physical_location_service
    await service.set_speed_percent(50, 1200)
    service._speed_correcture = 400

    # here the correcture should be applied
    old_speed = service._actual_speed
    service._adjust_speed_to(30)
    assert pytest.approx(old_speed + 30 + 400) == service._actual_speed

    # it shouldn't be applied here since the request is too low
    service._actual_speed = 0
    service._adjust_speed_to(5)
    assert pytest.approx(5) == service._actual_speed
    service._adjust_speed_to(0)
    assert pytest.approx(0) == service._actual_speed

    # it shouldn't be applied here since the car is doing a U-Turn
    await service.do_uturn()
    assert service._uturn_override is not None
    service._adjust_speed_to(20)
    assert pytest.approx(20) == service._actual_speed
    service._uturn_override = None

    # here the result would be negative so it should be reduced to 0
    service._speed_correcture = -2000
    service._adjust_speed_to(20)
    assert service._actual_speed == 0


def test_piece_history_collection(get_physical_location_service_duplicate_ids):
    """
    Test that the piece IDs are collected in the default case
    """
    service = get_physical_location_service_duplicate_ids
    service.notify_location_event(40, 0, 0, 0)
    service.notify_transition_event(0)
    service.notify_location_event(18, 0, 0, 0)
    service.notify_transition_event(0)
    service.notify_transition_event(0)
    service.notify_transition_event(0)
    service.notify_location_event(18, 0, 0, 0)
    history = service._piece_history
    assert history[0] == 40
    assert history[1] == 18
    assert history[4] == 18


def test_piece_history_resetting_when_not_matching(get_physical_location_service_duplicate_ids):
    """
    Test that the piece history is reset when a wrong datapoint is encountered
    """
    service = get_physical_location_service_duplicate_ids
    service.notify_location_event(40, 0, 0, 0)
    service.notify_transition_event(0)
    service.notify_location_event(18, 0, 0, 0)
    service.notify_transition_event(0)
    service.notify_transition_event(0)
    # This needs to be 40
    service.notify_location_event(18, 0, 0, 0)
    history = service._piece_history
    assert history.count(None) == 6


def test_piece_history_resetting_when_history_has_other_data(get_physical_location_service_duplicate_ids):
    """
    Test that the piece history is reset when trying to write a number into a position that already has another number
    """
    service = get_physical_location_service_duplicate_ids
    service.notify_location_event(40, 0, 0, 0)
    service.notify_transition_event(0)
    service.notify_location_event(18, 0, 0, 0)
    # loop one time around the track
    for _ in range(0, service._track.get_len() - 1):
        service.notify_transition_event(0)
    service.notify_location_event(18, 0, 0, 0)

    history = service._piece_history
    assert history.count(None) == 5


def test_piece_history_length_is_always_right(get_physical_location_service_duplicate_ids):
    """
    Test that the history always has enough None|int data to avoid out of bounds accesses
    """
    service = get_physical_location_service_duplicate_ids
    assert service._piece_history.count(None) == 6
    assert len(service._piece_history) == 6

    service.notify_location_event(40, 0, 0, 0)
    service.notify_transition_event(0)
    service.notify_location_event(18, 0, 0, 0)
    service.notify_transition_event(0)
    service.notify_transition_event(0)
    service.notify_transition_event(0)
    service.notify_location_event(18, 0, 0, 0)
    assert len(service._piece_history) == 6

    service._reset_piece_history()
    assert service._piece_history.count(None) == 6
    assert len(service._piece_history) == 6


def test_find_physical_location(get_physical_location_service_duplicate_ids):
    """
    Test that the history can be matched to the track with enough data
    """
    service = get_physical_location_service_duplicate_ids
    service.notify_location_event(40, 0, 0, 0)
    service.notify_transition_event(0)
    service.notify_location_event(18, 0, 0, 0)
    service.notify_transition_event(0)
    service.notify_transition_event(0)
    service.notify_transition_event(0)
    service.notify_location_event(18, 0, 0, 0)
    service.notify_transition_event(0)
    service.notify_location_event(20, 0, 0, 0)
    assert service._physical_piece == 5
    service.notify_transition_event(0)
    assert service._physical_piece == 0


def test_find_physical_location_not_enought_data(get_physical_location_service_duplicate_ids):
    """
    Test that the history doesn't get matched to the track, if there isn't enough data
    """
    service = get_physical_location_service_duplicate_ids
    service.notify_location_event(40, 0, 0, 0)
    service.notify_transition_event(0)
    service.notify_location_event(18, 0, 0, 0)
    service.notify_transition_event(0)
    service.notify_transition_event(0)
    service.notify_transition_event(0)
    service.notify_location_event(18, 0, 0, 0)
    service.notify_transition_event(0)
    assert service._physical_piece is None


def test_history_matching_for_offset(get_physical_location_service_duplicate_ids):
    """
    Test that the history can or can't get matched to the track correctly based on a given offset
    """
    service = get_physical_location_service_duplicate_ids
    service._piece_history = [None, None, 40, 18, None, None]
    assert service._test_history_matches_track_with_offset(4)
    assert service._test_history_matches_track_with_offset(1)
    assert not service._test_history_matches_track_with_offset(0)
