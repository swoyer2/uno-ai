from pathlib import Path
from .game import Game
from .deck import Deck
import yaml

class GameSaver:
    def __init__(self, game: Game, save_path: Path) -> None:
        self.save_path: Path = save_path
        self.move_list: list[int | None] = []  # ints = played card index, None = draw
        self.deck: Deck = game.deck

    def save_move(self, move: int | None) -> None:
        self.move_list.append(move)

    def export(self) -> None:
        """
        YAML export:
        - deck as a list of stringified cards
        - moves as a list of ints/None
        """
        payload = {
            "deck": [str(card) for card in self.deck.cards],
            "moves": self.move_list,
        }
        self.save_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.save_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(payload, f, sort_keys=False, allow_unicode=True)
    
    @staticmethod
    def load(path: Path) -> dict:
        """Load deck + moves back from YAML as a dict."""
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        # data will look like: {"deck": ["Card(...)"], "moves": [None, 2, 4]}
        return data
