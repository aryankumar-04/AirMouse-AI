"""Integration tests for GestureEngine pipeline."""

import unittest
import numpy as np

from config import GestureConfig
from app.vision.gesture_engine import GestureEngine, GestureEngineOutput
from app.vision.hand_tracker import DetectionResult, HandResult, HandLandmark
from app.core.gesture_state import GestureState


class TestGestureEngineIntegration(unittest.TestCase):

    def setUp(self):
        self.config = GestureConfig(stability_frames=2)
        self.engine = GestureEngine(config=self.config)

    def test_pipeline_with_mock_detection(self):
        # Create a mock 480x640 frame
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        landmarks = [HandLandmark(id=i, x=0.5, y=0.5, z=0.0, px=320, py=240) for i in range(21)]

        hand_res = HandResult(
            handedness="Right",
            score=0.98,
            landmarks=landmarks,
            wrist=(320, 400),
            index_tip=(320, 200),
            thumb_tip=(300, 250),
            bbox=(250, 180, 380, 420)
        )

        detection = DetectionResult(
            hands=[hand_res],
            processed_frame=frame,
            hand_count=1
        )

        out: GestureEngineOutput = self.engine.process(detection, draw_debug_overlay=True)

        self.assertIsNotNone(out)
        self.assertIsNotNone(out.processed_frame)
        self.assertIsNotNone(out.event)
        self.assertIsNotNone(out.mapped_action)
        self.assertGreaterEqual(out.processing_time_ms, 0.0)


if __name__ == "__main__":
    unittest.main()
