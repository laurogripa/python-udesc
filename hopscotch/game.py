import pygame

from hopscotch.camera import CameraManager
from hopscotch.court import build_tiles
from hopscotch.renderer import GameRenderer
from hopscotch.settings import FPS, HEIGHT, HOP_GROUPS, PLAYER_START_Y_OFFSET, WIDTH, HopGroup


class HopscotchGame:
    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption("Amarelinha")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.renderer = GameRenderer(self.screen)
        self.camera = CameraManager()
        self.settings_open = False

        self.tiles = build_tiles()
        self.tile_by_number = {tile.number: tile for tile in self.tiles}
        self.hop_groups = HOP_GROUPS
        self.start_pos = pygame.Vector2(WIDTH // 2, HEIGHT - PLAYER_START_Y_OFFSET)
        self.player_pos = self.start_pos.copy()
        self.player_positions = [self.start_pos.copy()]
        self.current_group = 0
        self.error_message = ""
        self.won = False

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

            self.camera.update()
            gesture = self.camera.consume_gesture()
            if gesture is not None and not self.won:
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
            return True

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
        if self.renderer.gear_rect.collidepoint(position):
            self.settings_open = not self.settings_open
            if self.settings_open and not self.camera.scanned:
                self.camera.discover()
            return

        if not self.settings_open:
            return

        camera_index = self.renderer.camera_option_at(position)
        if camera_index is not None:
            self.camera.select(camera_index)
            self.settings_open = False

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
        self.renderer.draw(
            self.tiles,
            self.player_positions,
            self.error_message,
            self.camera.frame,
            self.camera.devices,
            self.camera.selected_index,
            self.settings_open,
            self.camera.scanned,
        )

    def _reset(self) -> None:
        self.player_pos = self.start_pos.copy()
        self.player_positions = [self.start_pos.copy()]
        self.current_group = 0
        self.error_message = ""
        self.won = False
