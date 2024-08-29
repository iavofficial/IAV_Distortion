from datetime import datetime, timedelta

from CyberSecurityManager.CyberSecurityManager import CyberSecurityManager
from DataModel.Effects.VehicleEffect import VehicleEffect
from DataModel.Effects.VehicleEffectList import VehicleEffectIdentification
from DataModel.Vehicle import Vehicle
from EnvironmentManagement.ConfigurationHandler import ConfigurationHandler


class HackingProtection(VehicleEffect):
    def __init__(self, cyber_security_manager: CyberSecurityManager):
        super().__init__()
        self._cyber_security_manager = cyber_security_manager
        self._end_time = None

    def on_start(self, vehicle: 'Vehicle') -> None:
        super().on_start(vehicle)
        self._cyber_security_manager.activate_hacking_scenario_for_vehicle(vehicle.vehicle_id, "0")
        config_handler = ConfigurationHandler()
        duration = config_handler.get_configuration()['hacking_protection']['duration_seconds']
        self._end_time = datetime.now() + timedelta(seconds=duration)

    def identify(self) -> VehicleEffectIdentification:
        return VehicleEffectIdentification.HACKING_PROTECTION

    def effect_should_end(self, vehicle: 'Vehicle') -> bool:
        return self._end_time < datetime.now()
