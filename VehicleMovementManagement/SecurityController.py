class SecurityController:

    SpeedFactor = 0.0
    IsLaneChangeBlocked = False
    IsLightSwitchSwaped = False

    def set_speed_factor(self, value):
        self.SpeedFactor = value

    def block_lane_change(self):
        self.IsLaneChangeBlocked = True

    def unblock_lane_change(self):
        self.IsLaneChangeBlocked = False

    def swap_light_switch(self):
        self.IsLightSwitchSwaped = True

    def unswap_light_switch(self):
        self.IsLightSwitchSwaped = False