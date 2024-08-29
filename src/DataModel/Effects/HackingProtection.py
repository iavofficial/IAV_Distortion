from datetime import datetime, timedelta

from CyberSecurityManager.CyberSecurityManager import CyberSecurityManager
from DataModel.Effects.VehicleEffect import VehicleEffect
from DataModel.Effects.VehicleEffectList import VehicleEffectIdentification
from DataModel.Vehicle import Vehicle


class HackingProtection(VehicleEffect):
    def __init__(self, cyber_security_manager: CyberSecurityManager):
        super().__init__()
        self._cyber_security_manager = cyber_security_manager
        self._end_time = None

    def on_start(self, vehicle: 'Vehicle') -> None:
        super().on_start(vehicle)
        self._cyber_security_manager.activate_hacking_scenario_for_vehicle(vehicle.vehicle_id, "0")
        self._end_time = datetime.now() + timedelta(minutes=1)

    def identify(self) -> VehicleEffectIdentification:
        return VehicleEffectIdentification.HACKING_PROTECTION

    def effect_should_end(self, vehicle: 'Vehicle') -> bool:
        return self._end_time < datetime.now()
