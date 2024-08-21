from unittest.mock import MagicMock

import pytest

from DataModel.InitializationCar import _raw_location_to_normalized_location, ScannedPiece, InitializationCar
from LocationService.Track import FullTrack, TrackPieceType
from LocationService.TrackPieces import TrackBuilder

STRAIGHT_ID = 39
CURVE_ID = 20


@pytest.fixture
def initialization_car():
    controller_mock = MagicMock()
    init_car = InitializationCar(controller_mock, 'AA:AA:AA:AA:AA:AA')
    return init_car


def pass_real_event_trace_to_car(init_car: InitializationCar):
    """
    This passes the location + piece data of a real track to the Initialization car
    """
    init_car._receive_location((5, 33, 0, 0, 0))
    init_car._receive_transition((0, 0, 0, 0))
    init_car._receive_location((22, 18, 0, 0, 0))
    init_car._receive_location((21, 18, 0, 0, 0))
    init_car._receive_location((20, 18, 0, 0, 0))
    init_car._receive_transition((0, 0, 0, 0))
    init_car._receive_location((22, 23, 0, 0, 0))
    init_car._receive_location((21, 23, 0, 0, 0))
    init_car._receive_location((20, 23, 0, 0, 0))
    init_car._receive_transition((0, 0, 0, 0))
    init_car._receive_location((15, 39, 0, 0, 0))
    init_car._receive_location((16, 39, 0, 0, 0))
    init_car._receive_location((17, 39, 0, 0, 0))
    init_car._receive_transition((0, 0, 0, 0))
    init_car._receive_location((22, 17, 0, 0, 0))
    init_car._receive_location((21, 17, 0, 0, 0))
    init_car._receive_location((20, 17, 0, 0, 0))
    init_car._receive_transition((0, 0, 0, 0))
    init_car._receive_location((22, 20, 0, 0, 0))
    init_car._receive_location((21, 20, 0, 0, 0))
    init_car._receive_location((20, 20, 0, 0, 0))
    init_car._receive_transition((0, 0, 0, 0))
    init_car._receive_location((10, 34, 0, 0, 0))
    init_car._receive_location((11, 34, 0, 0, 0))
    init_car._receive_transition((0, 0, 0, 0))
    init_car._receive_location((5, 33, 0, 0, 0))


def test_location_conversion():
    """
    This tests whether the function that converts raw location into a normal format is doing these conversions right
    """

    # straight pieces
    assert _raw_location_to_normalized_location(STRAIGHT_ID, 6) == 0
    assert _raw_location_to_normalized_location(STRAIGHT_ID, 8) == 2

    # curve inner
    assert _raw_location_to_normalized_location(CURVE_ID, 4) == 0
    assert _raw_location_to_normalized_location(CURVE_ID, 1) == 1

    # curve outer
    assert _raw_location_to_normalized_location(CURVE_ID, 30) == 1
    assert _raw_location_to_normalized_location(CURVE_ID, 31) == 2


def test_scanned_piece_location_adding_and_resetting():
    """
    This tests whether adding / resetting locations works
    """
    scanned = ScannedPiece(STRAIGHT_ID, 3)
    scanned.add_location(4)
    assert len(scanned._locations) == 2
    scanned.reset_locations()
    assert len(scanned._locations) == 0


def test_scanned_piece_location_counting():
    """
    This tests that adding locations results in the right counting type
    """
    scanned = ScannedPiece(STRAIGHT_ID, 3)
    assert scanned.is_location_counting_downwards() is None
    scanned.add_location(4)
    assert scanned.is_location_counting_downwards() is False


def test_scanned_piece_is_fully_scanned():
    """
    This tests whether a scanned piece returns correctly whether it was fully scanned
    """
    scanned_straight = ScannedPiece(STRAIGHT_ID, 0)
    assert not scanned_straight.is_fully_scanned()
    scanned_straight.add_location(1)
    assert scanned_straight.is_fully_scanned()

    scanned_finish_piece = ScannedPiece(33, 0)
    assert scanned_finish_piece.is_fully_scanned()


def test_scanning_reset(initialization_car):
    """
    This tests whether the Initialization Car correctly resets when it doesn't have enough information about a piece
    """
    init_car = initialization_car
    init_car._receive_location((0, 33, 0, 0, 0))
    init_car._receive_transition((0, 0, 0, 0))
    init_car._receive_location((0, STRAIGHT_ID, 0, 0, 0))
    init_car._receive_transition((0, 0, 0, 0))
    # should fail since we don't know the location direction
    assert len(init_car._piece_ids) == 0


def test_scanning_starts_at_piece_33(initialization_car):
    """
    This tests that the track scanning starts after the start line (piece id 33)
    """
    init_car = initialization_car
    init_car._receive_location((0, STRAIGHT_ID, 0, 0, 0))
    init_car._receive_location((1, STRAIGHT_ID, 0, 0, 0))
    init_car._receive_transition((0, 0, 0, 0))
    assert len(init_car._piece_ids) == 0
    init_car._receive_location((0, 33, 0, 0, 0))
    init_car._receive_transition((0, 0, 0, 0))
    assert len(init_car._piece_ids) == 1


def test_round_finish_leads_to_stop_event(initialization_car):
    """
    This tests whether the finish event is set after the car scans the start piece twice
    """
    init_car = initialization_car
    pass_real_event_trace_to_car(init_car)
    assert init_car._finished_scanning_event.is_set()


def test_init_car_data_conversion(initialization_car):
    """
    This test simulates the car driving over a track and then tests whether building the recorded pieces into a track
    matches the expected track
    """
    init_car = initialization_car
    pass_real_event_trace_to_car(init_car)
    track = init_car._convert_collected_data_to_pieces(init_car._piece_ids)
    assert len(track) == 7
    converted_track = FullTrack(track)
    expected_track = TrackBuilder() \
        .append(TrackPieceType.START_PIECE_AFTER_LINE_WE, 33) \
        .append(TrackPieceType.CURVE_WS, 18) \
        .append(TrackPieceType.CURVE_NW, 23) \
        .append(TrackPieceType.STRAIGHT_EW, 39) \
        .append(TrackPieceType.CURVE_EN, 17) \
        .append(TrackPieceType.CURVE_SE, 20) \
        .append(TrackPieceType.START_PIECE_BEFORE_LINE_WE, 34) \
        .build()

    assert converted_track == expected_track
