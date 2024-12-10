import pytest

from LocationService.Track import FullTrack, TrackPieceType
from LocationService.TrackPieces import StraightPiece, CurvedPiece, StartPieceBeforeLine, StartPieceAfterLine, \
    TrackBuilder
from LocationService.TrackSerialization import construct_piece_from_dict, full_track_to_list_of_dicts, \
    parse_list_of_dicts_to_full_track


@pytest.fixture
def example_testdata_straight():
    straight_dict = {
        'type': 'LocationService.TrackPieces.StraightPiece',
        'rotation': 90,
        'physical_id': 3,
        'length': 40,
        'diameter': 3}
    straight_real = StraightPiece(40, 3, 90, physical_id=3)
    return straight_dict, straight_real


@pytest.fixture
def example_testdata_curve():
    curved_dict = {
        'type': 'LocationService.TrackPieces.CurvedPiece',
        'rotation': 90,
        'physical_id': 12,
        'square_size': 500,
        'diameter': 30,
        'mirrored': False}
    curved_real = CurvedPiece(500, 30, 90, False, physical_id=12)
    return curved_dict, curved_real


@pytest.fixture
def example_testdata_before_line():
    straight_before_line_dict = {
        'type': 'LocationService.TrackPieces.StartPieceBeforeLine',
        'rotation': 90,
        'physical_id': None,
        'length': 100,
        'diameter': 10}
    straight_before_line_real = StartPieceBeforeLine(100, 10, 90)
    return straight_before_line_dict, straight_before_line_real


@pytest.fixture
def example_testdata_after_line():
    straight_after_line_dict = {
        'type': 'LocationService.TrackPieces.StartPieceAfterLine',
        'rotation': 90,
        'physical_id': None,
        'length': 100,
        'diameter': 10,
        'start_line_width': 21}
    straight_after_line_real = StartPieceAfterLine(100, 10, 90, 21)
    return straight_after_line_dict, straight_after_line_real


@pytest.fixture
def example_full_track():
    track: FullTrack = TrackBuilder() \
        .append(TrackPieceType.START_PIECE_BEFORE_LINE_WE, 34) \
        .append(TrackPieceType.START_PIECE_AFTER_LINE_WE, 33) \
        .append(TrackPieceType.CURVE_WS, 18) \
        .append(TrackPieceType.CURVE_NW, 23) \
        .append(TrackPieceType.STRAIGHT_EW, 39) \
        .append(TrackPieceType.CURVE_EN, 17) \
        .append(TrackPieceType.CURVE_SE, 20) \
        .build()

    return track


def test_piece_deserialization(example_testdata_straight,
                               example_testdata_curve,
                               example_testdata_before_line,
                               example_testdata_after_line):
    """
    Test that pieces that are deserialized from a dict match their counterpart
    """
    straight_dict, straight_real = example_testdata_straight
    assert construct_piece_from_dict(straight_dict) == straight_real

    curved_dict, curved_real = example_testdata_curve
    assert construct_piece_from_dict(curved_dict) == curved_real

    straight_before_line_dict, straight_before_line_real = example_testdata_before_line
    assert construct_piece_from_dict(straight_before_line_dict) == straight_before_line_real

    straight_after_line_dict, straight_after_line_real = example_testdata_after_line
    assert construct_piece_from_dict(straight_after_line_dict) == straight_after_line_real


def test_serialization(example_testdata_straight,
                       example_testdata_curve,
                       example_testdata_before_line,
                       example_testdata_after_line):
    """
    Test that serializing a track piece returns the right serialized data
    """
    straight_dict, straight_real = example_testdata_straight
    assert straight_real.to_json_dict() == straight_dict

    curved_dict, curved_real = example_testdata_curve
    assert curved_real.to_json_dict() == curved_dict

    straight_before_line_dict, straight_before_line_real = example_testdata_before_line
    assert straight_before_line_real.to_json_dict() == straight_before_line_dict

    straight_after_line_dict, straight_after_line_real = example_testdata_after_line
    assert straight_after_line_real.to_json_dict() == straight_after_line_dict


def test_reconversion(example_full_track):
    """
    Test the serialization by having a full track, serializing it, deserializing it and comparing the deserialized
    data with the original data
    """
    track = example_full_track
    track_as_dictlist = full_track_to_list_of_dicts(track)
    reconstructed_track = parse_list_of_dicts_to_full_track(track_as_dictlist)
    assert track == reconstructed_track
