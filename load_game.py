# main.py
import sys
from pathlib import Path
import yaml

from uno import Game, Card
from uno import CardType
from uno import Color
from uno_pygame import UnoObserverUI

SAVES_DIR = Path(__file__).parent / "saved_games"

def parse_card(card_str: str) -> Card:
    parts = card_str.split(" ", 1)
    if len(parts) == 2:
        color_str, type_str = parts
        return Card(color=Color(color_str), card_type=CardType(type_str))
    elif len(parts) == 1:
        return Card(color=Color.WILD, card_type=CardType(parts[0]))
    raise ValueError(f"Invalid card string: {card_str}")

def _latest_save(path: Path) -> Path | None:
    if not path.exists():
        return None
    candidates = sorted(
        (p for p in path.iterdir() if p.suffix.lower() in (".yml", ".yaml")),
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )
    return candidates[0] if candidates else None

def load_game(path: Path) -> tuple[Game, list[int | None]] | None:
    with open(path, "r") as f:
        data = yaml.safe_load(f)

    if "deck" not in data or not data["deck"]:
        return None

    try:
        cards = [parse_card(s) for s in data["deck"]]
    except ValueError as e:
        print(f"[load] Error parsing cards: {e}")
        return None

    game = Game(player_count=4)
    game.deck.cards = cards
    game.start_game(shuffle=False)

    moves = data.get("moves", [])
    return game, moves

def main() -> int:
    save_path = _latest_save(SAVES_DIR)

    if save_path:
        loaded = load_game(save_path)
        if loaded is not None:
            print(f"[load] Loaded game from {save_path}")
            game, moves = loaded
            ui = UnoObserverUI(game, fullscreen=True)
            ui.moves = moves
            return ui.run()

    game = Game(player_count=4)
    game.start_game()
    ui = UnoObserverUI(game, fullscreen=True)
    return ui.run()

if __name__ == "__main__":
    sys.exit(main())
