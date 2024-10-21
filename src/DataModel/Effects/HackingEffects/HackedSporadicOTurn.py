from DataModel.Effects.HackingEffects.HackedEffect import HackedEffect
from DataModel.Effects.VehicleEffectList import VehicleEffectIdentification
from DataModel.Vehicle import Vehicle
import threading
import random
import time

class HackedSporadicOTurn(HackedEffect):
    def __init__(self):
        super().__init__()
        self.stop_event = threading.Event()

    def identify(self) -> VehicleEffectIdentification:
        return VehicleEffectIdentification.HACKED_SPORADIC_O_TURNS

    def on_start(self, vehicle: 'Vehicle') -> None:
        super().on_start(vehicle)
        self.remove_other_hacking_effects(vehicle)
        self.thread = threading.Thread(target=self.perform_uturns, args=(vehicle,)) # a new thread for the delayed u-turn
        self.thread.start()

    def perform_uturns(self, vehicle: 'Vehicle') -> None:
        while not self.stop_event.is_set():
            # todo: check threadsafty of request_uturn
            # todo: check error-handling of request_uturn
            vehicle.request_uturn()  # first u-turn of the pair
            time.sleep(2)  # delay 2 seconds
            vehicle.request_uturn()  # second u-turn of the pair
            time.sleep(random.uniform(2, 8))  # random delay before the next pair

    def on_end(self, vehicle: 'Vehicle') -> None:
        self.stop_event.set() # set the event to stop the thread
        self.thread.join()
