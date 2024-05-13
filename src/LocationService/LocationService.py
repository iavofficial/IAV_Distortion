import time
import math
from typing import Tuple
from threading import Event, Lock, Thread

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

        # Taken from AnkiController
        # TODO: Put this in a more central place where both the controller and the LocationService can get it
        self.__MAX_ANKI_SPEED = 1200
        self.__LANE_OFFSET = 22.25

        self._value_mutex: Lock = Lock()
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
        Updates the target speed of the car.
        Thread-safe
        speed: targeted speed in percent
        acceleration: used acceleration in mm/s^2
        """
        with self._value_mutex:
            self._target_speed = self.__MAX_ANKI_SPEED * speed / 100
            self._acceleration = acceleration

    def set_offset(self, offset: int):
        """
        Sets the targeted offset where the car should drive.
        Thread-safe
        offset: target offset where the car should drive (as int like
                in the AnkiController)
        """
        with self._value_mutex:
            # TODO: This doesn't check for out of bounds driving
            self._target_offset = self.__LANE_OFFSET * offset

    def _adjust_speed(self):
        """
        Updates internal speed values for the simulation based on the acceleration.
        Not Thread-safe
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
        Not Thread-safe
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

    def _run_simulation_step_threadsafe(self) -> Tuple[Position, Angle]:
        """
        Runs a single simulation step by calling _run_simulation_step internally.
        Thread-safe
        returns: The new position and the Angle where the car is pointing
        """
        with self._value_mutex:
            self._adjust_speed()
            trav_distance = self._adjust_offset(self._actual_speed / self._simulation_ticks_per_second)
            return self._run_simulation_step(trav_distance)

    def _run_simulation_step(self, distance: float) -> Tuple[Position, Angle]:
        """
        Advance the simulation one step without threadsafety. Should only be called
        internally.
        distance: Distance to travel
        returns: The new position and the Angle where the car is pointing
        """
        old_pos = self._current_position
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
            pos, rot = self._run_simulation_step_threadsafe()
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
