# Copyright 2024 IAV GmbH
#
# This file is part of the IAV Distortion project an interactive
# and educational showcase designed to demonstrate the need
# of automotive cybersecurity in a playful, engaging manner.
# and is released under the "Apache 2.0". Please see the LICENSE
# file that should have been included as part of this package.
#
from typing import TYPE_CHECKING
import logging

from DataModel.Effects.VehicleEffect import VehicleEffect
from DataModel.Effects.HackingEffects.CleanHackedEffect import CleanHackedEffect
from DataModel.Effects.HackingEffects.HackedNoDriving import HackedNoDriving
from DataModel.Effects.HackingEffects.HackedNoSafetyModule import HackedNoSafetyModule
from DataModel.Effects.HackingEffects.HackedReducedSpeed import HackedReducedSpeed
from DataModel.Effects.HackingEffects.HackedSporadicOTurn import HackedSporadicOTurn
from DataModel.Effects.HackingEffects.HackedInvertedUserInput import HackedInvertedUserInput


# fix circular import that only occurs because of type hinting
if TYPE_CHECKING:
    from EnvironmentManagement.EnvironmentManager import EnvironmentManager

logger = logging.getLogger(__name__)


def _set_scenarios() -> list[dict[str, str | VehicleEffect]]:
    scenario0 = {"id": "0",
                 "name": "normal",
                 "description": "no hacking",
                 "effect": CleanHackedEffect}

    scenario1 = {"id": "1",
                 "name": "slow_down",
                 "description": "drive with reduced speed",
                 "effect": HackedReducedSpeed}

    scenario3 = {"id": "3",
                 "name": "stop",
                 "description": "vehicle stops instantaneous",
                 "effect": HackedNoDriving}

    scenario4 = {"id": "4",
                 "name": "no safety",
                 "description": "the safemode module is deactivated",
                 "effect": HackedNoSafetyModule}

    scenario5 = {"id": "5",
                 "name": "O-turn",
                 "description": "the car perfoms a O-turn",
                 "effect": HackedSporadicOTurn}

    scenario6 = {"id": "6",
                 "name": "InputInversion",
                 "description": "the input from User is inverted",
                 "effect": HackedInvertedUserInput}

    return [scenario0, scenario1, scenario3, scenario4, scenario5, scenario6]


class CyberSecurityManager:

    def __init__(self, environment_manager: 'EnvironmentManager') -> None:
        self._hacking_scenarios = _set_scenarios()
        self._environment_manager: 'EnvironmentManager' = environment_manager

        return

    def get_all_hacking_scenarios(self) -> list[dict[str, str | VehicleEffect]]:
        return self._hacking_scenarios

    def activate_hacking_scenario_for_vehicle(self, uuid: str, scenario_id: str) -> bool:
        scenario: dict[str, str | VehicleEffect] | None = next((sce for sce in self._hacking_scenarios
                                                                if sce["id"] == scenario_id), None)
        if scenario is None:
            return False

        vehicle = self._environment_manager.get_vehicle_by_vehicle_id(uuid)
        if vehicle is None:
            logger.warning("Tried to activate scenario for the non existent vehicle %s. Ignoring the request", uuid)
            return False

        if isinstance(scenario["effect"], VehicleEffect):
            vehicle.apply_effect(scenario["effect"])

        return True

    def get_active_hacking_scenarios(self) -> dict[str, str]:
        scenario_map: dict[str, str] = {}
        for car in self._environment_manager.get_all_vehicles():
            scenario_map.update({car.vehicle_id: car.hacking_scenario})
        return scenario_map
