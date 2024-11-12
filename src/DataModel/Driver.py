from DataModel.Vehicle import Vehicle


class Driver:
    def __init__(self, player_id) -> None:
        self.player = player_id
        self.score = 0
        self.vehicle = None
        return
    
    def get_score(self) -> int:
        return self.score
    
    def increase_score(self, amount: int) -> None:
        self.score += amount

    def set_vehicle(self, vehicle: Vehicle) -> None:
        self.vehicle = vehicle

    def get_vehicle(self) -> Vehicle:
        return self.vehicle