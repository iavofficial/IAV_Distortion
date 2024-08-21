from abc import ABC, abstractmethod
from typing import List, Tuple, Dict, Any

from LocationService.Trigo import Position, Angle, Distance

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
    CURVE_ES = 8,  # mirrored
    CURVE_EN = 5,
    CURVE_SW = 9,  # mirrored
    CURVE_SE = 6,
    CURVE_WN = 10,  # mirrored
    CURVE_WS = 7,
    CURVE_NE = 11,  # mirrored

    START_PIECE_BEFORE_LINE_WE = 12,
    START_PIECE_BEFORE_LINE_NS = 13,
    START_PIECE_BEFORE_LINE_EW = 14,
    START_PIECE_BEFORE_LINE_SN = 15,
    START_PIECE_AFTER_LINE_WE = 16,
    START_PIECE_AFTER_LINE_NS = 17,
    START_PIECE_AFTER_LINE_EW = 18,
    START_PIECE_AFTER_LINE_SN = 19,


class TrackPiece(ABC):
    """
    Single TrackPiece class that allows calculating progress on itself and holds some metadata like it's size.
    """
    def __init__(self, rotation_deg: int, physical_id):
        self._rotation = Angle(rotation_deg)
        self._physical_id: int | None = physical_id

    def set_physical_id(self, physical_id: int | None) -> None:
        self._physical_id = physical_id

    def get_physical_id(self) -> int | None:
        return self._physical_id

    def __eq__(self, other):
        return type(self) == type(other) \
            and self._rotation == other._rotation \
            and self._physical_id == other._physical_id

    def __ne__(self, other):
        return not self.__eq__(other)

    @abstractmethod
    def process_update(self, start_progress: float, distance: float, offset: float) -> Tuple[float, Position]:
        """
        Drive a distance on the piece. Returns a tupe with the leftover distance that can be used on the next piece
        immediately (or 0, if the car is still on the same piece) and a position relativ to the center of the track
        piece (which should be ignored, if there is a leftover distance).
        To drive in the opposing direction start at the end (by getting the length) and then providing a negative
        distance.
        """
        raise NotImplementedError

    @abstractmethod
    def get_used_space_horiz(self):
        """
        Used space horizontally when looked at from above
        """
        raise NotImplementedError

    @abstractmethod
    def get_used_space_vert(self):
        """
        Used space vertically when looked at from above
        """
        raise NotImplementedError

    @abstractmethod
    def get_outgoing_offset(self) -> Distance:
        """
        Gets the offset in x and y required to go from the center to the end of the piece
        """
        raise NotImplementedError

    @abstractmethod
    def get_incoming_offset(self) -> Distance:
        """
        Gets the offset in x and y required to go from the incoming direction to the center
        """
        raise NotImplementedError

    @abstractmethod
    def get_outgoing_direction(self) -> Direction:
        """
        Direction where the next track piece should be attached relative
        to this piece
        """
        raise NotImplementedError

    @abstractmethod
    def get_incoming_direction(self) -> Direction:
        """
        Direction from where the previous track piece should go into this
        """
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
    def get_progress_based_on_location(self, location: int, offset: float) -> float:
        """
        Get the progress in mm based on the sent location data from a physical car. This assumes the piece
        is laid down in a way that in clockwise direction it counts down
        """
        raise NotImplementedError

    @abstractmethod
    def to_html_dict(self) -> dict:
        """
        Get the piece in a representation that can be used in JS to draw the track
        """
        raise NotImplementedError

    @abstractmethod
    def to_json_dict(self) -> Dict[str, Any]:
        """
        Returns the piece as a dict that for serialization that can later be de-serialized
        """
        return {
            'type': self.__module__ + '.' + self.__class__.__qualname__,
            'rotation': self._rotation.get_deg(),
            'physical_id': self._physical_id
        }


class TrackEntry():
    """
    Entry in a FullTrach that includes the piece itself and where
    it's relativ to the whole Track
    """
    def __init__(self, track_piece, offset):
        self.track_piece: TrackPiece = track_piece
        self.offset: Position = offset

    def get_piece(self) -> TrackPiece:
        """
        Get's the piece hold by this data structure
        """
        return self.track_piece

    def get_global_offset(self) -> Position:
        """
        Get's the position of the piece relativ to the track / on a global field
        """
        return self.offset


class FullTrack():
    """
    Class that represents an entire track. The upper left corner of the upper left
    track piece is at the coordinate 0, 0. All units are in mm.
    """
    def __init__(self, pieces: list[TrackPiece]):
        self.track_entries: list[TrackEntry] = list()
        offset = Position(0, 0)
        last_piece = pieces[0]
        self.track_entries.append(TrackEntry(last_piece, offset.clone()))
        for piece in pieces[1:]:
            offset += last_piece.get_outgoing_offset()
            offset += piece.get_incoming_offset()
            last_piece = piece
            self.track_entries.append(TrackEntry(last_piece, offset.clone()))

        # this section is here to move the top left corner of the top left piece to (0, 0)
        min_x = 0
        min_y = 0
        for entry in self.track_entries:
            piece = entry.get_piece()
            offset = entry.get_global_offset()
            local_x = offset.get_x() - piece.get_used_space_horiz() / 2
            local_y = offset.get_y() - piece.get_used_space_vert() / 2
            min_x = min(min_x, local_x)
            min_y = min(min_y, local_y)

        # the change is negative but a positive value needs to be applied so we use abs
        change_x = abs(min_x)
        change_y = abs(min_y)

        for entry in self.track_entries:
            entry.get_global_offset().add_offset(change_x, change_y)

    def get_entry_tupel(self, num: int) -> Tuple[TrackPiece, Position]:
        """
        Get a TrackEntry (so TrackPiece and global position of it) based on it's index
        """
        entry = self.track_entries[num]
        return (entry.get_piece(), entry.get_global_offset())

    def get_len(self):
        """
        Gets the number of track pieces in the whole track
        """
        return len(self.track_entries)

    def get_as_list(self) -> List[dict]:
        """
        Get's the offsets and pieces as list of dicts. Try preferring other
        functions if possible for type safety!
        """
        l: list[dict] = []
        for entry in self.track_entries:
            piece = entry.get_piece()
            offset = entry.get_global_offset()
            l.append({
                'offset': offset.to_dict(),
                'piece': piece.to_html_dict()
            })

        return l

    def contains_physical_piece(self, physical_id: int) -> bool:
        """
        Returns whether the track contains a piece with the given physical ID
        """
        for i in range(0, self.get_len()):
            piece: TrackPiece = self.track_entries[i].get_piece()
            if piece.get_physical_id() == physical_id:
                return True
        return False

    def get_used_space_as_dict(self) -> Dict[str, int]:
        """
        Returns a dict with the used horizontal and vertical space. The keys are
        `used_space_vertically` and `used_space_horizontally`
        """
        max_vert: int = 0
        max_horiz: int = 0
        for entry in self.track_entries:
            piece = entry.get_piece()
            offset = entry.get_global_offset()
            local_max_x = piece.get_used_space_vert() / 2 + offset.get_x()
            local_max_y = piece.get_used_space_horiz() / 2 + offset.get_y()
            max_vert = max(max_vert, local_max_x)
            max_horiz = max(max_horiz, local_max_y)

        return {
            'used_space_vertically': max_horiz,
            'used_space_horizontally': max_vert
        }

    def __eq__(self, other):
        if type(self) != type(other):
            return False

        if self.get_len() != other.get_len():
            return False

        for i in range(0, self.get_len()):
            own_piece, _ = self.get_entry_tupel(i)
            other_piece, _ = other.get_entry_tupel(i)
            if own_piece != other_piece:
                return False
        return True
