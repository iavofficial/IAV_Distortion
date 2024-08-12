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
            return

        new_piece, _ = self._track.get_entry_tupel(piece_index)
        self._physical_piece = piece_index

    def _calculate_distance_to_position(self, other_index: int, other_progress: float) -> float:
        """
        Calculates the difference between the simulation and another given position.
        A positive value means the simulation is in front of the other position. A negative value means the simulation
        is behind of the other position
        """
        if self._current_piece_index == other_index:
            return self._calculate_distance_on_same_piece(other_progress)

        forward_distance = self._calculate_distance_to_position_forward(other_index, other_progress)
        backward_distance = self._calculate_distance_to_position_backward(other_index, other_progress)

        # return smaller
        if abs(forward_distance) > abs(backward_distance):
            return backward_distance
        return forward_distance

    def _calculate_distance_to_position_forward(self, other_index: int, other_progress: float) -> float:
        """
        Calculate the distance to another position in the driving direction. The result signs are the same as in
        `_calculate_distance_to_position`
        """
        # progress on own piece
        diff: float
        if self._direction_mult == 1:
            diff = self._calculate_distance_to_end(self._current_piece_index, self._progress_on_current_piece)
        else:
            diff = self._calculate_distance_from_start(self._progress_on_current_piece)

        # add full length of all pieces between
        i = self._current_piece_index
        while True:
            i = (i + self._direction_mult) % self._track.get_len()
            if i == other_index:
                break
            piece, _ = self._track.get_entry_tupel(i)
            diff += piece.get_length(self._actual_offset)

        # add progress of the other car
        if self._direction_mult == 1:
            diff += self._calculate_distance_from_start(other_progress)
        else:
            diff += self._calculate_distance_to_end(i, other_progress)

        return diff

    # TODO: Check redundancy with _calculate_distance_to_position_forward
    def _calculate_distance_to_position_backward(self, other_index: int, other_progress: float) -> float:
        """
        Calculate the distance to another position against the driving direction. The result signs are the same as in
        `_calculate_distance_to_position`
        """
        # progress on own piece
        diff: float
        if self._direction_mult == 1:
            diff = self._calculate_distance_from_start(self._progress_on_current_piece)
        else:
            diff = self._calculate_distance_to_end(self._current_piece_index, self._progress_on_current_piece)

        # add full length of all pieces between
        i = self._current_piece_index
        while True:
            i = (i - self._direction_mult) % self._track.get_len()
            if i == other_index:
                break
            piece, _ = self._track.get_entry_tupel(i)
            diff += piece.get_length(self._actual_offset)

        # add progress of the other car
        if self._direction_mult == 1:
            diff += self._calculate_distance_to_end(i, other_progress)
        else:
            diff += self._calculate_distance_from_start(other_progress)
        return diff * -1

    def _calculate_distance_on_same_piece(self, other_position: float) -> float:
        """
        Calculates the distance to another position assuming we are on the same piece. The result signs are the same as
        in `_calculate_distance_to_position`
        """
        return (other_position - self._progress_on_current_piece) * self._direction_mult

    def _calculate_distance_from_start(self, progress: float):
        """
        Calculates how far the car is on the current piece. This function only returns its argument and exists
        purely for code readability
        """
        _ = self
        return progress

    def _calculate_distance_to_end(self, piece_index: int, progress: float) -> float:
        """
        Calculates how far the car is away from the end of a piece
        """
        piece, _ = self._track.get_entry_tupel(piece_index)
        return piece.get_length(self._actual_offset) - progress
