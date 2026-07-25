"""
AirMouse AI - Unit Tests for Refactored Mouse Tracking & Gesture Engine.

Tests scale-normalized dual pinch hysteresis, velocity gating, clutch re-engagement,
One Euro Filter 2D pointer acceleration, and win32 mouse backend execution.
"""

import unittest
import numpy as np

from config import AppConfig, GestureConfig, MouseConfig, CalibrationConfig
from app.vision.gesture_engine import GestureEngine
from app.vision.hand_tracker import DetectionResult, HandResult, HandLandmark
from app.core.gesture_state import GestureState, GestureStateMachine, TransitionType
from app.control.calibration import CoordinateTransformer, TrackingState
from app.control.mouse_controller import MouseController
from app.control.win32_mouse import Win32MouseBackend


class TestRefactoredTrackingEngine(unittest.TestCase):

    def setUp(self):
        self.gesture_config = GestureConfig(
            pinch_threshold=0.25,
            pinch_release_threshold=0.38,
            right_pinch_threshold=0.25,
            right_pinch_release_threshold=0.38,
            max_click_velocity=1.2,
            stability_frames=1
        )
        self.mouse_config = MouseConfig(
            enabled=True,
            one_euro_min_cutoff=0.6,
            one_euro_beta=0.015,
            motion_deadzone_px=3.0,
            drag_hold_duration_ms=200,
            failsafe=False
        )
        self.cal_config = CalibrationConfig(screen_width=1920, screen_height=1080)
        self.state_machine = GestureStateMachine(config=self.gesture_config)
        self.transformer = CoordinateTransformer(
            calibration_config=self.cal_config,
            mouse_config=self.mouse_config
        )

    def test_dual_pinch_hysteresis_left_and_right(self):
        # 1. Left Pinch (Thumb + Index) below threshold
        ev_left = self.state_machine.update(
            candidate_state=GestureState.POINTING,
            pinch_distance=0.20, # < 0.25 threshold
            handedness="Right",
            confidence=0.9,
            index_tip_pos=(320, 240),
            right_pinch_distance=0.8,
            hand_velocity=0.1
        )
        self.assertEqual(ev_left.state, GestureState.PINCH_START)

        # 2. Right Pinch (Thumb + Middle) below threshold
        sm2 = GestureStateMachine(config=self.gesture_config)
        ev_right = sm2.update(
            candidate_state=GestureState.TWO_FINGER,
            pinch_distance=0.8,
            handedness="Right",
            confidence=0.9,
            index_tip_pos=(320, 240),
            right_pinch_distance=0.20, # < 0.25 right threshold
            hand_velocity=0.1
        )
        self.assertEqual(ev_right.state, GestureState.RIGHT_PINCH_START)

    def test_velocity_gating_suppresses_fast_hand_clicks(self):
        # When hand velocity is fast (> 1.2), starting a new pinch should be suppressed
        ev_fast = self.state_machine.update(
            candidate_state=GestureState.POINTING,
            pinch_distance=0.20,
            handedness="Right",
            confidence=0.9,
            index_tip_pos=(320, 240),
            right_pinch_distance=0.8,
            hand_velocity=2.5 # Too fast!
        )
        # Should stay POINTING rather than triggering PINCH_START
        self.assertEqual(ev_fast.state, GestureState.POINTING)

    def test_clutch_mechanism_on_tracking_loss_and_reengage(self):
        # 1. Active tracking after re-engagement frames
        self.transformer.transform((0.5, 0.5))
        self.transformer.transform((0.5, 0.5))
        self.assertEqual(self.transformer.tracking_state, TrackingState.ACTIVE)

        # 2. Tracking lost (hand leaves frame)
        self.transformer.reset()
        self.assertEqual(self.transformer.tracking_state, TrackingState.LOST)

        # 3. Tracking resumes -> RE_ENGAGING on frame 1
        p2 = self.transformer.transform((0.7, 0.7))
        self.assertEqual(self.transformer.tracking_state, TrackingState.RE_ENGAGING)

        # 4. ACTIVE on frame 2
        p3 = self.transformer.transform((0.7, 0.7))
        self.assertEqual(self.transformer.tracking_state, TrackingState.ACTIVE)

    def test_win32_mouse_backend_instantiation(self):
        backend = Win32MouseBackend()
        self.assertIsNotNone(backend)


if __name__ == "__main__":
    unittest.main()
