from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pygame

from game.settings import (
    CAMERA_HEIGHT,
    CAMERA_SCAN_LIMIT,
    CAMERA_WIDTH,
    GESTURE_STABLE_FRAMES,
)

MODEL_PATH = Path(__file__).parent.parent / "assets" / "models" / "hand_landmarker.task"


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
        self._landmarker: Any | None = None
        self._pending_gesture: int | None = None
        self._pending_frames = 0
        self._latched_gesture: int | None = None
        self._gesture_event: int | None = None
        self._timestamp_ms = 0

    def discover(self) -> None:
        self.devices = []
        for index in range(CAMERA_SCAN_LIMIT):
            capture = self._open_capture(index)
            if capture.isOpened():
                self.devices.append(CameraDevice(index=index, name=f"Câmera {index + 1}"))
            capture.release()
        self.scanned = True

    def ensure_devices(self) -> None:
        if not self.scanned:
            self.discover()

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
        self._landmarker = self._create_landmarker()
        self.selected_index = index

    def select_default(self, preferred_index: int | None = None) -> bool:
        self.ensure_devices()
        candidates: list[int] = []
        if preferred_index is not None:
            candidates.append(preferred_index)
        candidates.extend(device.index for device in self.devices if device.index not in candidates)

        for candidate in candidates:
            self.select(candidate)
            if self.selected_index == candidate:
                return True
        return False

    def update(self) -> None:
        if self._capture is None:
            return

        import cv2

        success, frame = self._capture.read()
        if not success:
            return

        frame = cv2.flip(frame, 1)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        self._detect_gesture(frame)
        frame = self._crop_to_preview(frame)
        self.frame = pygame.image.frombuffer(
            frame.tobytes(), (CAMERA_WIDTH, CAMERA_HEIGHT), "RGB"
        ).copy()

    def consume_gesture(self) -> int | None:
        gesture = self._gesture_event
        self._gesture_event = None
        return gesture

    def close(self) -> None:
        if self._capture is not None:
            self._capture.release()
        if self._landmarker is not None:
            self._landmarker.close()
        self._capture = None
        self._landmarker = None
        self.selected_index = None
        self.frame = None
        self._reset_gesture_state()

    def _open_capture(self, index: int) -> Any:
        import cv2

        if hasattr(cv2, "CAP_AVFOUNDATION"):
            return cv2.VideoCapture(index, cv2.CAP_AVFOUNDATION)
        return cv2.VideoCapture(index)

    def _create_landmarker(self) -> Any:
        import mediapipe as mp

        options = mp.tasks.vision.HandLandmarkerOptions(
            base_options=mp.tasks.BaseOptions(
                model_asset_path=str(MODEL_PATH),
                delegate=mp.tasks.BaseOptions.Delegate.CPU,
            ),
            running_mode=mp.tasks.vision.RunningMode.VIDEO,
            num_hands=1,
            min_hand_detection_confidence=0.6,
            min_hand_presence_confidence=0.6,
            min_tracking_confidence=0.6,
        )
        return mp.tasks.vision.HandLandmarker.create_from_options(options)

    def _detect_gesture(self, frame: Any) -> None:
        if self._landmarker is None:
            return

        import mediapipe as mp

        self._timestamp_ms += 1
        image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)
        result = self._landmarker.detect_for_video(image, self._timestamp_ms)
        gesture = self._count_fingers(result)
        self._update_gesture_state(gesture)

    def _count_fingers(self, result: Any) -> int | None:
        if not result.hand_landmarks:
            return None

        landmarks = result.hand_landmarks[0]
        index_up = landmarks[8].y < landmarks[6].y
        middle_up = landmarks[12].y < landmarks[10].y
        ring_up = landmarks[16].y < landmarks[14].y
        pinky_up = landmarks[20].y < landmarks[18].y

        if index_up and not middle_up and not ring_up and not pinky_up:
            return 1
        if index_up and middle_up and not ring_up and not pinky_up:
            return 2
        return None

    def _update_gesture_state(self, gesture: int | None) -> None:
        if gesture != self._pending_gesture:
            self._pending_gesture = gesture
            self._pending_frames = 1
            return

        self._pending_frames += 1
        if self._pending_frames < GESTURE_STABLE_FRAMES:
            return

        if gesture is None:
            self._latched_gesture = None
        elif gesture != self._latched_gesture:
            self._gesture_event = gesture
            self._latched_gesture = gesture

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

    def _reset_gesture_state(self) -> None:
        self._pending_gesture = None
        self._pending_frames = 0
        self._latched_gesture = None
        self._gesture_event = None
        self._timestamp_ms = 0
