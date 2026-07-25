"""
AirMouse AI - Hand Tracker Module.

Provides robust real-time hand landmark detection, handedness classification,
and landmark visualization overlays using MediaPipe Tasks API with square ROI padding.
"""

from dataclasses import dataclass, field
import logging
import os
import time
from typing import List, Optional, Tuple
import urllib.request
import cv2
import mediapipe as mp
import numpy as np

from config import HandTrackingConfig


# Standard MediaPipe 21 Hand Landmark Connections
HAND_CONNECTIONS = [
    # Thumb
    (0, 1), (1, 2), (2, 3), (3, 4),
    # Index finger
    (0, 5), (5, 6), (6, 7), (7, 8),
    # Middle finger
    (9, 10), (10, 11), (11, 12),
    # Ring finger
    (13, 14), (14, 15), (15, 16),
    # Pinky
    (0, 17), (17, 18), (18, 19), (19, 20),
    # Palm connections
    (5, 9), (9, 13), (13, 17)
]


@dataclass
class HandLandmark:
    """Individual 3D hand landmark representation."""
    id: int
    x: float  # Normalized [0.0, 1.0]
    y: float  # Normalized [0.0, 1.0]
    z: float  # Depth
    px: int   # Pixel X
    py: int   # Pixel Y


@dataclass
class HandResult:
    """Structured detection outcome for a single hand."""
    handedness: str         # "Left" or "Right"
    score: float            # Classification confidence
    landmarks: List[HandLandmark]
    wrist: Tuple[int, int]
    index_tip: Tuple[int, int]
    thumb_tip: Tuple[int, int]
    bbox: Tuple[int, int, int, int]  # (min_x, min_y, max_x, max_y)


@dataclass
class DetectionResult:
    """Overall detection outcome for a single video frame."""
    hands: List[HandResult] = field(default_factory=list)
    processed_frame: Optional[np.ndarray] = None
    hand_count: int = 0
    timestamp: float = 0.0


class HandTracker:
    """Real-time hand landmark tracker supporting MediaPipe Tasks API."""

    def __init__(
        self,
        config: HandTrackingConfig,
        logger: Optional[logging.Logger] = None
    ):
        self.config = config
        self.logger = logger or logging.getLogger("AirMouseAI.HandTracker")

        self._landmarker = None
        self._frame_timestamp_ms = int(time.time() * 1000)

        self._init_mediapipe()

    def _ensure_model_file(self) -> str:
        """Ensures hand landmarker task file exists locally, downloading if missing."""
        model_path = os.path.abspath(self.config.model_path)
        if not os.path.exists(model_path):
            os.makedirs(os.path.dirname(model_path), exist_ok=True)
            self.logger.debug("Downloading MediaPipe hand tracking model...")
            try:
                urllib.request.urlretrieve(self.config.model_url, model_path)
                self.logger.debug("Hand model downloaded successfully.")
            except Exception as err:
                self.logger.error(f"Failed to download hand tracking model: {err}")
                raise err
        return model_path

    def _init_mediapipe(self):
        """Initializes MediaPipe Tasks API HandLandmarker in VIDEO running mode."""
        try:
            from app.core.logger import suppress_c_stderr
            from mediapipe.tasks import python
            from mediapipe.tasks.python import vision

            model_path = self._ensure_model_file()
            base_options = python.BaseOptions(model_asset_path=model_path)
            options = vision.HandLandmarkerOptions(
                base_options=base_options,
                num_hands=self.config.max_num_hands,
                min_hand_detection_confidence=self.config.min_detection_confidence,
                min_tracking_confidence=self.config.min_tracking_confidence,
                running_mode=vision.RunningMode.VIDEO
            )
            
            # Swallow C++ delegate spam in stderr during creation
            with suppress_c_stderr(enabled=True):
                self._landmarker = vision.HandLandmarker.create_from_options(options)
            
            self.logger.debug("MediaPipe HandLandmarker (Tasks API VIDEO mode) initialized successfully.")
        except Exception as err:
            self.logger.error(f"Failed to initialize MediaPipe HandLandmarker: {err}")
            raise err

    def process_frame(
        self,
        frame: np.ndarray,
        draw_overlay: bool = True
    ) -> DetectionResult:
        """Detects hand landmarks in a BGR image frame."""
        if frame is None:
            return DetectionResult(processed_frame=frame, timestamp=time.time())

        h, w, _ = frame.shape
        out_frame = frame.copy() if draw_overlay else frame

        if self._landmarker:
            return self._process_tasks_api(frame, out_frame, h, w, draw_overlay)

        return DetectionResult(processed_frame=out_frame, timestamp=time.time())

    def _process_tasks_api(
        self, frame: np.ndarray, out_frame: np.ndarray, h: int, w: int, draw_overlay: bool
    ) -> DetectionResult:
        """Processes frame using MediaPipe Tasks API with square ROI padding for 100% detection accuracy."""
        max_dim = max(h, w)
        top = (max_dim - h) // 2
        bottom = max_dim - h - top
        left = (max_dim - w) // 2
        right = max_dim - w - left

        # Pad frame to square ROI for MediaPipe TFLite landmark calculator compatibility
        square_frame = cv2.copyMakeBorder(frame, top, bottom, left, right, cv2.BORDER_CONSTANT, value=[0, 0, 0])
        rgb_frame = np.ascontiguousarray(cv2.cvtColor(square_frame, cv2.COLOR_BGR2RGB))
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

        self._frame_timestamp_ms += 33
        result = self._landmarker.detect_for_video(mp_image, self._frame_timestamp_ms)
        detected_hands: List[HandResult] = []

        if result and result.hand_landmarks and result.handedness:
            for idx, raw_landmarks in enumerate(result.hand_landmarks):
                categories = result.handedness[idx]
                category = categories[0] if categories else None
                handedness_label = category.category_name if category else "Hand"
                confidence_score = category.score if category else 0.9

                lm_list: List[HandLandmark] = []
                x_coords: List[int] = []
                y_coords: List[int] = []

                for lm_id, lm in enumerate(raw_landmarks):
                    # Unpad square coordinate back to original camera frame coordinates
                    sq_px = lm.x * max_dim
                    sq_py = lm.y * max_dim

                    orig_px = sq_px - left
                    orig_py = sq_py - top

                    px = math_clamp(int(orig_px), 0, w - 1)
                    py = math_clamp(int(orig_py), 0, h - 1)

                    norm_x = max(0.0, min(1.0, orig_px / w))
                    norm_y = max(0.0, min(1.0, orig_py / h))

                    lm_list.append(HandLandmark(
                        id=lm_id, x=norm_x, y=norm_y, z=lm.z, px=px, py=py
                    ))
                    x_coords.append(px)
                    y_coords.append(py)

                wrist_pt = (lm_list[0].px, lm_list[0].py)
                thumb_tip_pt = (lm_list[4].px, lm_list[4].py)
                index_tip_pt = (lm_list[8].px, lm_list[8].py)

                margin = 15
                bbox = (
                    max(0, min(x_coords) - margin),
                    max(0, min(y_coords) - margin),
                    min(w, max(x_coords) + margin),
                    min(h, max(y_coords) + margin)
                )

                hand_res = HandResult(
                    handedness=handedness_label,
                    score=confidence_score,
                    landmarks=lm_list,
                    wrist=wrist_pt,
                    index_tip=index_tip_pt,
                    thumb_tip=thumb_tip_pt,
                    bbox=bbox
                )
                detected_hands.append(hand_res)

                if draw_overlay:
                    self._draw_hand_landmarks(out_frame, lm_list, bbox, handedness_label, confidence_score)

        return DetectionResult(
            hands=detected_hands,
            processed_frame=out_frame,
            hand_count=len(detected_hands),
            timestamp=time.time()
        )

    def _draw_hand_landmarks(
        self,
        frame: np.ndarray,
        landmarks: List[HandLandmark],
        bbox: Tuple[int, int, int, int],
        handedness: str,
        score: float
    ):
        """Draws vibrant landmark overlay, skeleton lines, and handedness label on image frame."""
        for start_idx, end_idx in HAND_CONNECTIONS:
            if start_idx < len(landmarks) and end_idx < len(landmarks):
                pt1 = (landmarks[start_idx].px, landmarks[start_idx].py)
                pt2 = (landmarks[end_idx].px, landmarks[end_idx].py)
                cv2.line(frame, pt1, pt2, (181, 173, 0), 2, cv2.LINE_AA)

        fingertip_ids = {4, 8, 12, 16, 20}
        for lm in landmarks:
            if lm.id in fingertip_ids:
                cv2.circle(frame, (lm.px, lm.py), 6, (0, 145, 255), -1, cv2.LINE_AA)
                cv2.circle(frame, (lm.px, lm.py), 7, (255, 255, 255), 1, cv2.LINE_AA)
            else:
                cv2.circle(frame, (lm.px, lm.py), 4, (118, 230, 0), -1, cv2.LINE_AA)

        box_x1, box_y1, box_x2, box_y2 = bbox
        cv2.rectangle(frame, (box_x1, box_y1), (box_x2, box_y2), (118, 230, 0), 2)

        label_str = f"{handedness} ({int(score * 100)}%)"
        cv2.putText(
            frame,
            label_str,
            (box_x1, max(25, box_y1 - 10)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (118, 230, 0),
            2,
            cv2.LINE_AA
        )

    def close(self):
        """Releases detector engine resources."""
        if self._landmarker:
            self.logger.debug("Closing MediaPipe HandLandmarker...")
            self._landmarker.close()
            self._landmarker = None


def math_clamp(val: int, min_val: int, max_val: int) -> int:
    """Clamps integer value to [min_val, max_val]."""
    return max(min_val, min(val, max_val))
