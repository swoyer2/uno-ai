# pygame_things/hand.py
from __future__ import annotations

import math
from typing import List, Tuple, Optional

import pygame
from .card import CardSprite


class Hand:
    """
    Arrange and draw a fanned hand of CardSprite objects.

    Parameters
    ----------
    cards : list[CardSprite]
        The sprites to display (images should already be scaled if desired).
    center : (int, int)
        The visual center of the hand (roughly where the middle card sits).
    fan_angle_deg : float
        Total angular spread across the hand (e.g., 60 degrees).
    base_angle_deg : float
        Base orientation: 0 = bottom, 180 = top, 90 = left, -90 = right.
    spacing : int
        Baseline horizontal spacing (pixels) used before inward edge pull.
    arc_height : float
        How much the row bows into an arc (pixels of lift at the center).
    scale_by_rotation : bool
        If True, uses rotozoom for better quality on rotation (slightly heavier).
    edge_pull : float
        Pull outer cards inward (0..1). Higher => edges come in more.
    arc_power : float
        Curve exponent for vertical lift; <1 => stronger center lift.
    """

    def __init__(
        self,
        cards: List[CardSprite],
        center: Tuple[int, int],
        fan_angle_deg: float = 60.0,
        base_angle_deg: float = 0.0,
        spacing: int = 44,
        arc_height: float = 22.0,
        scale_by_rotation: bool = True,
        edge_pull: float = 0.35,
        arc_power: float = 0.6,
    ) -> None:
        self.cards = cards
        self.center = center
        self.fan_angle_deg = float(fan_angle_deg)
        self.base_angle_deg = float(base_angle_deg)
        self.spacing = int(spacing)
        self.arc_height = float(arc_height)
        self.scale_by_rotation = bool(scale_by_rotation)
        self.edge_pull = float(edge_pull)
        self.arc_power = float(arc_power)

    # ---------- API ----------

    def set_cards(self, cards: List[CardSprite]) -> None:
        self.cards = cards

    def set_center(self, center: Tuple[int, int]) -> None:
        self.center = center

    def draw(self, surface: pygame.Surface, mouse_pos: Optional[Tuple[int, int]] = None) -> None:
        """
        Draw the hand. Does NOT modify CardSprites' images/rects; we render
        rotated copies directly for this hand view.
        """
        if not self.cards:
            return

        positions, angles = self._layout()

        # Draw from edges to center so the center ends up on top.
        n = len(self.cards)
        mid = (n - 1) * 0.5
        order = sorted(range(n), key=lambda i: abs(i - mid), reverse=True)

        for i in order:
            card = self.cards[i]
            cx, cy = positions[i]
            angle = angles[i] + self.base_angle_deg

            if self.scale_by_rotation:
                rotated = pygame.transform.rotozoom(card.image, -angle, 1.0)
            else:
                rotated = pygame.transform.rotate(card.image, -angle)

            rect = rotated.get_rect(center=(int(cx), int(cy)))
            surface.blit(rotated, rect.topleft)

    # ---------- Layout math ----------

    def _layout(self) -> Tuple[List[Tuple[float, float]], List[float]]:
        """
        Compute per-card centers and relative angles (degrees) across the fan,
        before applying the base hand rotation.
        """
        n = len(self.cards)
        cx, cy = self.center

        if n == 1:
            return [(cx, cy)], [0.0]

        # Evenly spaced angles across the fan, e.g., [-30 .. +30]
        rel_angles = [
            self._lerp(-self.fan_angle_deg * 0.5, self.fan_angle_deg * 0.5, i / (n - 1))
            for i in range(n)
        ]

        mid = (n - 1) * 0.5
        xs: List[float] = []
        ys: List[float] = []

        # Non-linear X (edge pull) and stronger center lift in Y
        for i in range(n):
            # t in [-1, 1], center at 0
            t = (i - mid) / max(mid, 1e-6)

            # --- X: base spacing, then pull edges inward with a smooth factor ---
            x_base = (i - mid) * self.spacing
            inward = 1.0 - self.edge_pull * (abs(t) ** 0.8)  # ease at the edges
            x = cx + x_base * inward

            # --- Y: lift center more using a power curve ---
            lift = (1.0 - abs(t)) ** self.arc_power  # center 1.0 -> edges 0.0
            y = cy - self.arc_height * lift

            xs.append(x)
            ys.append(y)

        # Rotate whole fan for non-bottom orientations
        if abs(self.base_angle_deg) > 1e-3:
            cos_a = math.cos(math.radians(self.base_angle_deg))
            sin_a = math.sin(math.radians(self.base_angle_deg))
            rot_xs, rot_ys = [], []
            for x, y in zip(xs, ys):
                dx, dy = (x - cx), (y - cy)
                rx = cx + dx * cos_a - dy * sin_a
                ry = cy + dx * sin_a + dy * cos_a
                rot_xs.append(rx)
                rot_ys.append(ry)
            xs, ys = rot_xs, rot_ys

        return list(zip(xs, ys)), rel_angles

    @staticmethod
    def _lerp(a: float, b: float, t: float) -> float:
        return a + (b - a) * t
