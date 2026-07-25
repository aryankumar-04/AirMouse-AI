"""
AirMouse AI - Gesture Engine Module.

Processes video frames and hand landmark detections through smoothing filters,
geometry classification rules, state machine debouncing, and renders live debug graphics.
"""

from dataclasses import dataclass, field
import logging
import time
from typing import List, Optional, Tuple
import cv2
import numpy as np

from config import GestureConfig
from app.core.gesture_state import GestureEvent, GestureState, GestureStateMachine, TransitionType
from app.control.gesture_mapper import GestureMapper, MappedAction, ActionIntent
from app.vision.hand_tracker import DetectionResult, HandLandmark, HandResult
from app.utils.geometry import (
    calculate_hand_size,
    calculate_normalized_distance,
    euclidean_distance_2d,
    get_finger_extension_states
)
from app.utils.smoothing import LandmarkSmoother


@dataclass
class GestureEngineOutput:
    """Complete output product of the gesture processing pipeline for a single frame."""
    event: GestureEvent
    mapped_action: MappedAction
    processed_frame: Optional[np.ndarray] = None
    pinch_distance: float = 0.0
    hand_size: float = 1.0
    smoothed_landmarks: List[HandLandmark] = field(default_factory=list)
    anchor_pos: Tuple[float, float] = (0.5, 0.5)  # Rigid palm-backed control anchor (cx, cy)
    processing_time_ms: float = 0.0


class GestureEngine:
    """Core gesture recognition engine with anti-jitter smoothing and debug visualization."""

    def __init__(
        self,
        config: GestureConfig,
        logger: Optional[logging.Logger] = None
    ):
        self.config = config
        self.logger = logger or logging.getLogger("AirMouseAI.GestureEngine")

        from app.utils.smoothing import AdaptiveLandmarkSmoother
        self.landmark_smoother = AdaptiveLandmarkSmoother(min_cutoff=0.8, beta=0.02)
        self.state_machine = GestureStateMachine(config=config)
        self.gesture_mapper = GestureMapper()

        self._last_anchor_pos: Optional[Tuple[float, float]] = None
        self._last_anchor_time: Optional[float] = None
        self.current_hand_velocity: float = 0.0

    def process(
        self,
        detection_result: DetectionResult,
        draw_debug_overlay: bool = True
    ) -> GestureEngineOutput:
        """Processes hand landmark detection into a stabilized gesture event."""
        start_time = time.perf_counter()

        frame = detection_result.processed_frame
        out_frame = frame.copy() if (frame is not None and draw_debug_overlay) else frame
        h, w, _ = frame.shape if frame is not None else (480, 640, 3)

        if not detection_result.hands or len(detection_result.hands) == 0:
            # Reset smoother and state machine on tracking loss
            self.landmark_smoother.reset()
            self._last_anchor_pos = None
            self._last_anchor_time = None
            self.current_hand_velocity = 0.0

            event = self.state_machine.update(
                candidate_state=GestureState.NO_HAND,
                pinch_distance=1.0,
                handedness="None",
                confidence=0.0,
                index_tip_pos=(0, 0),
                right_pinch_distance=1.0,
                hand_velocity=0.0
            )
            action = self.gesture_mapper.map_event(event)
            proc_time = (time.perf_counter() - start_time) * 1000.0

            if out_frame is not None and draw_debug_overlay:
                self._draw_no_hand_overlay(out_frame)

            return GestureEngineOutput(
                event=event,
                mapped_action=action,
                processed_frame=out_frame,
                anchor_pos=(0.5, 0.5),
                processing_time_ms=proc_time
            )

        # Focus primary tracking on first detected hand
        primary_hand: HandResult = detection_result.hands[0]
        raw_landmarks = primary_hand.landmarks

        # 1. One Euro Adaptive landmark smoothing
        smoothed_landmarks = self.landmark_smoother.smooth(raw_landmarks, width=w, height=h, timestamp=start_time)

        # 2. Scale-invariant reference calculations
        hand_size = calculate_hand_size(smoothed_landmarks)
        frame_scale = hand_size * min(w, h)

        thumb_tip = (smoothed_landmarks[4].px, smoothed_landmarks[4].py)
        index_tip = (smoothed_landmarks[8].px, smoothed_landmarks[8].py)
        middle_tip = (smoothed_landmarks[12].px, smoothed_landmarks[12].py)

        # Left pinch: Thumb + Index
        norm_pinch_dist = calculate_normalized_distance(thumb_tip, index_tip, frame_scale)
        # Right pinch: Thumb + Middle
        norm_right_pinch_dist = calculate_normalized_distance(thumb_tip, middle_tip, frame_scale)

        # 3. Rigid palm-backed control anchor (0.65 MCP + 0.35 Tip)
        index_mcp_lm = smoothed_landmarks[5]
        index_tip_lm = smoothed_landmarks[8]
        anchor_x = 0.65 * index_mcp_lm.x + 0.35 * index_tip_lm.x
        anchor_y = 0.65 * index_mcp_lm.y + 0.35 * index_tip_lm.y
        anchor_pos = (max(0.0, min(1.0, anchor_x)), max(0.0, min(1.0, anchor_y)))

        # 4. Calculate hand centroid velocity (norm units / sec)
        if self._last_anchor_pos is not None and self._last_anchor_time is not None:
            dt = start_time - self._last_anchor_time
            if dt > 1e-4:
                dist = np.hypot(anchor_pos[0] - self._last_anchor_pos[0], anchor_pos[1] - self._last_anchor_pos[1])
                self.current_hand_velocity = float(dist / dt)
        else:
            self.current_hand_velocity = 0.0

        self._last_anchor_pos = anchor_pos
        self._last_anchor_time = start_time

        # 5. Finger extension classification
        ext_states = get_finger_extension_states(
            smoothed_landmarks, ratio_threshold=self.config.finger_extension_ratio
        )
        num_extended = sum(1 for is_ext in ext_states.values() if is_ext)

        # 6. Pose candidate evaluation (Strict Mutually Exclusive Priority Order)
        #    Priority: FIST > OPEN_PALM > TWO_FINGER > RIGHT_PINCH > LEFT_PINCH > POINTING
        candidate_pose = GestureState.UNKNOWN
        palm_min_fingers = getattr(self.config, 'palm_open_min_fingers', 4)

        if num_extended == 0:
            # Priority 1: Closed fist — emergency stop
            candidate_pose = GestureState.FIST
        elif num_extended >= palm_min_fingers:
            # Priority 2: Open palm — neutral / pause (only if NO pinch is active)
            # Guard: prevent open_palm if thumb+index or thumb+middle are actually pinching
            if norm_pinch_dist < self.config.pinch_threshold:
                candidate_pose = GestureState.PINCH_START
            elif norm_right_pinch_dist < getattr(self.config, 'right_pinch_threshold', 0.22):
                candidate_pose = GestureState.RIGHT_PINCH_START
            else:
                candidate_pose = GestureState.OPEN_PALM
        elif ext_states["index"] and ext_states["middle"] and not ext_states["ring"] and not ext_states["pinky"]:
            # Priority 3: Two-finger scroll mode
            # Guard: suppress if thumb+middle are pinching (right click takes priority over scroll)
            right_thresh = getattr(self.config, 'right_pinch_threshold', 0.22)
            if norm_right_pinch_dist < right_thresh:
                candidate_pose = GestureState.RIGHT_PINCH_START
            else:
                candidate_pose = GestureState.TWO_FINGER
        elif ext_states["index"] and ext_states["middle"] and ext_states["ring"] and not ext_states["pinky"]:
            candidate_pose = GestureState.THREE_FINGER
        elif ext_states["index"] and not ext_states["middle"] and not ext_states["ring"] and not ext_states["pinky"]:
            # Priority 6: Single index pointing — hover movement
            # Guard: check if thumb+index pinch is active (left click overrides hover)
            if norm_pinch_dist < self.config.pinch_threshold:
                candidate_pose = GestureState.PINCH_START
            else:
                candidate_pose = GestureState.POINTING
        elif ext_states["thumb"] and ext_states["index"] and not ext_states["middle"]:
            if norm_pinch_dist < self.config.pinch_threshold:
                candidate_pose = GestureState.PINCH_START
            else:
                candidate_pose = GestureState.POINTING
        else:
            # Fallback: check for pinch in ambiguous hand poses
            right_thresh = getattr(self.config, 'right_pinch_threshold', 0.22)
            if norm_right_pinch_dist < right_thresh and num_extended <= 3:
                candidate_pose = GestureState.RIGHT_PINCH_START
            elif norm_pinch_dist < self.config.pinch_threshold and num_extended <= 3:
                candidate_pose = GestureState.PINCH_START

        # 7. Feed into State Machine for debouncing, hysteresis & velocity gating
        event = self.state_machine.update(
            candidate_state=candidate_pose,
            pinch_distance=norm_pinch_dist,
            handedness=primary_hand.handedness,
            confidence=primary_hand.score,
            index_tip_pos=(int(anchor_pos[0] * w), int(anchor_pos[1] * h)),
            right_pinch_distance=norm_right_pinch_dist,
            hand_velocity=self.current_hand_velocity
        )

        # 8. Map to abstract action intent
        mapped_action = self.gesture_mapper.map_event(event)
        proc_time = (time.perf_counter() - start_time) * 1000.0

        # 9. Render debug overlay on video frame
        if out_frame is not None and draw_debug_overlay:
            self._draw_debug_overlay(
                out_frame,
                event=event,
                action=mapped_action,
                pinch_dist=norm_pinch_dist,
                hand_size=hand_size,
                anchor_pos=anchor_pos,
                proc_time_ms=proc_time
            )

        return GestureEngineOutput(
            event=event,
            mapped_action=mapped_action,
            processed_frame=out_frame,
            pinch_distance=norm_pinch_dist,
            hand_size=hand_size,
            smoothed_landmarks=smoothed_landmarks,
            anchor_pos=anchor_pos,
            processing_time_ms=proc_time
        )

    def _draw_no_hand_overlay(self, frame: np.ndarray):
        """Renders overlay when no hand is present."""
        cv2.putText(
            frame,
            "GESTURE: NO HAND",
            (15, 35),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.75,
            (100, 100, 100),
            2,
            cv2.LINE_AA
        )

    def _draw_debug_overlay(
        self,
        frame: np.ndarray,
        event: GestureEvent,
        action: MappedAction,
        pinch_dist: float,
        hand_size: float,
        anchor_pos: Tuple[float, float],
        proc_time_ms: float
    ):
        """Renders rich debug overlay showing active gesture, pinch gauge, and state metrics."""
        badge_state_text = f"GESTURE: {event.state.name}"
        color_map = {
            GestureState.OPEN_PALM: (0, 200, 83),     # Green
            GestureState.POINTING: (255, 179, 0),     # Amber/Orange
            GestureState.PINCH_START: (0, 229, 255),  # Cyan
            GestureState.PINCH_HOLD: (0, 229, 255),   # Cyan
            GestureState.PINCH_RELEASE: (186, 104, 200),# Purple
            GestureState.TWO_FINGER: (255, 64, 129),  # Pink
            GestureState.THREE_FINGER: (156, 39, 176),# Purple/Magenta (Right Click)
            GestureState.FIST: (213, 0, 0),           # Red
            GestureState.NO_HAND: (100, 100, 100)     # Gray
        }
        badge_color = color_map.get(event.state, (200, 200, 200))

        # Main Gesture Label
        cv2.putText(
            frame,
            badge_state_text,
            (15, 35),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.75,
            badge_color,
            2,
            cv2.LINE_AA
        )

        # Mapped Action Label
        action_text = f"ACTION: {action.action.name}"
        cv2.putText(
            frame,
            action_text,
            (15, 65),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (255, 255, 255),
            1,
            cv2.LINE_AA
        )

        # Pinch Meter Gauge Bar
        gauge_x = 15
        gauge_y = 80
        gauge_w = 160
        gauge_h = 12
        cv2.rectangle(frame, (gauge_x, gauge_y), (gauge_x + gauge_w, gauge_y + gauge_h), (50, 50, 50), -1)

        fill_ratio = max(0.0, min(1.0, 1.0 - (pinch_dist / 0.5)))
        fill_w = int(gauge_w * fill_ratio)
        gauge_color = (0, 229, 255) if fill_ratio > 0.5 else (0, 150, 200)

        cv2.rectangle(frame, (gauge_x, gauge_y), (gauge_x + fill_w, gauge_y + gauge_h), gauge_color, -1)
        cv2.rectangle(frame, (gauge_x, gauge_y), (gauge_x + gauge_w, gauge_y + gauge_h), (200, 200, 200), 1)

        cv2.putText(
            frame,
            f"Pinch: {pinch_dist:.2f}",
            (gauge_x + gauge_w + 10, gauge_y + 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            (200, 200, 200),
            1,
            cv2.LINE_AA
        )

        # Frame Stability & Anchor Info
        stability_str = f"Stability: {event.stability_count}/{self.config.stability_frames} ({'STABLE' if event.is_stable else 'TRANSITION'})"
        cv2.putText(
            frame,
            stability_str,
            (15, 115),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            (0, 230, 118) if event.is_stable else (255, 171, 0),
            1,
            cv2.LINE_AA
        )

        # Draw anchor point marker on out_frame
        h, w, _ = frame.shape
        ax_px = int(anchor_pos[0] * w)
        ay_px = int(anchor_pos[1] * h)
        cv2.circle(frame, (ax_px, ay_px), 5, (0, 255, 255), -1, cv2.LINE_AA)
        cv2.circle(frame, (ax_px, ay_px), 8, (255, 255, 255), 1, cv2.LINE_AA)
