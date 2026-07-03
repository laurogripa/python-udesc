import json
from collections import deque
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import pygame

from game.settings import (
    BODY_MIN_FEET_DISTANCE_FRAC,
    BODY_SINGLE_LEG_Y_DELTA_FRAC,
    BODY_STABLE_FRAMES,
    BODY_VISIBILITY_THRESHOLD,
    CALIBRATION_DOT_RADIUS,
    CALIBRATION_MIN_CONTOUR_AREA,
    CAMERA_HEIGHT,
    CAMERA_SCAN_LIMIT,
    CAMERA_WIDTH,
    GESTURE_STABLE_FRAMES,
    HAND_MODEL_PATH,
    HEIGHT,
    JUMP_GRAVITY_THRESHOLD,
    JUMP_HISTORY_SIZE,
    JUMP_LIFT_THRESHOLD,
    JUMP_VELOCITY_THRESHOLD,
    LOGS_DIR,
    POSE_LEFT_FOOT_INDEX,
    POSE_LEFT_HEEL,
    POSE_MODEL_PATH,
    POSE_RIGHT_FOOT_INDEX,
    POSE_RIGHT_HEEL,
    WIDTH,
)


@dataclass(frozen=True)
class CameraDevice:
    index: int
    name: str


HAND_CONNECTIONS: tuple[tuple[int, int], ...] = (
    (0, 1),
    (1, 2),
    (2, 3),
    (3, 4),
    (0, 5),
    (5, 6),
    (6, 7),
    (7, 8),
    (5, 9),
    (9, 10),
    (10, 11),
    (11, 12),
    (9, 13),
    (13, 14),
    (14, 15),
    (15, 16),
    (13, 17),
    (0, 17),
    (17, 18),
    (18, 19),
    (19, 20),
)
POSE_CONNECTIONS: tuple[tuple[int, int], ...] = (
    (0, 1),
    (1, 2),
    (2, 3),
    (3, 7),
    (0, 4),
    (4, 5),
    (5, 6),
    (6, 8),
    (9, 10),
    (11, 12),
    (11, 13),
    (13, 15),
    (15, 17),
    (15, 19),
    (15, 21),
    (17, 19),
    (12, 14),
    (14, 16),
    (16, 18),
    (16, 20),
    (16, 22),
    (18, 20),
    (11, 23),
    (12, 24),
    (23, 24),
    (23, 25),
    (25, 27),
    (27, 29),
    (29, 31),
    (27, 31),
    (24, 26),
    (26, 28),
    (28, 30),
    (30, 32),
    (28, 32),
)


class CameraManager:
    def __init__(self) -> None:
        self.devices: list[CameraDevice] = []
        self.selected_index: int | None = None
        self.frame: pygame.Surface | None = None
        self.scanned = False
        self._capture: Any | None = None
        self._raw_frame: Any | None = None
        self._hand_landmarker: Any | None = None
        self._pose_detector: Any | None = None
        self.body_tracking_available = False
        self.show_skeleton = False
        self._foot_points: dict[str, tuple[float, float] | None] = {"left": None, "right": None}
        self._projected_foot_points: dict[str, tuple[float, float] | None] = {
            "left": None,
            "right": None,
        }
        self._body_support: str | None = None
        self.jump_probability = 0.0
        self._calibration_points: list[list[float]] = []
        self._jump_history: deque[_JumpSample] = deque(maxlen=JUMP_HISTORY_SIZE)
        self._gesture_queue: list[int] = []
        self._gesture_states = {
            "hand": _GestureState(stable_frames=GESTURE_STABLE_FRAMES),
            "body": _GestureState(stable_frames=BODY_STABLE_FRAMES),
        }
        self._calibration_attempt = 0
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
        self._hand_landmarker = self._create_hand_landmarker()
        self._pose_detector = self._create_pose_detector()
        self.body_tracking_available = self._pose_detector is not None
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
        self._raw_frame = frame.copy()
        self._detect_gestures(frame)
        self._draw_calibration_outline(frame)
        frame = self._crop_to_preview(frame)
        self.frame = pygame.image.frombuffer(
            frame.tobytes(), (CAMERA_WIDTH, CAMERA_HEIGHT), "RGB"
        ).copy()

    def consume_gesture(self) -> int | None:
        if not self._gesture_queue:
            return None
        return self._gesture_queue.pop(0)

    def close(self) -> None:
        if self._capture is not None:
            self._capture.release()
        if self._hand_landmarker is not None:
            self._hand_landmarker.close()
        if self._pose_detector is not None:
            self._pose_detector.close()
        self._capture = None
        self._raw_frame = None
        self._hand_landmarker = None
        self._pose_detector = None
        self.body_tracking_available = False
        self.selected_index = None
        self.frame = None
        self._foot_points = {"left": None, "right": None}
        self._projected_foot_points = {"left": None, "right": None}
        self._body_support = None
        self.jump_probability = 0.0
        self._jump_history.clear()
        self._reset_gesture_state()

    def set_show_skeleton(self, show_skeleton: bool) -> None:
        self.show_skeleton = show_skeleton

    def set_calibration(self, points: list[list[float]]) -> None:
        self._calibration_points = [list(point) for point in points]

    def projected_feet(self) -> dict[str, tuple[float, float] | None]:
        return {
            "left": self._projected_foot_points["left"],
            "right": self._projected_foot_points["right"],
        }

    def auto_calibrate(self) -> list[list[float]] | None:
        frame = self._raw_frame
        if frame is None:
            self._log_calibration_event("auto_calibrate:no_frame", {})
            return None

        import cv2
        import numpy as np

        self._calibration_attempt += 1
        attempt = self._calibration_attempt
        bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
        lower_red_1 = np.array([0, 35, 35], dtype=np.uint8)
        upper_red_1 = np.array([12, 255, 255], dtype=np.uint8)
        lower_red_2 = np.array([168, 35, 35], dtype=np.uint8)
        upper_red_2 = np.array([180, 255, 255], dtype=np.uint8)
        mask_a = cv2.inRange(hsv, lower_red_1, upper_red_1)
        mask_b = cv2.inRange(hsv, lower_red_2, upper_red_2)
        red_mask = cv2.bitwise_or(mask_a, mask_b)
        kernel = np.ones((5, 5), dtype=np.uint8)
        red_mask = cv2.morphologyEx(red_mask, cv2.MORPH_OPEN, kernel)
        red_mask = cv2.morphologyEx(red_mask, cv2.MORPH_CLOSE, kernel)
        self._save_calibration_debug_image(attempt, "raw", bgr)
        self._save_calibration_debug_image(attempt, "mask", red_mask)

        contours, _ = cv2.findContours(red_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        candidates: list[tuple[float, tuple[float, float], list[tuple[float, float]]]] = []
        min_area = CALIBRATION_MIN_CONTOUR_AREA
        rejected: list[dict[str, Any]] = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < min_area:
                rejected.append({"reason": "small_area", "area": round(area, 2)})
                continue
            moments = cv2.moments(contour)
            if moments["m00"] == 0:
                rejected.append({"reason": "zero_moment", "area": round(area, 2)})
                continue
            center = (moments["m10"] / moments["m00"], moments["m01"] / moments["m00"])
            points = [
                (float(point[0][0]), float(point[0][1]))
                for point in contour
            ]
            candidates.append((area, center, points))

        markers = [(center, points) for area, center, points in sorted(
            candidates,
            key=lambda item: item[0],
            reverse=True,
        )[:4]]

        self._log_calibration_event(
            "auto_calibrate:contours",
            {
                "attempt": attempt,
                "contours": len(contours),
                "candidates": len(candidates),
                "accepted_markers": len(markers),
                "min_area": min_area,
                "rejected": rejected,
            },
        )
        if len(markers) < 4:
            self._log_calibration_event(
                "auto_calibrate:failed",
                {"attempt": attempt, "reason": "markers_lt_4"},
            )
            return None

        top = sorted(markers, key=lambda item: item[0][1])[:2]
        bottom = sorted(markers, key=lambda item: item[0][1])[2:]
        top_left, top_right = sorted(top, key=lambda item: item[0][0])
        bottom_left, bottom_right = sorted(bottom, key=lambda item: item[0][0])
        points = [
            # Camera view is upside down relative to the projected game.
            list(self._marker_corner(bottom_right[1], "bottom_right")),
            list(self._marker_corner(bottom_left[1], "bottom_left")),
            list(self._marker_corner(top_right[1], "top_right")),
            list(self._marker_corner(top_left[1], "top_left")),
        ]
        self._log_calibration_event(
            "auto_calibrate:success",
            {
                "attempt": attempt,
                "points": points,
                "camera_marker_centers": [
                    [round(marker[0][0], 2), round(marker[0][1], 2)] for marker in markers
                ],
            },
        )
        return points

    def _open_capture(self, index: int) -> Any:
        import cv2

        if hasattr(cv2, "CAP_AVFOUNDATION"):
            return cv2.VideoCapture(index, cv2.CAP_AVFOUNDATION)
        return cv2.VideoCapture(index)

    def _create_hand_landmarker(self) -> Any:
        import mediapipe as mp

        options = mp.tasks.vision.HandLandmarkerOptions(
            base_options=mp.tasks.BaseOptions(
                model_asset_path=str(HAND_MODEL_PATH),
                delegate=mp.tasks.BaseOptions.Delegate.CPU,
            ),
            running_mode=mp.tasks.vision.RunningMode.VIDEO,
            num_hands=1,
            min_hand_detection_confidence=0.6,
            min_hand_presence_confidence=0.6,
            min_tracking_confidence=0.6,
        )
        return mp.tasks.vision.HandLandmarker.create_from_options(options)

    def _create_pose_detector(self) -> Any:
        import mediapipe as mp

        if not POSE_MODEL_PATH.exists():
            return None

        options = mp.tasks.vision.PoseLandmarkerOptions(
            base_options=mp.tasks.BaseOptions(
                model_asset_path=str(POSE_MODEL_PATH),
                delegate=mp.tasks.BaseOptions.Delegate.CPU,
            ),
            running_mode=mp.tasks.vision.RunningMode.VIDEO,
            num_poses=1,
            min_pose_detection_confidence=0.6,
            min_pose_presence_confidence=0.6,
            min_tracking_confidence=0.6,
        )
        return mp.tasks.vision.PoseLandmarker.create_from_options(options)

    def _detect_gestures(self, frame: Any) -> None:
        hand_result, hand_gesture = self._detect_hand_gesture(frame)
        pose_landmarks, body_gesture = self._detect_body_gesture(frame)
        self._update_gesture_state("hand", hand_gesture)
        self._update_gesture_state("body", body_gesture)
        if self.show_skeleton:
            self._draw_hand_skeleton(frame, hand_result)
            self._draw_pose_skeleton(frame, pose_landmarks)

    def _detect_hand_gesture(self, frame: Any) -> tuple[Any | None, int | None]:
        if self._hand_landmarker is None:
            return None, None

        import mediapipe as mp

        self._timestamp_ms += 1
        image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)
        result = self._hand_landmarker.detect_for_video(image, self._timestamp_ms)
        return result, self._count_fingers(result)

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

    def _detect_body_gesture(self, frame: Any) -> tuple[Any | None, int | None]:
        if self._pose_detector is None:
            return None, None

        pose_landmarks, feet = self._extract_pose_feet(frame)
        if feet is None:
            self._foot_points = {"left": None, "right": None}
            self._projected_foot_points = {"left": None, "right": None}
            self._body_support = None
            self.jump_probability = 0.0
            self._jump_history.clear()
            return pose_landmarks, None

        left_x, left_y, right_x, right_y = feet
        self._update_jump_probability(pose_landmarks)
        self._foot_points = {
            "left": (left_x, left_y),
            "right": (right_x, right_y),
        }
        self._projected_foot_points = {
            "left": self._project_point(left_x, left_y),
            "right": self._project_point(right_x, right_y),
        }
        foot_distance = ((left_x - right_x) ** 2 + (left_y - right_y) ** 2) ** 0.5
        if foot_distance < BODY_MIN_FEET_DISTANCE_FRAC:
            self._body_support = self._single_support(left_y, right_y)
            return pose_landmarks, 1

        if abs(left_y - right_y) >= BODY_SINGLE_LEG_Y_DELTA_FRAC:
            self._body_support = "left" if left_y > right_y else "right"
            return pose_landmarks, 1
        self._body_support = "both"
        return pose_landmarks, 2

    def _extract_pose_feet(
        self,
        frame: Any,
    ) -> tuple[Any | None, tuple[float, float, float, float] | None]:
        detector = self._pose_detector
        if detector is None:
            return None, None

        import mediapipe as mp

        self._timestamp_ms += 1
        image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)
        result = detector.detect_for_video(image, self._timestamp_ms)
        if not result.pose_landmarks:
            return None, None

        landmarks = result.pose_landmarks[0]
        left_heel = landmarks[POSE_LEFT_HEEL]
        right_heel = landmarks[POSE_RIGHT_HEEL]
        left_foot_index = landmarks[POSE_LEFT_FOOT_INDEX]
        right_foot_index = landmarks[POSE_RIGHT_FOOT_INDEX]

        if not self._landmarks_visible(
            left_heel,
            right_heel,
            left_foot_index,
            right_foot_index,
        ):
            return landmarks, None

        left_x = (left_heel.x + left_foot_index.x) / 2
        left_y = (left_heel.y + left_foot_index.y) / 2
        right_x = (right_heel.x + right_foot_index.x) / 2
        right_y = (right_heel.y + right_foot_index.y) / 2
        return landmarks, (left_x, left_y, right_x, right_y)

    def _landmarks_visible(self, *landmarks: Any) -> bool:
        return all(
            getattr(landmark, "visibility", 0.0) >= BODY_VISIBILITY_THRESHOLD
            for landmark in landmarks
        )

    def _update_gesture_state(self, source: str, gesture: int | None) -> None:
        state = self._gesture_states[source]
        if gesture != state.pending_gesture:
            state.pending_gesture = gesture
            state.pending_frames = 1
            return

        state.pending_frames += 1
        if state.pending_frames < state.stable_frames:
            return

        if gesture is None:
            state.latched_gesture = None
        elif gesture != state.latched_gesture:
            self._queue_gesture(gesture)
            state.latched_gesture = gesture

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
        self._gesture_queue = []
        for state in self._gesture_states.values():
            state.pending_gesture = None
            state.pending_frames = 0
            state.latched_gesture = None
        self._timestamp_ms = 0

    def _queue_gesture(self, gesture: int) -> None:
        if self._gesture_queue and self._gesture_queue[-1] == gesture:
            return
        self._gesture_queue.append(gesture)

    def _draw_hand_skeleton(self, frame: Any, result: Any | None) -> None:
        if result is None or not result.hand_landmarks:
            return
        for landmarks in result.hand_landmarks:
            self._draw_connections(frame, landmarks, HAND_CONNECTIONS, (255, 216, 80))

    def _draw_pose_skeleton(self, frame: Any, landmarks: Any | None) -> None:
        if landmarks is None:
            return
        self._draw_connections(frame, landmarks, POSE_CONNECTIONS, (78, 196, 112))

    def _draw_connections(
        self,
        frame: Any,
        landmarks: Any,
        connections: tuple[tuple[int, int], ...],
        color: tuple[int, int, int],
    ) -> None:
        import cv2

        height, width = frame.shape[:2]
        for start, end in connections:
            start_landmark = landmarks[start]
            end_landmark = landmarks[end]
            start_point = (int(start_landmark.x * width), int(start_landmark.y * height))
            end_point = (int(end_landmark.x * width), int(end_landmark.y * height))
            cv2.line(frame, start_point, end_point, color, 2)

        for landmark in landmarks:
            point = (int(landmark.x * width), int(landmark.y * height))
            cv2.circle(frame, point, 3, color, -1)

    def _single_support(self, left_y: float, right_y: float) -> str:
        return "left" if left_y >= right_y else "right"

    def _draw_calibration_outline(self, frame: Any) -> None:
        if len(self._calibration_points) != 4:
            return

        import cv2
        import numpy as np

        points = np.array(self._ordered_outline_points(), dtype=np.int32)
        cv2.polylines(frame, [points], True, (0, 255, 0), 3)

    def _update_jump_probability(self, landmarks: Any | None) -> None:
        if landmarks is None:
            self.jump_probability = 0.0
            self._jump_history.clear()
            return

        sample = self._jump_sample(landmarks)
        if sample is None:
            self.jump_probability = 0.0
            self._jump_history.clear()
            return

        self._jump_history.append(sample)
        if len(self._jump_history) < 3:
            self.jump_probability = 0.0
            return

        older = self._jump_history[0]
        middle = self._jump_history[len(self._jump_history) // 2]
        newer = self._jump_history[-1]
        dt_old = max(middle.timestamp_ms - older.timestamp_ms, 1) / 1000
        dt_new = max(newer.timestamp_ms - middle.timestamp_ms, 1) / 1000

        lift = newer.height - older.height
        velocity_old = (middle.height - older.height) / dt_old
        velocity_new = (newer.height - middle.height) / dt_new
        gravity_effect = max(0.0, velocity_old - velocity_new)

        lift_score = max(0.0, min(1.0, lift / JUMP_LIFT_THRESHOLD))
        velocity_score = max(0.0, min(1.0, velocity_old / JUMP_VELOCITY_THRESHOLD))
        gravity_score = max(0.0, min(1.0, gravity_effect / JUMP_GRAVITY_THRESHOLD))
        self.jump_probability = min(
            1.0,
            0.45 * lift_score + 0.35 * velocity_score + 0.2 * gravity_score,
        )

    def _jump_sample(self, landmarks: Any) -> "_JumpSample | None":
        left_shoulder = landmarks[11]
        right_shoulder = landmarks[12]
        left_hip = landmarks[23]
        right_hip = landmarks[24]
        left_knee = landmarks[25]
        right_knee = landmarks[26]
        required = (
            left_shoulder,
            right_shoulder,
            left_hip,
            right_hip,
            left_knee,
            right_knee,
        )
        if not self._landmarks_visible(*required):
            return None

        shoulder_y = (left_shoulder.y + right_shoulder.y) / 2
        hip_y = (left_hip.y + right_hip.y) / 2
        knee_y = (left_knee.y + right_knee.y) / 2
        center_y = (shoulder_y + hip_y + knee_y) / 3
        torso_height = max(hip_y - shoulder_y, 1e-4)
        normalized_height = -center_y / torso_height
        return _JumpSample(timestamp_ms=self._timestamp_ms, height=normalized_height)

    def _project_point(self, x: float, y: float) -> tuple[float, float] | None:
        if len(self._calibration_points) != 4:
            return None

        import cv2
        import numpy as np

        source = np.float32(self._calibration_points)
        target = np.float32(
            [
                [0, 0],
                [WIDTH, 0],
                [0, HEIGHT],
                [WIDTH, HEIGHT],
            ]
        )
        matrix = cv2.getPerspectiveTransform(source, target)
        point = np.array([[[x * CAMERA_WIDTH, y * CAMERA_HEIGHT]]], dtype=np.float32)
        transformed = cv2.perspectiveTransform(point, matrix)[0][0]
        return float(transformed[0]), float(transformed[1])

    def _ordered_outline_points(self) -> list[list[float]]:
        camera_bottom_right, camera_bottom_left, camera_top_right, camera_top_left = (
            self._calibration_points
        )
        return [
            camera_top_left,
            camera_top_right,
            camera_bottom_right,
            camera_bottom_left,
        ]

    def _marker_corner(
        self,
        points: list[tuple[float, float]],
        position: str,
    ) -> tuple[float, float]:
        targets = {
            "top_left": (0.0, 0.0),
            "top_right": (float(CAMERA_WIDTH), 0.0),
            "bottom_left": (0.0, float(CAMERA_HEIGHT)),
            "bottom_right": (float(CAMERA_WIDTH), float(CAMERA_HEIGHT)),
        }
        target_x, target_y = targets[position]
        return min(
            points,
            key=lambda point: (point[0] - target_x) ** 2 + (point[1] - target_y) ** 2,
        )

    def _log_calibration_event(self, event: str, payload: dict[str, Any]) -> None:
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        record = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "event": event,
            **payload,
        }
        with (LOGS_DIR / "calibration.log").open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")

    def _save_calibration_debug_image(self, attempt: int, suffix: str, image: Any) -> None:
        import cv2

        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        path = LOGS_DIR / f"calibration_{attempt:03d}_{suffix}.png"
        cv2.imwrite(str(path), image)


@dataclass
class _GestureState:
    stable_frames: int
    pending_gesture: int | None = None
    pending_frames: int = 0
    latched_gesture: int | None = None


@dataclass
class _JumpSample:
    timestamp_ms: int
    height: float
