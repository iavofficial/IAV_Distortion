class Vehicle:
    uuid = ""
    name = ""
    speed = 0
    lane = -1
    isLightOn = False

    def __init__(self, uuid, name):
        self.uuid = uuid
        self.name = name

    def change_speed(self, new_speed):
        self.speed = new_speed

    def change_lane(self, new_lane):
        self.lane = new_lane

    def turn_on_lights(self):
        self.isLightOn = True

    def turn_off_lights(self):
        self.isLightOn = False
