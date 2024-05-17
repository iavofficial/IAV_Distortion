import pytest

from LocationService.TrackPieces import TrackBuilder, FullTrack
from LocationService.LocationService import LocationService
from LocationService.Track import TrackPieceType, TrackPiece
from LocationService.Trigo import Position

# Constants
def STRAIGHT_PIECE_LENGTH():
    return TrackBuilder().STRAIGHT_PIECE_LENGTH

def STRAIGHT_PIECE_DIAMETER():
    return TrackBuilder().STRAIGHT_PIECE_DIAMETER

def CURVE_PIECE_SIZE():
    return TrackBuilder().CURVE_PIECE_SIZE

# Helper functions for generating tracks
def get_loop_track() -> FullTrack:
    track = TrackBuilder()\
        .append(TrackPieceType.STRAIGHT_WE)\
        .append(TrackPieceType.CURVE_WS)\
        .append(TrackPieceType.CURVE_NW)\
        .append(TrackPieceType.STRAIGHT_EW)\
        .append(TrackPieceType.CURVE_EN)\
        .append(TrackPieceType.CURVE_SE)\
        .build()
    return track

def get_two_straight_pieces() -> FullTrack:
    track = TrackBuilder()\
        .append(TrackPieceType.STRAIGHT_EW)\
        .append(TrackPieceType.STRAIGHT_EW)\
        .build()
    return track

# Tests
def test_track_transistion():
    """
    Test the transition from one track piece onto the next one
    """
    location_service = LocationService(get_two_straight_pieces(), simulation_ticks_per_second=1, start_immeaditly=False)
    location_service._set_speed_mm(1, acceleration=1)
    for i in range(0, STRAIGHT_PIECE_LENGTH()):
        location_service._run_simulation_step_threadsafe()
        # assert it moved 1 mm since this is the speed
        assert location_service._progress_on_current_piece == i + 1
    assert location_service._current_piece_index == 0
    assert location_service._progress_on_current_piece == STRAIGHT_PIECE_LENGTH()
    # transition onto next track piece
    location_service._run_simulation_step_threadsafe()
    assert location_service._current_piece_index == 1
    assert location_service._progress_on_current_piece == 1
