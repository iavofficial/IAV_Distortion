from VehicleManagement.VehicleController import TurnTrigger, Turns, VehicleController


class EmptyController(VehicleController):
    """
    Controller that does absolutely nothing on every function call. Used for
    virtual vehicles that don't need to send their data to any physical car
    """
    def __init__(self) -> None:
        return

    def __del__(self) -> None:
        return

    def change_speed_to(self, velocity: int, acceleration: int = 1000, respect_speed_limit: bool = True) -> bool:
        return True

    def change_lane_to(self, change_direction: int, velocity: int, acceleration: int = 1000) -> bool:
        return True

    def do_turn_with(self, direction: Turns,
                     turntrigger: TurnTrigger = TurnTrigger.VEHICLE_TURN_TRIGGER_IMMEDIATE) -> bool:
        return True
