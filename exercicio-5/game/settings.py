Color = tuple[int, int, int]
HopGroup = tuple[int, ...]
TileLayout = dict[int, tuple[float, int]]

WIDTH = 1280
HEIGHT = 720
FPS = 60

TILE_SIZE = 76
SKY_TILE_WIDTH = 106
SKY_TILE_HEIGHT = 90
SKY_TILE_OFFSET_Y = 14
COURT_BOTTOM_Y_OFFSET = 162

START_LINE_Y_OFFSET = 72
START_LINE_LEFT = 510
START_LINE_RIGHT = 770

PLAYER_RADIUS = 19
PLAYER_START_Y_OFFSET = 34

BG: Color = (66, 66, 62)
INK: Color = (247, 244, 232)
COURT_LINE: Color = (236, 232, 216)
PLAYER: Color = (255, 132, 83)
PLAYER_SHADOW: Color = (92, 64, 55)
ERROR: Color = (235, 76, 76)
PANEL: Color = (48, 48, 45)
PANEL_BORDER: Color = (102, 102, 96)
PANEL_HOVER: Color = (78, 78, 73)

CAMERA_WIDTH = 320
CAMERA_HEIGHT = 180
CAMERA_MARGIN = 24
CAMERA_SCAN_LIMIT = 5
GESTURE_STABLE_FRAMES = 5
SETTINGS_WIDTH = 300
SETTINGS_MARGIN = 24
GEAR_SIZE = 42

NUMBER_COLORS: dict[int, Color] = {
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

TILE_LAYOUT: TileLayout = {
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

HOP_GROUPS: tuple[HopGroup, ...] = ((1,), (2, 3), (4,), (5, 6), (7,), (8, 9), (10,))
