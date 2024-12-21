import time


class Reaction_Contest():
    def __init__(self, game_length: int):
        """
        Parameters:
        -----------
        game_length: int
            Time before the box turns green in seconds.
        """
        self._game_length = game_length
        self._winner = -1

    def start(self) -> None:
        """
        Starts the game and timer for the green phase.
        """
        self._winner = -1
        self._green_box_time = time.time() + self._game_length

    def is_box_green(self) -> bool:
        return time.time() >= self._green_box_time

    def press_button(self, player: int) -> None:
        """
        Determines the winner based on which player presses the button first after it turns green.
        """
        if self.is_box_green() and self._winner == -1:
            self._winner = player

    def get_winner(self) -> int:
        """
        Get the winner of the game.
        Returns:
        --------
        int: Number/Index of the winner [0-1]. -1 if no winner yet.
        """
        return self._winner
