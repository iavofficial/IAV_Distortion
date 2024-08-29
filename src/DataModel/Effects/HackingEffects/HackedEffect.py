from abc import ABC
from typing import List

from DataModel.Effects.VehicleEffect import VehicleEffect
from DataModel.Effects.VehicleEffectList import VehicleEffectIdentification
from DataModel.Vehicle import Vehicle


class HackedEffect(VehicleEffect, ABC):
    def __init__(self, scenario: str):
        super().__init__()
        self._scenario = scenario

    def on_start(self, vehicle: 'Vehicle') -> None:
        vehicle.hacking_scenario = self._scenario

    def effect_should_end(self, vehicle: 'Vehicle') -> bool:
        return False

    def conflicts_with(self) -> List[VehicleEffectIdentification]:
        return [VehicleEffectIdentification.HACKING_PROTECTION]

    def remove_other_hacking_effects(self, vehicle: Vehicle):
        """
        Removes all hacking effects so a new one can be applied without problems
        """
        for effect in vehicle.get_active_effects():
            if effect is self:
                continue
            effect_type = effect.identify()
            if effect_type == VehicleEffectIdentification.HACKED_NO_SAFETY_MODULE or \
                    effect_type == VehicleEffectIdentification.HACKED_NO_DRIVING or \
                    effect_type == VehicleEffectIdentification.HACKED_REDUCED_SPEED:
                vehicle.remove_effect(effect)
