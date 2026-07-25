"""Unit tests for CalibrationConfig and transformer parameters."""

import unittest
from config import CalibrationConfig, MouseConfig
from app.control.calibration import CoordinateTransformer


class TestCalibration(unittest.TestCase):

    def test_update_smoothing_factor(self):
        cal_cfg = CalibrationConfig(screen_width=1000, screen_height=1000)
        mouse_cfg = MouseConfig(smoothing_factor=0.5)
        transformer = CoordinateTransformer(cal_cfg, mouse_cfg)

        transformer.update_smoothing_factor(0.8)
        self.assertAlmostEqual(transformer.mouse_config.smoothing_factor, 0.8)

    def test_update_padding_bounds(self):
        cal_cfg = CalibrationConfig(screen_width=1000, screen_height=1000)
        mouse_cfg = MouseConfig()
        transformer = CoordinateTransformer(cal_cfg, mouse_cfg)

        transformer.update_padding(0.20, 0.20)
        self.assertAlmostEqual(transformer.cal_config.padding_x, 0.20)
        self.assertAlmostEqual(transformer.cal_config.padding_y, 0.20)


if __name__ == "__main__":
    unittest.main()
