import sys
from uno import Game
from pygame_things.pygame_ui import UnoObserverUI

def main() -> int:
    game = Game(player_count=4)
    ui = UnoObserverUI(game, fullscreen=True)  # set fullscreen=False for windowed
    return ui.run()

if __name__ == "__main__":
    sys.exit(main())
