from DataModel.Effects.HackingEffects.HackedEffect import HackedEffect
from DataModel.Effects.VehicleEffectList import VehicleEffectIdentification
from DataModel.Vehicle import Vehicle


class HackedReducedSpeed(HackedEffect):
    def identify(self) -> VehicleEffectIdentification:
        return VehicleEffectIdentification.HACKED_REDUCED_SPEED

    def on_start(self, vehicle: 'Vehicle') -> bool:
        super().on_start(vehicle)
        self.remove_other_hacking_effects(vehicle)
        vehicle.speed_factor = 0.3

        return True

    def on_end(self, vehicle: 'Vehicle') -> None:
        vehicle.speed_factor = 1
