from Minigames.Minigame import Minigame

from quart import Blueprint
import asyncio

from socketio import AsyncServer


class Minigame_Test(Minigame):

    def __init__(self, sio: AsyncServer, namespace: str, blueprint: Blueprint | None = None, name=__name__):
        super().__init__(sio, blueprint, name)
        self.values: dict = {}

        @self._sio.on('minigame_test_value_submit')
        def on_value_submit(sid: str, data: dict) -> None:
            """
            Store the submitted value of the player in a dict
            """
            player = data["player"]
            self.values[player] = data["value"]
            print("VALUES", self.values)
            print("PLAYER", player, "HAS SUBMITTED", data["value"])

    async def _play(self) -> str:
        self.values.clear()
        player1 = self._players[0]
        player2 = self._players[1]
        while player1 not in self.values.keys() or player2 not in self.values.keys():
            await asyncio.sleep(1.0)
        player1_value: str = self.values[player1]
        player2_value: str = self.values[player2]
        print("PLAYER1 VALUE", player1_value, "PLAYER2 VALUE", player2_value)

        self._players.clear()
        self._ready_players.clear()

        if len(player1_value) > len(player2_value):
            return player1
        else:
            return player2

    def set_players(self, *players: str) -> list[str]:
        """
        Sets the specified players as players associated with this game
        """
        if players is None or len(players) < 2:
            raise Exception(f"Not enough players were given for minigame {self.get_name()}.")
        self._players.clear()
        self._players.append(players[0])
        self._players.append(players[1])
        return self.get_players()

    def description(self) -> str:
        return "Longest text = winner"

    def cancel(self) -> None:
        super().cancel()
        self.values.clear()
