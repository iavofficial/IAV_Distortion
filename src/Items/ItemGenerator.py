import asyncio
from asyncio import Task
from typing import Any

from DataModel.Effects.HackingProtection import HackingProtection
from EnvironmentManagement.ConfigurationHandler import ConfigurationHandler
from Items.Item import Item
from Items.ItemCollisionDetection import ItemCollisionDetector
from LocationService.Track import FullTrack


class ItemGenerator:
    def __init__(self,
                 item_collision_detection: ItemCollisionDetector,
                 track: FullTrack | None,
                 configuration_handler: ConfigurationHandler = ConfigurationHandler()) -> None:

        self._item_collision_detection: ItemCollisionDetector = item_collision_detection
        self._track: FullTrack | None = track
        self._item_generation_task: Task[Any] | None = None
        self._config_handler:  ConfigurationHandler = configuration_handler

        max_item_length = self._config_handler.get_configuration()['item']['item_max_count'] - 1
        for _ in range(0, max_item_length):
            self._item_collision_detection.add_item(self.generate_item())

        return

    def notify_new_track(self, track: FullTrack):
        self._track = track
        num_items = len(self._item_collision_detection.get_current_items())
        self._item_collision_detection.clear_items()
        for _ in range(0, num_items):
            self._item_collision_detection.add_item(self.generate_item())

    def generate_item(self) -> Item:
        return Item(self._track, HackingProtection())

    async def start_item_generation(self) -> None:
        self._item_generation_task = asyncio.create_task(self._generate_item_task_function())

    async def _generate_item_task_function(self) -> None:
        interval_time: int
        try:
            # TODO: Realise default values via a config object!
            interval_time = self._config_handler.get_configuration()['item']['item_spawn_interval']
        except KeyError:
            interval_time = 30
        while True:
            await asyncio.sleep(interval_time)
            self._item_collision_detection.add_item(self.generate_item())
