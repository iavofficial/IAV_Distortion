from typing import List

from DataModel.Vehicle import Vehicle
from Items.Item import Item
from LocationService.Track import FullTrack
from LocationService.Trigo import Position, Angle


class ItemCollisionDetector:
    def __init__(self, track: FullTrack | None):
        self.items: List[Item] = []
        for _ in range(0, 3):
            self.items.append(Item(track))

    def notify_new_vehicle_position(self, vehicle: Vehicle, vehicle_position: Position, vehicle_rotation: Angle):
        for item in self.items:
            if item.get_position().distance_to(vehicle_position) < 40:
                vehicle.notify_item_collected(item)
                self.items.remove(item)

    def notify_new_track(self, track: FullTrack):
        for item in self.items:
            item.generate_new_position(track)
