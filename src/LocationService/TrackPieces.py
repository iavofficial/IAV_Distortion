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
        # handle the car driving more than the piece is long
        if end >= self._length:
            left = end - self._length
            end = self._length
        elif end <= 0:
            left = end
            end = 0

        endposition = Position(-offset, self._length / 2 - end)
        endposition.rotate_around_0_0(self._rotation)

        return (left, endposition)

    def get_length(self, offset: float) -> float:
        return self._length

    def get_equivalent_progress_for_offset(self, old_offset: float, new_offset: float, old_progress: float) -> float:
        return old_progress

    def to_dict(self) -> dict:
        line_1_start = Position(-self._diameter / 2, -self._length / 2)
        line_1_end = Position(-self._diameter / 2, self._length / 2)
        line_1_start.rotate_around_0_0(self._rotation)
        line_1_end.rotate_around_0_0(self._rotation)

        line_2_start = Position(self._diameter / 2, -self._length / 2)
        line_2_end = Position(self._diameter / 2, self._length / 2)
        line_2_start.rotate_around_0_0(self._rotation)
        line_2_end.rotate_around_0_0(self._rotation)

        return {

            'type': 'straight_piece',
            'rotation': str(self._rotation),
            'line_1_start': {
                'x': line_1_start.get_x(),
                'y': line_1_start.get_y()
            },
            'line_1_end': {
                'x': line_1_end.get_x(),
                'y': line_1_end.get_y()
            },
            'line_2_start': {
                'x': line_2_start.get_x(),
                'y': line_2_start.get_y()
            },
            'line_2_end': {
                'x': line_2_end.get_x(),
                'y': line_2_end.get_y()
            }
        }

class CurvedPiece(TrackPiece):
    def __init__(self, square_size, diameter: int, rot: int, mirror: bool):
        super().__init__(rot)
        self._size = square_size
        self._radius = square_size / 2
        self._diameter = diameter
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
        travel_len = self.get_length(offset)
        # handle the car driving more than the piece is long
        if end >= travel_len:
            left = end - travel_len
            end = travel_len
        elif end <= 0:
            left = end
            end = 0
        progress = end / travel_len
        angle = Angle(progress * 90)
        distance_to_middle = self._radius + offset
        position = Position(distance_to_middle * angle.get_x_mult(), distance_to_middle * angle.get_y_mult())
        position.add_offset(-self._size / 2, -self._size / 2)
        if self._is_mirrored:
            position = Position(position.get_x() * -1, position.get_y() * -1)
        position.rotate_around_0_0(self._rotation)
        return (left, position)

    def get_length(self, offset: float) -> float:
        return (self._radius + offset) * math.pi / 2

    def get_equivalent_progress_for_offset(self, old_offset: float, new_offset: float, old_progress: float) -> float:
        percent = old_progress / self.get_length(old_offset)
        return percent * self.get_length(new_offset)

    def to_dict(self) -> dict:
        start_angle: int = int(self._rotation.get_deg())
        point: Position = Position(-self._size / 2, -self._size / 2)
        point.rotate_around_0_0(self._rotation)
        radius_1: float = self._radius - self._diameter / 2
        radius_2: float = self._radius + self._diameter / 2
        return {
            'type': 'curved_piece',
            'start_angle': start_angle,
            'radius_1': radius_1,
            'radius_2': radius_2,
            'point': {
                'x': point.get_x(),
                'y': point.get_y()
            }
        }


class TrackBuilder():
    """
    Class to build an entire track by chaining append() calls with the desired direction
    """
    def __init__(self):
        self.piece_list: List[TrackPiece] = [] 
        # Constants
        self.STRAIGHT_PIECE_LENGTH = 559
        self.PIECE_DIAMETER = 184
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
            # Straight
            case TrackPieceType.STRAIGHT_SN:
                return StraightPiece(self.STRAIGHT_PIECE_LENGTH, self.PIECE_DIAMETER, 0)
            case TrackPieceType.STRAIGHT_WE:
                return StraightPiece(self.STRAIGHT_PIECE_LENGTH, self.PIECE_DIAMETER, 90)
            case TrackPieceType.STRAIGHT_NS:
                return StraightPiece(self.STRAIGHT_PIECE_LENGTH, self.PIECE_DIAMETER, 180)
            case TrackPieceType.STRAIGHT_EW:
                return StraightPiece(self.STRAIGHT_PIECE_LENGTH, self.PIECE_DIAMETER, 270)

            # Curve
            case TrackPieceType.CURVE_NW:
                return CurvedPiece(self.CURVE_PIECE_SIZE, self.PIECE_DIAMETER, 0, False)
            case TrackPieceType.CURVE_EN:
                return CurvedPiece(self.CURVE_PIECE_SIZE, self.PIECE_DIAMETER, 90, False)
            case TrackPieceType.CURVE_SE:
                return CurvedPiece(self.CURVE_PIECE_SIZE, self.PIECE_DIAMETER, 180, False)
            case TrackPieceType.CURVE_WS:
                return CurvedPiece(self.CURVE_PIECE_SIZE, self.PIECE_DIAMETER, 270, False)

            # Mirrored
            case TrackPieceType.CURVE_ES:
                return CurvedPiece(self.CURVE_PIECE_SIZE, self.PIECE_DIAMETER, 0, True)
            case TrackPieceType.CURVE_SW:
                return CurvedPiece(self.CURVE_PIECE_SIZE, self.PIECE_DIAMETER,  90, True)
            case TrackPieceType.CURVE_WN:
                return CurvedPiece(self.CURVE_PIECE_SIZE, self.PIECE_DIAMETER, 180, True)
            case TrackPieceType.CURVE_NE:
                return CurvedPiece(self.CURVE_PIECE_SIZE, self.PIECE_DIAMETER, 270, True)
