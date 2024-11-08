from Minigames.Minigame import Minigame

from quart import Blueprint, render_template, request
import uuid
import logging
import asyncio
import time

from socketio import AsyncServer
from abc import abstractmethod

class Minigame_Test(Minigame):


    def __init__(self, sio: AsyncServer, blueprint : Blueprint, name=__name__):
        super().__init__(sio, blueprint, name)
        self.values : dict = {}

        @self._sio.on('minigame_test_value_submit')
        def on_value_submit(sid: str, data: dict) -> None:
            """
            Store the submitted value of the player in a dict
            """
            player = data["player"]
            self.values[player] = data["value"]
            print("VALUES", self.values)
            print("PLAYER", player, "HAS SUBMITTED", data["value"])
        

    async def play(self, player1 : str, player2 : str = None) -> str:
        while player1 not in self.values.keys() or player2 not in self.values.keys():
            await asyncio.sleep(1.0)
        player1_value : str = self.values[player1]
        player2_value : str = self.values[player2]
        print("PLAYER1 VALUE", player1_value, "PLAYER2 VALUE", player2_value)
        if len(player1_value) > len(player2_value):
            return player1
        else:
            return player2
    
    def cancel(self) -> None:
        return

    def description(self) -> str:
        return "Longest text = winner"

   