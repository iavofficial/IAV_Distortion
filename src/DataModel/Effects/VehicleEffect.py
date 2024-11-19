from abc import ABC, abstractmethod

from DataModel.Effects.VehicleEffectList import VehicleEffectIdentification

from typing import TYPE_CHECKING, List

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

    @abstractmethod
    def can_be_applied(self, vehicle: 'Vehicle') -> bool:
        """
        Returns whether the effect can be applied to a Vehicle
        """
        raise NotImplementedError

    @abstractmethod
    def on_start(self, vehicle: 'Vehicle') -> bool:
        """
        Runs when added to a vehicle. Can also be used to start a background task
        """
        raise NotImplementedError

    @abstractmethod
    def on_end(self, vehicle: 'Vehicle') -> None:
        """
        Runs when removed from a vehicle. Should be used for cleaning up
        """
        raise NotImplementedError

    @abstractmethod
    def effect_should_end(self, vehicle: 'Vehicle') -> bool:
        """
        Returns whether the effect should be removed on next cleanup run
        """
        raise NotImplementedError

    @abstractmethod
    def conflicts_with(self) -> List[VehicleEffectIdentification]:
        """
        Returns a list of other effects that prevent this effect from being applied
        """
        raise NotImplementedError
