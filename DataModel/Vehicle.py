from VehicleManagement.VehicleController import VehicleController
from bleak import BleakClient

class Vehicle:
    def __init__(self, uuid: str, controller: VehicleController) -> None:
        self.vehicle_id = uuid
        self.player: str = ""
        self._controller: VehicleController = controller

        self.__speed: int = 0
        self.__speed_request: int = 0
        self.__speed_factor: float = 1.0

        self.__lane_change: int = 0
        self.__lane_change_request: int = 0
        self.__lange_change_blocked: bool = False

        self._is_light_on: bool = False
        self._is_light_inverted: bool = False
        self._is_safemode_on: bool = True

        self._road_piece: int = 0
        self._prev_road_piece: int = 0
        self._road_location: int = 0
        self._offset_from_center: float = 0.0
        self._speed_actual: int = 0
        self._direction: int = 0
        self._battery: str = ""
        self._version: str = ""

        self._controller.connect_to_vehicle(BleakClient(uuid), True)
        self._controller.set_callbacks(self.__receive_location,
                                       self.__receive_transition,
                                       self.__receive_offset_update,
                                       self.__receive_version,
                                       self.__receive_battery)
        self._controller.request_version()
        self._controller.request_battery()

        return

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
        return

    @property
    def speed(self) -> float:
        return self.__speed

    def calculate_speed(self) -> None:
        self.__speed = self.__speed_request * self.__speed_factor
        self._controller.change_speed_to(int(self.__speed))
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

        self._controller.change_lane_to(self.__lane_change, self.__speed)
        print(f"actual offset: {self._offset_from_center}")
        return

    def turn_on_lights(self) -> None:
        self._is_light_on = True
        return

    def turn_off_lights(self) -> None:
        self._is_light_on = False
        return

    def set_safemode(self, value):
        self._is_safemode_on = value

    def __receive_location(self, value_tuple) -> None:
        location, piece, offset, speed, clockwise = value_tuple
        self._road_location = location
        self._road_piece = piece
        self._offset_from_center = offset
        self._speed_actual = speed
        self._direction = clockwise
        # print(f"actual offset: {self._offset_from_center}")
        return

    def __receive_transition(self, value_tuple) -> None:
        piece, piece_prev, offset, direction = value_tuple
        self._road_piece = piece
        self._prev_road_piece = piece_prev
        self._offset_from_center = offset
        self._direction = direction
        # print(f"actual offset: {self._offset_from_center}")
        return

    def __receive_offset_update(self, value_tuple) -> None:
        offset = value_tuple[0]
        self._offset_from_center = offset
        return

    def __receive_version(self, value_tuple) -> None:
        print(f"{self.vehicle_id} version_tuple: {value_tuple}")
        return

    def __receive_battery(self, value_tuple)-> None:
        print(f"{self.vehicle_id} battery_tuple: {value_tuple}")
        return
