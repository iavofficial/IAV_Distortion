from DataModel.Effects.HackingEffects.HackedEffect import HackedEffect
from DataModel.Effects.VehicleEffectList import VehicleEffectIdentification
from DataModel.Vehicle import Vehicle
import asyncio
import random


class HackedSporadicOTurn(HackedEffect):
    def identify(self) -> VehicleEffectIdentification:
        return VehicleEffectIdentification.HACKED_SPORADIC_O_TURNS

    def on_start(self, vehicle: 'Vehicle') -> None:
        super().on_start(vehicle)
        self.remove_other_hacking_effects(vehicle)
        self.task = asyncio.create_task(self.perform_uturns(vehicle))  # create an async task

    async def perform_uturns(self, vehicle: 'Vehicle') -> None:
        while True:
            vehicle.request_uturn()  # first u-turn of the pair
            await asyncio.sleep(2)  # delay 2 seconds
            vehicle.request_uturn()  # second u-turn of the pair
            await asyncio.sleep(random.uniform(4, 12))  # random delay before the next pair

    def on_end(self, vehicle: 'Vehicle') -> None:
        self.task.cancel()  # cancel the task
