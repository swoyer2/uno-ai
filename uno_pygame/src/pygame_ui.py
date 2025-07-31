# pygame_things/pygame_ui.py
import pygame  # pygame-ce
from pathlib import Path
from typing import TYPE_CHECKING, TypedDict, Optional

from .card import CardSprite
from .hand import Hand
from uno import Game

if TYPE_CHECKING:
    # Ensure uno/__init__.py exports Card; otherwise: from uno.card import Card
    from uno import Card

ASSETS_ROOT = Path("uno_pygame/assets")
CARD_SCALE = 0.8          # card scaling for hands and last-played card
DECK_SCALE = CARD_SCALE   # deck image scale; keep in sync with cards for visual parity

# ---------- spacing helpers ----------

def spacing_for_count(
    n: int,
    card_width: int,
    screen_width: int,
    *,
    target_overlap: float = 0.20,  # smaller => more visible (bigger gap)
    min_spacing: int = 80,
    max_spacing: int = 156,
    margin_px: int | None = None,
) -> int:
    """
    Compute spacing from card width and screen width.
    target_overlap: 0.0 (no overlap) .. 1.0 (full overlap)
    """
    if n <= 1:
        return 0

    visible = int(card_width * (1.0 - target_overlap))
    margin = margin_px if margin_px is not None else max(24, screen_width // 40)
    max_by_screen = (screen_width - 2 * margin) // max(n, 1)
    spacing = min(visible, max_by_screen)
    return max(min_spacing, min(max_spacing, spacing))


class HandParams(TypedDict):
    fan_angle_deg: float
    base_angle_deg: float
    spacing: int
    arc_height: float


def cards_to_faceup_sprites(cards: list["Card"], assets_root: Path) -> list[CardSprite]:
    """Convert uno.Game cards -> list of face-up CardSprites."""
    sprites: list[CardSprite] = []
    for c in cards:
        sprites.append(
            CardSprite(
                card_type=c.card_type,
                color=c.color,
                position=(0, 0),
                number_offset=(0, 0),
                assets_root=assets_root,
                scale=CARD_SCALE,
            )
        )
    return sprites


def layout_hands(screen: pygame.Surface, hands_cards: list[list[CardSprite]]) -> tuple[Hand, ...]:
    """Build Hand objects for up to 4 players in order: bottom, left, top, right."""
    w, h = screen.get_width(), screen.get_height()

    # Use first available card to read width (guards against empty hands)
    card_width = None
    for lst in hands_cards:
        if lst:
            card_width = lst[0].rect.w
            break
    if card_width is None:
        card_width = 100  # fallback

    def hand_params(idx: int, n_cards: int) -> HandParams:
        base_angle = (0, 90, 180, -90)[idx]
        # Wider default fan for better visibility; scales with count
        fan = float(min(120.0, 90.0 + max(0, n_cards - 5) * 4.0))
        return {
            "fan_angle_deg": fan,
            "base_angle_deg": float(base_angle),
            "spacing": spacing_for_count(n_cards, card_width, w),
            "arc_height": 30.0 if base_angle in (0, 180) else 24.0,
        }

    centers = [
        (w // 2, h - 130),   # bottom
        (140,     h // 2),   # left
        (w // 2,  130),      # top
        (w - 140, h // 2),   # right
    ]

    hands = [
        Hand(
            cards=sprites,
            center=centers[i],
            **hand_params(i, len(sprites)),
            # Assuming you're using the improved Hand with these extra params:
            edge_pull=0.35,
            arc_power=0.55,
        )
        for i, sprites in enumerate(hands_cards)
    ]
    return tuple(hands)


# ---------- main UI wrapper ----------

class UnoObserverUI:
    """
    Encapsulates the pygame UI for observing an UNO game.
    Draws deck (left of center) and last played card (to its right), and fans all hands face-up.
    """

    def __init__(
        self,
        game: Game,
        assets_root: Path = ASSETS_ROOT,
        fullscreen: bool = True,
        window_size: tuple[int, int] = (1080, 720),
    ) -> None:
        self.game = game
        self.assets_root = assets_root
        self.fullscreen = fullscreen
        self.initial_window_size = window_size

        self.screen: Optional[pygame.Surface] = None

        # Background
        self.background_src: Optional[pygame.Surface] = None
        self.background: Optional[pygame.Surface] = None

        # Deck (draw pile)
        self.deck_src: Optional[pygame.Surface] = None
        self.deck_image: Optional[pygame.Surface] = None
        self.deck_rect: Optional[pygame.Rect] = None

        # Last played card (discard top)
        self.last_sprite: Optional[CardSprite] = None
        self.last_rect: Optional[pygame.Rect] = None

        # Hands
        self.hands: tuple[Hand, ...] = tuple()

    # --- setup & rebuild ---

    def init_display(self) -> None:
        flags = pygame.RESIZABLE | (pygame.FULLSCREEN if self.fullscreen else 0)
        size = (0, 0) if self.fullscreen else self.initial_window_size
        self.screen = pygame.display.set_mode(size, flags)
        pygame.display.set_caption("UNO Observer (pygame-ce)")

        # Background
        self.background_src = pygame.image.load(str(self.assets_root / "background.png")).convert()
        self.background = pygame.transform.smoothscale(self.background_src, self.screen.get_size())

        # Deck
        self.deck_src = pygame.image.load(str(self.assets_root / "deck.png")).convert_alpha()
        self._build_deck_image_and_layout()

        # Build hands and last-played from game state
        self.refresh_hands()
        self.refresh_last_played()

    def _build_deck_image_and_layout(self) -> None:
        """Scale the deck to DECK_SCALE and position it slightly left of center."""
        assert self.screen is not None and self.deck_src is not None
        w0, h0 = self.deck_src.get_size()
        new_size = (int(w0 * DECK_SCALE), int(h0 * DECK_SCALE))
        self.deck_image = pygame.transform.smoothscale(self.deck_src, new_size)

        sw, sh = self.screen.get_size()
        dw, dh = self.deck_image.get_size()

        # Move deck a bit left of center: ~0.6 * its width
        left_shift = int(dw * 0.6)
        deck_center = (sw // 2 - left_shift, sh // 2)
        self.deck_rect = self.deck_image.get_rect(center=deck_center)

        # After deck placed, (re)place last-played if it exists
        self._layout_last_played_rect()

    def refresh_hands(self) -> None:
        """Rebuild all Hand objects from the current game state."""
        assert self.screen is not None
        players = list(self.game.players)
        hands_cards: list[list[CardSprite]] = []
        for player in players:
            player_cards = list(self.game.get_cards(player))
            sprites = cards_to_faceup_sprites(player_cards, self.assets_root)
            hands_cards.append(sprites)
        self.hands = layout_hands(self.screen, hands_cards)

    def refresh_last_played(self) -> None:
        """Build/replace the last-played CardSprite from game state and position it."""
        if self.game.played_cards:
            last_card = self.game.played_cards[-1]
            # Build a face-up sprite for the last played card
            self.last_sprite = CardSprite(
                card_type=last_card.card_type,
                color=last_card.color,
                position=(0, 0),
                number_offset=(0, 0),
                assets_root=self.assets_root,
                scale=CARD_SCALE,
            )
        else:
            self.last_sprite = None
            self.last_rect = None

        self._layout_last_played_rect()

    # --- layout helpers for piles ---

    def _layout_last_played_rect(self) -> None:
        """Position last-played to the right of the deck with a sensible gap."""
        if self.screen is None or self.deck_rect is None:
            return

        if self.last_sprite is None:
            self.last_rect = None
            return

        gap = max(18, int(self.deck_rect.width * 0.18))  # small gap scaled by deck width
        # Align vertically with deck center; place to the right of the deck
        self.last_rect = self.last_sprite.image.get_rect(
            midleft=(self.deck_rect.right + gap, self.deck_rect.centery)
        )

    # --- event helpers ---

    def handle_resize(self, size: tuple[int, int]) -> None:
        assert self.background_src is not None
        flags = pygame.RESIZABLE | (pygame.FULLSCREEN if self.fullscreen else 0)
        self.screen = pygame.display.set_mode(size, flags)
        self.background = pygame.transform.smoothscale(self.background_src, size)

        # Re-center deck and last played
        if self.deck_src is not None:
            self._build_deck_image_and_layout()

        # Re-layout hands using existing sprite objects
        self.hands = layout_hands(self.screen, [h.cards for h in self.hands])

    def toggle_fullscreen(self) -> None:
        self.fullscreen = not self.fullscreen
        # Recreate display with the new flags and rebuild everything
        self.init_display()

    # --- draw & loop ---

    def draw(self) -> None:
        assert self.screen is not None and self.background is not None
        self.screen.blit(self.background, (0, 0))

        # Draw deck
        if self.deck_image and self.deck_rect and self.game.deck:
            self.screen.blit(self.deck_image, self.deck_rect.topleft)

        # Draw last played card (if any)
        if self.last_sprite and self.last_rect:
            self.screen.blit(self.last_sprite.image, self.last_rect.topleft)

        # Draw all hands
        for hand in self.hands:
            hand.draw(self.screen)

        pygame.display.flip()

    def run(self) -> int:
        pygame.init()
        try:
            clock = pygame.time.Clock()
            self.init_display()

            running = True
            while running:
                _dt = clock.tick(60)
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            running = False
                        elif event.key == pygame.K_F11:
                            self.toggle_fullscreen()
                    elif event.type == pygame.VIDEORESIZE:
                        self.handle_resize(event.size)

                # If the Game state changes elsewhere, you can call:
                # self.refresh_last_played(); self.refresh_hands()
                self.draw()

            return 0
        finally:
            pygame.quit()
