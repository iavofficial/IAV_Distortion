import asyncio
from time import sleep
from unittest.mock import MagicMock

import pytest

from DataModel.Effects.HackingProtection import HackingProtection
from DataModel.Effects.VehicleEffect import VehicleEffect
from DataModel.Vehicle import Vehicle
from Items.Item import Item
from VehicleManagement.VehicleController import VehicleController
from VehicleManagement.FleetController import FleetController

dummy_uuid = "FA:14:67:0F:39:FE"


@pytest.fixture
def init_vehicle():
    return Vehicle('123', disable_item_removal=True)


@pytest.mark.skip_ci
def test_get_location():
    vctrl = VehicleController()
    fleet_ctrl = FleetController()

    found_vehicles = fleet_ctrl.scan_for_anki_cars()
    mut = Vehicle(found_vehicles[0], vctrl)

    mut.speed_request = 80.0

    sleep(5)

    mut.speed_request = 0.0

    assert mut


def test_vehicle_cant_have_same_effect_twice(init_vehicle):
    """
    This test ensures that 2 items with the same identification only lead to one being added
    """
    car = init_vehicle
    cyber_mock = MagicMock()
    effect1 = HackingProtection(cyber_mock)
    item1 = Item(None, effect1)
    effect2 = HackingProtection(cyber_mock)
    item2 = Item(None, effect2)

    assert len(car._effects) == 0
    car.notify_item_collected(item1)
    assert len(car._effects) == 1
    car.notify_item_collected(item2)
    assert len(car._effects) == 1


@pytest.mark.slow
@pytest.mark.asyncio
async def test_vehicle_removes_effect():
    """
    This tests that vehicle effects are cleaned up, if they are told to
    """
    mock_effect = MagicMock(spec=VehicleEffect)
    mock_effect.effect_should_end.return_value = True
    vehicle = Vehicle('123')

    assert len(vehicle._effects) == 0
    vehicle._effects.append(mock_effect)
    await asyncio.sleep(5)
    assert len(vehicle._effects) == 0
