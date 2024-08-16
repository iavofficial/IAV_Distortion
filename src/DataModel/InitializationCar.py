import asyncio
from asyncio import Event
from typing import List

from bleak import BleakClient

from LocationService.Track import TrackPiece
from LocationService.TrackPieces import StartPieceAfterLine, TrackBuilder, StartPieceBeforeLine, StraightPiece, \
    CurvedPiece
from VehicleManagement.AnkiController import AnkiController

_START_PIECE_ID_AFTER_LINE: int = 33
_START_PIECE_ID_BEFORE_LINE: int = 34

_STRAIGHT_PIECE_IDS: List[int] = [36, 39, 40]
_CURVE_PIECE_IDS: List[int] = [17, 18, 20, 23]


def _raw_location_to_normalized_location(piece: int, location: int) -> int:
    """
    This function converts location data to a normalized value for pieces that require it and returns -1 otherwise.
    This is important to avoid scanning e.g. 3, 1, 2, on a straight piece since it would later be classified as counting
    downwards while in reality it's counting upwards.

    Parameters
    ----------
    piece: The ID of the piece on which the location value was scanned on
    location: The location value that was scanned
    """
    if piece in _STRAIGHT_PIECE_IDS:
        return location % 3
    elif piece in _CURVE_PIECE_IDS:
        if location < 20:
            return location % 2
        return (location - 20) % 3
    return -1


class ScannedPiece:
    """
    Class that holds the data (it's physical ID and normalized location data) for a scanned piece
    """
    def __init__(self, piece_id: int, location: int):
        self._piece_id: int = piece_id
        self._locations: List[int] = list()
        self._locations.append(_raw_location_to_normalized_location(piece_id, location))

    def get_id(self) -> int | None:
        """
        Get the stored physical piece ID
        """
        return self._piece_id

    def add_location(self, location: int) -> None:
        """
        Add a location value to the list of encountered location values
        """
        self._locations.append(_raw_location_to_normalized_location(self._piece_id, location))

    def reset_locations(self) -> None:
        """
        Reset all scanned location values. This should be called when there is a transition event and there
        isn't enough location data yet
        """
        self._locations.clear()

    def is_fully_scanned(self) -> bool:
        """
        Returns whether there is enough data for the piece to determine what kind of piece it is
        """
        return len(self._locations) >= 2 \
            or self._piece_id == _START_PIECE_ID_AFTER_LINE \
            or self._piece_id == _START_PIECE_ID_BEFORE_LINE

    def is_location_counting_downwards(self) -> bool | None:
        """
        Returns whether the locations on this piece are counted downwards. If there aren't enough location
        points `None` is returned
        """
        if len(self._locations) < 2:
            return None
        return self._locations[0] > self._locations[1]

    def __eq__(self, other):
        """
        Checks whether this scanned piece is equal to another scanned piece
        """
        return type(self) == type(other) and \
            self.get_id() == other.get_id() and \
            (self.is_location_counting_downwards() == other.is_location_counting_downwards())


class InitializationCar:
    """
    Class that has the ability to drive in a track in order to scan it and return a list of track pieces with
    physical IDs.
    To do this the car should be placed at the outer edge of the track and heading clockwise. After that
    the `run` method can be awaited while the car drives on the track. It returns the track when on 2 consecutive
    scanning rounds it had the same result. The track needs to have *exactly* one start piece!

    Please note that the starting piece will always be heading right in the created track.

    After the scan finished the AnkiController is automatically destroyed
    """
    def __init__(self, controller: AnkiController, ble_mac: str):
        self._controller: AnkiController = controller
        self._ble_mac: str = ble_mac
        self._piece_ids: List[ScannedPiece] = list()
        self._finished_scanning_event: Event = Event()
        self._new_piece = True

    async def run(self) -> List[TrackPiece] | None:
        """
        Start the scanning
        """
        controller: AnkiController = self._controller
        if not await controller.connect_to_vehicle(BleakClient(self._ble_mac), True):
            return None

        controller.set_callbacks(self._receive_location,
                                 self._receive_transition,
                                 self._nop,
                                 self._nop,
                                 self._nop,
                                 self._nop)

        await asyncio.sleep(2)

        old_scan: List[ScannedPiece] = []
        new_scan: List[ScannedPiece] = await self._scan_for_track_ids()

        while old_scan != new_scan:
            old_scan = new_scan
            new_scan = await self._scan_for_track_ids()

        controller.__del__()

        return self._convert_collected_data_to_pieces(new_scan)

    async def _scan_for_track_ids(self) -> List[ScannedPiece]:
        """
        Drives a scanning round and returns the IDs after that
        """
        self._piece_ids.clear()
        self._finished_scanning_event.clear()

        self._controller.change_speed_to(40)
        await self._finished_scanning_event.wait()
        self._controller.change_speed_to(0)

        return self._piece_ids.copy()

    def _receive_location(self, value_tuple):
        """
        Callback for when a location event is sent
        """
        location, piece, _, _, _ = value_tuple
        if not self._new_piece:
            self._piece_ids[-1].add_location(location)
            return

        # 33 marks start and end of the scanning
        if len(self._piece_ids) == 0:
            if piece == 33:
                new_piece = ScannedPiece(piece, location)
                self._piece_ids.append(new_piece)
            return

        if piece == 33:
            self._finished_scanning_event.set()
            return

        new_piece: ScannedPiece = ScannedPiece(piece, location)
        self._piece_ids.append(new_piece)
        self._new_piece = False

    def _receive_transition(self, value_tuple):
        """
        Callback for when a transition event is sent
        """
        _ = value_tuple
        self._new_piece = True
        if len(self._piece_ids) == 0:
            return

        if not self._piece_ids[-1].is_fully_scanned():
            self._piece_ids.clear()

    def _nop(self):
        """
        Do nothing (passed to callback functions that we don't need)
        """
        _ = self

    def _convert_collected_data_to_pieces(self, scanned_pieces: list[ScannedPiece]) -> list[TrackPiece]:
        """
        Converts a list of scanned piece into a list of valid TrackPieces including rotations
        """
        angle: int = 90
        _ = self
        # get piece constants from the track builder
        constants = TrackBuilder()

        converted_list: List[TrackPiece] = list()
        for piece in scanned_pieces:
            if piece.get_id() == _START_PIECE_ID_AFTER_LINE:
                converted_list.append(StartPieceAfterLine(constants.START_PIECE_AFTER_LINE_LENGTH,
                                                          constants.PIECE_DIAMETER,
                                                          angle,
                                                          constants.START_LINE_WIDTH,
                                                          physical_id=piece.get_id()))
            elif piece.get_id() == _START_PIECE_ID_BEFORE_LINE:
                converted_list.append(StartPieceBeforeLine(constants.START_PIECE_BEFORE_LINE_LENGTH,
                                                           constants.PIECE_DIAMETER,
                                                           angle,
                                                           physical_id=piece.get_id()))
            elif piece.get_id() in _STRAIGHT_PIECE_IDS:
                converted_list.append(StraightPiece(constants.STRAIGHT_PIECE_LENGTH,
                                                    constants.PIECE_DIAMETER,
                                                    angle,
                                                    physical_id=piece.get_id()))
            elif piece.get_id() in _CURVE_PIECE_IDS:
                # right turn curve; mirrored = False
                if piece.is_location_counting_downwards():
                    incoming_angle = (angle - 180) % 360
                    converted_list.append(CurvedPiece(constants.CURVE_PIECE_SIZE,
                                                      constants.PIECE_DIAMETER,
                                                      incoming_angle,
                                                      False,
                                                      physical_id=piece.get_id()))
                    angle = (angle + 90) % 360
                # left turn curve; mirrored = True
                else:
                    incoming_angle = (angle + 90) % 360
                    converted_list.append(CurvedPiece(constants.CURVE_PIECE_SIZE,
                                                      constants.PIECE_DIAMETER,
                                                      incoming_angle,
                                                      True,
                                                      physical_id=piece.get_id()))
                    angle = (angle - 90) % 360
        return converted_list
