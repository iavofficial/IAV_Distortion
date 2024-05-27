import math
from typing import Dict, Tuple

class Angle():
    """
    Generic class for angles where 0° means the Angle is pointing up/north
    """
    def __init__(self, degree = 0.0):
        self._angle_degree = degree

    def get_sin(self):
        return math.sin(math.radians(self._angle_degree))

    def get_cos(self):
        return math.cos(math.radians(self._angle_degree))

    def get_x_mult(self):
        return self.get_cos()

    def get_y_mult(self):
        return self.get_sin()

    def set_deg(self, degree):
        self._angle_degree = degree

    def get_deg(self):
        return self._angle_degree

    def __str__(self):
        return f"{round(self._angle_degree)}"

    def get_as_x_y(self) -> Tuple[float, float]:
        deg = self._angle_degree - 90
        return (math.cos(math.radians(deg)), math.sin(math.radians(deg)))


class Position():
    """
    Generic Position in a 2 dimensional space
    """
    def __init__(self, x = 0.0, y = 0.0):
        self._x = x
        self._y = y

    def set_x(self, x):
        self._x = x

    def set_y(self, y):
        self._y = y

    def add_offset_with_angle(self, change, angle):
        self._x += angle.get_x_mult() * change
        self._y += angle.get_y_mult() * change

    def get_x(self):
        return self._x

    def get_y(self):
        return self._y

    def __add__(self, other):
        comb_x = self._x + other._x
        comb_y = self._y + other._y
        return Position(comb_x, comb_y)

    def __sub__(self, other):
        comb_x = self._x - other._x
        comb_y = self._y - other._y
        return Position(comb_x, comb_y)

    def add_offset(self, x, y):
        self._x += x
        self._y += y
    
    def get_as_dict(self):
        return {'x' : self._x, 'y' : self._y }

    def rotate_around_0_0(self, rotation: Angle):
        new_x = self._x * rotation.get_cos() - self._y * rotation.get_sin()
        new_y = self._x * rotation.get_sin() + self._y * rotation.get_cos()
        self._x = new_x
        self._y = new_y

    def __str__(self) -> str:
        return f"({round(self._x)}, {round(self._y)})"

    def calculate_angle_to(self, other) -> Angle:
        pos = other - self
        # yes atan2 takes y first and x second!
        # the - 0.5 * math.pi is here because atan2 defines pointing right as 0 degree
        rad = math.atan2(pos.get_y(), pos.get_x()) - 0.5 * math.pi
        if rad < 0:
            rad += 2 * math.pi
        deg = math.degrees(rad)
        return Angle(deg)
    
    def distance_to(self, other) -> float:
        in_sqrt = math.pow(self.get_x() - other.get_x(), 2) + math.pow(self.get_y() - other.get_y(), 2)
        return math.sqrt(in_sqrt)

    def clone(self):
        return Position(self._x, self._y)

    def to_dict(self) -> dict:
        return { 'x': self._x, 'y': self._y }
