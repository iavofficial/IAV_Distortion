import random

from LocationService.Track import FullTrack, TrackEntry
from LocationService.Trigo import Position


class Item:
    def __init__(self, track: FullTrack | None):
        self.position: Position | None = None
        if track is not None:
            self.generate_new_position(track)

    def generate_new_position(self, track: FullTrack):
        random_entry: TrackEntry = random.choice(track.track_entries)
        piece_offset = random_entry.get_global_offset()
        _, piece_position = random_entry.get_piece().process_update(0, 0, 0)
        self.position = piece_offset + piece_position

    def get_position(self) -> Position:
        return self.position
