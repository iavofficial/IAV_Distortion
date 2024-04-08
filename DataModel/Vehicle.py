class Vehicle:
    def __init__(self, uuid):
        self.uuid = uuid
        self.player = ""

        self.__speed = 0.0
        self.__speed_request = 0.0
        self.__speed_factor = 1.0

        self.__lane_change = 0
        self.__lane_change_request = 0
        self.__lange_change_blocked = False

        self._is_light_on = False
        self._is_light_inverted = False
        self._is_safemode_on = True

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
    def lane_change (self) -> int:
        return self.__lane_change

    def calculate_lane_change(self) -> None:
        if not self.__lange_change_blocked:
            self.__lane_change = self.__lane_change + self.__lane_change_request
        else:
            self.__lane_change = self.__lane_change
        print(f"calculate_lane_change: {self.__lane_change}")
        return

    def turn_on_lights(self):
        self._is_light_on = True

    def turn_off_lights(self):
        self._is_light_on = False

    def set_safemode(self, value):
        self._is_safemode_on = value
