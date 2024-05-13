from typing import List, Tuple
import math

from LocationService.Track import Direction, FullTrack, TrackPiece, TrackPieceType
from LocationService.Trigo import Position, Angle


class StraightPiece(TrackPiece):
    def __init__(self, length, diameter, rotation):
        super().__init__(rotation)
        if rotation == 0 or rotation == 180:
            self._horiz_length = diameter
            self._vert_length = length
        else:
            self._horiz_length = length
            self._vert_length = diameter

        self._length = length
        self._diameter = diameter

    def get_used_space_vert(self):
        return self._vert_length

    def get_used_space_horiz(self):
        return self._horiz_length

    def get_next_attachment_direction(self) -> Direction:
        match self._rotation.get_deg():
            case 0:
                return Direction.NORTH
            case 90:
                return Direction.EAST
            case 180:
                return Direction.SOUTH
            case 270:
                return Direction.WEST
        raise NotImplementedError

    def process_update(self, start_progress: float, distance: float, offset: float) -> Tuple[float, Position]:
        end = start_progress + distance
        left = 0
        if end >= self._length:
            left = end - self._length
            end = self._length

        endposition = Position(-offset, self._length / 2 - end)
        endposition.rotate_around_0_0(self._rotation)

        return (left, endposition)

class CurvedPiece(TrackPiece):
    def __init__(self, square_size, rot: int, mirror: bool):
        super().__init__(rot)
        self._size = square_size
        self._radius = square_size / 2
        self._is_mirrored = mirror

    def get_used_space_horiz(self):
        return self._size

    def get_used_space_vert(self):
        return self._size

    def get_next_attachment_direction(self) -> Direction:
        match self._rotation.get_deg():
            case 0:
                return Direction.WEST
            case 90:
                return Direction.NORTH
            case 180:
                return Direction.EAST
            case 270:
                return Direction.SOUTH
        raise NotImplementedError

    def process_update(self, start_progress: float, distance: float, offset: float):
        end = start_progress + distance
        left = 0
        travel_len = self.get_track_length(offset)
        if end >= travel_len:
            left = end - travel_len
            end = travel_len
        progress = end / travel_len
        angle = Angle(progress * 90)
        distance_to_middle = self._radius + offset
        position = Position(distance_to_middle * angle.get_x_mult(), distance_to_middle * angle.get_y_mult())
        position.add_offset(-self._size / 2, -self._size / 2)
        if self._is_mirrored:
            position = Position(position.get_x() * -1, position.get_y() * -1)
        position.rotate_around_0_0(self._rotation)
        return (left, position)

    def get_track_length(self, offset: float) -> float:
        return (self._radius + offset) * math.pi / 2


class TrackBuilder():
    """
    Class to build an entire track by chaining append() calls with the desired direction
    """
    def __init__(self):
        self.piece_list: List[TrackPiece] = [] 
        # Constants
        self.STRAIGHT_PIECE_LENGTH = 555
        self.STRAIGHT_PIECE_DIAMETER = 260
        # This has to be the same as STRAIGHT_PIECE_LENGTH; otherwise the simulation
        # would need extra calculations to do the transition onto the piece; since every
        # piece we have fulfills this requirement the case isn't handled
        self.CURVE_PIECE_SIZE = self.STRAIGHT_PIECE_LENGTH

    def append(self, track_piece: TrackPieceType):
        self.piece_list.append(self._get_track_piece(track_piece))
        return self

    def build(self) -> FullTrack:
        return FullTrack(self.piece_list)

    # This isn't the best way but it works for now
    def _get_track_piece(self, track_piece_type: TrackPieceType) -> TrackPiece:
        match track_piece_type:
            case TrackPieceType.STRAIGHT_SN:
                return StraightPiece(self.STRAIGHT_PIECE_LENGTH, self.STRAIGHT_PIECE_DIAMETER, 0)
            case TrackPieceType.STRAIGHT_WE:
                return StraightPiece(self.STRAIGHT_PIECE_LENGTH, self.STRAIGHT_PIECE_DIAMETER, 90)
            case TrackPieceType.STRAIGHT_NS:
                return StraightPiece(self.STRAIGHT_PIECE_LENGTH, self.STRAIGHT_PIECE_DIAMETER, 180)
            case TrackPieceType.STRAIGHT_EW:
                return StraightPiece(self.STRAIGHT_PIECE_LENGTH, self.STRAIGHT_PIECE_DIAMETER, 270)
            case TrackPieceType.CURVE_NW:
                return CurvedPiece(self.CURVE_PIECE_SIZE, 0, False)
            case TrackPieceType.CURVE_EN:
                return CurvedPiece(self.CURVE_PIECE_SIZE, 90, False)
            case TrackPieceType.CURVE_SE:
                return CurvedPiece(self.CURVE_PIECE_SIZE, 180, False)
            case TrackPieceType.CURVE_WS:
                return CurvedPiece(self.CURVE_PIECE_SIZE, 270, False)

            # Mirrored
            case TrackPieceType.CURVE_ES:
                return CurvedPiece(self.CURVE_PIECE_SIZE, 0, True)
            case TrackPieceType.CURVE_SW:
                return CurvedPiece(self.CURVE_PIECE_SIZE, 90, True)
            case TrackPieceType.CURVE_WN:
                return CurvedPiece(self.CURVE_PIECE_SIZE, 180, True)
            case TrackPieceType.CURVE_NE:
                return CurvedPiece(self.CURVE_PIECE_SIZE, 270, True)
