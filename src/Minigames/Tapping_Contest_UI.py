from quart import Blueprint
import asyncio
from socketio import AsyncServer
from Minigames.Minigame import Minigame
from Minigames.Tapping_Contest import Tapping_Contest
from EnvironmentManagement.ConfigurationHandler import ConfigurationHandler
import random

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

        @self._sio.on('Tapping_Contest_join')
        async def on_join_game(sid: str, data):
            player_id = data['player_id']
            if player_id in self._players:
                await self._sio.enter_room(sid, "Tapping_Contest")
                await self._sio.emit('joined', {'player_id': player_id}, room=player_id)

        @self._sio.on('Tapping_Contest_click')
        async def handle_click(sid: str, data):
            player_id = data['player_id']
            await self._record_click(player_id)

    def set_players(self, *players: str) -> list[str]:
        super().set_players()
        if players is None or len(players) < 1:
            print("Tapping_Contest_UI: The given player list is None or not long enough.")
            return []

        # Create game instance with current config
        try:
            self._game_length = int(self._config_handler.get_configuration()['minigame']['tapping-contest']['game-length'])
        except Exception:
            self._game_length = 10
            print("Tapping_Contest_UI: No (proper) Configuration found for \
                ['minigame']['tapping-contest']['game-length]. Using default value of 10 seconds.")
        self._game: Tapping_Contest = Tapping_Contest(self._game_length)

        self._players.clear()
        self._players.append(players[0])
        if len(players) > 1:
            self._players.append(players[1])
        return self.get_players()

    async def _play(self) -> str:
        # Start the 10-second game timer after countdown
        await self._start_game()

        # Bot player
        if len(self._players) < 2:
            asyncio.create_task(self._play_as_bot())

        await asyncio.sleep(self._game_length)  # Game duration

        winner_index = self._game.get_winner()
        while winner_index == -1:
            winner_index = self._game.get_winner()
            await asyncio.sleep(1)

        if winner_index == -2:
            # Tie
            winner = ""
        else:
            if winner_index == 1 and len(self._players) < 2:
                winner = "bot"
            else:
                winner = self._players[winner_index]
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

    async def _play_as_bot(self):
        """
        Simulates a second player.
        """
        await asyncio.sleep(self._game_length / 2)
        current_clicks_player1 = self._game.get_clicks()[0]
        self._game.increase_clicks_for_player(1,
                                              current_clicks_player1 +
                                              int(random.random() * current_clicks_player1))
