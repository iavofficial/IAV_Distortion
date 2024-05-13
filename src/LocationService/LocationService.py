import time
import math
from typing import Tuple
from threading import Event, Thread

from LocationService.Trigo import Position, Angle
from LocationService.Track import FullTrack


class LocationService():
    def __init__(self, track: FullTrack, starting_offset: float = 0, simulation_ticks_per_second: int = 24, start_immeaditly: bool = False):
        """
        Init the location service
        track: List of all Track Pieces
        simulation_ticks_per_second: how many steps should be ran per second. A higher value
            increases accuracy and the required CPU time
        """
        self.__MAX_USED_DISTANCE_FOR_OFFSET_PERCENT = 0.30
        self._simulation_ticks_per_second = simulation_ticks_per_second

        # TODO: Protect these with a Mutex for thread safety
        self._actual_speed: float = 0
        self._target_speed: float = 0
        self._acceleration: float = 0
        self._actual_offset: float = 0
        self._target_offset: float = 0

        self._track: FullTrack = track
        self._current_piece_index: int = 0
        self._progress_on_current_piece: float = 0
        first_piece, _ = self._track.get_entry_tupel(0)
        _, self._current_position = first_piece.process_update(0, 0, starting_offset)

        self._stop_event: Event = Event()
        self._simulation_thread: Thread | None = None

        if start_immeaditly:
            self.start()

    def set_speed(self, speed: int, acceleration: int = 1000):
        """
        Updates the target speed of the car
        speed: targeted speed in mm/s
        acceleration: used acceleration in mm/s^2
        """
        self._target_speed = speed
        self._acceleration = acceleration

    def set_offset(self, offset: float):
        """
        Sets the targeted offset where the car should drive
        """
        self._target_offset = offset

    def _adjust_speed(self):
        """
        Updates internal speed values for the simulation based on the acceleration
        """
        if self._actual_speed < self._target_speed:
            self._actual_speed += self._acceleration / self._simulation_ticks_per_second

        # TODO: Use better slowdown approach
        if self._actual_speed > self._target_speed:
            self._actual_speed = self._target_speed

    def _adjust_offset(self, travel_distance: float) -> float:
        """
        Changes the current offset to get closer to the target based on the
        traveled distance.
        returns: leftover distance that can be traveled straight
        """
        needed_offset = abs(self._actual_offset - self._target_offset)
        max_change = self.__MAX_USED_DISTANCE_FOR_OFFSET_PERCENT * travel_distance
        change = max_change
        if max_change > needed_offset:
            change = needed_offset

        if needed_offset < change:
            change = needed_offset
        if self._target_offset > self._actual_offset:
            self._actual_offset += change
        else:
            self._actual_offset -= change

        # use pythagoras for more accuracy
        remaining_way = math.sqrt(travel_distance * travel_distance - change * change)
        return remaining_way

    def _run_simulation_step(self, distance: float | None = None) -> Tuple[Position, Angle]:
        """
        Advance the simulation one simulation step. Should be called all 1/TICKS_PER_SECOND
        seconds. If distance is None the speed will be used to determine the distance. Can be
        overwritten by giving a distance argument
        returns: The new position and the Angle where the car is pointing
        """
        old_pos = self._current_position
        # if distance is not given we were called normally. If distance is given we were called
        # recursively and don't need to get the distance and adjust the offset again
        if distance is None:
            self._adjust_speed()
            distance = self._adjust_offset(self._actual_speed / self._simulation_ticks_per_second)
        piece, global_track_offset = self._track.get_entry_tupel(self._current_piece_index)
        leftover_distance, new_pos = piece.process_update(self._progress_on_current_piece, distance, self._actual_offset)
        self._progress_on_current_piece += distance
        if leftover_distance != 0:
            self._current_piece_index += 1
            self._progress_on_current_piece = 0
            if self._current_piece_index >= self._track.get_len():
                self._current_piece_index = 0
            return self._run_simulation_step(leftover_distance)
        self._current_position = new_pos + global_track_offset
        return (self._current_position, self._current_position.calculate_angle_to(old_pos))

    def _run_task(self):
        """
        Runs the simulation asynchronously in an own thread
        """
        while not self._stop_event.is_set():
            # TODO: publish position and rotation via callback or similar
            pos, rot = self._run_simulation_step()
            time.sleep(1 / self._simulation_ticks_per_second)

    def start(self):
        """
        Start the thread that's responsible for the simulation
        """
        if self._simulation_thread is not None:
            # TODO: Log error that the location service is already running!
            return
        self._stop_event.clear()
        # TODO: Check if Flask-SocketIO's start_background_task is needed here
        self._simulation_thread = Thread(target=self._run_task)
        self._simulation_thread.start()

    def stop(self):
        """
        Stops the thread that's responsible for the simulation
        """
        if self._simulation_thread is None:
            # TODO: Log that it was attempted to stop a stopped LocationService!
            return
        self._stop_event.set()
        self._simulation_thread.join()
        self._simulation_thread = None
