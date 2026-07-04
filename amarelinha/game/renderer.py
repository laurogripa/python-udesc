import math

import pygame

from game.camera import CameraDevice
from game.court import Segment, merge_segments, rect_segments
from game.models import Tile
from game.settings import (
    BG,
    CALIBRATION_DOT_RADIUS,
    CALIBRATION_MARKER,
    CALIBRATION_MARKER_SIZE,
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
        self.settings_skeleton_rect = pygame.Rect(0, 0, 0, 0)
        self.settings_calibrate_rect = pygame.Rect(0, 0, 0, 0)

    def draw(
        self,
        tiles: list[Tile],
        player_positions: list[pygame.Vector2],
        foot_positions: dict[str, tuple[float, float] | None],
        jump_probability: float,
        show_markers: bool,
        show_feet: bool,
        error_message: str,
        camera_frame: pygame.Surface | None,
        camera_devices: list[CameraDevice],
        selected_camera: int | None,
        settings_open: bool,
        cameras_scanned: bool,
    ) -> None:
        self.screen.fill(BG)
        self._draw_instructions(error_message, jump_probability)
        self._draw_court(tiles)
        if show_markers:
            self._draw_calibration_markers()
        self._draw_start_line()
        self._draw_player(player_positions)
        if show_feet:
            self._draw_feet(foot_positions)
        self._draw_camera_preview(camera_frame)
        self._draw_gear()
        if settings_open:
            self._draw_settings(camera_devices, selected_camera, cameras_scanned)
        pygame.display.flip()

    def draw_auto_calibration_screen(self, message: str) -> None:
        self.screen.fill(BG)
        self._draw_calibration_markers()

        title = self.title_font.render("Calibração Automática", True, INK)
        self.screen.blit(title, title.get_rect(center=(WIDTH // 2, 72)))
        subtitle = self.menu_font.render(
            message,
            True,
            INK,
        )
        self.screen.blit(subtitle, subtitle.get_rect(center=(WIDTH // 2, 112)))
        pygame.display.flip()

    def _draw_calibration_markers(self) -> None:
        size = CALIBRATION_MARKER_SIZE
        markers = (
            (pygame.Rect(0, 0, size, size), (0, 0)),
            (pygame.Rect(WIDTH - size, 0, size, size), (WIDTH, 0)),
            (pygame.Rect(0, HEIGHT - size, size, size), (0, HEIGHT)),
            (pygame.Rect(WIDTH - size, HEIGHT - size, size, size), (WIDTH, HEIGHT)),
        )
        for rect, corner in markers:
            pygame.draw.rect(self.screen, CALIBRATION_MARKER, rect)
            dot_x = min(
                max(corner[0], rect.left + CALIBRATION_DOT_RADIUS),
                rect.right - CALIBRATION_DOT_RADIUS,
            )
            dot_y = min(
                max(corner[1], rect.top + CALIBRATION_DOT_RADIUS),
                rect.bottom - CALIBRATION_DOT_RADIUS,
            )
            inner = pygame.Rect(0, 0, CALIBRATION_DOT_RADIUS * 2, CALIBRATION_DOT_RADIUS * 2)
            inner.center = (dot_x, dot_y)
            pygame.draw.rect(self.screen, (255, 255, 255), inner)

    def draw_settings_screen(
        self,
        camera_frame: pygame.Surface | None,
        camera_devices: list[CameraDevice],
        selected_camera: int | None,
        cameras_scanned: bool,
        show_skeleton: bool,
        error_message: str,
    ) -> None:
        self.screen.fill(BG)
        title = self.title_font.render("Configurações da câmera", True, INK)
        self.screen.blit(title, title.get_rect(center=(WIDTH // 2, 64)))
        subtitle = self.menu_font.render(
            "Selecione câmera e esqueleto. Enter ou clique em Confirmar.",
            True,
            INK,
        )
        self.screen.blit(subtitle, subtitle.get_rect(center=(WIDTH // 2, 104)))

        self._draw_camera_preview(camera_frame)
        self._draw_settings(
            camera_devices,
            selected_camera,
            cameras_scanned,
            show_skeleton,
        )

        self.settings_confirm_rect = pygame.Rect(WIDTH // 2 - 90, HEIGHT - 110, 180, 44)
        self.settings_calibrate_rect = pygame.Rect(WIDTH // 2 - 90, HEIGHT - 166, 180, 44)
        pygame.draw.rect(self.screen, PANEL_HOVER, self.settings_calibrate_rect, border_radius=10)
        pygame.draw.rect(
            self.screen,
            PANEL_BORDER,
            self.settings_calibrate_rect,
            width=2,
            border_radius=10,
        )
        calibrate = self.small_font.render("Calibrar", True, INK)
        self.screen.blit(calibrate, calibrate.get_rect(center=self.settings_calibrate_rect.center))
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
        camera_frame: pygame.Surface | None = None,
    ) -> None:
        self.screen.fill(BG)
        title = self.title_font.render("Calibração", True, INK)
        self.screen.blit(title, title.get_rect(center=(WIDTH // 2, 62)))
        self._draw_camera_preview(camera_frame)

        preview = self._camera_preview_rect()
        point_labels = ("1", "2", "3", "4")
        for index, point in enumerate(points):
            x = preview.x + point[0]
            y = preview.y + point[1]
            pygame.draw.circle(self.screen, PLAYER, (int(x), int(y)), 10)
            tag = self.menu_font.render(point_labels[index], True, INK)
            self.screen.blit(tag, (int(x) + 12, int(y) - 12))

        if len(points) == 4:
            outline = [
                (preview.x + points[0][0], preview.y + points[0][1]),
                (preview.x + points[1][0], preview.y + points[1][1]),
                (preview.x + points[3][0], preview.y + points[3][1]),
                (preview.x + points[2][0], preview.y + points[2][1]),
            ]
            pygame.draw.lines(self.screen, (78, 196, 112), True, outline, 3)

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

    def calibration_point_at(self, position: tuple[int, int]) -> tuple[float, float] | None:
        preview = self._camera_preview_rect()
        if not preview.collidepoint(position):
            return None
        return float(position[0] - preview.x), float(position[1] - preview.y)

    def camera_option_at(self, position: tuple[int, int]) -> int | None:
        for index, rect in self.camera_option_rects.items():
            if rect.collidepoint(position):
                return index
        return None

    def settings_confirm_at(self, position: tuple[int, int]) -> bool:
        return self.settings_confirm_rect.collidepoint(position)

    def settings_skeleton_at(self, position: tuple[int, int]) -> bool:
        return self.settings_skeleton_rect.collidepoint(position)

    def settings_calibrate_at(self, position: tuple[int, int]) -> bool:
        return self.settings_calibrate_rect.collidepoint(position)

    def _draw_instructions(self, error_message: str, jump_probability: float) -> None:
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

        probability = self.small_font.render(
            f"Salto: {jump_probability * 100:.0f}%",
            True,
            INK,
        )
        self.screen.blit(probability, (x, y + 70))

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

    def _draw_feet(self, foot_positions: dict[str, tuple[float, float] | None]) -> None:
        left = foot_positions.get("left")
        right = foot_positions.get("right")
        center = foot_positions.get("center")
        if left is not None:
            self._draw_foot_marker(left, (0, 0, 255), 30)
        if right is not None:
            self._draw_foot_marker(right, (255, 0, 0), 30)
        if center is not None:
            self._draw_foot_marker(center, (0, 255, 0), 35)

    def _draw_foot_marker(
        self,
        point: tuple[float, float],
        color: tuple[int, int, int],
        radius: int,
    ) -> None:
        center = (int(point[0]), int(point[1]))
        pygame.draw.circle(self.screen, color, center, radius)

    def _draw_camera_preview(self, frame: pygame.Surface | None) -> None:
        rect = self._camera_preview_rect()
        pygame.draw.rect(self.screen, PANEL, rect)
        pygame.draw.rect(self.screen, PANEL_BORDER, rect, width=2)

        if frame is not None:
            self.screen.blit(frame, rect)
            return

        text = self.menu_font.render("Selecione uma câmera", True, INK)
        self.screen.blit(text, text.get_rect(center=rect.center))

    def _camera_preview_rect(self) -> pygame.Rect:
        return pygame.Rect(
            WIDTH - CAMERA_MARGIN - CAMERA_WIDTH,
            (HEIGHT - CAMERA_HEIGHT) // 2,
            CAMERA_WIDTH,
            CAMERA_HEIGHT,
        )

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
        show_skeleton: bool,
    ) -> None:
        panel_height = 136 + max(1, len(devices)) * 44
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
        skeleton = self.small_font.render("Esqueleto", True, INK)
        self.screen.blit(skeleton, (panel.x + 18, panel.y + 56))
        self.camera_option_rects = {}
        self.settings_skeleton_rect = pygame.Rect(panel.x + 150, panel.y + 52, 128, 32)
        self._draw_checkbox(self.settings_skeleton_rect, show_skeleton)

        if not cameras_scanned:
            status = "Procurando câmeras..."
        elif not devices:
            status = "Nenhuma câmera encontrada"
        else:
            status = ""

        if status:
            text = self.menu_font.render(status, True, INK)
            self.screen.blit(text, (panel.x + 18, panel.y + 98))
            return

        mouse_position = pygame.mouse.get_pos()
        for row, device in enumerate(devices):
            option = pygame.Rect(panel.x + 10, panel.y + 92 + row * 44, panel.width - 20, 36)
            if option.collidepoint(mouse_position):
                pygame.draw.rect(self.screen, PANEL_HOVER, option)
            if device.index == selected_camera:
                pygame.draw.circle(self.screen, INK, (option.x + 15, option.centery), 5)

            label = self.menu_font.render(device.name, True, INK)
            self.screen.blit(label, (option.x + 30, option.y + 8))
            self.camera_option_rects[device.index] = option

    def _draw_checkbox(self, rect: pygame.Rect, checked: bool) -> None:
        box = pygame.Rect(rect.x, rect.y + 4, 24, 24)
        pygame.draw.rect(self.screen, INK, box, border_radius=4)
        pygame.draw.rect(self.screen, PANEL_BORDER, box, width=2, border_radius=4)
        if checked:
            pygame.draw.lines(
                self.screen,
                PANEL,
                False,
                [(box.x + 5, box.y + 12), (box.x + 10, box.y + 17), (box.x + 19, box.y + 6)],
                3,
            )

        label = self.menu_font.render("Mostrar", True, INK)
        self.screen.blit(label, (box.right + 10, rect.y + 7))

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
