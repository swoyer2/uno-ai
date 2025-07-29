import pygame
from pygame.sprite import Sprite
from pathlib import Path
from typing import Tuple, Dict
from uno import CardType
from uno import Color

_IMAGE_CACHE: Dict[Path, pygame.Surface] = {}

def _load_image(path: Path) -> pygame.Surface:
    key = path.resolve()
    if key not in _IMAGE_CACHE:
        _IMAGE_CACHE[key] = pygame.image.load(str(key)).convert_alpha()
    return _IMAGE_CACHE[key]

def _base_path_for_color(assets_root: Path, color: Color) -> Path | None:
    """ Returns None if wild card """
    # e.g., assets/red_base.png
    if color == Color.WILD:
        return None
    
    return assets_root / f"{color.name.lower()}_base.png"

def _overlay_path_for_card_type(assets_root: Path, card_type: CardType) -> Path:
    # e.g., assets/three.png or assets/draw_two.png
    return assets_root / f"{card_type.name.lower()}.png"

class CardSprite(Sprite):
    def __init__(
        self,
        card_type: CardType,
        color: Color,
        position: Tuple[int, int],
        number_offset: Tuple[int, int] = (0, 0),
        assets_root: Path = Path("assets"),
        scale: float = 0.5,
    ):
        super().__init__()

        # Load base (color) and overlay (number/special) images
        base_path = _base_path_for_color(assets_root, color)
        overlay_path = _overlay_path_for_card_type(assets_root, card_type)

        if base_path:
            base = _load_image(base_path)
            overlay = _load_image(overlay_path)

            # Compose once at full resolution
            composed = base.copy()
            composed.blit(overlay, overlay.get_rect(topleft=number_offset))
        
        else: # If it is a wild card (wild cards don't have color)
            overlay = _load_image(overlay_path)
            composed = overlay.copy()

        # Scale result
        if scale != 1.0:
            w, h = composed.get_size()
            new_size = (int(w * scale), int(h * scale))
            self.image: pygame.Surface = pygame.transform.smoothscale(composed, new_size)
        else:
            self.image = composed

        self.rect: pygame.Rect = self.image.get_rect(topleft=position)

    def draw(self, surface: pygame.Surface):
        surface.blit(self.image, self.rect)

    def set_position(self, x: int, y: int):
        self.rect.topleft = (x, y)
