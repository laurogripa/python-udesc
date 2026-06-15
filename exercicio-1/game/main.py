import pygame

from game.court import build_tiles
from game.renderer import GameRenderer
from game.settings import FPS, HEIGHT, HOP_GROUPS, PLAYER_START_Y_OFFSET, WIDTH, HopGroup


class Amarelinha:
    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption("Amarelinha")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.renderer = GameRenderer(self.screen)
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
                    self._handle_key(event.key)

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

    def _move_player_to_group(self, group: HopGroup) -> None:
        centers = [pygame.Vector2(self.tile_by_number[number].rect.center) for number in group]
        center = sum(centers, pygame.Vector2(0, 0)) / len(centers)
        self.player_pos.update(center)
        self.player_positions = centers

    def _draw(self) -> None:
        self.renderer.draw(self.tiles, self.player_positions, self.error_message)

    def _reset(self) -> None:
        self.player_pos = self.start_pos.copy()
        self.player_positions = [self.start_pos.copy()]
        self.current_group = 0
        self.error_message = ""
        self.won = False
