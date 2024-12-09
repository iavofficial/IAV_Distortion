import asyncio
import time
from time import sleep
from unittest.mock import MagicMock

import pytest

from DataModel.Effects.HackingProtection import HackingProtection
from DataModel.Effects.VehicleEffect import VehicleEffect
from DataModel.Vehicle import Vehicle
from Items.Item import Item
from LocationService.LocationService import LocationService
from VehicleManagement.FleetController import FleetController

dummy_uuid = "FA:14:67:0F:39:FE"


@pytest.fixture
def init_vehicle():
    location_service_mock = MagicMock(spec=LocationService)
    return Vehicle('123', location_service_mock, disable_item_removal=True)


def init_vehicle_with_id(car_id: int):
    location_service_mock = MagicMock(spec=LocationService)
    return Vehicle(car_id, location_service_mock, disable_item_removal=True)


def init_vehicle_with_id(car_id: int):
    location_service_mock = MagicMock(spec=LocationService)
    return Vehicle(car_id, location_service_mock, disable_item_removal=True)


@pytest.mark.one_anki_car_needed
@pytest.mark.asyncio
async def test_get_location():
    loc_Service = LocationService(None)
    fleet_ctrl = FleetController()

    found_vehicles = await fleet_ctrl.scan_for_anki_cars()
    mut = Vehicle(found_vehicles[0], loc_Service)

    mut.request_speed_percent(80.0)

    sleep(5)

    mut.request_speed_percent(0.0)

    assert mut


def test_vehicle_cant_have_same_effect_twice(init_vehicle):
    """
    This test ensures that 2 items with the same identification only lead to one being added
    """
    car = init_vehicle
    effect1 = HackingProtection()
    item1 = Item(None, effect1)
    effect2 = HackingProtection()
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
    location_service_mock = MagicMock(spec=LocationService)
    vehicle = Vehicle('123', location_service_mock)

    assert len(vehicle._effects) == 0
    vehicle._effects.append(mock_effect)
    await asyncio.sleep(5)
    assert len(vehicle._effects) == 0


def test_vehicle_reset_proximity():
    """
    This tests if the proximity timer is reset
    """
    car = init_vehicle_with_id(123)
    car.reset_proximity_timer()
    assert car.proximity_timer == pytest.approx(time.time(), 0.0001)


def test_vehicle():
    pass
