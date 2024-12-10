from DataModel.Effects.HackingEffects.HackedEffect import HackedEffect
from DataModel.Effects.VehicleEffectList import VehicleEffectIdentification
from DataModel.Vehicle import Vehicle


class HackedNoSafetyModule(HackedEffect):
    def identify(self) -> VehicleEffectIdentification:
        return VehicleEffectIdentification.HACKED_NO_SAFETY_MODULE

    def can_be_applied(self, vehicle: Vehicle) -> bool:
        _ = vehicle
        return True

    def conflicts_with(self) -> list[VehicleEffectIdentification]:
        conflict_list: list[VehicleEffectIdentification] = super().conflicts_with()
        return conflict_list

    def on_start(self, vehicle: Vehicle) -> bool:
        super().on_start(vehicle)
        self.remove_other_hacking_effects(vehicle)
        vehicle.speed_factor = 1.5
        vehicle.set_safemode(False)
        return True

    def on_end(self, vehicle: Vehicle) -> bool:
        super().on_end(vehicle)
        vehicle.speed_factor = 1
        vehicle.set_safemode(True)
        return True
