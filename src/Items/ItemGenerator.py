import asyncio
from asyncio import Task

from CyberSecurityManager.CyberSecurityManager import CyberSecurityManager
from DataModel.Effects.HackingProtection import HackingProtection
from Items.Item import Item
from Items.ItemCollisionDetection import ItemCollisionDetector
from LocationService.Track import FullTrack


class ItemGenerator:
    def __init__(self, item_collision_detection: ItemCollisionDetector, cyber_security_manager: CyberSecurityManager,
                 track: FullTrack | None):
        self._item_collision_detection: ItemCollisionDetector = item_collision_detection
        self._cyber_security_manager: CyberSecurityManager = cyber_security_manager
        self._track: FullTrack | None = track
        self._item_generation_task: Task | None = None
        for _ in range(0, 3):
            self._item_collision_detection.add_item(self.generate_item())

    def notify_new_track(self, track: FullTrack):
        self._track = track
        num_items = len(self._item_collision_detection.get_current_items())
        self._item_collision_detection.clear_items()
        for _ in range(0, num_items):
            self._item_collision_detection.add_item(self.generate_item())

    def generate_item(self) -> Item:
        return Item(self._track, HackingProtection(self._cyber_security_manager))

    async def start_item_generation(self) -> None:
        self._item_generation_task = asyncio.create_task(self._generate_item_task_function())

    async def _generate_item_task_function(self) -> None:
        while True:
            await asyncio.sleep(30)
            self._item_collision_detection.add_item(self.generate_item())
