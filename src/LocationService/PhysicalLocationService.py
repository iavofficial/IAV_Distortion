from LocationService.LocationService import LocationService
from LocationService.Track import FullTrack


class PhysicalLocationService(LocationService):
    def __init__(self,
                 track: FullTrack,
                 starting_offset: float = 0,
                 simulation_ticks_per_second: int = 24,
                 start_immediately: bool = False):
        super().__init__(track, starting_offset, simulation_ticks_per_second, start_immediately)
        # watch piece indices from location events separately so it doesn't get changed by the default location service
        self._physical_piece: int | None = None
        # amount of time the BLE message should take. Based on that additional travelling distance will be added to
        self._BLE_LATENCY_CORRECTION = 0.1

    def _notification_offset_to_internal_offset(self, offset: float) -> float:
        return offset * -1 * self._direction_mult

    def notify_transition_event(self, offset: float) -> None:
        """
        Function that should be called when a physical car sent a transition event message
        """
        if self._physical_piece is None:
            return
        # offset in a simulation format
        internal_offset = self._notification_offset_to_internal_offset(offset)
        piece_index = (self._physical_piece + self._direction_mult) % self._track.get_len()

        self._target_offset = internal_offset
        self._physical_piece = piece_index
        self._current_piece_index = piece_index

        if self._direction_mult == 1:
            self._progress_on_current_piece = 0
        else:
            new_piece, _ = self._track.get_entry_tupel(self._current_piece_index)
            self._progress_on_current_piece = new_piece.get_length(internal_offset)

        self._run_simulation_step(self._actual_speed * self._BLE_LATENCY_CORRECTION * self._direction_mult)

    def notify_location_event(self, piece: int, location: int, offset: float, speed: int) -> None:
        """
        Function that should be called when a physical car sent a location event
        """
        offset = self._notification_offset_to_internal_offset(offset)
        self._target_offset = offset
        self._target_speed = speed

        piece_index = self._track.find_piece_index_with_physical_id(piece)
        if piece_index is None:
            self.logger.warn(
                "Couldn't find a piece matching the physical ID %d we got from the location event. Ignoring it", piece)

        new_piece, _ = self._track.get_entry_tupel(piece_index)
        self._physical_piece = piece_index
        self._current_piece_index = piece_index

        self._progress_on_current_piece = new_piece.get_progress_based_on_location(location, offset)

        self._run_simulation_step(self._actual_speed * self._BLE_LATENCY_CORRECTION * self._direction_mult)
