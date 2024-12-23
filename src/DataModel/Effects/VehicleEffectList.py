from enum import Enum


class VehicleEffectIdentification(Enum):
    # todo this list should be resorted
    NO_EFFECT = 0,
    HACKING_PROTECTION = 1,
    HACKED_REDUCED_SPEED = 2,
    HACKED_NO_DRIVING = 3,
    HACKED_NO_SAFETY_MODULE = 4,
    CLEAN_HACKED_EFFECTS = 5,
    HACKED_SPORADIC_O_TURNS = 6,
    HACKED_INVERTED_USER_INPUT = 7,
