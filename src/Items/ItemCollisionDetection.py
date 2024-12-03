from typing import Callable

from DataModel.Vehicle import Vehicle
from EnvironmentManagement.ConfigurationHandler import ConfigurationHandler
from Items.Item import Item
from LocationService.Trigo import Position, Angle


class ItemCollisionDetector:
    def __init__(self,
                 configuration_handler: ConfigurationHandler = ConfigurationHandler()) -> None:

        self.config_handler: ConfigurationHandler = configuration_handler
        self._items: list[Item] = []
        self._on_item_change: Callable[[list[Item]], None] | None = None
        return

    def notify_new_vehicle_position(self, vehicle: Vehicle, vehicle_position: Position, vehicle_rotation: Angle):
        for item in self._items:
            if item.get_position() is None:
                continue
            if item.get_position().distance_to(vehicle_position) < 40:
                vehicle.notify_item_collected(item)
                self.remove_item(item)

    def set_on_item_change_callback(self, callback: Callable[[list[Item]], None]):
        self._on_item_change = callback

    def add_item(self, item: Item):
        config = self.config_handler.get_configuration()
        max_item_length = config['item']['item_max_count'] - 1
        if len(self._items) <= max_item_length:
            self._items.append(item)

        if self._on_item_change is not None:
            self._on_item_change(self._items)

    def remove_item(self, item: Item):
        self._items.remove(item)
        if self._on_item_change is not None:
            self._on_item_change(self._items)

    def clear_items(self):
        self._items.clear()
        self._on_item_change(self._items)

    def get_current_items(self):
        return self._items
