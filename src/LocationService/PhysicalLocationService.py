from typing import List, Tuple

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
        self._BLE_LATENCY_CORRECTION = 0.05

        # alpha filter to smoothen the correcture
        self._speed_correcture: float = 0
        self._ALPHA_VALUE = 0.5

        # list that tracks the history of pieces so we can figure out the position even when there are duplicate IDs
        # It always has a int or None for indices that are also in the track
        self._piece_history: List[int | None] = list()
        self._piece_history_index: int = 0
        self._reset_piece_history()

    # overwritten method to implement a speed correcture based on the sent data
    def _adjust_speed_to(self, target_speed: float) -> None:
        new_speed = target_speed + self._speed_correcture
        # we don't want to apply speed correctures here since they break the expected behaviour
        if self._uturn_override is not None or target_speed < 10:
            return super()._adjust_speed_to(target_speed)
        # prevent negative values since the speed needs to always be a positive value
        if new_speed < 0:
            return super()._adjust_speed_to(0)

        return super()._adjust_speed_to(new_speed)

    # ignore offset change requests and only use car values
    async def set_offset_int(self, offset: int) -> None:
        _ = offset
        return

    def _notification_offset_to_internal_offset(self, offset: float) -> float:
        return offset * -1 * self._direction_mult

    def notify_transition_event(self, offset: float) -> None:
        """
        Function that should be called when a physical car sent a transition event message
        """
        self._piece_history_index = (self._piece_history_index + self._direction_mult) % self._track.get_len()
        if self._physical_piece is None:
            return
        # offset in a simulation format
        internal_offset = self._notification_offset_to_internal_offset(offset)
        piece_index = (self._physical_piece + self._direction_mult) % self._track.get_len()

        self._target_offset = internal_offset
        self._physical_piece = piece_index

        simulation_difference: float
        if self._direction_mult == 1:
            simulation_difference = self._calculate_distance_to_position(piece_index,
                                                                         self._actual_speed
                                                                         * self._BLE_LATENCY_CORRECTION)
        else:
            piece, _ = self._track.get_entry_tupel(piece_index)
            simulation_difference = self._calculate_distance_to_position(piece_index,
                                                                         piece.get_length(internal_offset)
                                                                         - self._actual_speed
                                                                         * self._BLE_LATENCY_CORRECTION)

        self._speed_correcture = (simulation_difference * self._ALPHA_VALUE) +\
                                 ((1 - self._ALPHA_VALUE) * self._speed_correcture)

    def notify_location_event(self, piece: int, location: int, offset: float, speed: int) -> None:
        """
        Function that should be called when a physical car sent a location event
        """
        offset = self._notification_offset_to_internal_offset(offset)
        self._target_offset = offset
        self._target_speed = speed

        if not self._track.contains_physical_piece(piece):
            self.logger.warn(
                "Couldn't find a piece matching the physical ID %d we got from the location event. Ignoring it", piece)
            return

        old_piece: int | None = self._piece_history[self._piece_history_index]
        if old_piece is not None and old_piece != piece:
            self.logger.warn("The piece history had another piece in this position. Clearing the list!")
            self._reset_piece_history()

        self._piece_history[self._piece_history_index] = piece

        self._find_physical_location()

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

    def _reset_piece_history(self) -> None:
        """
        Resets the own piece_history list to have None in every position
        to avoid out of bounds exceptions
        """
        self._piece_history.clear()
        for _ in range(0, self._track.get_len()):
            self._piece_history.append(None)

    def _find_physical_location(self) -> None:
        """
        Matches the piece history with the track piece IDs to figure out where we are
        on the track
        """
        # the bool stands for whether it was found while seraching in the opposite direction
        possible_start_indices: List[Tuple[int, bool]] = list()
        track_len = self._track.get_len()

        for starting_offset in range(0, track_len):
            if self._test_history_matches_track_with_offset(starting_offset, 1):
                possible_start_indices.append((starting_offset, False))
            if self._test_history_matches_track_with_offset(starting_offset, -1):
                possible_start_indices.append((starting_offset, True))

        if len(possible_start_indices) == 1:
            index, direction = possible_start_indices[0]
            self._physical_piece = (self._piece_history_index + index) % track_len
            if direction:
                self._direction_mult *= -1
                self._piece_history.reverse()
                self._piece_history_index = self._track.get_len() - self._piece_history_index
                self._physical_piece = self._track.get_len() - self._physical_piece
            return

        if len(possible_start_indices) == 0:
            self.logger.warn("The piece history doesn't match the track with any offset. Resetting the piece history")
            self._reset_piece_history()
            return

        self.logger.info("Didn't get enough data to determine the physical position yet. "
                         "Number of possible starting points: %d", len(possible_start_indices))

    def _test_history_matches_track_with_offset(self, offset: int, counting_direction: int) -> bool:
        """
        Test whether the piece history matches the track at every point when using a certain offset.
        Missing pieces in the piece history are ignored and considered matching
        """
        track_len = self._track.get_len()
        for i in range(0, track_len):
            track_index: int
            track_index = (i * counting_direction + offset) % track_len
            track_piece, _ = self._track.get_entry_tupel(track_index)
            history_id: int
            history_id = self._piece_history[i]
            if history_id is not None and track_piece.get_physical_id() != self._piece_history[i]:
                return False
        return True
