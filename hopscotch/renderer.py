import math

import pygame

from hopscotch.court import Segment, merge_segments, rect_segments
from hopscotch.models import Tile
from hopscotch.settings import (
    BG,
    COURT_LINE,
    ERROR,
    HEIGHT,
    INK,
    NUMBER_COLORS,
    PLAYER,
    PLAYER_RADIUS,
    PLAYER_SHADOW,
    START_LINE_LEFT,
    START_LINE_RIGHT,
    START_LINE_Y_OFFSET,
    Color,
)


class GameRenderer:
    def __init__(self, screen: pygame.Surface) -> None:
        self.screen = screen
        self.font = pygame.font.SysFont("arial", 34, bold=True)
        self.small_font = pygame.font.SysFont("arial", 22)
        self.sky_font = pygame.font.SysFont("arial", 30, bold=True)

    def draw(
        self,
        tiles: list[Tile],
        player_positions: list[pygame.Vector2],
        error_message: str,
    ) -> None:
        self.screen.fill(BG)
        self._draw_instructions(error_message)
        self._draw_court(tiles)
        self._draw_start_line()
        self._draw_player(player_positions)
        pygame.display.flip()

    def _draw_instructions(self, error_message: str) -> None:
        lines = [
            "Aperte 1 para",
            "pular com um pé",
            "",
            "Aperte 2 para",
            "pular com os",
            "dois pés",
        ]
        x = 52
        y = 210
        for line in lines:
            if line:
                text = self.small_font.render(line, True, INK)
                self.screen.blit(text, (x, y))
            y += 30

        if error_message:
            error = self.small_font.render(error_message, True, ERROR)
            self.screen.blit(error, (x, y + 24))

    def _draw_court(self, tiles: list[Tile]) -> None:
        court_segments: set[Segment] = set()
        for tile in tiles:
            if tile.number == 10:
                self._draw_sky_tile(tile.rect)
            else:
                court_segments.update(rect_segments(tile.rect))

        for start, end in merge_segments(court_segments):
            pygame.draw.line(self.screen, COURT_LINE, start, end, 2)

        for tile in tiles:
            self._draw_tile_label(tile)

    def _draw_tile_label(self, tile: Tile) -> None:
        label = "CÉU" if tile.number == 10 else str(tile.number)
        font = self.sky_font if tile.number == 10 else self.font
        center = (
            (tile.rect.centerx, tile.rect.centery + 8) if tile.number == 10 else tile.rect.center
        )
        number = font.render(label, True, NUMBER_COLORS[tile.number])
        number_rect = number.get_rect(center=center)
        self.screen.blit(number, number_rect)

    def _draw_start_line(self) -> None:
        start_y = HEIGHT - START_LINE_Y_OFFSET
        self._draw_crayon_line((START_LINE_LEFT, start_y), (START_LINE_RIGHT, start_y), INK, 4)

    def _draw_player(self, player_positions: list[pygame.Vector2]) -> None:
        for position in player_positions:
            shadow_center = (int(position.x + 5), int(position.y + 7))
            center = (int(position.x), int(position.y))
            pygame.draw.circle(self.screen, PLAYER_SHADOW, shadow_center, PLAYER_RADIUS)
            pygame.draw.circle(self.screen, PLAYER, center, PLAYER_RADIUS)
            pygame.draw.circle(self.screen, INK, center, PLAYER_RADIUS, width=3)

    def _draw_sky_tile(self, rect: pygame.Rect) -> None:
        scale = 4
        padding = 4
        width = rect.width
        height = rect.height
        radius = width / 2
        side_top = radius
        center_x = width / 2

        surface = pygame.Surface(
            ((width + padding * 2) * scale, (height + padding * 2) * scale),
            pygame.SRCALPHA,
        )

        local_points: list[tuple[float, float]] = [(0, height), (0, side_top)]
        for step in range(72, -1, -1):
            angle = math.pi * step / 72
            x = center_x + math.cos(angle) * radius
            y = side_top - math.sin(angle) * radius
            local_points.append((x, y))
        local_points.extend([(width, height), (0, height)])

        points = [
            (round((x + padding) * scale), round((y + padding) * scale)) for x, y in local_points
        ]
        pygame.draw.lines(surface, COURT_LINE, False, points, 2 * scale)

        smooth = pygame.transform.smoothscale(
            surface,
            (surface.get_width() // scale, surface.get_height() // scale),
        )
        self.screen.blit(smooth, (rect.left - padding, rect.top - padding))

    def _draw_crayon_line(
        self,
        start: tuple[int, int],
        end: tuple[int, int],
        color: Color,
        width: int,
    ) -> None:
        offsets = [(0, 0), (1, -1), (-1, 1)]
        for dx, dy in offsets:
            pygame.draw.line(
                self.screen,
                color,
                (start[0] + dx, start[1] + dy),
                (end[0] + dx, end[1] + dy),
                width,
            )
