import math


class Angle():
    """
    Generic class for angles where 0° means the Angle is pointing up/north
    """
    def __init__(self, degree=0.0):
        self._angle_degree = degree

    def get_sin(self):
        """
        Gets the sinus of the value
        """
        return math.sin(math.radians(self._angle_degree))

    def get_cos(self):
        """
        Gets the cosinus of the value
        """
        return math.cos(math.radians(self._angle_degree))

    def get_x_mult(self):
        """
        Gets the cosinus value (usually used for multiplications with x)
        """
        return self.get_cos()

    def get_y_mult(self):
        """
        Gets the sinus value (usually used for multiplications with y)
        """
        return self.get_sin()

    def set_deg(self, degree):
        """
        Sets the degree value
        """
        self._angle_degree = degree

    def get_deg(self):
        """
        Gets the set degree value
        """
        return self._angle_degree

    def __str__(self):
        """
        Represents the value as string. Warning: Rounds the value!
        """
        return f"{round(self._angle_degree)}"

    def __eq__(self, other):
        return type(self) == type(other) and self._angle_degree == other._angle_degree


class Position():
    """
    Generic Position in a 2 dimensional space
    """
    def __init__(self, x=0.0, y=0.0):
        self._x = x
        self._y = y

    def set_x(self, x):
        """
        Sets the x value of the position
        """
        self._x = x

    def set_y(self, y):
        """
        Sets the y value of the position
        """
        self._y = y

    def get_x(self):
        """
        Gets the x value
        """
        return self._x

    def get_y(self):
        """
        Gets the y value
        """
        return self._y

    def __add__(self, other):
        """
        Adds another Position as offset to itself
        """
        comb_x = self._x + other._x
        comb_y = self._y + other._y
        return Position(comb_x, comb_y)

    def __sub__(self, other):
        """
        Subtracts another Position as negative offset to itself
        """
        comb_x = other._x - self._x
        comb_y = other._y - self._y
        return Position(comb_x, comb_y)

    def add_offset(self, x, y):
        """
        Adds x and y as offset to itself
        """
        self._x += x
        self._y += y

    def get_as_dict(self):
        """
        Gets the data represented as dict with the fields
        'x' and 'y'
        """
        return {'x': self._x, 'y': self._y}

    def rotate_around_0_0(self, rotation: Angle):
        """
        Rotates the point around (0, 0) based on 'rotation'
        """
        new_x = self._x * rotation.get_cos() - self._y * rotation.get_sin()
        new_y = self._x * rotation.get_sin() + self._y * rotation.get_cos()
        self._x = new_x
        self._y = new_y

    def __str__(self) -> str:
        """
        Gets the point represented as string. Warning: Uses rounding!
        """
        return f"({round(self._x)}, {round(self._y)})"

    def calculate_angle_to(self, other) -> Angle:
        """
        Calculate angle from this point to another point. 0 degrees means the other
        point is above this point. A degree of 90 means the other point is right of this point
        """
        pos = other - self
        # yes atan2 takes y first and x second!
        # the - 0.5 * math.pi is here because atan2 defines pointing right as 0 degree
        rad = math.atan2(pos.get_y(), pos.get_x()) - 0.5 * math.pi
        if rad < 0:
            rad += 2 * math.pi
        deg = math.degrees(rad)
        return Angle(deg)

    def distance_to(self, other) -> float:
        """
        Calculates the distance between this point and another point
        """
        in_sqrt = math.pow(self.get_x() - other.get_x(), 2) + math.pow(self.get_y() - other.get_y(), 2)
        return math.sqrt(in_sqrt)

    def clone(self):
        """
        Returns a new object with the same attributes
        """
        return Position(self._x, self._y)

    def to_dict(self) -> dict:
        """
        Returns the data as dict with the fields 'x' and 'y'
        """
        return {'x': self._x, 'y': self._y}


class Distance(Position):
    """
    Class that represents a distance. It's the same as a point and only exists for clarity reasons
    """
    pass
