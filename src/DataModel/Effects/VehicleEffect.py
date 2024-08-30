from abc import ABC, abstractmethod

from DataModel.Effects.VehicleEffectList import VehicleEffectIdentification

from typing import TYPE_CHECKING

# fix circular import that only occurs because of type hinting
if TYPE_CHECKING:
    from DataModel.Vehicle import Vehicle


class VehicleEffect(ABC):
    """
    Class that represents a effect on a vehicle
    """
    def __init__(self):
        pass

    @abstractmethod
    def identify(self) -> VehicleEffectIdentification:
        """
        Identifies the Effect type by returning an Enum
        """
        raise NotImplementedError

    def can_be_applied(self, vehicle: 'Vehicle') -> bool:
        """
        Returns whether the effect can be applied to a Vehicle
        """
        _ = vehicle
        return True

    def on_start(self, vehicle: 'Vehicle') -> None:
        """
        Runs when added to a vehicle. Can also be used to start a background task
        """
        pass

    def on_end(self, vehicle: 'Vehicle') -> None:
        """
        Runs when removed from a vehicle. Should be used for cleaning up
        """
        pass

    @abstractmethod
    def effect_should_end(self, vehicle: 'Vehicle') -> bool:
        """
        Returns whether the effect should be removed on next cleanup run
        """
        raise NotImplementedError
