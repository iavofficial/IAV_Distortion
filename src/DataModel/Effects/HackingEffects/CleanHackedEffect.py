from DataModel.Effects.VehicleEffect import VehicleEffect
from DataModel.Effects.VehicleEffectList import VehicleEffectIdentification
from DataModel.Vehicle import Vehicle


class CleanHackedEffect(VehicleEffect):

    def __init__(self, scenario: str):
        super().__init__()
        self._scenario = scenario

    def identify(self) -> VehicleEffectIdentification:
        return VehicleEffectIdentification.CLEAN_HACKED_EFFECTS

    def can_be_applied(self, vehicle: Vehicle) -> bool:
        _ = vehicle
        return True

    def conflicts_with(self) -> list[VehicleEffectIdentification]:
        return []

    def effect_should_end(self, vehicle: Vehicle) -> bool:
        # this should end immediately since it's a quick "remove all bad effects" effect
        return True

    def on_start(self, vehicle: Vehicle) -> bool:
        # remove all hacked effects
        for effect in vehicle.get_active_effects():
            effect_type = effect.identify()
            #todo : adding more hacked effect types here is arkward. change the logic 
            if effect_type == VehicleEffectIdentification.HACKED_NO_SAFETY_MODULE or \
                    effect_type == VehicleEffectIdentification.HACKED_NO_DRIVING or \
                    effect_type == VehicleEffectIdentification.HACKED_REDUCED_SPEED or \
                    effect_type == VehicleEffectIdentification.HACKED_SPORADIC_O_TURNS or \
                    effect_type == VehicleEffectIdentification.HACKED_INVERTED_USER_INPUT :
                vehicle.remove_effect(effect)
                vehicle.hacking_scenario = self._scenario
        return True

    def on_end(self, vehicle: 'Vehicle') -> None:
        return
