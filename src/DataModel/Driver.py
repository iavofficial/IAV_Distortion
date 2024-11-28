class Driver:
    """
    A class to store driver specific information.
    Can later be used to make the project more object oriented.

    Parameters
    ----------
    player_id: str
        ID of the player, a Driver instance is to be created for
    """
    def __init__(self, player_id: str) -> None:
        self.__player: str = player_id
        self.__score: int = 0
        self.__in_physical_vehicle: bool = False
        return

    def get_score(self) -> int:
        return self.__score

    def increase_score(self, amount: int) -> None:
        self.__score += amount

    def set_is_in_physical_vehicle(self, b: bool) -> None:
        self.__in_physical_vehicle = b

    def get_is_in_physical_vehicle(self) -> bool:
        return self.__in_physical_vehicle

    def get_player_id(self) -> str:
        return self.__player
