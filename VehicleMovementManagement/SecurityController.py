class SecurityController:

    SpeedFactor = 0.0
    IsLaneChangeBlocked = False
    IsLightSwitchSwaped = False

    def set_speed_factor(self, uuid, value):
        self.SpeedFactor = value

    def block_lane_change(self, uuid):
        self.IsLaneChangeBlocked = True

    def unblock_lane_change(self, uuid):
        self.IsLaneChangeBlocked = False

    def swap_light_switch(self, uuid):
        self.IsLightSwitchSwaped = True

    def unswap_light_switch(self, uuid):
        self.IsLightSwitchSwaped = False