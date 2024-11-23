from quart import Blueprint
import time
import asyncio
from socketio import AsyncServer
from Minigames.Minigame import Minigame
from Minigames.Tapping_Contest import Tapping_Contest
from EnvironmentManagement.ConfigurationHandler import ConfigurationHandler


class Tapping_Contest_UI(Minigame):
    def __init__(self, sio: AsyncServer, blueprint: Blueprint, name=__name__):
        super().__init__(sio, blueprint, name)
        self._players: list[str] = []
        self._config_handler = ConfigurationHandler()
        try:
            self._game_length = int(self._config_handler.config_file['minigame']['tapping-contest']['game_length'])
        except Exception:
            self._game_length = 10
            print("Tapping_Contest_UI: No (proper) Configuration found for ['minigame']['tapping-contest']['game-length]. \
                Using default value of 10 seconds.")
        self._game: Tapping_Contest = Tapping_Contest(game_length)

        @self._sio.on('join_game')
        async def on_join_game(sid: str, data):
            player_id = data['player_id']
            if player_id in self._players:
                await self._sio.enter_room(sid, "Tapping_Contest")
                await self._sio.emit('joined', {'player_id': player_id}, room=player_id)

        @self._sio.on('click')
        async def handle_click(sid: str, data):
            player_id = data['player_id']
            await self._record_click(player_id)

    async def _play(self, player1: str, player2: str) -> str:
        self._players = [player1, player2]
        self._clicks = {player1: 0, player2: 0}
        self._start_time = time.time() + 3  # 3-second countdown

        await asyncio.sleep(2)
        # Notify players of the countdown
        await self._broadcast_countdown()

        # Start the 10-second game timer after countdown
        await self._start_game()

        await asyncio.sleep(self._game_length)  # Game duration

        self._players.clear()
        self._clicks.clear()
        return winner

    async def _broadcast_countdown(self):
        for sec in range(3, -1, -1):
            await self._sio.emit('countdown', {'count': sec}, room="Tapping_Contest")
            await asyncio.sleep(1)

    async def _start_game(self):
        await self._sio.emit('start_game', {'message': 'Game started!'}, room="Tapping_Contest")

    async def _record_click(self, player_id: str):
        if player_id not in self._players:
            return
        player_index = self._players.index(player_id)
        self._game.increase_clicks_for_player(player_index, 1)

        cps = self._game.get_clicks()[player_index] / self._game.get_elapsed_time() \
            if self._game.get_elapsed_time() > 0 else 0
        await self._sio.emit(
            'update_clicks',
            {'player_id': player_id, 'clicks': self._game.get_clicks()[player_index], 'cps': cps},
            room="Tapping_Contest"
        )
