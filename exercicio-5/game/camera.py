from dataclasses import dataclass
from typing import Any

import pygame

from game.settings import (
    CAMERA_HEIGHT,
    CAMERA_SCAN_LIMIT,
    CAMERA_WIDTH,
)


@dataclass(frozen=True)
class CameraDevice:
    index: int
    name: str


class CameraManager:
    def __init__(self) -> None:
        self.devices: list[CameraDevice] = []
        self.selected_index: int | None = None
        self.frame: pygame.Surface | None = None
        self.scanned = False
        self._capture: Any | None = None

    def discover(self) -> None:
        self.devices = []
        for index in range(CAMERA_SCAN_LIMIT):
            capture = self._open_capture(index)
            if capture.isOpened():
                self.devices.append(CameraDevice(index=index, name=f"Câmera {index + 1}"))
            capture.release()
        self.scanned = True

    def select(self, index: int) -> None:
        import cv2

        self.close()
        capture = self._open_capture(index)
        if not capture.isOpened():
            capture.release()
            return

        capture.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
        capture.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
        self._capture = capture
        self.selected_index = index

    def update(self) -> None:
        if self._capture is None:
            return

        import cv2

        success, frame = self._capture.read()
        if not success:
            return

        frame = cv2.flip(frame, 1)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame = self._crop_to_preview(frame)
        self.frame = pygame.image.frombuffer(
            frame.tobytes(), (CAMERA_WIDTH, CAMERA_HEIGHT), "RGB"
        ).copy()

    def consume_gesture(self) -> int | None:
        # TODO: use o modelo em assets/models para reconhecer os gestos 1 e 2.
        return None

    def close(self) -> None:
        if self._capture is not None:
            self._capture.release()
        self._capture = None
        self.selected_index = None
        self.frame = None

    def _open_capture(self, index: int) -> Any:
        import cv2

        if hasattr(cv2, "CAP_AVFOUNDATION"):
            return cv2.VideoCapture(index, cv2.CAP_AVFOUNDATION)
        return cv2.VideoCapture(index)

    def _crop_to_preview(self, frame: Any) -> Any:
        import cv2

        height, width = frame.shape[:2]
        target_ratio = CAMERA_WIDTH / CAMERA_HEIGHT
        source_ratio = width / height

        if source_ratio > target_ratio:
            crop_width = round(height * target_ratio)
            left = (width - crop_width) // 2
            frame = frame[:, left : left + crop_width]
        elif source_ratio < target_ratio:
            crop_height = round(width / target_ratio)
            top = (height - crop_height) // 2
            frame = frame[top : top + crop_height, :]

        return cv2.resize(frame, (CAMERA_WIDTH, CAMERA_HEIGHT))
