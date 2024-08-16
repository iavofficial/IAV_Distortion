from typing import List, Dict, Any

from LocationService.Track import FullTrack, TrackPiece
from LocationService.TrackPieces import StraightPiece, CurvedPiece, StartPieceBeforeLine, StartPieceAfterLine


class PieceDecodingException(BaseException):
    pass


def full_track_to_list_of_dicts(track: FullTrack) -> List[Dict[str, Any]]:
    """
    Converts a track to a list that consists of dictionaries that each represent a track piece
    """
    ret: List[Dict[str, Any]] = list()
    for entry in track.track_entries:
        piece = entry.get_piece()
        ret.append(piece.to_json_dict())
    return ret


def parse_list_of_dicts_to_full_track(input_list: List[Dict[str, Any]]) -> FullTrack:
    """
    Tries to parse a list of dictionaries to a FullTrack. This can raise a PieceDecodingException
    """
    parsed_list: List[TrackPiece] = list()
    for piece_dict in input_list:
        piece = construct_piece_from_dict(piece_dict)
        parsed_list.append(piece)
    return FullTrack(parsed_list)


def get_dict_attribute(search_dict: Dict[str, Any], searched_property: str) -> Any:
    """
    Gets an attribute of a dict. If the attribute isn't in the dict a PieceDecodingException is raised
    """
    val = search_dict.get(searched_property)
    if val is None:
        raise PieceDecodingException(f'Error decoding a piece. Needed property {searched_property} does not exist!')
    return val


def construct_piece_from_dict(piece_dict: Dict[str, Any]) -> TrackPiece:
    """
    Constructs a piece from a dict. If a needed value is missing or has another problem a PieceDecodingException
    is raised
    """
    piece_type = get_dict_attribute(piece_dict, 'type')
    rotation = get_dict_attribute(piece_dict, 'rotation')
    physical_id = piece_dict.get('physical_id')
    diameter = get_dict_attribute(piece_dict, 'diameter')

    match piece_type:
        case 'LocationService.TrackPieces.StraightPiece':
            length = get_dict_attribute(piece_dict, 'length')
            return StraightPiece(length, diameter, rotation, physical_id)

        case 'LocationService.TrackPieces.CurvedPiece':
            square_size = get_dict_attribute(piece_dict, 'square_size')
            is_mirrored = get_dict_attribute(piece_dict, 'mirrored')
            return CurvedPiece(square_size, diameter, rotation, is_mirrored, physical_id)

        case 'LocationService.TrackPieces.StartPieceBeforeLine':
            length = get_dict_attribute(piece_dict, 'length')
            return StartPieceBeforeLine(length, diameter, rotation, physical_id)

        case 'LocationService.TrackPieces.StartPieceAfterLine':
            length = get_dict_attribute(piece_dict, 'length')
            start_line_width = get_dict_attribute(piece_dict, 'start_line_width')
            return StartPieceAfterLine(length, diameter, rotation, start_line_width, physical_id)

    raise PieceDecodingException('Piece had invalid type value')
