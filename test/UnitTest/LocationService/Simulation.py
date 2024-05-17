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

@pytest.mark.parametrize("speed,acceleration", [(200, 9), (10, 2), (100, 53), (10, 100)])
def test_acceleration(speed, acceleration):
    """
    Test that the vehicle accelerates correctly
    """
    location_service = LocationService(get_two_straight_pieces(), simulation_ticks_per_second=1, start_immeaditly=False)
    location_service._set_speed_mm(speed, acceleration=acceleration)
    sum = 0
    for _ in range(0, int(speed / acceleration)):
        sum += acceleration
        location_service._run_simulation_step_threadsafe()
        assert location_service._actual_speed == sum

def get_top_left_in_global(piece: TrackPiece, pos: Position) -> Position:
    x = pos.get_x() - piece.get_used_space_horiz() / 2
    y = pos.get_y() - piece.get_used_space_vert() / 2
    return Position(x, y)

def test_top_left_corner():
    """
    Create a full track and test, that there is a piece at (0, 0). It needs to be ran
    on a full closing track. As of now the test doesn't account for the fact that there
    are tracks without clean top left piece!
    """
    track = get_loop_track()
    piece, pos = track.get_entry_tupel(0)
    top_left_pos = get_top_left_in_global(piece, pos)
    min_x = top_left_pos.get_x()
    # indices of the minimum. Since there can be equal ones it needs to be a list
    min_x_list = list()
    min_y = top_left_pos.get_y()
    min_y_list = list()
    for i in range(0, track.get_len()):
        piece, pos_on_track = track.get_entry_tupel(i)
        top_left_corner = get_top_left_in_global(piece, pos_on_track)
        if top_left_corner.get_x() < min_x:
            min_x = top_left_corner.get_x()
            min_x_list.clear()
            min_x_list.append(i)
        elif top_left_corner.get_x() == min_x:
            min_x_list.append(i)
        if top_left_corner.get_y() < min_y:
            min_y = top_left_corner.get_y()
            min_y_list.clear()
            min_y_list.append(i)
        elif top_left_corner.get_y() == min_y:
            min_y_list.append(i)

    piece, pos = track.get_entry_tupel(1)
    assert min_x == 0
    assert min_y == 0
    # Check, if the (0, 0) is on the same piece
    assert len(set(min_x_list).intersection(min_y_list)) >= 1
