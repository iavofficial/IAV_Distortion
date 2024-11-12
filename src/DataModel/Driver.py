from DataModel.Vehicle import Vehicle


class Driver:
    def __init__(self, player_id: str) -> None:
        self.player: str = player_id
        self.score: int = 0
        self.vehicle: Vehicle = None
        return
    
    def get_score(self) -> int:
        return self.score
    
    def increase_score(self, amount: int) -> None:
        self.score += amount

    def set_vehicle(self, vehicle: Vehicle) -> None:
        self.vehicle = vehicle

    def get_vehicle(self) -> Vehicle:
        return self.vehicle
    
    def get_player_id(self) -> str:
        return self.player