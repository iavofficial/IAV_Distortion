from DataModel.Effects.HackingEffects.HackedEffect import HackedEffect
from DataModel.Effects.VehicleEffectList import VehicleEffectIdentification
from DataModel.Vehicle import Vehicle


class HackedInvertedUserInput(HackedEffect):
    def identify(self) -> VehicleEffectIdentification:
        return VehicleEffectIdentification.HACKED_INVERTED_USER_INPUT

    def on_start(self, vehicle: 'Vehicle') -> None:
        super().on_start(vehicle)
        self.remove_other_hacking_effects(vehicle)
        vehicle.speed_factor = -1
        vehicle.speed_offset = 1
        vehicle.lange_change_inverted = True

    def on_end(self, vehicle: 'Vehicle') -> None:
        vehicle.speed_factor = 1
        vehicle.speed_offset = 0
        vehicle.lange_change_inverted = False
