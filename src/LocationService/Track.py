from abc import ABC, abstractmethod
from typing import Tuple

from LocationService.Trigo import Position, Angle

from enum import Enum

class Direction(Enum):
    NORTH = 0,
    WEST = 1,
    SOUTH = 2,
    EAST = 3

class TrackPieceType(Enum):
    STRAIGHT_WE = 0,
    STRAIGHT_NS = 1,
    STRAIGHT_EW = 2,
    STRAIGHT_SN = 3,
    CURVE_NW = 4,
    CURVE_ES = 8, # mirrored
    CURVE_EN = 5,
    CURVE_SW = 9, # mirrored
    CURVE_SE = 6,
    CURVE_WN = 10, # mirrored
    CURVE_WS = 7,
    CURVE_NE = 11 # mirrored

class TrackPiece(ABC):
    """
    Single TrackPiece class that allows calculating progress on itself and holds some metadata like it's size.
    """
    def __init__(self, rotation_deg: int):
        self._rotation = Angle(rotation_deg)

    @abstractmethod
    def process_update(self, start_progress: float, distance: float, offset: float) -> Tuple[float, Position]:
        """
        Drive a distance on the piece. Returns a tupe with the leftover distance that can be used on the next piece
        immediately (or 0, if the car is still on the same piece) and a position relativ to the center of the track piece
        (which should be ignored, if there is a leftover distance).
        """
        raise NotImplementedError

    @abstractmethod
    def get_used_space_horiz(self):
        raise NotImplementedError

    @abstractmethod
    def get_used_space_vert(self):
        raise NotImplementedError

    @abstractmethod
    def get_next_attachment_direction(self) -> Direction:
        raise NotImplementedError

class TrackEntry():
    def __init__(self, track_piece, offset):
        self.track_piece: TrackPiece = track_piece
        self.offset: Position = offset

    def get_piece(self) -> TrackPiece:
        return self.track_piece

    def get_global_offset(self) -> Position:
        return self.offset

class FullTrack():
    """
    Class that represents an entire track. The upper left corner of the upper left
    track piece is at the coordinate 0, 0. All units are in mm.
    """
    def __init__(self, pieces):
        self.track_entries: list[TrackEntry] = list()
        cur_y = 0
        cur_x = 0
        max_x = 0
        max_y = 0
        for track in pieces:
            self.track_entries.append(TrackEntry(track, Position(cur_x, cur_y)))
            match track.get_next_attachment_direction():
                case Direction.WEST:
                    cur_x -= track.get_used_space_horiz()
                case Direction.NORTH:
                    cur_y -= track.get_used_space_vert()
                case Direction.EAST:
                    cur_x += track.get_used_space_horiz()
                case Direction.SOUTH:
                    cur_y += track.get_used_space_vert()
            if max_x > cur_x:
                max_x = cur_x
            if max_y > cur_y:
                max_y = cur_y
        # change positions so that the top left corner of the top left piece is at (0, 0)
        for entry in self.track_entries:
            entry.get_global_offset().add_offset(-max_x + pieces[0].get_used_space_horiz() / 2, -max_y + pieces[0].get_used_space_vert() / 2)

    def get_entry_tupel(self, num: int) -> Tuple[TrackPiece, Position]:
        entry = self.track_entries[num]
        return (entry.get_piece(), entry.get_global_offset())

    def get_len(self):
        return len(self.track_entries)
