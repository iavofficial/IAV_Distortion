import time


class Tapping_Contest():
    def __init__(self, game_length: int):
        """
        Parameters:
        -----------
        game_length: int
            Time duration after which the game ends automatically in seconds.
        """
        self._game_length = game_length

    def start(self) -> None:
        """
        Starts the game and timer.
        """
        self._players_clicks: list[int] = [0, 0]
        self._start_time = time.time()

    def increase_clicks_for_player(self, player: int, clicks: int) -> None:
        """
        Increase the clicks for the specified player for the specified amount.

        Parameters:
        -----------
        player: int
            Number of the player [0-1]
        clicks: int
            Amount of clicks to increase by
        """

        if self._time_ran_out():
            print(f"Tapping_Contest: An Input was made for player {player}, but the game has already ended. \
                Ignoring the request.")
            return

        self._players_clicks[player] += clicks

    def get_winner(self) -> int:
        """
        Get the winner of the game.

        Returns:
        --------
        int: Number/Index of the winner [0-1]. -1 while the game is still running. -2 in case of tie.
        """

        if self._time_ran_out():
            print("Tapping_Contest: Winner was requested, but the game is not over yet. Returning -1.")
            return -1

        if self._players_clicks[0] > self._players_clicks[1]:
            return 0
        elif self._players_clicks[1] > self._players_clicks[0]:
            return 1
        else:
            return -2

    def get_clicks(self) -> list[int]:
        """
        Get a copy of the taps list.

        Returns:
        --------
        list[int]: amount of recorded taps for both players at their corresponding indices.
        """
        return self._players_clicks.copy()

    def _time_ran_out(self) -> bool:
        """
        Check if the time has run out.
        """
        return time.time() - self._start_time > self._game_length

    def get_elapsed_time(self) -> float:
        return time.time() - self._start_time
