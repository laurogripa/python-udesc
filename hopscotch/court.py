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

Point = tuple[int, int]
Segment = tuple[Point, Point]
Span = tuple[int, int]


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


def rect_segments(rect: pygame.Rect) -> set[Segment]:
    return {
        (rect.topleft, rect.topright),
        (rect.topright, rect.bottomright),
        (rect.bottomleft, rect.bottomright),
        (rect.topleft, rect.bottomleft),
    }


def merge_segments(segments: set[Segment]) -> list[Segment]:
    horizontals: dict[int, list[Span]] = {}
    verticals: dict[int, list[Span]] = {}

    for start, end in segments:
        if start[1] == end[1]:
            y = start[1]
            x1, x2 = sorted((start[0], end[0]))
            horizontals.setdefault(y, []).append((x1, x2))
        elif start[0] == end[0]:
            x = start[0]
            y1, y2 = sorted((start[1], end[1]))
            verticals.setdefault(x, []).append((y1, y2))

    merged: list[Segment] = []
    for y, spans in horizontals.items():
        merged.extend(((x1, y), (x2, y)) for x1, x2 in merge_spans(spans))

    for x, spans in verticals.items():
        merged.extend(((x, y1), (x, y2)) for y1, y2 in merge_spans(spans))

    return merged


def merge_spans(spans: list[Span]) -> list[Span]:
    merged: list[Span] = []
    for start, end in sorted(spans):
        if not merged or start > merged[-1][1]:
            merged.append((start, end))
            continue

        previous_start, previous_end = merged[-1]
        merged[-1] = (previous_start, max(previous_end, end))

    return merged
