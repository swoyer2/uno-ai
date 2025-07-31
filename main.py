# main.py
import sys
from pathlib import Path
import yaml

from uno import Game, Card
from uno import CardType
from uno import Color
from uno_pygame import UnoObserverUI


SAVES_DIR = Path(__file__).parent / "saved_games"


def _latest_save(path: Path) -> Path | None:
    if not path.exists():
        return None
    candidates = sorted((p for p in path.iterdir() if p.suffix.lower() in (".yml", ".yaml")),
                        key=lambda p: p.stat().st_mtime,
                        reverse=True)
    return candidates[0] if candidates else None


def _reconstruct_cards(objs: list[dict]) -> list[Card]:
    """Expect list of {'type': 'REVERSE', 'color': 'RED'} dicts."""
    cards: list[Card] = []
    for o in objs:
        try:
            card_type = CardType[o["type"]]
            color = Color[o["color"]]
            cards.append(Card(color, card_type))
        except Exception:
            # Ignore malformed entries
            continue
    return cards


def _load_game_from_yaml(save_path: Path) -> Game | None:
    """
    Try to load a game from a YAML file.
    Supported schema:
      version/meta (optional)
      deck:           [{type, color}, ...]   # remaining draw pile (top is end)
      discard_pile:   [{type, color}, ...]   # played pile (top is last)
    """
    try:
        with open(save_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    except Exception as e:
        print(f"[load] Failed to read {save_path}: {e}")
        return None

    # If this looks like the minimal schema with stringified cards, we can’t rebuild.
    if data and isinstance(data.get("deck"), list) and data["deck"] and isinstance(data["deck"][0], str):
        print("[load] Found minimal YAML (stringified cards). Cannot reconstruct state; using fresh game.")
        return None

    # Pull meta if present
    player_count = 4
    meta = data.get("meta") or {}
    if isinstance(meta, dict) and isinstance(meta.get("player_count"), int):
        player_count = meta["player_count"]

    # Build a game object without calling setup_game(); we assume your Game allows that.
    game = Game(player_count=player_count)

    # If your Game.__init__ auto-deals, and you want a clean slate when loading,
    # you could add a Game(reset=True) flag in your codebase. For now we just overwrite piles.

    # Reconstruct deck/discard if available
    deck_list = data.get("deck") or []
    discard_list = data.get("discard_pile") or []

    if isinstance(deck_list, list) and deck_list and isinstance(deck_list[0], dict):
        game.deck.cards = _reconstruct_cards(deck_list)

    if isinstance(discard_list, list) and discard_list and isinstance(discard_list[0], dict):
        game.played_cards = _reconstruct_cards(discard_list)

    # Optional: restore turn/meta if present
    if isinstance(meta.get("whos_turn"), int):
        game.whos_turn = meta["whos_turn"]
    if isinstance(meta.get("clockwise_turn"), bool):
        game.clockwise_turn = meta["clockwise_turn"]
    if isinstance(meta.get("draw_debt"), int):
        game.draw_debt = meta["draw_debt"]

    return game


def main() -> int:
    # Try to load the newest save from ./saved_games
    save_path = _latest_save(SAVES_DIR)
    if save_path:
        loaded = _load_game_from_yaml(save_path)
        if loaded is not None:
            print(f"[load] Loaded game from {save_path}")
            game = loaded
            # NOTE: we skip setup_game() when a save is loaded
        else:
            game = Game(player_count=4)
            game.setup_game()
    else:
        game = Game(player_count=4)
        game.setup_game()

    ui = UnoObserverUI(game, fullscreen=True)
    return ui.run()


if __name__ == "__main__":
    sys.exit(main())
