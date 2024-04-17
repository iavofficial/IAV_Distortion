from VehicleManagement.VehicleController import VehicleController

class Vehicle:
    def __init__(self, uuid: str, controller: VehicleController):
        self.uuid = uuid
        self.player = ""
        self.controller = controller

        self.__speed = 0.0
        self.__speed_request = 0.0
        self.__speed_factor = 1.0

        self.__lane_change = 0
        self.__lane_change_request = 0
        self.__lange_change_blocked = False

        self._is_light_on = False
        self._is_light_inverted = False
        self._is_safemode_on = True

        self._road_piece = 0
        self._prev_road_piece = 0
        self._road_location = 0
        self._offset_from_center = 0.0
        self._speed_actual = 0
        self._direction = 0
        self._battery = ""
        self._version = ""

        self.controller.connect_to_anki_cars(uuid, True)
        self.controller.set_callbacks(self.__receive_location,
                                      self.__receive_transition,
                                      self.__receive_offset_update,
                                      self.__receive_version,
                                      self.__receive_battery)
        self.controller.request_version_of(uuid)
        self.controller.request_battery_of(uuid)

    @property
    def speed_request(self) -> float:
        return self.__speed_request

    @speed_request.setter
    def speed_request(self, value: float) -> None:
        self.__speed_request = value
        self.calculate_speed()
        return

    @property
    def speed_factor(self) -> float:
        return self.__speed_factor

    @speed_factor.setter
    def speed_factor(self, value: float) -> None:
        self.__speed_factor = value
        self.calculate_speed()

    @property
    def speed(self) -> float:
        return self.__speed

    def calculate_speed(self) -> None:
        self.__speed = self.__speed_request * self.__speed_factor
        self.controller.change_speed(self.uuid, self.__speed)

        # mock self._speed_actual
        self._speed_actual = self.__speed * 2.55  # calculate _speed_actual as m/s by assuming simple factor
        return

    @property
    def lane_change_request(self) -> int:
        return self.__lane_change_request

    @lane_change_request.setter
    def lane_change_request(self, value: int) -> None:
        self.__lane_change_request = value
        self.calculate_lane_change()
        return

    @property
    def lange_change_blocked(self) -> bool:
        return self.__lange_change_blocked

    @lange_change_blocked.setter
    def lange_change_blocked(self, value: bool) -> None:
        self.__lange_change_blocked = value
        return

    @property
    def lane_change(self) -> int:
        return self.__lane_change

    def calculate_lane_change(self) -> None:
        if self.__lange_change_blocked:
            return

        if 65.0 > self._offset_from_center > -65.0:
            self.__lane_change = self.__lane_change + self.__lane_change_request
        elif 65.0 <= self._offset_from_center and self.__lane_change_request == -1:
            self.__lane_change = self.__lane_change + self.__lane_change_request
        elif 65.0 <= self._offset_from_center and self.__lane_change_request == 1:
            self.__lane_change = 3
        elif -65.0 >= self._offset_from_center and self.__lane_change_request == 1:
            self.__lane_change = self.__lane_change + self.__lane_change_request
        elif -65.0 >= self._offset_from_center and self.__lane_change_request == -1:
            self.__lane_change = -3
        else:
            self.__lane_change = self.__lane_change


        self.controller.change_lane(self.uuid, self.__lane_change, self.__speed)
        print(f"actual offset: {self._offset_from_center}")
        return

    def turn_on_lights(self):
        self._is_light_on = True

    def turn_off_lights(self):
        self._is_light_on = False

    def set_safemode(self, value):
        self._is_safemode_on = value

    def __receive_location(self, value_tuple):
        location, piece, offset, speed, clockwise = value_tuple
        self._road_location = location
        self._road_piece = piece
        self._offset_from_center = offset
        self._speed_actual = speed
        self._direction = clockwise
        # print(f"actual offset: {self._offset_from_center}")

    def __receive_transition(self, value_tuple):
        piece, piece_prev, offset, direction = value_tuple
        self._road_piece = piece
        self._prev_road_piece = piece_prev
        self._offset_from_center = offset
        self._direction = direction
        # print(f"actual offset: {self._offset_from_center}")

    def __receive_offset_update(self, value_tuple):
        offset = value_tuple[0]
        self._offset_from_center = offset

    def __receive_version(self, value_tuple):
        print(f"{self.uuid} version_tuple: {value_tuple}")

    def __receive_battery(self, value_tuple):
        print(f"{self.uuid} battery_tuple: {value_tuple}")



    def get_speed_request(self):
        return self.__speed_request
