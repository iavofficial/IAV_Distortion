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
        self.a = 1
        self.b = 2

        

    async def play(player1 : str, player2 : str = None) -> str:
        if self.a > self.b:
            return player1
        else:
            return player2
    
    def cancel() -> None:
        pass

    def description() -> str:
        return "Victory depends on the numbers entered in __init__."
