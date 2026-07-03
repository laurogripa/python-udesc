import math

import pygame

from game.camera import CameraDevice
from game.court import Segment, merge_segments, rect_segments
from game.models import Tile
from game.settings import (
    BG,
    CALIBRATION_MARKER_RADIUS,
    CAMERA_HEIGHT,
    CAMERA_MARGIN,
    CAMERA_WIDTH,
    COURT_LINE,
    ERROR,
    GEAR_SIZE,
    HEIGHT,
    INK,
    NUMBER_COLORS,
    PANEL,
    PANEL_BORDER,
    PANEL_HOVER,
    PLAYER,
    PLAYER_RADIUS,
    PLAYER_SHADOW,
    SETTINGS_MARGIN,
    SETTINGS_WIDTH,
    START_LINE_LEFT,
    START_LINE_RIGHT,
    START_LINE_Y_OFFSET,
    WIDTH,
    Color,
)


class GameRenderer:
    def __init__(self, screen: pygame.Surface) -> None:
        self.screen = screen
        self.font = pygame.font.SysFont("arial", 34, bold=True)
        self.small_font = pygame.font.SysFont("arial", 22)
        self.menu_font = pygame.font.SysFont("arial", 18)
        self.sky_font = pygame.font.SysFont("arial", 30, bold=True)
        self.title_font = pygame.font.SysFont("arial", 38, bold=True)
        self.gear_rect = pygame.Rect(
            WIDTH - SETTINGS_MARGIN - GEAR_SIZE,
            SETTINGS_MARGIN,
            GEAR_SIZE,
            GEAR_SIZE,
        )
        self.camera_option_rects: dict[int, pygame.Rect] = {}
        self.settings_confirm_rect = pygame.Rect(0, 0, 0, 0)

    def draw(
        self,
        tiles: list[Tile],
        player_positions: list[pygame.Vector2],
        error_message: str,
        camera_frame: pygame.Surface | None,
        camera_devices: list[CameraDevice],
        selected_camera: int | None,
        settings_open: bool,
        cameras_scanned: bool,
    ) -> None:
        self.screen.fill(BG)
        self._draw_instructions(error_message)
        self._draw_court(tiles)
        self._draw_start_line()
        self._draw_player(player_positions)
        self._draw_camera_preview(camera_frame)
        self._draw_gear()
        if settings_open:
            self._draw_settings(camera_devices, selected_camera, cameras_scanned)
        pygame.display.flip()

    def draw_settings_screen(
        self,
        camera_frame: pygame.Surface | None,
        camera_devices: list[CameraDevice],
        selected_camera: int | None,
        cameras_scanned: bool,
        error_message: str,
    ) -> None:
        self.screen.fill(BG)
        title = self.title_font.render("Configurações da câmera", True, INK)
        self.screen.blit(title, title.get_rect(center=(WIDTH // 2, 64)))
        subtitle = self.menu_font.render(
            "Selecione uma câmera e pressione Enter ou clique em Confirmar.",
            True,
            INK,
        )
        self.screen.blit(subtitle, subtitle.get_rect(center=(WIDTH // 2, 104)))

        self._draw_camera_preview(camera_frame)
        self._draw_settings(camera_devices, selected_camera, cameras_scanned)

        self.settings_confirm_rect = pygame.Rect(WIDTH // 2 - 90, HEIGHT - 110, 180, 44)
        pygame.draw.rect(self.screen, PANEL_HOVER, self.settings_confirm_rect, border_radius=10)
        pygame.draw.rect(
            self.screen,
            PANEL_BORDER,
            self.settings_confirm_rect,
            width=2,
            border_radius=10,
        )
        label = self.small_font.render("Confirmar", True, INK)
        self.screen.blit(label, label.get_rect(center=self.settings_confirm_rect.center))

        if error_message:
            error = self.menu_font.render(error_message, True, ERROR)
            self.screen.blit(error, error.get_rect(center=(WIDTH // 2, HEIGHT - 48)))

        pygame.display.flip()

    def draw_calibration_screen(
        self,
        points: list[list[float]],
        complete: bool,
        message: str,
    ) -> None:
        self.screen.fill((25, 25, 30))
        markers = (
            (0, 0, "1"),
            (WIDTH, 0, "2"),
            (0, HEIGHT, "3"),
            (WIDTH, HEIGHT, "4"),
        )
        for x, y, label in markers:
            pygame.draw.circle(self.screen, NUMBER_COLORS[1], (x, y), CALIBRATION_MARKER_RADIUS)
            text = self.font.render(label, True, BG)
            px = min(max(x, 34), WIDTH - 34)
            py = min(max(y, 34), HEIGHT - 34)
            self.screen.blit(text, text.get_rect(center=(px, py)))

        for index, (x, y) in enumerate(points, start=1):
            pygame.draw.circle(self.screen, PLAYER, (int(x), int(y)), 10)
            tag = self.menu_font.render(str(index), True, INK)
            self.screen.blit(tag, (int(x) + 12, int(y) - 12))

        if complete:
            instruction = "4 cantos marcados. Enter confirma, Backspace desfaz, R reinicia."
        else:
            labels = (
                "1) canto superior esquerdo",
                "2) canto superior direito",
                "3) canto inferior esquerdo",
                "4) canto inferior direito",
            )
            instruction = f"Clique em {labels[len(points)]}."

        header = self.small_font.render(instruction, True, INK)
        self.screen.blit(header, header.get_rect(center=(WIDTH // 2, HEIGHT - 84)))
        if message:
            footer = self.menu_font.render(message, True, INK)
            self.screen.blit(footer, footer.get_rect(center=(WIDTH // 2, HEIGHT - 42)))

        pygame.display.flip()

    def camera_option_at(self, position: tuple[int, int]) -> int | None:
        for index, rect in self.camera_option_rects.items():
            if rect.collidepoint(position):
                return index
        return None

    def settings_confirm_at(self, position: tuple[int, int]) -> bool:
        return self.settings_confirm_rect.collidepoint(position)

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

    def _draw_camera_preview(self, frame: pygame.Surface | None) -> None:
        rect = pygame.Rect(
            WIDTH - CAMERA_MARGIN - CAMERA_WIDTH,
            HEIGHT - CAMERA_MARGIN - CAMERA_HEIGHT,
            CAMERA_WIDTH,
            CAMERA_HEIGHT,
        )
        pygame.draw.rect(self.screen, PANEL, rect)
        pygame.draw.rect(self.screen, PANEL_BORDER, rect, width=2)

        if frame is not None:
            self.screen.blit(frame, rect)
            return

        text = self.menu_font.render("Selecione uma câmera", True, INK)
        self.screen.blit(text, text.get_rect(center=rect.center))

    def _draw_gear(self) -> None:
        center = self.gear_rect.center
        pygame.draw.circle(self.screen, PANEL, center, GEAR_SIZE // 2)
        pygame.draw.circle(self.screen, PANEL_BORDER, center, GEAR_SIZE // 2, width=2)

        for angle in range(0, 360, 45):
            direction = pygame.Vector2(0, -1).rotate(angle)
            start = pygame.Vector2(center) + direction * 10
            end = pygame.Vector2(center) + direction * 16
            pygame.draw.line(self.screen, INK, start, end, 4)

        pygame.draw.circle(self.screen, INK, center, 9, width=3)
        pygame.draw.circle(self.screen, PANEL, center, 3)

    def _draw_settings(
        self,
        devices: list[CameraDevice],
        selected_camera: int | None,
        cameras_scanned: bool,
    ) -> None:
        panel_height = 86 + max(1, len(devices)) * 44
        panel = pygame.Rect(
            WIDTH // 2 - SETTINGS_WIDTH // 2,
            148,
            SETTINGS_WIDTH,
            panel_height,
        )
        pygame.draw.rect(self.screen, PANEL, panel)
        pygame.draw.rect(self.screen, PANEL_BORDER, panel, width=2)

        title = self.small_font.render("Câmera", True, INK)
        self.screen.blit(title, (panel.x + 18, panel.y + 16))
        self.camera_option_rects = {}

        if not cameras_scanned:
            status = "Procurando câmeras..."
        elif not devices:
            status = "Nenhuma câmera encontrada"
        else:
            status = ""

        if status:
            text = self.menu_font.render(status, True, INK)
            self.screen.blit(text, (panel.x + 18, panel.y + 56))
            return

        mouse_position = pygame.mouse.get_pos()
        for row, device in enumerate(devices):
            option = pygame.Rect(panel.x + 10, panel.y + 52 + row * 44, panel.width - 20, 36)
            if option.collidepoint(mouse_position):
                pygame.draw.rect(self.screen, PANEL_HOVER, option)
            if device.index == selected_camera:
                pygame.draw.circle(self.screen, INK, (option.x + 15, option.centery), 5)

            label = self.menu_font.render(device.name, True, INK)
            self.screen.blit(label, (option.x + 30, option.y + 8))
            self.camera_option_rects[device.index] = option

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
