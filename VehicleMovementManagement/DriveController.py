class DriverController:

    speedRequest = 0
    laneChangeRequest = 0
    def __init__(self):
        self.speedRequest = 0
        self.laneChangeRequest = 0
    def request_speed_change(self, uuid, value):
        self.speedRequest = value

    def request_lane_change(self, value):
        if value == "left":
            laneChangeRequest = 1

        elif value == "right":
            laneChangeRequest = -1

        else:
            laneChangeRequest = 0
