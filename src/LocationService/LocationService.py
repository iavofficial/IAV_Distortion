import time
import math
from typing import Tuple, Callable
from threading import Event, Lock, Thread

from LocationService.Trigo import Position, Angle
from LocationService.Track import FullTrack


class LocationService():
    def __init__(self, track: FullTrack, on_update_callback: Callable[[Position, Angle, dict], None] | None, starting_offset: float = 0, simulation_ticks_per_second: int = 24, start_immeaditly: bool = False):
        """
        Init the location service
        track: List of all Track Pieces
        simulation_ticks_per_second: how many steps should be ran per second. A higher value
            increases accuracy and the required CPU time
        on_update_callback: Callback that gets executed every time a new position was
            calculated. It includes the global position, the global angle and a dict
            with additional data. This data is:
                offset: offset from the center (a positive value means right; a negative left in
                                                driving direction)
                speed: simulated actual speed of the car
                going_clockwise: true, if the car is going clockwise (assuming a round track)
                uturn_in_progress: True, if it's currently doing a U-Turn
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
        # the real cars will multiply the offset by -1 when changing directions. We will account
        # for this change in all function calls that read/write the offset
        self._actual_offset: float = 0
        self._target_offset: float = 0
        # direction multiplier. 1 if going the default rotation (clockwise on a round track) and -1 if going the opposing direction
        self._direction_mult: int = 1
        # used to save direction, if the car comes to a stop
        self._stop_direction: Angle = Angle(90)

        self._uturn_override: UTurnOverride | None = None

        self._track: FullTrack = track
        self._current_piece_index: int = 0
        self._progress_on_current_piece: float = 0
        first_piece, _ = self._track.get_entry_tupel(0)
        _, self._current_position = first_piece.process_update(0, 0, starting_offset)

        self._stop_event: Event = Event()
        self._simulation_thread: Thread | None = None

        self._on_update_callback: Callable[[Position, Angle, dict], None] | None = on_update_callback

        if start_immeaditly:
            self.start()

    def __del__(self):
        if self._simulation_thread != None:
            self.stop()

    def do_uturn(self):
        """
        Do a U-Turn.
        Thread-Safe
        """
        with self._value_mutex:
            # block a U-Turn in a U-Turn
            if self._uturn_override is None:
                self._uturn_override = UTurnOverride(self, self._actual_offset > 0)

    def set_speed_percent(self, speed: int, acceleration: int = 1000):
        """
        Updates the target speed of the car.
        Thread-safe
        speed: targeted speed in percent
        acceleration: used acceleration in mm/s^2
        """
        with self._value_mutex:
            self._set_speed_mm(self.__MAX_ANKI_SPEED * speed / 100, acceleration)

    def _set_speed_mm(self, speed_mm: float, acceleration: int = 1000):
        """
        Update the target speed of the car
        Not Thread-safe
        speed: target speed in mm/s
        acceleration: used acceleration in mm/s^2
        """
        self._target_speed = speed_mm
        self._acceleration = acceleration

    def set_offset_int(self, offset: int):
        """
        Sets the targeted offset where the car should drive. Use positive
        values to go right and negative values to go left in the driving
        direction.
        Thread-safe
        offset: target offset where the car should drive (as int like
                in the AnkiController)
        """
        with self._value_mutex:
            # TODO: This doesn't check for out of bounds driving
            self._set_offset_mm(self.__LANE_OFFSET * offset)

    def _set_offset_mm(self, offset: float):
        """
        Sets the targeted offset where the car should drive on the track.
        Not Thread-safe
        offset: target offset where the car should drive in mm of
                distance to the track center
        """
        self._target_offset = offset * -1 * self._direction_mult

    def _adjust_speed(self):
        """
        Updates internal speed values for the simulation based on the acceleration.
        Not Thread-safe
        """
        self._adjust_speed_to(self._target_speed)

    def _adjust_speed_to(self, target_speed: float):
        """
        Updates internal speed values for the simulation based on the acceleration.
        Takes the target speed as argument
        Not Thread-safe
        """
        max_change = self._acceleration / self._simulation_ticks_per_second
        if self._actual_speed < target_speed:
            self._actual_speed += max_change
            # accelerated too much
            if self._actual_speed > target_speed:
                self._actual_speed = target_speed

        if self._actual_speed > target_speed:
            self._actual_speed -= max_change
            # decelerated too much
            if self._actual_speed < target_speed:
                self._actual_speed = target_speed


    def _adjust_offset(self, travel_distance: float) -> float:
        """
        Changes the current offset to get closer to the target based on the
        traveled distance.
        Not Thread-safe
        returns: leftover distance that can be traveled straight
        """
        # slightly changes the progress on the piece itself
        needed_offset = abs(self._actual_offset - self._target_offset)
        max_change = self.__MAX_USED_DISTANCE_FOR_OFFSET_PERCENT * travel_distance
        change = max_change
        if max_change > needed_offset:
            change = needed_offset

        if needed_offset < change:
            change = needed_offset
        old_offset = self._actual_offset
        if self._target_offset > self._actual_offset:
            new_offset = self._actual_offset + change
        else:
            new_offset = self._actual_offset - change
        self._adjust_offset_on_piece(old_offset, new_offset)

        # use pythagoras for more accuracy
        remaining_way = math.sqrt(travel_distance * travel_distance - change * change)
        return remaining_way

    def _adjust_offset_on_piece(self, old_offset: float, new_offset: float):
        """
        Adjusts the offset on the current piece.
        Not Thread-safe
        """
        piece, _ = self._track.get_entry_tupel(self._current_piece_index)
        self._progress_on_current_piece = piece.get_equivalent_progress_for_offset(old_offset, new_offset, self._progress_on_current_piece)
        self._actual_offset = new_offset

    def _run_simulation_step_threadsafe(self) -> Tuple[Position, Angle]:
        """
        Runs a single simulation step by calling _run_simulation_step internally.
        Thread-safe
        returns: The new position and the Angle where the car is pointing
        """
        with self._value_mutex:
            if self._uturn_override is not None:
                trav_distance = self._uturn_override.override_simulation()
            else:
                self._adjust_speed()
                trav_distance = self._adjust_offset(self._actual_speed / self._simulation_ticks_per_second)
            return self._run_simulation_step(trav_distance * self._direction_mult)

    def _run_simulation_step(self, distance: float) -> Tuple[Position, Angle]:
        """
        Advance the simulation one step without threadsafety. Should only be called
        internally.
        distance: Distance to travel
        returns: The new position and the Angle where the car is pointing
        """
        if self._direction_mult == -1 and distance > 0:
            # TODO: Log as critical via Logger
            print("Critical: The leftover distance is positive while driving in opposing direction. This would create a infinite recursion. Breaking the loop to prevent this!")
            return (self._current_position, self._stop_direction)
        elif self._direction_mult == 1 and distance < 0:
            # TODO: Log as critical via Logger
            print("Critical: The leftover distance is negative while driving in default direction. This would create a infinite recursion. Breaking the loop to prevent this!")
            return (self._current_position, self._stop_direction)

        old_pos = self._current_position
        piece, global_track_offset = self._track.get_entry_tupel(self._current_piece_index)
        leftover_distance, new_pos = piece.process_update(self._progress_on_current_piece, distance, self._actual_offset)
        self._progress_on_current_piece += distance
        if leftover_distance != 0:
            self._current_piece_index = (self._current_piece_index + self._direction_mult) % self._track.get_len()
            if self._direction_mult == 1:
                self._progress_on_current_piece = 0
            else:
                new_piece, _ = self._track.get_entry_tupel(self._current_piece_index)
                self._progress_on_current_piece = new_piece.get_length(self._actual_offset)
            return self._run_simulation_step(leftover_distance)
        self._current_position = new_pos + global_track_offset
        distance = self._current_position.distance_to(old_pos)
        if distance < 0.1:
            rot = self._stop_direction
        else:
            rot = self._current_position.calculate_angle_to(old_pos)
            self._stop_direction = rot
        return (self._current_position, rot)

    def _run_task(self):
        """
        Runs the simulation asynchronously in an own thread
        """
        while not self._stop_event.is_set():
            pos, rot = self._run_simulation_step_threadsafe()
            if self._on_update_callback is not None:
                data: dict = {
                    'offset': self._actual_offset * self._direction_mult * -1,
                    'speed': self._actual_speed,
                    'going_clockwise': self._direction_mult == 1,
                    'uturn_in_progress': self._uturn_override is not None
                }
                self._on_update_callback(pos, rot, data)
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

    
class UTurnOverride():
    """
    Class that overrides the complete LocationService behavior to
    do a complete U-Turn
    """
    def __init__(self, location_service, drive_to_outside_of_tack: bool):
        """
        Create a UTurn override object that can be set in the LocationService
        to perform a U-Turn. Based on direction_mult it will either be clockwise
        or counter-clockwise. The allowed values for this argument are -1 and 1.
        """
        self._SPEED_FOR_UTURN = 300
        self._CIRCLE_RADIUS = 22.5
        self._CIRCLE_LENGTH = self._CIRCLE_RADIUS * math.pi
        self._DEGREE_PER_STEP = (self._SPEED_FOR_UTURN * 180) / (self._CIRCLE_LENGTH * location_service._simulation_ticks_per_second) * -1

        self._location_service = location_service

        self._phase = 0
        self._curve_progress = 0

        if drive_to_outside_of_tack:
            self._angle_multiplier = 1
        else:
            self._angle_multiplier = -1

        # Point around which the U-Turn will resolve. Generally dx is the length and dy the offset
        self._last_curve_pos: Position = Position(0, self._angle_multiplier)
        self._orig_mult = self._location_service._direction_mult

    def override_simulation(self) -> float:
        """
        Function that is called in the simulation step. It will return a float with
        the distance the car will travel in piece direction
        """
        match self._phase:
            # change speed to safe value for U-Turns
            case 0:
                if abs(self._location_service._actual_speed - self._SPEED_FOR_UTURN) < 0.1:
                    self._phase = 1
                    return self.override_simulation()
                self._location_service._adjust_speed_to(self._SPEED_FOR_UTURN)
                return self._location_service._actual_speed / self._location_service._simulation_ticks_per_second
            # first half of the curve
            case 1:
                # check if we entered the 2nd half already
                if self._last_curve_pos.get_y() <= 0 and self._angle_multiplier == 1 or\
                        self._last_curve_pos.get_y() >= 0 and self._angle_multiplier == -1:
                    self._location_service._direction_mult *= -1
                    self._phase = 2
                # this is done since dy could be negative for the last step which would create a infinite recursion
                return abs(self._do_curve_step())
            # second half of the curve
            case 2:
                # check if the curve was finished already
                if self._last_curve_pos.get_x() <= 0:
                    self._location_service._uturn_override = None
                    self._location_service._target_offset = self._location_service._actual_offset
                    return 0
                # this isn't a problem since the abs and the inverted driving direction cancel out each other
                return abs(self._do_curve_step())
        raise RuntimeError(f"The U-Turn override got into phase {self._phase} which doesn't exist!")
    
    def _do_curve_step(self) -> float:
        """
        Does a single curve step by applying the changed offset and returning the
        travelled distance
        """
        new_pos = self._last_curve_pos.clone()
        new_pos.rotate_around_0_0(Angle(self._DEGREE_PER_STEP * self._angle_multiplier))
        dx = new_pos.get_x() - self._last_curve_pos.get_x()
        dy = new_pos.get_y() - self._last_curve_pos.get_y()

        self._last_curve_pos = new_pos
        dx *= self._CIRCLE_RADIUS
        dy *= self._CIRCLE_RADIUS

        old_offset = self._location_service._actual_offset
        new_offset = old_offset + dy
        self._location_service._adjust_offset_on_piece(old_offset, new_offset)
        return dx
