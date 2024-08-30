from unittest.mock import MagicMock

import pytest

from DataModel.Effects.HackingEffects.CleanHackedEffect import CleanHackedEffect
from DataModel.Effects.HackingEffects.HackedNoDriving import HackedNoDriving
from DataModel.Effects.HackingEffects.HackedNoSafetyModule import HackedNoSafetyModule
from DataModel.Effects.HackingEffects.HackedReducedSpeed import HackedReducedSpeed
from DataModel.VirtualCar import VirtualCar
from LocationService.LocationService import LocationService
from VehicleManagement.VehicleController import VehicleController


@pytest.fixture
def init_vehicle():
    location_mock = MagicMock(spec=LocationService)
    controller_mock = MagicMock(spec=VehicleController)
    car = VirtualCar('123', location_mock, disable_item_removal=True)
    return car


@pytest.fixture
def init_effects():
    cleanup_effect = CleanHackedEffect("0")
    reduced_speed_effect = HackedReducedSpeed("1")
    no_driving_effect = HackedNoDriving("3")
    no_safemodule_effect = HackedNoSafetyModule("4")
    return cleanup_effect, reduced_speed_effect, no_driving_effect, no_safemodule_effect


@pytest.mark.asyncio
async def test_cleanup_effect_works(init_vehicle, init_effects):
    """
    Tests that the cleanup effect removes other hacking effects and resets the speed factor
    """
    car = init_vehicle
    cleanup_effect, reduced_speed_effect, _, _ = init_effects
    car.apply_effect(reduced_speed_effect)

    assert reduced_speed_effect in car._effects
    car.apply_effect(cleanup_effect)
    assert reduced_speed_effect not in car._effects
    assert car.speed_factor == 1.0


@pytest.mark.asyncio
async def test_only_one_hacking_effect_can_be_active(init_vehicle, init_effects):
    """
    Tests that when multiple hacking effects are applied only one is active
    """
    car = init_vehicle
    _, reduced_speed_effect, no_driving_effect, no_safemodule_effect = init_effects
    car.apply_effect(reduced_speed_effect)

    car.apply_effect(no_driving_effect)
    assert len(car._effects) == 1

    car.apply_effect(no_safemodule_effect)
    assert len(car._effects) == 1

    car.apply_effect(reduced_speed_effect)
    assert len(car._effects) == 1


@pytest.mark.asyncio
async def test_hacking_effects_change_speedfactor(init_vehicle, init_effects):
    """
    Test that the hacking effects change the speed factor attribute of the car
    """
    car = init_vehicle
    _, reduced_speed_effect, no_driving_effect, no_safemodule_effect = init_effects
    car.apply_effect(reduced_speed_effect)
    assert car.speed_factor == 0.3
    car.remove_effect(reduced_speed_effect)

    car.apply_effect(no_driving_effect)
    assert car.speed_factor == 0.0
    car.remove_effect(no_driving_effect)

    car.apply_effect(no_safemodule_effect)
    assert not car.isSafeModeOn
    assert car.speed_factor == 1.5
    car.remove_effect(no_safemodule_effect)


@pytest.mark.asyncio
async def test_hacking_effects_restore_old_values(init_vehicle, init_effects):
    """
    Test that all hacking effects restore a speed factor of 1.0 when applied
    """
    car = init_vehicle
    _, reduced_speed_effect, no_driving_effect, no_safemodule_effect = init_effects

    car.apply_effect(reduced_speed_effect)
    car.remove_effect(reduced_speed_effect)
    assert car.speed_factor == 1.0

    car.apply_effect(no_driving_effect)
    car.remove_effect(no_driving_effect)
    assert car.speed_factor == 1.0

    car.apply_effect(no_safemodule_effect)
    car.remove_effect(no_safemodule_effect)
    assert car.speed_factor == 1.0
