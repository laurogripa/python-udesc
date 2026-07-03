from pathlib import Path

Color = tuple[int, int, int]
HopGroup = tuple[int, ...]
TileLayout = dict[int, tuple[float, int]]

WIDTH = 1280
HEIGHT = 720
FPS = 60

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"
SETTINGS_FILE = DATA_DIR / "settings.json"
CALIBRATION_FILE = DATA_DIR / "calibration.json"
HAND_MODEL_PATH = BASE_DIR / "assets" / "models" / "hand_landmarker.task"
POSE_MODEL_PATH = BASE_DIR / "assets" / "models" / "pose_landmarker_heavy.task"

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

BG: Color = (255, 255, 255)
INK: Color = (0, 0, 0)
COURT_LINE: Color = (0, 0, 0)
PLAYER: Color = (255, 132, 83)
PLAYER_SHADOW: Color = (92, 64, 55)
ERROR: Color = (235, 76, 76)
PANEL: Color = (245, 245, 245)
PANEL_BORDER: Color = (0, 0, 0)
PANEL_HOVER: Color = (228, 228, 228)

CAMERA_WIDTH = 384
CAMERA_HEIGHT = 216
CAMERA_MARGIN = 24
CAMERA_SCAN_LIMIT = 5
GESTURE_STABLE_FRAMES = 5
BODY_STABLE_FRAMES = 4
SETTINGS_WIDTH = 300
SETTINGS_MARGIN = 24
GEAR_SIZE = 42
CALIBRATION_MARKER_RADIUS = 60
CALIBRATION_MARKER_SIZE = 144
CALIBRATION_DOT_RADIUS = 28
AUTO_CALIBRATION_DELAY_MS = 1200
CALIBRATION_MIN_CONTOUR_AREA = 60.0
BODY_VISIBILITY_THRESHOLD = 0.55
BODY_MIN_FEET_DISTANCE_FRAC = 0.025
BODY_SINGLE_LEG_Y_DELTA_FRAC = 0.06
JUMP_HISTORY_SIZE = 6
JUMP_LIFT_THRESHOLD = 0.12
JUMP_VELOCITY_THRESHOLD = 0.8
JUMP_GRAVITY_THRESHOLD = 0.35
POSE_LEFT_HEEL = 29
POSE_RIGHT_HEEL = 30
POSE_LEFT_FOOT_INDEX = 31
POSE_RIGHT_FOOT_INDEX = 32

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
