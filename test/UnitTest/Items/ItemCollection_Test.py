from unittest.mock import Mock

from DataModel.Vehicle import Vehicle
from Items.Item import Item
from Items.ItemCollisionDetection import ItemCollisionDetector
from LocationService.Trigo import Position, Angle
from EnvironmentManagement.ConfigurationHandler import ConfigurationHandler


def test_item_collision_notification():
    """
    This tests that an item is only collected, when a location is reported that is in proximity
    """
    item_Mock = Mock(spec=Item)
    configuration_handler_mock = Mock(spec=ConfigurationHandler)
    configuration_handler_mock.get_configuration.return_value = {
                    "virtual_cars_pics": {"AB:CD:EF:12:34:56": "ABCDEF123456.svg",
                                          "GH:IJ:KL:78:90:21": "GHIJKL789021.svg"},
                    "driver": {"key1": "value1", "key2": "value2"},
                    "game_config": {"game_cfg_playing_time_limit_min": 1},
                    "item": {"item_max_count": 1}}
    item_Mock.get_position.return_value = Position(100, 100)

    item_collision_detector = ItemCollisionDetector(configuration_handler_mock)
    item_collision_detector._items.clear()
    item_collision_detector._items.append(item_Mock)

    vehicle_mock = Mock(spec=Vehicle)
    item_collision_detector.notify_new_vehicle_position(vehicle_mock, Position(1000, 900), Angle(0))
    vehicle_mock.notify_item_collected.assert_not_called()
    item_collision_detector.notify_new_vehicle_position(vehicle_mock, Position(1000, 30), Angle(0))
    vehicle_mock.notify_item_collected.assert_not_called()
    item_collision_detector.notify_new_vehicle_position(vehicle_mock, Position(30, 900), Angle(0))
    vehicle_mock.notify_item_collected.assert_not_called()

    item_collision_detector.notify_new_vehicle_position(vehicle_mock, Position(95, 105), Angle(0))
    vehicle_mock.notify_item_collected.assert_called()
    vehicle_mock.notify_item_collected.assert_called_with(item_Mock)


def test_callbacks_are_executed():
    """
    This tests that when an item gets added or removed the callback is executed
    """
    itemMock = Mock(spec=Item)
    configuration_handler_mock = Mock(spec=ConfigurationHandler)
    configuration_handler_mock.get_configuration.return_value = {
                    "virtual_cars_pics": {"AB:CD:EF:12:34:56": "ABCDEF123456.svg",
                                          "GH:IJ:KL:78:90:21": "GHIJKL789021.svg"},
                    "driver": {"key1": "value1", "key2": "value2"},
                    "game_config": {"game_cfg_playing_time_limit_min": 1},
                    "item": {"item_max_count": 1}}
    item_changed_callback = Mock()

    mut = ItemCollisionDetector(configuration_handler_mock)
    mut.set_on_item_change_callback(item_changed_callback)

    mut.add_item(itemMock)
    item_changed_callback.assert_called()

    item_changed_callback.reset_mock()

    mut.remove_item(itemMock)
    item_changed_callback.assert_called()

    item_changed_callback.reset_mock()

    mut.clear_items()
    item_changed_callback.assert_called()
