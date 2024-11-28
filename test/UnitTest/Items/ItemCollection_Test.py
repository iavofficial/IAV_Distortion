from unittest.mock import MagicMock, patch

from DataModel.Vehicle import Vehicle
from EnvironmentManagement.ConfigurationHandler import ConfigurationHandler
from Items.Item import Item
from Items.ItemCollisionDetection import ItemCollisionDetector
from LocationService.Trigo import Position, Angle


def test_item_collision_notification():
    """
    This tests that an item is only collected, when a location is reported that is in proximity
    """
    item = MagicMock(spec=Item)
    item.get_position.return_value = Position(100, 100)

    item_collision_detector = ItemCollisionDetector()
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


def test_callbacks_are_executed():
    """
    This tests that when an item gets added or removed the callback is executed
    """
    item = MagicMock(spec=Item)
    item_changed_callback = MagicMock()
    item_collision_detector = ItemCollisionDetector()

    with patch.object(ConfigurationHandler, 'get_configuration', return_value={'item':{'item_max_count': 10}}):

        item_collision_detector.set_on_item_change_callback(item_changed_callback)
        item_collision_detector.add_item(item)

    item_changed_callback.assert_called()

    item_changed_callback.reset_mock()

    item_collision_detector.remove_item(item)
    item_changed_callback.assert_called()

    item_changed_callback.reset_mock()

    item_collision_detector.clear_items()
    item_changed_callback.assert_called()
