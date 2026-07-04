import json
from dataclasses import dataclass, field

from game.settings import CALIBRATION_FILE, DATA_DIR


@dataclass
class Calibration:
    points: list[list[float]] = field(default_factory=list)
    camera_index: int | None = None

    @property
    def complete(self) -> bool:
        return len(self.points) == 4

    def add_point(self, x: float, y: float) -> None:
        if not self.complete:
            self.points.append([float(x), float(y)])

    def undo(self) -> None:
        if self.points:
            self.points.pop()

    def clear(self) -> None:
        self.points = []
        self.camera_index = None

    def save(self, camera_index: int | None) -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.camera_index = camera_index
        payload = {
            "camera_index": camera_index,
            "points": self.points,
        }
        CALIBRATION_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def load(self, camera_index: int | None) -> bool:
        if not CALIBRATION_FILE.exists():
            return False
        try:
            payload = json.loads(CALIBRATION_FILE.read_text(encoding="utf-8"))
        except (OSError, ValueError, TypeError):
            return False

        saved_camera = payload.get("camera_index")
        points = payload.get("points", [])
        if camera_index is not None and saved_camera not in (None, camera_index):
            return False
        if len(points) != 4:
            return False

        try:
            self.points = [[float(x), float(y)] for x, y in points]
        except (ValueError, TypeError):
            return False
        self.camera_index = saved_camera
        return True
