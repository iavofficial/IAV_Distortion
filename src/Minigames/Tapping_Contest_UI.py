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
            self._game_length = int(self._config_handler.get_configuration()['minigame']['tapping-contest']['game-length'])
        except Exception:
            self._game_length = 10
            print("Tapping_Contest_UI: No (proper) Configuration found for \
                ['minigame']['tapping-contest']['game-length]. Using default value of 10 seconds.")

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

    def set_players(self, *players: str) -> list[str]:
        super().set_players()
        if players is None or len(players) < 2:
            print("Tapping_Contest_UI: The given player list is None or not long enough.")
            return []

        # Create game instance with current config
        try:
            self._game_length = int(self._config_handler.config_file['minigame']['tapping-contest']['game_length'])
        except Exception:
            self._game_length = 10
            print("Tapping_Contest_UI: No (proper) Configuration found for \
                ['minigame']['tapping-contest']['game-length]. Using default value of 10 seconds.")
        self._game: Tapping_Contest = Tapping_Contest(self._game_length)

        self._players.clear()
        self._players.append(players[0])
        self._players.append(players[1])
        return self.get_players()

    async def _play(self) -> str:
        # Start the 10-second game timer after countdown
        await self._start_game()

        await asyncio.sleep(self._game_length)  # Game duration

        while self._game.get_winner() == -1:
            await asyncio.sleep(1)

        if self._game.get_winner() == -2:
            # Tie
            winner = ""
        else:
            winner = self._players[self._game.get_winner()]
        self._players.clear()
        return winner

    async def _start_game(self):
        self._game.start()
        await self._sio.emit('start_game', {'game-length': self._game_length}, room="Tapping_Contest")

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

    async def _send_tie(self):
        await self._sio.emit('tie', to="Tapping_Contest")

    def description(self) -> str:
        return f"Whoever clicks more times in {self._game_length} seconds, wins."
