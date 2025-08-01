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
        Export to YAML:
        - deck is only written if file doesn't exist
        - moves are always updated
        """
        payload = {
            "moves": self.move_list
        }

        if self.save_path.exists():
            # Load existing file and preserve its deck
            with open(self.save_path, "r", encoding="utf-8") as f:
                existing = yaml.safe_load(f) or {}
            payload["deck"] = existing.get("deck", [str(card) for card in self.deck.cards])
        else:
            # First time: write full payload
            payload["deck"] = [str(card) for card in self.deck.cards]

        self.save_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.save_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(payload, f, sort_keys=False, allow_unicode=True)