import asyncio
from asyncio import Lock
import math
import logging
from typing import Any, Tuple, Callable, List

import Constants
from LocationService.Trigo import Position, Angle
from LocationService.Track import FullTrack

logger = logging.getLogger(__name__)


class LocationService:
    def __init__(self,
                 track: FullTrack | None,
                 starting_offset: float = 0,
                 simulation_ticks_per_second: int = 24,
                 start_immediately: bool = False):
        """
        Init the location service
        track: List of all Track Pieces
        simulation_ticks_per_second: how many steps should be calculated per second. A higher value
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
        self.__start_immediately = start_immediately

        self._value_mutex: Lock = Lock()
        self._actual_speed: float = 0
        self._target_speed: float = 0
        self._acceleration: float = 0
        # the real cars will multiply the offset by -1 when changing directions. We will account
        # for this change in all function calls that read/write the offset
        self._actual_offset: float = 0
        self._target_offset: float = 0
        # direction multiplier. 1 if going the default rotation (clockwise on a round track) and
        # -1 if going the opposing direction
        self._direction_mult: int = 1
        # used to save direction, if the car comes to a stop
        self._stop_direction: Angle = Angle(90)

        self._uturn_override: UTurnOverride | None = None

        self._track: FullTrack | None = track
        self._current_piece_index: int = 0
        self._progress_on_current_piece: float = 0
        self._current_position: Position | None
        if track is not None:
            first_piece, _ = self._track.get_entry_tupel(0)
            _, self._current_position = first_piece.process_update(0, 0, starting_offset)
        else:
            self._current_position = None

        self._on_update_callback: List[Callable[[Position, Angle, dict[str, Any]], None]] = []

        self.__task = None
        if self.__start_immediately:
            self.start()

    def __del__(self):
        if self.__task is not None:
            self.stop()

    def add_on_update_callback(self, callback_function: Callable[[Position, Angle, dict[str, Any]], None]) -> None:
        self._on_update_callback.append(callback_function)

        return

    async def do_uturn(self) -> None:
        """
        Do a U-Turn.
        Thread-Safe
        """
        async with self._value_mutex:
            # block a U-Turn in a U-Turn
            if self._uturn_override is None:
                self._uturn_override = UTurnOverride(self, self._actual_offset > 0)
        return

    async def set_speed_percent(self, speed: int, acceleration: int = 1000) -> None:
        """
        Updates the target speed of the car.
        Thread-safe

        Parameters
        ----------
        speed: int
            Targeted speed in percent.
        acceleration: int
            Used acceleration in mm/s^2.
        """
        async with self._value_mutex:
            self._set_speed_mm(Constants.MAX_ANKI_SPEED * speed / 100, acceleration)
        return

    def _set_speed_mm(self, speed_mm: float, acceleration: int = 1000) -> None:
        """
        Update the target speed of the car
        Not Thread-safe

        Parameters
        ----------
        speed_mm: float
            Target speed in mm/s.
        acceleration: int
            Used acceleration in mm/s^2.
        """
        self._target_speed = speed_mm
        self._acceleration = acceleration
        return

    async def set_offset_int(self, offset: int) -> None:
        """
        Sets the targeted offset where the car should drive. Use positive
        values to go right and negative values to go left in the driving
        direction.
        Thread-safe

        Parameters
        ----------
        offset: int
            Target offset where the car should drive (as int like in the AnkiController)
        """
        async with self._value_mutex:
            # TODO: This doesn't check for out of bounds driving
            self._set_offset_mm(Constants.TRACK_LANE_WIDTH * offset)
        return

    def _set_offset_mm(self, offset: float) -> None:
        """
        Sets the targeted offset where the car should drive on the track.
        Not Thread-safe

        Parameters
        ----------
        offset: float
            Target offset where the car should drive in mm of distance to the track center.
        """
        self._target_offset = offset * -1 * self._direction_mult
        return

    def _adjust_speed(self) -> None:
        """
        Updates internal speed values for the simulation based on the acceleration.
        Not Thread-safe
        """
        self._adjust_speed_to(self._target_speed)
        return

    def _adjust_speed_to(self, target_speed: float) -> None:
        """
        Updates internal speed values for the simulation based on the acceleration.
        Not Thread-safe

        Parameters
        ----------
        target_speed: float
            Target speed.
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

        Parameters
        ----------
        travel_distance: float
            Distance to travel during on simulation step.

        Returns
        -------
        remaining_way: float
            Leftover distance that can be traveled straight.
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

    def _adjust_offset_on_piece(self, old_offset: float, new_offset: float) -> None:
        """
        Adjusts the offset on the current piece.
        Not Thread-safe

        Parameters
        ----------
        old_offset: float
            # TODO: parameter description
        new_offset: float
            # TODO: parameter description
        """
        piece, _ = self._track.get_entry_tupel(self._current_piece_index)
        self._progress_on_current_piece = piece.get_equivalent_progress_for_offset(old_offset, new_offset,
                                                                                   self._progress_on_current_piece)
        self._actual_offset = new_offset
        return

    async def _run_simulation_step_threadsafe(self) -> tuple[Position|None, Angle]:
        """
        Runs a single simulation step by calling _run_simulation_step internally.
        Thread-safe

        Returns
        -------
        Tuple[Position, Angle]
            The new position and the Angle where the car is pointing.
        """
        async with self._value_mutex:
            if self._uturn_override is not None:
                trav_distance = self._uturn_override.override_simulation()
            else:
                self._adjust_speed()
                trav_distance = self._adjust_offset(self._actual_speed / self._simulation_ticks_per_second)
            return self._run_simulation_step(trav_distance * self._direction_mult)

    def _run_simulation_step(self, distance: float) -> Tuple[Position|None, Angle]:
        """
        Advance the simulation one step without threadsafety. Should only be called
        internally.

        Parameters
        ----------
        distance: float
            Distance to travel

        Returns
        -------
        Tuple[Position, Angle]
            The new position and the Angle where the car is pointing.
        """
        # prevent "maximum recursion depth exceeded" Errors in case the simulation has a bug
        if self._direction_mult == -1 and distance > 0:
            logger.critical(
                "The leftover distance is positive while driving in opposing direction."
                "This would create a infinite recursion. Breaking the loop to prevent this!")
            return self._current_position, self._stop_direction
        elif self._direction_mult == 1 and distance < 0:
            logger.critical(
                "The leftover distance is negative while driving in default direction."
                "This would create a infinite recursion. Breaking the loop to prevent this!")
            return self._current_position, self._stop_direction

        old_pos = self._current_position
        piece, global_track_offset = self._track.get_entry_tupel(self._current_piece_index)
        leftover_distance, new_pos = piece.process_update(self._progress_on_current_piece, distance,
                                                          self._actual_offset)
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
            rot = old_pos.calculate_angle_to(self._current_position)
            self._stop_direction = rot
        return self._current_position, rot

    async def _run_task(self) -> None:
        """
        Runs the simulation asynchronously in an asynchronous loop.
        """
        # while not self._stop_event.is_set():
        while True:
            pos, rot = await self._run_simulation_step_threadsafe()
            data: dict[str, Any] = {
                'offset': self._actual_offset * self._direction_mult * -1,
                'speed': self._actual_speed,
                'going_clockwise': self._direction_mult == 1,
                'uturn_in_progress': self._uturn_override is not None
            }
            for callback in self._on_update_callback:
                callback(pos, rot, data)

            # time.sleep(1 / self._simulation_ticks_per_second)
            await asyncio.sleep(1 / self._simulation_ticks_per_second)

    def start(self) -> None:
        """
        Creates a task and adds it to the event loop.
        """
        if self._track is not None:
            self.__task = asyncio.create_task(self._run_task())
        else:
            logger.error("Location service was told to start while there is no track. Ignoring the request!")
        #        if self._simulation_thread is not None:
        #            self.logger.error("It was attempted to start an already running LocationService Thread.
        #            Ignoring the request!")
        #            return
        #        self._stop_event.clear()
        #        # TODO: Check if Flask-SocketIO's start_background_task is needed here
        #        self._simulation_thread = Thread(target=self._run_task)
        #        self._simulation_thread.start()
        return

    def stop(self) -> None:
        """
        Cancels the task that runs the simulation.
        """
        if self.__task is not None:
            self.__task.cancel()
        #        #if self._simulation_thread is None:
        #        #    self.logger.error("It was attempted to stop an already stopped LocationService Thread.
        #        Ignoring the request!")
        #        #    return
        #        self._stop_event.set()
        #        #self._simulation_thread.join()
        #        #self._simulation_thread = None
        return

    def notify_new_track(self, new_track: FullTrack) -> None:
        self._track = new_track
        first_piece, _ = self._track.get_entry_tupel(0)
        _, self._current_position = first_piece.process_update(0, 0, self._actual_offset)
        if self.__task is not None:
            self.__task.cancel()
        self.start()


class UTurnOverride:
    """
    Class that overrides the complete LocationService behavior to
    do a complete U-Turn
    """

    def __init__(self, location_service: LocationService, drive_to_outside_of_tack: bool):
        """
        Create a UTurn override object that can be set in the LocationService
        to perform a U-Turn. Based on direction_mult it will either be clockwise
        or counter-clockwise. The allowed values for this argument are -1 and 1.
        """
        self._SPEED_FOR_UTURN = 300
        self._CIRCLE_RADIUS = 22.5
        self._CIRCLE_LENGTH = self._CIRCLE_RADIUS * math.pi
        self._DEGREE_PER_STEP = (self._SPEED_FOR_UTURN * 180) / (
                self._CIRCLE_LENGTH * location_service._simulation_ticks_per_second) * -1

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

        Returns
        -------
        float
            Distance the car will travel in piece direction.
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
                if self._last_curve_pos.get_y() <= 0 and self._angle_multiplier == 1 or \
                        self._last_curve_pos.get_y() >= 0 and self._angle_multiplier == -1:
                    self._location_service._direction_mult *= -1
                    self._phase = 2
                # this is done since dy could be negative for the last step which would create an infinite recursion
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
            case _:
                raise RuntimeError(f"The U-Turn override got into phase {self._phase} which doesn't exist!")
        

    def _do_curve_step(self) -> float:
        """
        Does a single curve step by applying the changed offset and returning the
        travelled distance

        Returns
        -------
        dx: float
            Traveled distance.
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
