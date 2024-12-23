from abc import ABC

from DataModel.Effects.VehicleEffect import VehicleEffect
from DataModel.Effects.VehicleEffectList import VehicleEffectIdentification
from DataModel.Vehicle import Vehicle


class HackedEffect(VehicleEffect, ABC):
    def __init__(self, scenario: str):
        super().__init__()
        self._scenario = scenario

    def identify(self) -> VehicleEffectIdentification:
        return VehicleEffectIdentification.NO_EFFECT

    def can_be_applied(self, vehicle: 'Vehicle') -> bool:
        return False

    def on_start(self, vehicle: Vehicle) -> bool:
        vehicle.hacking_scenario = self._scenario
        return True

    def on_end(self, vehicle: 'Vehicle') -> bool:
        vehicle.hacking_scenario = "0"
        return True

    def effect_should_end(self, vehicle: Vehicle) -> bool:
        return False

    def conflicts_with(self) -> list[VehicleEffectIdentification]:
        return [VehicleEffectIdentification.HACKING_PROTECTION]

    def remove_other_hacking_effects(self, vehicle: Vehicle) -> None:
        """
        Removes all hacking effects so a new one can be applied without problems
        """
        for effect in vehicle.get_active_effects():
            if effect is self:
                continue
            effect_type = effect.identify()
            if effect_type == VehicleEffectIdentification.HACKED_NO_SAFETY_MODULE or \
                    effect_type == VehicleEffectIdentification.HACKED_NO_DRIVING or \
                    effect_type == VehicleEffectIdentification.HACKED_REDUCED_SPEED or \
                    effect_type == VehicleEffectIdentification.HACKED_SPORADIC_O_TURNS or \
                    effect_type == VehicleEffectIdentification.HACKED_INVERTED_USER_INPUT:
                vehicle.remove_effect(effect)
        return
