from datetime import datetime, timedelta

from DataModel.Effects.HackingEffects.CleanHackedEffect import CleanHackedEffect
from DataModel.Effects.VehicleEffect import VehicleEffect
from DataModel.Effects.VehicleEffectList import VehicleEffectIdentification
from DataModel.Vehicle import Vehicle
from EnvironmentManagement.ConfigurationHandler import ConfigurationHandler


class HackingProtection(VehicleEffect):
    def __init__(self):
        super().__init__()
        self._end_time = None

    def on_start(self, vehicle: 'Vehicle') -> None:
        super().on_start(vehicle)
        clean_effect = CleanHackedEffect("0")
        vehicle.apply_effect(clean_effect)
        vehicle.remove_effect(clean_effect)
        config_handler = ConfigurationHandler()
        try:
            # TODO: Implement general config objects and handle default values there!
            duration = config_handler.get_configuration()['hacking_protection']['duration_seconds']
        except KeyError:
            duration = 60
        self._end_time = datetime.now() + timedelta(seconds=duration)

    def identify(self) -> VehicleEffectIdentification:
        return VehicleEffectIdentification.HACKING_PROTECTION

    def effect_should_end(self, vehicle: 'Vehicle') -> bool:
        return self._end_time < datetime.now()
