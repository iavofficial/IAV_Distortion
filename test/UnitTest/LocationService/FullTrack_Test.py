import pytest

from LocationService.Track import TrackPieceType, FullTrack
from LocationService.TrackPieces import TrackBuilder


@pytest.fixture
def small_track() -> FullTrack:
    track: FullTrack = TrackBuilder() \
        .append(TrackPieceType.STRAIGHT_WE) \
        .append(TrackPieceType.CURVE_WS) \
        .append(TrackPieceType.CURVE_NW) \
        .append(TrackPieceType.STRAIGHT_EW) \
        .append(TrackPieceType.CURVE_EN) \
        .append(TrackPieceType.CURVE_SE) \
        .build()

    return track


@pytest.fixture
def big_track() -> FullTrack:
    track: FullTrack = TrackBuilder() \
        .append(TrackPieceType.CURVE_WS) \
        .append(TrackPieceType.STRAIGHT_NS) \
        .append(TrackPieceType.CURVE_NE) \
        .append(TrackPieceType.CURVE_WN) \
        .append(TrackPieceType.STRAIGHT_SN) \
        .append(TrackPieceType.CURVE_SE) \
        .append(TrackPieceType.CURVE_WS) \
        .append(TrackPieceType.STRAIGHT_NS) \
        .append(TrackPieceType.CURVE_NE) \
        .append(TrackPieceType.CURVE_WN) \
        .append(TrackPieceType.STRAIGHT_SN) \
        .append(TrackPieceType.CURVE_SE) \
        .append(TrackPieceType.STRAIGHT_WE) \
        .append(TrackPieceType.CURVE_WS) \
        .append(TrackPieceType.STRAIGHT_NS) \
        .append(TrackPieceType.STRAIGHT_NS) \
        .append(TrackPieceType.CURVE_NW) \
        .append(TrackPieceType.STRAIGHT_EW) \
        .append(TrackPieceType.STRAIGHT_EW) \
        .append(TrackPieceType.STRAIGHT_EW) \
        .append(TrackPieceType.STRAIGHT_EW) \
        .append(TrackPieceType.STRAIGHT_EW) \
        .append(TrackPieceType.CURVE_EN) \
        .append(TrackPieceType.STRAIGHT_SN) \
        .append(TrackPieceType.STRAIGHT_SN) \
        .append(TrackPieceType.CURVE_SE) \
        .build()

    return track


def test_track_size_calculation(small_track: FullTrack, big_track: FullTrack):
    track_square_size = 559
    size_small = small_track.get_used_space_as_dict()
    size_big = big_track.get_used_space_as_dict()

    assert pytest.approx(track_square_size * 3) == size_small['used_space_vertically']
    assert pytest.approx(track_square_size * 2) == size_small['used_space_horizontally']

    assert pytest.approx(track_square_size * 7) == size_big['used_space_vertically']
    assert pytest.approx(track_square_size * 4) == size_big['used_space_horizontally']
