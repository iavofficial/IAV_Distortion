from DataModel.Effects.HackingEffects.HackedEffect import HackedEffect
from DataModel.Effects.VehicleEffectList import VehicleEffectIdentification
from DataModel.Vehicle import Vehicle
import asyncio
import random


class HackedSporadicOTurn(HackedEffect):
    def identify(self) -> VehicleEffectIdentification:
        return VehicleEffectIdentification.HACKED_SPORADIC_O_TURNS

    def can_be_applied(self, vehicle: Vehicle) -> bool:
        _ = vehicle
        return True

    def conflicts_with(self) -> list[VehicleEffectIdentification]:
        conflict_list: list[VehicleEffectIdentification] = super().conflicts_with()
        conflict_list.append(VehicleEffectIdentification.HACKED_NO_DRIVING)
        return conflict_list

    def on_start(self, vehicle: 'Vehicle') -> bool:
        super().on_start(vehicle)
        self.remove_other_hacking_effects(vehicle)
        self.task = asyncio.create_task(self.perform_uturns(vehicle))  # create an async task
        return True

    def on_end(self, vehicle: 'Vehicle') -> bool:
        super().on_end(vehicle)
        self.task.cancel()  # cancel the task
        return True

    async def perform_uturns(self, vehicle: 'Vehicle') -> None:
        while True:
            vehicle.request_uturn()  # first u-turn of the pair
            await asyncio.sleep(2)  # delay 2 seconds
            vehicle.request_uturn()  # second u-turn of the pair
            await asyncio.sleep(random.uniform(4, 12))  # random delay before the next pair
