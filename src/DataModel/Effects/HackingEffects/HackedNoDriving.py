from DataModel.Effects.HackingEffects.HackedEffect import HackedEffect
from DataModel.Effects.VehicleEffectList import VehicleEffectIdentification
from DataModel.Vehicle import Vehicle


class HackedNoDriving(HackedEffect):
    def identify(self) -> VehicleEffectIdentification:
        return VehicleEffectIdentification.HACKED_NO_DRIVING

    def can_be_applied(self, vehicle: Vehicle) -> bool:
        _ = vehicle
        return True

    def on_start(self, vehicle: 'Vehicle') -> None:
        super().on_start(vehicle)
        self.remove_other_hacking_effects(vehicle)
        vehicle.speed_factor = 0.0

    def on_end(self, vehicle: 'Vehicle') -> None:
        vehicle.speed_factor = 1
