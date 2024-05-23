import pytest

from LocationService.TrackPieces import TrackBuilder, FullTrack
from LocationService.LocationService import LocationService
from LocationService.Track import TrackPieceType, TrackPiece
from LocationService.Trigo import Position, Angle

def do_nothing(pos: Position, angle: Angle):
    pass

# Constants
def STRAIGHT_PIECE_LENGTH():
    return TrackBuilder().STRAIGHT_PIECE_LENGTH

def STRAIGHT_PIECE_DIAMETER():
    return TrackBuilder().PIECE_DIAMETER

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
    location_service = LocationService(get_two_straight_pieces(), do_nothing, simulation_ticks_per_second=1, start_immeaditly=False)
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
    location_service = LocationService(get_two_straight_pieces(), do_nothing, simulation_ticks_per_second=1, start_immeaditly=False)
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

@pytest.mark.parametrize("offset", [(0), (40), (-10), (20), (60), (-40)])
@pytest.mark.parametrize("speed", [(200), (1), (100), (10), (2500), (1000), (1715)])
def test_multiple_transitions(speed: float, offset: float):
    """
    Test the transitions against jumping at a full track
    """
    track = get_loop_track()
    location_service = LocationService(track, do_nothing, simulation_ticks_per_second=1, start_immeaditly=False)
    location_service._set_speed_mm(speed, acceleration=1)
    location_service._set_offset_mm(offset)
    # progress a bit on the first piece
    for _ in range(0, 20):
        location_service._run_simulation_step_threadsafe()

    old_pos, _ = location_service._run_simulation_step_threadsafe()
    for _ in range(0, track.get_len() * STRAIGHT_PIECE_LENGTH()):
        new_pos, _ = location_service._run_simulation_step_threadsafe()
        # allow small floating errors
        assert old_pos.distance_to(new_pos) < speed * 1.000001
        old_pos = new_pos

    old_pos, _ = location_service._run_simulation_step_threadsafe()
    for _ in range(0, track.get_len() * STRAIGHT_PIECE_LENGTH()):
        new_pos, _ = location_service._run_simulation_step_threadsafe()
        # allow small floating errors
        assert old_pos.distance_to(new_pos) < speed * 1.000001
        old_pos = new_pos

@pytest.mark.parametrize("offset", [(20), (1), (75), (10), (-15), (0), (-72)])
def test_offset(offset: float):
    """
    Test the offset changing on the track itself for different values
    """
    location_service = LocationService(get_two_straight_pieces(), do_nothing, simulation_ticks_per_second=1, start_immeaditly=False)
    location_service._set_speed_mm(1, acceleration=1)
    old_pos, _ = location_service._run_simulation_step_threadsafe()
    location_service._set_offset_mm(offset)
    for _ in range(0, 500):
        location_service._run_simulation_step_threadsafe()
    new_pos, _ = location_service._run_simulation_step_threadsafe()
    # * - 1 since the track is going in the reverse direction
    exp_y = old_pos.get_y() + offset * -1
    assert new_pos.get_y() == pytest.approx(exp_y)

def test_position_rotation():
    """
    Test the returned rotation value, where the car is pointing for plausibility
    """
    track = get_loop_track()
    location_service = LocationService(track, do_nothing, simulation_ticks_per_second=1, start_immeaditly=False)
    location_service._set_speed_mm(1, acceleration=1)
    location_service._run_simulation_step_threadsafe()
    # for the 1st piece it should always be 90° (pointing right)
    while True:
        _, rot = location_service._run_simulation_step_threadsafe()
        if location_service._current_piece_index != 0:
            break
        assert rot.get_deg() == pytest.approx(90)
    _, last = location_service._run_simulation_step_threadsafe()
    while True:
        _, new = location_service._run_simulation_step_threadsafe()
        # go over both curve pieces
        if location_service._current_piece_index == 3:
            break
        assert new.get_deg() > last.get_deg()
        last = new
    # now we are on a straight piece again and should point right
    _, rot = location_service._run_simulation_step_threadsafe()
    assert rot.get_deg() == 270
