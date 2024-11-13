from DataModel.Vehicle import Vehicle


class Driver:
    def __init__(self, player_id: str) -> None:
        self.player: str = player_id
        self.score: float = 0
        self.in_physical_vehicle: bool = False
        return
    
    def get_score(self) -> float:
        return self.score
    
    def increase_score(self, amount: float) -> None:
        self.score += amount

    def set_is_in_physical_vehicle(self, b: bool) -> None:
        self.in_physicalvehicle = b

    def get_is_in_physical_vehicle(self) -> bool:
        return self.in_physical_vehicle
    
    def get_player_id(self) -> str:
        return self.player