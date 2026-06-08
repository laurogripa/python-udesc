import pygame

from hopscotch.models import Tile
from hopscotch.settings import (
    COURT_BOTTOM_Y_OFFSET,
    HEIGHT,
    SKY_TILE_HEIGHT,
    SKY_TILE_OFFSET_Y,
    SKY_TILE_WIDTH,
    TILE_LAYOUT,
    TILE_SIZE,
    WIDTH,
)


def build_tiles() -> list[Tile]:
    center_x = WIDTH // 2
    bottom_y = HEIGHT - COURT_BOTTOM_Y_OFFSET

    tiles: list[Tile] = []
    for number, (x_factor, level) in TILE_LAYOUT.items():
        tile_width = SKY_TILE_WIDTH if number == 10 else TILE_SIZE
        tile_height = SKY_TILE_HEIGHT if number == 10 else TILE_SIZE
        x = center_x + int(x_factor * TILE_SIZE) - tile_width // 2
        y = bottom_y - level * TILE_SIZE
        if number == 10:
            y -= SKY_TILE_OFFSET_Y

        tiles.append(Tile(number, pygame.Rect(x, y, tile_width, tile_height)))

    return tiles
