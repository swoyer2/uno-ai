import sys
import pygame  # pygame-ce
from pathlib import Path

from enums.card_type import CardType
from enums.color import Color
from pygame_things.card import CardSprite
from pygame_things.hand import Hand 
from uno import Game

WINDOW_SIZE = (1080, 720)

def make_cards(pairs, assets_root: Path) -> list[CardSprite]:
    """pairs: list[(CardType, Color)] -> CardSprite list"""
    cards = []
    for ct, col in pairs:
        cards.append(
            CardSprite(
                card_type=ct,
                color=col,
                position=(0, 0),       # Hand will place/rotate when drawing
                number_offset=(0, 0),
                assets_root=assets_root,
            )
        )
    return cards

def main() -> int:
    pygame.init()
    try:
        screen = pygame.display.set_mode(WINDOW_SIZE, pygame.RESIZABLE)
        pygame.display.set_caption("UNO Hand Demo (pygame-ce)")
        clock = pygame.time.Clock()

        # Background
        bg_src = pygame.image.load(str(Path("uno-pygame/assets/background.png"))).convert()
        background = pygame.transform.smoothscale(bg_src, screen.get_size())

        # Game logic placeholder (not used below, but you can wire it up)
        uno_game_logic = Game(player_count=4)

        # --- Build some demo hands ---
        assets_root = Path("uno-pygame/assets")

        bottom_cards = make_cards(
            [
                (CardType.ONE, Color.RED),
                (CardType.TWO, Color.GREEN),
                (CardType.THREE, Color.BLUE),
                (CardType.FOUR, Color.YELLOW),
                (CardType.SKIP, Color.RED),
                (CardType.NINE, Color.BLUE),
            ],
            assets_root,
        )

        top_cards = make_cards(
            [
                (CardType.FIVE, Color.GREEN),
                (CardType.SEVEN, Color.YELLOW),
                (CardType.REVERSE, Color.BLUE),
                (CardType.DRAW_TWO, Color.RED),
                (CardType.EIGHT, Color.GREEN),
            ],
            assets_root,
        )

        left_cards = make_cards(
            [
                (CardType.TWO, Color.YELLOW),
                (CardType.THREE, Color.YELLOW),
                (CardType.FOUR, Color.YELLOW),
                (CardType.FIVE, Color.YELLOW),
            ],
            assets_root,
        )

        right_cards = make_cards(
            [
                (CardType.SEVEN, Color.RED),
                (CardType.SKIP, Color.GREEN),
                (CardType.REVERSE, Color.RED),
                (CardType.DRAW_TWO, Color.BLUE),
            ],
            assets_root,
        )

        # --- Create Hand views (positions will update on resize) ---
        def mk_hands():
            w, h = screen.get_width(), screen.get_height()
            return (
                Hand(  # bottom player
                    cards=bottom_cards,
                    center=(w // 2, h - 130),
                    fan_angle_deg=75,
                    base_angle_deg=0,
                    spacing=54,
                    arc_height=24,
                ),
                Hand(  # top player
                    cards=top_cards,
                    center=(w // 2, 130),
                    fan_angle_deg=75,
                    base_angle_deg=180,
                    spacing=54,
                    arc_height=24,
                ),
                Hand(  # left player
                    cards=left_cards,
                    center=(140, h // 2),
                    fan_angle_deg=60,
                    base_angle_deg=90,
                    spacing=50,
                    arc_height=18,
                ),
                Hand(  # right player
                    cards=right_cards,
                    center=(w - 140, h // 2),
                    fan_angle_deg=60,
                    base_angle_deg=-90,
                    spacing=50,
                    arc_height=18,
                ),
            )

        hand_bottom, hand_top, hand_left, hand_right = mk_hands()

        running = True
        while running:
            dt = clock.tick(60)  # ~60 FPS

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    running = False
                elif event.type == pygame.VIDEORESIZE:
                    # Re-create the display surface and rescale background
                    screen = pygame.display.set_mode(event.size, pygame.RESIZABLE)
                    background = pygame.transform.smoothscale(bg_src, event.size)
                    # Re-center the hands for the new size
                    hand_bottom, hand_top, hand_left, hand_right = mk_hands()

            # --- Draw ---
            screen.blit(background, (0, 0))
            hand_bottom.draw(screen)
            hand_top.draw(screen)
            hand_left.draw(screen)
            hand_right.draw(screen)
            pygame.display.flip()

        return 0
    finally:
        pygame.quit()

if __name__ == "__main__":
    sys.exit(main())
