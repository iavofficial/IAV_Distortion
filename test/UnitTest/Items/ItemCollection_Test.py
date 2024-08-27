from unittest.mock import MagicMock

from DataModel.Vehicle import Vehicle
from Items.Item import Item
from Items.ItemCollisionDetection import ItemCollisionDetector
from LocationService.Trigo import Position, Angle


def test_item_collision_notification():
    """
    This tests that an item is only collected, when a location is reported that is in proximity
    """
    item = MagicMock(spec=Item)
    item.get_position.return_value = Position(100, 100)

    item_collision_detector = ItemCollisionDetector(None)
    item_collision_detector._items.clear()
    item_collision_detector._items.append(item)

    vehicle_mock = MagicMock(spec=Vehicle)
    item_collision_detector.notify_new_vehicle_position(vehicle_mock, Position(1000, 900), Angle(0))
    vehicle_mock.notify_item_collected.assert_not_called()
    item_collision_detector.notify_new_vehicle_position(vehicle_mock, Position(1000, 30), Angle(0))
    vehicle_mock.notify_item_collected.assert_not_called()
    item_collision_detector.notify_new_vehicle_position(vehicle_mock, Position(30, 900), Angle(0))
    vehicle_mock.notify_item_collected.assert_not_called()

    item_collision_detector.notify_new_vehicle_position(vehicle_mock, Position(95, 105), Angle(0))
    vehicle_mock.notify_item_collected.assert_called()
    vehicle_mock.notify_item_collected.assert_called_with(item)
