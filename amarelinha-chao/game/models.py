from dataclasses import dataclass

import pygame


@dataclass(frozen=True)
class Tile:
    number: int
    rect: pygame.Rect
