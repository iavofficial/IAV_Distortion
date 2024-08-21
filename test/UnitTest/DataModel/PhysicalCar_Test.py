from unittest.mock import MagicMock

import pytest

import DataModel
from DataModel.PhysicalCar import PhysicalCar
from LocationService.Track import TrackPieceType, FullTrack
from LocationService.TrackPieces import TrackBuilder


@pytest.mark.parametrize("offset", [-70, 10, -66.5, 77, 60, -40])
def test_physical_car_offset_correction(offset: float):
    location_service_mock = MagicMock()
    controller = MagicMock()
    car = PhysicalCar('123', controller, location_service_mock)

    location_tuple = (13, 39, offset, 40, 128)
    car._receive_location(location_tuple)
    location_service_mock.notify_location_event.assert_called()
    args, _ = location_service_mock.notify_location_event.call_args
    given_offset = args[2]
    assert -66.5 <= given_offset <= 66.5

    transition_tuple = (0, 0, offset, 128)
    car._receive_transition(transition_tuple)
    location_service_mock.notify_transition_event.assert_called()
    args, _ = location_service_mock.notify_transition_event.call_args
    given_offset = args[0]
    assert -66.5 <= given_offset <= 66.5


@pytest.mark.parametrize("val,minimum,maximum,expected",
                         [(30, -10, 40, 30), (-30, -40, -20, -30), (10, 20, 30, 20), (10, 0, 5, 5), (-5, -20, -10, -10),
                          (-5, -3, -1, -3)])
def test_clamp(val: float, minimum: float, maximum: float, expected: float):
    clamped = DataModel.PhysicalCar.clamp(val, minimum, maximum)
    assert clamped == expected


@pytest.mark.parametrize("searched_physical_id", [10, 19, 77, -5, 103])
def test_wrong_track_piece_returns_none(searched_physical_id: int):
    track: FullTrack = TrackBuilder() \
        .append(TrackPieceType.STRAIGHT_WE, 40) \
        .append(TrackPieceType.CURVE_WS, 18) \
        .append(TrackPieceType.CURVE_NW, 23) \
        .append(TrackPieceType.STRAIGHT_EW, 39) \
        .append(TrackPieceType.CURVE_EN, 17) \
        .append(TrackPieceType.CURVE_SE, 20) \
        .build()
    assert not track.contains_physical_piece(searched_physical_id)
