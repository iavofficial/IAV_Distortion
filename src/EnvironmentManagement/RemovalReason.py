from enum import Enum


class RemovalReason(Enum):
    NONE = 0
    PLAYING_TIME_IS_UP = 1
    PLAYER_NOT_REACHABLE = 2
    CAR_DISCONNECTED = 3
    CAR_MANUALLY_REMOVED = 4
