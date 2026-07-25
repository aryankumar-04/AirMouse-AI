"""Unit tests for CoordinateTransformer camera-to-screen coordinate mapping."""

import unittest
from config import CalibrationConfig, MouseConfig
from app.control.calibration import CoordinateTransformer


class TestMouseMapping(unittest.TestCase):

    def setUp(self):
        self.cal_config = CalibrationConfig(
            padding_x=0.1,
            padding_y=0.1,
            screen_width=1920,
            screen_height=1080,
            flip_horizontal=True
        )
        self.mouse_config = MouseConfig(smoothing_factor=1.0, motion_deadzone_px=0.0)
        self.transformer = CoordinateTransformer(
            calibration_config=self.cal_config,
            mouse_config=self.mouse_config
        )

    def test_center_coordinate_mapping(self):
        # Center in camera space (0.5, 0.5) with horizontal flip -> (0.5, 0.5)
        sx, sy = self.transformer.transform((0.5, 0.5))
        expected_x = (self.transformer.screen_width - 1) / 2
        expected_y = (self.transformer.screen_height - 1) / 2
        self.assertAlmostEqual(sx, expected_x, delta=5)
        self.assertAlmostEqual(sy, expected_y, delta=5)

    def test_horizontal_mirror_flip(self):
        # Moving hand left in camera view (cx = 0.2) should map towards right of screen when flipped (cx' = 0.8)
        sx_left, _ = self.transformer.transform((0.2, 0.5))
        self.transformer.reset()

        # Moving hand right in camera view (cx = 0.8) should map towards left of screen when flipped (cx' = 0.2)
        sx_right, _ = self.transformer.transform((0.8, 0.5))

        self.assertGreater(sx_left, sx_right)

    def test_workspace_margin_clamping(self):
        # Coordinates outside padding boundaries should clamp safely to screen bounds
        sx, sy = self.transformer.transform((0.0, 0.0))
        self.assertGreaterEqual(sx, 0)
        self.assertLess(sx, 1920)
        self.assertGreaterEqual(sy, 0)
        self.assertLess(sy, 1080)


if __name__ == "__main__":
    unittest.main()
