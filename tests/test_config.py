"""Unit tests for configuration dataclasses."""

import unittest
from config import AppConfig, CameraConfig, HandTrackingConfig, UIConfig


class TestConfig(unittest.TestCase):

    def test_default_config_instantiation(self):
        config = AppConfig()
        self.assertEqual(config.camera.camera_index, 0)
        self.assertEqual(config.camera.frame_width, 640)
        self.assertEqual(config.camera.frame_height, 480)
        self.assertEqual(config.tracking.max_num_hands, 2)
        self.assertAlmostEqual(config.tracking.min_detection_confidence, 0.90)

    def test_custom_config_override(self):
        custom_cam = CameraConfig(camera_index=1, frame_width=1280, frame_height=720)
        config = AppConfig(camera=custom_cam, debug_mode=False)
        self.assertEqual(config.camera.camera_index, 1)
        self.assertEqual(config.camera.frame_width, 1280)
        self.assertFalse(config.debug_mode)


if __name__ == "__main__":
    unittest.main()
