class Vehicle:
    uuid = ""
    name = ""

    _speed = 0
    _speed_request = 0
    _speed_factor = 0.0

    _lane = -1
    _lane_request = -1
    _lange_change_blocked = False

    _is_light_on = False
    _is_light_inverted = False
    _is_safemode_on = True

    def __init__(self, uuid, name):
        self.uuid = uuid
        self.name = name

    @property
    def speed_request(self):
        return self._speed_request

    @speed_request.setter
    def speed_request(self, value: int):
        self._speed_request = value
        self.calculate_speed()

    @property
    def speed_factor(self):
        return self._speed_factor

    @speed_factor.setter
    def speed_factor(self, value: float):
        self._speed_factor = value
        self.calculate_speed()

    def calculate_speed(self):
        self._speed = self._speed_request * self._speed_factor

    @property
    def lane_change_request(self):
        return self._lane_request

    @lane_change_request.setter
    def lane_change_request(self, value):
        self._lane_request = self._lane_request + value
        self.calculate_lane()

    @property
    def lange_change_blocked(self):
        return self._lange_change_blocked

    @lange_change_blocked.setter
    def lange_change_blocked(self, value):
        self._lange_change_blocked = value

    def calculate_lane(self):
        if not self._lange_change_blocked:
            self._lane = self._lane_request
            return

    def turn_on_lights(self):
        self._is_light_on = True

    def turn_off_lights(self):
        self._is_light_on = False

    def set_safemode(self, value):
        self._is_safemode_on = value
