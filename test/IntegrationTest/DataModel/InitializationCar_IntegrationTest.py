from typing import List

import pytest
from bleak import BleakClient

from DataModel.InitializationCar import InitializationCar
from LocationService.Track import FullTrack, TrackPieceType, TrackPiece
from LocationService.TrackPieces import TrackBuilder
from VehicleManagement.AnkiController import AnkiController

_expected_track = TrackBuilder() \
    .append(TrackPieceType.START_PIECE_AFTER_LINE_WE, 33) \
    .append(TrackPieceType.CURVE_WS, 18) \
    .append(TrackPieceType.CURVE_NW, 23) \
    .append(TrackPieceType.STRAIGHT_EW, 39) \
    .append(TrackPieceType.CURVE_EN, 17) \
    .append(TrackPieceType.CURVE_SE, 20) \
    .append(TrackPieceType.START_PIECE_BEFORE_LINE_WE, 34) \
    .build()


@pytest.mark.skip_ci
@pytest.mark.slow
@pytest.mark.manual
@pytest.mark.one_anki_car_needed
@pytest.mark.asyncio
async def test_track_scanning(expected_track: FullTrack = _expected_track, uuid: str = 'DF:8B:DC:02:2C:23'):
    """
    This tests whether the scanned track of a car is the same as an expected track
    """
    anki_car_controller = AnkiController()
    await anki_car_controller.connect_to_vehicle(BleakClient(uuid))
    init_car = InitializationCar(anki_car_controller)
    raw_scanned_track: List[TrackPiece] = await init_car.run()
    scanned_track = FullTrack(raw_scanned_track)
    assert expected_track == scanned_track
