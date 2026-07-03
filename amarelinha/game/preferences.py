import json

from game.settings import DATA_DIR, SETTINGS_FILE


class Preferences:
    def __init__(self) -> None:
        self.camera_index: int | None = None
        self.show_skeleton = False

    def load(self) -> None:
        if not SETTINGS_FILE.exists():
            return
        try:
            payload = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
        except (OSError, ValueError, TypeError):
            return

        camera_index = payload.get("camera_index")
        if isinstance(camera_index, int):
            self.camera_index = camera_index
        show_skeleton = payload.get("show_skeleton")
        if isinstance(show_skeleton, bool):
            self.show_skeleton = show_skeleton

    def save(self) -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        payload = {
            "camera_index": self.camera_index,
            "show_skeleton": self.show_skeleton,
        }
        SETTINGS_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")
