from abc import ABC, abstractmethod
from typing import List, Tuple

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
        To drive in the opposing direction start at the end (by getting the length) and then providing a negative distance.
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

    @abstractmethod
    def get_length(self, offset: float) -> float:
        """
        Get the length of the track at a given offset
        """
        raise NotImplementedError

    @abstractmethod
    def get_equivalent_progress_for_offset(self, old_offset: float, new_offset: float, old_progress: float) -> float:
        """
        Get the current progress on the track for changing the offset
        """
        raise NotImplementedError

    @abstractmethod
    def to_dict(self) -> dict:
        """
        Get the piece represented as dict
        """
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
    def __init__(self, pieces: list[TrackPiece]):
        self.track_entries: list[TrackEntry] = list()
        cur_y = 0
        cur_x = 0
        min_x = 0
        min_y = 0
        max_used_horiz = 0
        max_used_vert = 0
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
            if cur_x < min_x:
                min_x = cur_x
            if cur_y < min_y:
                min_y = cur_y
            if track.get_used_space_horiz() > max_used_horiz:
                max_used_horiz = track.get_used_space_horiz()
            if track.get_used_space_vert() > max_used_vert:
                max_used_vert = track.get_used_space_vert()
        # change positions so that the top left corner of the top left piece is at (0, 0)
        diff_x = -min_x + max_used_horiz / 2
        diff_y = -min_y + max_used_vert / 2
        for entry in self.track_entries:
            entry.get_global_offset().add_offset(diff_x, diff_y)

    def get_entry_tupel(self, num: int) -> Tuple[TrackPiece, Position]:
        entry = self.track_entries[num]
        return (entry.get_piece(), entry.get_global_offset())

    def get_len(self):
        return len(self.track_entries)

    def get_as_list(self) -> List[dict]:
        l: list[dict] = []
        for entry in self.track_entries:
            piece = entry.get_piece()
            offset = entry.get_global_offset()
            l.append({
                'offset': offset.to_dict(),
                'piece': piece.to_dict()
            })

        return l
