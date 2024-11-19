from typing import List, Tuple, Dict, Any
import math

from LocationService.Track import Direction, FullTrack, TrackPiece, TrackPieceType
from LocationService.Trigo import Position, Angle, Distance


class StraightPiece(TrackPiece):
    def __init__(self, length: float, diameter: float, rotation: int, physical_id: int | None = None):
        super().__init__(rotation, physical_id=physical_id)
        if rotation == 0 or rotation == 180:
            self._horiz_length: float = diameter
            self._vert_length: float = length
        else:
            self._horiz_length = length
            self._vert_length = diameter

        self._length = length
        self._diameter = diameter

    def get_used_space_vert(self) -> float:
        return self._vert_length

    def get_used_space_horiz(self) -> float:
        return self._horiz_length

    def get_outgoing_offset(self) -> Distance:
        match self._rotation.get_deg():
            case 0.0:
                return Distance(0, -self._vert_length / 2)
            case 90.0:
                return Distance(self._horiz_length / 2, 0)
            case 180.0:
                return Distance(0, self._vert_length / 2)
            case 270.0:
                return Distance(-self._horiz_length / 2, 0)
            case _:
                raise NotImplementedError

    def get_incoming_offset(self) -> Distance:
        return self.get_outgoing_offset()

    def get_outgoing_direction(self) -> Direction:
        match self._rotation.get_deg():
            case 0.0:
                return Direction.NORTH
            case 90.0:
                return Direction.EAST
            case 180.0:
                return Direction.SOUTH
            case 270.0:
                return Direction.WEST
            case _:
                raise NotImplementedError

    def get_incoming_direction(self) -> Direction:
        match self._rotation.get_deg():
            case 0.0:
                return Direction.SOUTH
            case 90.0:
                return Direction.WEST
            case 180.0:
                return Direction.NORTH
            case 270.0:
                return Direction.EAST
            case _:
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

    def get_progress_based_on_location(self, location: int, offset: float) -> float:
        return self.get_length(offset) * 0.25 * (3 - location % 3)

    def to_html_dict(self) -> dict[str, str | dict[str,float]]:
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

    def to_json_dict(self) -> Dict[str, Any]:
        orig = super().to_json_dict()
        orig.update({
            'length': self._length,
            'diameter': self._diameter
        })
        return orig


class CurvedPiece(TrackPiece):
    def __init__(self, square_size: float, diameter: int, rot: int, mirror: bool, physical_id: int | None =None):
        super().__init__(rot, physical_id=physical_id)
        self._size = square_size
        self._radius = square_size / 2
        self._diameter = diameter
        self._is_mirrored = mirror

    def get_used_space_horiz(self) -> float:
        return self._size

    def get_used_space_vert(self) -> float:
        return self._size

    def get_outgoing_offset(self) -> Distance:
        match self.get_outgoing_direction():
            case Direction.NORTH:
                return Distance(0, -self._size / 2)
            case Direction.WEST:
                return Distance(-self._size / 2, 0)
            case Direction.SOUTH:
                return Distance(0, self._size / 2)
            case Direction.EAST:
                return Distance(self._size / 2, 0)
        raise NotImplementedError

    def get_incoming_offset(self) -> Distance:
        match self.get_incoming_direction():
            case Direction.NORTH:
                return Distance(0, self._size / 2)
            case Direction.WEST:
                return Distance(self._size / 2, 0)
            case Direction.SOUTH:
                return Distance(0, -self._size / 2)
            case Direction.EAST:
                return Distance(-self._size / 2, 0)
        raise NotImplementedError

    def get_outgoing_direction(self) -> Direction:
        if not self._is_mirrored:
            match self._rotation.get_deg():
                case 0:
                    return Direction.WEST
                case 90:
                    return Direction.NORTH
                case 180:
                    return Direction.EAST
                case 270:
                    return Direction.SOUTH
                case _:
                    raise NotImplementedError
        else:
            match self._rotation.get_deg():
                case 0:
                    return Direction.SOUTH
                case 90:
                    return Direction.WEST
                case 180:
                    return Direction.NORTH
                case 270:
                    return Direction.EAST
                case _:
                    raise NotImplementedError

    def get_incoming_direction(self) -> Direction:
        if not self._is_mirrored:
            match self._rotation.get_deg():
                case 0:
                    return Direction.NORTH
                case 90:
                    return Direction.EAST
                case 180:
                    return Direction.SOUTH
                case 270:
                    return Direction.WEST
                case _:
                    raise NotImplementedError
        else:
            match self._rotation.get_deg():
                case 0:
                    return Direction.EAST
                case 90:
                    return Direction.SOUTH
                case 180:
                    return Direction.WEST
                case 270:
                    return Direction.NORTH
                case _:
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
        if self._is_mirrored:
            offset *= -1
        distance_to_middle = self._radius + offset
        position = Position(distance_to_middle * angle.get_x_mult(), distance_to_middle * angle.get_y_mult())
        position.add_offset(-self._size / 2, -self._size / 2)
        if self._is_mirrored:
            position = Position(position.get_y() * -1, position.get_x() * -1)
        position.rotate_around_0_0(self._rotation)
        return (left, position)

    def get_length(self, offset: float) -> float:
        if self._is_mirrored:
            offset *= -1
        return (self._radius + offset) * math.pi / 2

    def get_equivalent_progress_for_offset(self, old_offset: float, new_offset: float, old_progress: float) -> float:
        percent = old_progress / self.get_length(old_offset)
        return percent * self.get_length(new_offset)

    def get_progress_based_on_location(self, location: int, offset: float) -> float:
        if location < 20:
            return 0.33 * (2 - location % 2) * self.get_length(offset)
        return 0.25 * (3 - (location - 20) % 3) * self.get_length(offset)

    def to_html_dict(self) -> dict[str, str | int | float | dict[str,float]]:
        start_angle: int = int(self._rotation.get_deg())
        if self._is_mirrored:
            start_angle = (start_angle + 180) % 360
        point: Position = Position(-self._size / 2, -self._size / 2)
        if self._is_mirrored:
            point.rotate_around_0_0(Angle(180))
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

    def __eq__(self, other: 'TrackPiece'):
        return super().__eq__(other) and self._is_mirrored == other._is_mirrored

    def to_json_dict(self) -> Dict[str, Any]:
        orig = super().to_json_dict()
        orig.update({
            'square_size': self._size,
            'diameter': self._diameter,
            'mirrored': self._is_mirrored
        })
        return orig


class StartPieceBeforeLine(StraightPiece):
    """
    Class that represents the part of a start piece before the line
    """
    def get_progress_based_on_location(self, location: int, offset: float) -> float:
        return 0.33 * (2 - location % 2) * self.get_length(offset)


class StartPieceAfterLine(StraightPiece):
    """
    Class that represents the part of a start piece after the line (including the line itself)
    """
    def __init__(self, length: float, diameter: float, rotation: int, start_line_width: int, physical_id: int | None =None):
        super().__init__(length, diameter, rotation, physical_id)
        self._start_line_width = start_line_width

    def get_progress_based_on_location(self, location: int, offset: float) -> float:
        _ = location
        _ = offset
        return 0.5 * self.get_length(offset)

    def to_html_dict(self) -> dict[str, str | dict[str, float]]:
        startline_start = Position(self._diameter / 2, self._length / 2 - self._start_line_width / 2)
        startline_end = Position(-self._diameter / 2, self._length / 2 - self._start_line_width / 2)
        startline_start.rotate_around_0_0(self._rotation)
        startline_end.rotate_around_0_0(self._rotation)
        orig = super().to_html_dict()
        orig.update({
            'start_line_start': {
                'x': startline_start.get_x(),
                'y': startline_start.get_y()
            },
            'start_line_end': {
                'x': startline_end.get_x(),
                'y': startline_end.get_y()
            }
        })
        return orig

    def to_json_dict(self) -> Dict[str, Any]:
        orig = super().to_json_dict()
        orig.update({
            'start_line_width': self._start_line_width
        })
        return orig


class TrackBuilder():
    """
    Class to build an entire track by chaining append() calls with the desired direction
    and finally build()
    """
    def __init__(self):
        self.piece_list: List[TrackPiece] = []
        # Constants
        self.STRAIGHT_PIECE_LENGTH = 559
        self.PIECE_DIAMETER = 184
        # This should be the same as STRAIGHT_PIECE_LENGTH to match the real pieces closely
        self.CURVE_PIECE_SIZE = self.STRAIGHT_PIECE_LENGTH
        self.START_PIECE_BEFORE_LINE_LENGTH = 349
        # The after line part contains the line itself
        self.START_PIECE_AFTER_LINE_LENGTH = 210
        self.START_LINE_WIDTH = 21

    def append(self, track_piece: TrackPieceType, physical_id: int | None =None):
        """
        Append a piece to the track. Whether the direction are right
        *aren't* checked!
        """
        piece = self._get_track_piece(track_piece)
        piece.set_physical_id(physical_id)
        self.piece_list.append(piece)
        return self

    def build(self) -> FullTrack:
        """
        Converts the internally saved track to a FullTrack object
        """
        return FullTrack(self.piece_list)

    # This isn't the best way but it works for now
    def _get_track_piece(self, track_piece_type: TrackPieceType) -> TrackPiece:
        """
        Internal function to quickly get the correct TrackPiece based on it's type
        """
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

            # start piece first part
            case TrackPieceType.START_PIECE_BEFORE_LINE_SN:
                return StartPieceBeforeLine(self.START_PIECE_BEFORE_LINE_LENGTH, self.PIECE_DIAMETER, 0)
            case TrackPieceType.START_PIECE_BEFORE_LINE_WE:
                return StartPieceBeforeLine(self.START_PIECE_BEFORE_LINE_LENGTH, self.PIECE_DIAMETER, 90)
            case TrackPieceType.START_PIECE_BEFORE_LINE_NS:
                return StartPieceBeforeLine(self.START_PIECE_BEFORE_LINE_LENGTH, self.PIECE_DIAMETER, 180)
            case TrackPieceType.START_PIECE_BEFORE_LINE_EW:
                return StartPieceBeforeLine(self.START_PIECE_BEFORE_LINE_LENGTH, self.PIECE_DIAMETER, 270)

            # start piece second part
            case TrackPieceType.START_PIECE_AFTER_LINE_SN:
                return StartPieceAfterLine(self.START_PIECE_AFTER_LINE_LENGTH, self.PIECE_DIAMETER, 0,
                                           self.START_LINE_WIDTH)
            case TrackPieceType.START_PIECE_AFTER_LINE_WE:
                return StartPieceAfterLine(self.START_PIECE_AFTER_LINE_LENGTH, self.PIECE_DIAMETER, 90,
                                           self.START_LINE_WIDTH)
            case TrackPieceType.START_PIECE_AFTER_LINE_NS:
                return StartPieceAfterLine(self.START_PIECE_AFTER_LINE_LENGTH, self.PIECE_DIAMETER, 180,
                                           self.START_LINE_WIDTH)
            case TrackPieceType.START_PIECE_AFTER_LINE_EW:
                return StartPieceAfterLine(self.START_PIECE_AFTER_LINE_LENGTH, self.PIECE_DIAMETER, 270,
                                           self.START_LINE_WIDTH)
