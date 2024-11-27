import logging
from datetime import datetime, timedelta

from DataModel.Effects.HackingEffects.CleanHackedEffect import CleanHackedEffect
from DataModel.Effects.VehicleEffect import VehicleEffect
from DataModel.Effects.VehicleEffectList import VehicleEffectIdentification
from DataModel.Vehicle import Vehicle
from EnvironmentManagement.ConfigurationHandler import ConfigurationHandler

logger = logging.getLogger(__name__)


class HackingProtection(VehicleEffect):

    def __init__(self):
        super().__init__()
        self._end_time = None
        self._config_handler = ConfigurationHandler()

    def identify(self) -> VehicleEffectIdentification:
        return VehicleEffectIdentification.HACKING_PROTECTION

    def can_be_applied(self, vehicle: Vehicle) -> bool:
        _ = vehicle
        return True

    def conflicts_with(self) -> list[VehicleEffectIdentification]:
        return []

    def on_start(self, vehicle: 'Vehicle') -> bool:
        clean_effect = CleanHackedEffect("0")
        vehicle.apply_effect(clean_effect)
        vehicle.remove_effect(clean_effect)

        try:
            # TODO: Implement general config objects and handle default values there!
            duration = int(self._config_handler.get_configuration()['hacking_protection']['portection_duration_s'])
        except KeyError:
            duration = 15

        self._end_time = datetime.now() + timedelta(seconds=duration)

        return True

    def on_end(self, vehicle: 'Vehicle') -> None:
        return

    def effect_should_end(self, vehicle: 'Vehicle') -> bool:
        if self._end_time is None:
            logger.error("The effect had no valid end time set. Removing it now")
            return True
        return self._end_time < datetime.now()
