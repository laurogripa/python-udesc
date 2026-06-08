from __future__ import annotations

import argparse
import math
from dataclasses import dataclass

import pygame


WIDTH = 900
HEIGHT = 800
FPS = 60

BG = (66, 66, 62)
INK = (247, 244, 232)
COURT_LINE = (236, 232, 216)
PLAYER = (255, 132, 83)
PLAYER_SHADOW = (92, 64, 55)
ERROR = (235, 76, 76)
NUMBER_COLORS = {
    1: (255, 216, 80),
    2: (235, 76, 154),
    3: (78, 196, 112),
    4: (250, 239, 83),
    5: (58, 185, 208),
    6: (255, 205, 82),
    7: (240, 88, 73),
    8: (243, 150, 70),
    9: (80, 193, 124),
    10: (255, 216, 80),
}


@dataclass(frozen=True)
class Tile:
    number: int
    rect: pygame.Rect


class HopscotchGame:
    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption("Amarelinha")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("arial", 34, bold=True)
        self.small_font = pygame.font.SysFont("arial", 22)
        self.sky_font = pygame.font.SysFont("arial", 30, bold=True)

        self.tiles = self._build_tiles()
        self.tile_by_number = {tile.number: tile for tile in self.tiles}
        self.hop_groups = [(1,), (2, 3), (4,), (5, 6), (7,), (8, 9), (10,)]
        self.start_pos = pygame.Vector2(WIDTH // 2, HEIGHT - 34)
        self.player_pos = self.start_pos.copy()
        self.player_positions = [self.start_pos.copy()]
        self.player_radius = 19
        self.current_group = 0
        self.error_message = ""
        self.won = False

    def _build_tiles(self) -> list[Tile]:
        size = 76
        gap = 0
        center_x = WIDTH // 2
        bottom_y = HEIGHT - 242

        layout = {
            1: (0, 0),
            2: (-0.5, 1),
            3: (0.5, 1),
            4: (0, 2),
            5: (-0.5, 3),
            6: (0.5, 3),
            7: (0, 4),
            8: (-0.5, 5),
            9: (0.5, 5),
            10: (0, 6),
        }

        tiles: list[Tile] = []
        for number, (x_factor, level) in layout.items():
            tile_width = 106 if number == 10 else size
            tile_height = 90 if number == 10 else size
            x = center_x + int(x_factor * size) - tile_width // 2
            y = bottom_y - level * size
            if number == 10:
                y -= 14
            tiles.append(Tile(number, pygame.Rect(x, y, tile_width, tile_height)))

        return tiles

    def run(self) -> None:
        running = True
        while running:
            dt = self.clock.tick(FPS) / 1000
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    self._handle_key(event.key)

            self._update(dt)
            self._draw()

        pygame.quit()

    def smoke_test(self) -> None:
        self._draw()
        pygame.display.flip()
        pygame.quit()

    def _handle_key(self, key: int) -> None:
        if key == pygame.K_r:
            self._reset()
            return

        if self.won:
            return

        if key == pygame.K_1:
            self._try_hop(feet=1)
        elif key == pygame.K_2:
            self._try_hop(feet=2)

    def _try_hop(self, feet: int) -> None:
        group = self.hop_groups[self.current_group]
        expected_feet = len(group)

        if feet != expected_feet:
            self.error_message = "Movimento errado!"
            return

        self.error_message = ""
        self._move_player_to_group(group)
        self.current_group += 1
        self.won = self.current_group == len(self.hop_groups)

    def _move_player_to_group(self, group: tuple[int, ...]) -> None:
        centers = [pygame.Vector2(self.tile_by_number[number].rect.center) for number in group]
        center = sum(centers, pygame.Vector2(0, 0)) / len(centers)
        self.player_pos.update(center)
        self.player_positions = centers

    def _update(self, dt: float) -> None:
        _ = dt

    def _draw(self) -> None:
        self.screen.fill(BG)
        self._draw_instructions()
        self._draw_court()
        self._draw_start_line()
        self._draw_player()
        pygame.display.flip()

    def _draw_instructions(self) -> None:
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

        if self.error_message:
            error = self.small_font.render(self.error_message, True, ERROR)
            self.screen.blit(error, (x, y + 24))

    def _draw_court(self) -> None:
        court_segments: set[tuple[tuple[int, int], tuple[int, int]]] = set()
        for tile in self.tiles:
            if tile.number == 10:
                self._draw_sky_tile(tile.rect)
            else:
                court_segments.update(self._rect_segments(tile.rect))

        for start, end in self._merge_segments(court_segments):
            pygame.draw.line(self.screen, COURT_LINE, start, end, 2)

        for tile in self.tiles:
            label = "CÉU" if tile.number == 10 else str(tile.number)
            number = self.font.render(label, True, NUMBER_COLORS[tile.number])
            number_rect = number.get_rect(center=tile.rect.center)
            if tile.number == 10:
                number = self.sky_font.render(label, True, NUMBER_COLORS[tile.number])
                number_rect = number.get_rect(center=(tile.rect.centerx, tile.rect.centery + 8))
            self.screen.blit(number, number_rect)

    def _draw_start_line(self) -> None:
        start_y = HEIGHT - 72
        self._draw_crayon_line((320, start_y), (580, start_y), INK, 4)

    def _draw_player(self) -> None:
        for position in self.player_positions:
            shadow_center = (int(position.x + 5), int(position.y + 7))
            center = (int(position.x), int(position.y))
            pygame.draw.circle(self.screen, PLAYER_SHADOW, shadow_center, self.player_radius)
            pygame.draw.circle(self.screen, PLAYER, center, self.player_radius)
            pygame.draw.circle(self.screen, INK, center, self.player_radius, width=3)

    def _rect_segments(self, rect: pygame.Rect) -> set[tuple[tuple[int, int], tuple[int, int]]]:
        return {
            (rect.topleft, rect.topright),
            (rect.topright, rect.bottomright),
            (rect.bottomleft, rect.bottomright),
            (rect.topleft, rect.bottomleft),
        }

    def _merge_segments(
        self,
        segments: set[tuple[tuple[int, int], tuple[int, int]]],
    ) -> list[tuple[tuple[int, int], tuple[int, int]]]:
        horizontals: dict[int, list[tuple[int, int]]] = {}
        verticals: dict[int, list[tuple[int, int]]] = {}

        for start, end in segments:
            if start[1] == end[1]:
                y = start[1]
                x1, x2 = sorted((start[0], end[0]))
                horizontals.setdefault(y, []).append((x1, x2))
            elif start[0] == end[0]:
                x = start[0]
                y1, y2 = sorted((start[1], end[1]))
                verticals.setdefault(x, []).append((y1, y2))

        merged: list[tuple[tuple[int, int], tuple[int, int]]] = []
        for y, spans in horizontals.items():
            for x1, x2 in self._merge_spans(spans):
                merged.append(((x1, y), (x2, y)))

        for x, spans in verticals.items():
            for y1, y2 in self._merge_spans(spans):
                merged.append(((x, y1), (x, y2)))

        return merged

    def _merge_spans(self, spans: list[tuple[int, int]]) -> list[tuple[int, int]]:
        merged: list[tuple[int, int]] = []
        for start, end in sorted(spans):
            if not merged or start > merged[-1][1]:
                merged.append((start, end))
            else:
                previous_start, previous_end = merged[-1]
                merged[-1] = (previous_start, max(previous_end, end))

        return merged

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
            (round((x + padding) * scale), round((y + padding) * scale))
            for x, y in local_points
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
        color: tuple[int, int, int],
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

    def _reset(self) -> None:
        self.player_pos = self.start_pos.copy()
        self.player_positions = [self.start_pos.copy()]
        self.current_group = 0
        self.error_message = ""
        self.won = False


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Jogo simples de amarelinha feito com pygame.")
    parser.add_argument("--smoke-test", action="store_true", help="Initialize and draw one frame, then exit.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    game = HopscotchGame()
    if args.smoke_test:
        game.smoke_test()
    else:
        game.run()


if __name__ == "__main__":
    main()
