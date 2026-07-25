"""Unit tests for HandTracker module."""

import unittest
import numpy as np

from config import HandTrackingConfig
from app.vision.hand_tracker import HandTracker, DetectionResult


class TestHandTracker(unittest.TestCase):

    def setUp(self):
        self.config = HandTrackingConfig(max_num_hands=1)
        self.tracker = HandTracker(config=self.config)

    def tearDown(self):
        if self.tracker:
            self.tracker.close()

    def test_process_blank_image(self):
        # Create a black 480x640 frame
        blank_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        result: DetectionResult = self.tracker.process_frame(blank_frame, draw_overlay=True)

        self.assertIsNotNone(result)
        self.assertEqual(result.hand_count, 0)
        self.assertEqual(len(result.hands), 0)
        self.assertIsNotNone(result.processed_frame)

    def test_process_none_frame_handles_gracefully(self):
        result = self.tracker.process_frame(None)
        self.assertIsNotNone(result)
        self.assertEqual(result.hand_count, 0)


if __name__ == "__main__":
    unittest.main()
