import pygame

from game.calibration import Calibration
from game.camera import CameraManager
from game.court import build_tiles
from game.preferences import Preferences
from game.renderer import GameRenderer
from game.settings import (
    AUTO_CALIBRATION_DELAY_MS,
    FPS,
    HEIGHT,
    HOP_GROUPS,
    PLAYER_START_Y_OFFSET,
    WIDTH,
    HopGroup,
)


class ScreenState:
    GAME = "game"
    SETTINGS = "settings"
    CALIBRATION = "calibration"


class Amarelinha:
    def __init__(
        self,
        show_skeleton: bool = False,
        screen_index: int = 0,
        show_markers: bool = False,
        show_feet: bool = False,
    ) -> None:
        pygame.init()
        pygame.display.set_caption("Amarelinha")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT), display=screen_index)
        self.clock = pygame.time.Clock()
        self.renderer = GameRenderer(self.screen)
        self.camera = CameraManager()
        self.preferences = Preferences()
        self.preferences.load()
        if show_skeleton:
            self.preferences.show_skeleton = True
        self.calibration = Calibration()
        self.screen_state = ScreenState.GAME
        self.settings_error = ""
        self.calibration_message = ""
        self.calibration_started_ms = 0
        self.calibration_attempted = False

        self.tiles = build_tiles()
        self.tile_by_number = {tile.number: tile for tile in self.tiles}
        self.hop_groups = HOP_GROUPS
        self.start_pos = pygame.Vector2(WIDTH // 2, HEIGHT - PLAYER_START_Y_OFFSET)
        self.player_pos = self.start_pos.copy()
        self.player_positions = [self.start_pos.copy()]
        self.current_group = 0
        self.error_message = ""
        self.won = False
        self.show_markers = show_markers
        self.show_feet = show_feet
        self._initialize_camera()

    def run(self) -> None:
        running = True
        while running:
            self.clock.tick(FPS)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    running = not self._handle_key(event.key, event.mod)
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self._handle_click(event.pos)

            if self.screen_state == ScreenState.CALIBRATION:
                self.camera.update()
                self._update_auto_calibration()
            else:
                self.camera.update()
                gesture = self.camera.consume_gesture()
                if gesture is not None and not self.won and self.screen_state == ScreenState.GAME:
                    self._try_hop(feet=gesture)
            self._draw()

        self.camera.close()
        pygame.quit()

    def smoke_test(self) -> None:
        self._draw()
        pygame.display.flip()
        pygame.quit()

    def _handle_key(self, key: int, modifiers: int) -> bool:
        control_pressed = bool(modifiers & pygame.KMOD_CTRL)
        if control_pressed and key in (pygame.K_c, pygame.K_d):
            if key == pygame.K_c:
                if self.screen_state == ScreenState.CALIBRATION:
                    self.screen_state = ScreenState.GAME
                    self.calibration_message = ""
                else:
                    self._start_auto_calibration()
                return False
            return True
        if control_pressed and key == pygame.K_s:
            self._open_settings()
            return False

        if self.screen_state == ScreenState.SETTINGS:
            return self._handle_settings_key(key)
        if self.screen_state == ScreenState.CALIBRATION:
            return self._handle_calibration_key(key)

        if key == pygame.K_r:
            self._reset()
            return False

        if self.won:
            return False

        if key == pygame.K_1:
            self._try_hop(feet=1)
        elif key == pygame.K_2:
            self._try_hop(feet=2)

        return False

    def _handle_click(self, position: tuple[int, int]) -> None:
        if self.screen_state == ScreenState.SETTINGS:
            self._handle_settings_click(position)
            return
        if self.screen_state == ScreenState.CALIBRATION:
            self._handle_calibration_click(position)
            return

        if self.renderer.gear_rect.collidepoint(position):
            if self.screen_state == ScreenState.SETTINGS:
                self.screen_state = ScreenState.GAME
            else:
                self.screen_state = ScreenState.SETTINGS
            if self.screen_state == ScreenState.SETTINGS:
                self.camera.ensure_devices()
            return

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

    def _move_player_to_group(self, group: HopGroup) -> None:
        centers = [pygame.Vector2(self.tile_by_number[number].rect.center) for number in group]
        center = sum(centers, pygame.Vector2(0, 0)) / len(centers)
        self.player_pos.update(center)
        self.player_positions = centers

    def _draw(self) -> None:
        if self.screen_state == ScreenState.SETTINGS:
            self.renderer.draw_settings_screen(
                self.camera.frame,
                self.camera.devices,
                self.camera.selected_index,
                self.camera.scanned,
                self.preferences.show_skeleton,
                self.settings_error,
            )
            return

        if self.screen_state == ScreenState.CALIBRATION:
            self.renderer.draw_auto_calibration_screen(self.calibration_message)
            return

        self.renderer.draw(
            self.tiles,
            self.player_positions,
            self.camera.projected_feet(),
            self.camera.jump_probability,
            self.show_markers,
            self.show_feet,
            self.error_message,
            self.camera.frame,
            self.camera.devices,
            self.camera.selected_index,
            False,
            self.camera.scanned,
        )

    def _reset(self) -> None:
        self.player_pos = self.start_pos.copy()
        self.player_positions = [self.start_pos.copy()]
        self.current_group = 0
        self.error_message = ""
        self.won = False

    def _initialize_camera(self) -> None:
        if self.camera.select_default(self.preferences.camera_index):
            self.camera.set_show_skeleton(self.preferences.show_skeleton)
            self.preferences.camera_index = self.camera.selected_index
            self.preferences.save()
            self._load_calibration()

    def _open_settings(self) -> None:
        self.camera.ensure_devices()
        self.settings_error = ""
        self.screen_state = ScreenState.SETTINGS

    def _start_auto_calibration(self) -> None:
        self.camera.ensure_devices()
        self.calibration_message = "Posicione os marcadores. Capturando..."
        self.calibration_started_ms = pygame.time.get_ticks()
        self.calibration_attempted = False
        self.screen_state = ScreenState.CALIBRATION

    def _handle_settings_key(self, key: int) -> bool:
        if key in (pygame.K_ESCAPE, pygame.K_RETURN):
            self.screen_state = ScreenState.GAME
        return False

    def _handle_calibration_key(self, key: int) -> bool:
        if key == pygame.K_ESCAPE:
            self.screen_state = ScreenState.GAME
        elif key == pygame.K_r:
            self._start_auto_calibration()
        return False

    def _handle_settings_click(self, position: tuple[int, int]) -> None:
        camera_index = self.renderer.camera_option_at(position)
        if camera_index is not None:
            self.camera.select(camera_index)
            if self.camera.selected_index == camera_index:
                self.camera.set_show_skeleton(self.preferences.show_skeleton)
                self.preferences.camera_index = camera_index
                self.preferences.save()
                if not self.calibration.load(camera_index):
                    self.calibration.clear()
                    self.camera.set_calibration([])
                else:
                    self.camera.set_calibration(self.calibration.points)
                self.settings_error = ""
            else:
                self.settings_error = f"Não foi possível abrir a câmera {camera_index}."
            return

        if self.renderer.settings_skeleton_at(position):
            self.preferences.show_skeleton = not self.preferences.show_skeleton
            self.camera.set_show_skeleton(self.preferences.show_skeleton)
            self.preferences.save()
            return

        if self.renderer.settings_calibrate_at(position):
            self._start_auto_calibration()
            return

        if self.renderer.settings_confirm_at(position):
            self.screen_state = ScreenState.GAME

    def _handle_calibration_click(self, position: tuple[int, int]) -> None:
        return

    def _load_calibration(self) -> None:
        if not self.calibration.load(self.camera.selected_index):
            self.calibration.clear()
            self.camera.set_calibration([])
            return
        self.camera.set_calibration(self.calibration.points)

    def _update_auto_calibration(self) -> None:
        if self.calibration_attempted:
            return
        if pygame.time.get_ticks() - self.calibration_started_ms < AUTO_CALIBRATION_DELAY_MS:
            return

        self.calibration_attempted = True
        points = self.camera.auto_calibrate()
        if points is None:
            self.calibration_message = (
                "Falha ao detectar marcadores. Pressione R para tentar de novo."
            )
            return

        self.calibration.points = points
        self.calibration.save(self.camera.selected_index)
        self.camera.set_calibration(self.calibration.points)
        self.calibration_message = "Calibração salva."
        self.screen_state = ScreenState.GAME
