"""Unit tests for GestureEngine pose classification rules."""

import unittest
import numpy as np

from config import GestureConfig
from app.vision.gesture_engine import GestureEngine
from app.vision.hand_tracker import DetectionResult, HandResult, HandLandmark
from app.core.gesture_state import GestureState


class TestGestureRules(unittest.TestCase):

    def setUp(self):
        self.config = GestureConfig(stability_frames=1)  # 1 frame for instant classification unit testing
        self.engine = GestureEngine(config=self.config)

    def test_process_empty_detection_returns_no_hand(self):
        empty_detection = DetectionResult(hands=[], processed_frame=np.zeros((480, 640, 3), dtype=np.uint8))
        out = self.engine.process(empty_detection, draw_debug_overlay=False)

        self.assertEqual(out.event.state, GestureState.NO_HAND)
        self.assertIsNotNone(out.mapped_action)

    def test_pointing_gesture_classification(self):
        # Create landmarks for pointing index finger
        landmarks = [HandLandmark(id=i, x=0.5, y=0.5, z=0.0, px=320, py=240) for i in range(21)]
        # Wrist
        landmarks[0] = HandLandmark(id=0, x=0.5, y=0.9, z=0.0, px=320, py=450)

        # Index extended high
        landmarks[5] = HandLandmark(id=5, x=0.5, y=0.7, z=0.0, px=320, py=350)
        landmarks[6] = HandLandmark(id=6, x=0.5, y=0.5, z=0.0, px=320, py=250)
        landmarks[8] = HandLandmark(id=8, x=0.5, y=0.1, z=0.0, px=320, py=50)

        # Middle, Ring, Pinky folded near palm (y = 0.7)
        for tip in (12, 16, 20):
            landmarks[tip] = HandLandmark(id=tip, x=0.5, y=0.7, z=0.0, px=320, py=350)

        hand_res = HandResult(
            handedness="Right",
            score=0.95,
            landmarks=landmarks,
            wrist=(320, 450),
            index_tip=(320, 50),
            thumb_tip=(300, 350),
            bbox=(250, 40, 400, 460)
        )

        detection = DetectionResult(
            hands=[hand_res],
            processed_frame=np.zeros((480, 640, 3), dtype=np.uint8),
            hand_count=1
        )

        out = self.engine.process(detection, draw_debug_overlay=False)
        self.assertEqual(out.event.state, GestureState.POINTING)


if __name__ == "__main__":
    unittest.main()
