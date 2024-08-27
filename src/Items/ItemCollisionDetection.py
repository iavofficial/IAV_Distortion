from typing import List, Callable

from DataModel.Vehicle import Vehicle
from Items.Item import Item
from LocationService.Track import FullTrack
from LocationService.Trigo import Position, Angle


class ItemCollisionDetector:
    def __init__(self, track: FullTrack | None):
        self._items: List[Item] = []
        self._on_item_change: Callable[[List[Item]], None] | None = None
        for _ in range(0, 3):
            self.add_item(Item(track))

    def notify_new_vehicle_position(self, vehicle: Vehicle, vehicle_position: Position, vehicle_rotation: Angle):
        for item in self._items:
            if item.get_position().distance_to(vehicle_position) < 40:
                vehicle.notify_item_collected(item)
                self.remove_item(item)

    def notify_new_track(self, track: FullTrack):
        for item in self._items:
            item.generate_new_position(track)

    def set_on_item_change_callback(self, callback: Callable[[List[Item]], None]):
        self._on_item_change = callback

    def add_item(self, item: Item):
        self._items.append(item)
        if self._on_item_change is not None:
            self._on_item_change(self._items)

    def remove_item(self, item: Item):
        self._items.remove(item)
        if self._on_item_change is not None:
            self._on_item_change(self._items)

    def get_current_items(self):
        return self._items
