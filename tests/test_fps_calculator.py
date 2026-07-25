"""Unit tests for FPSCalculator utility."""

import time
import unittest
from app.utils.fps_calculator import FPSCalculator


class TestFPSCalculator(unittest.TestCase):

    def test_initial_fps_is_zero(self):
        fps_calc = FPSCalculator()
        self.assertEqual(fps_calc.get_fps(), 0.0)

    def test_single_tick_returns_zero(self):
        fps_calc = FPSCalculator()
        fps_calc.tick()
        self.assertEqual(fps_calc.get_fps(), 0.0)

    def test_fps_calculation_with_simulated_ticks(self):
        fps_calc = FPSCalculator(buffer_size=10)
        # Simulate 10 frames over 0.5 seconds (~20 FPS)
        for _ in range(10):
            fps_calc.tick()
            time.sleep(0.02)
        fps = fps_calc.get_fps()
        self.assertGreater(fps, 0.0)
        self.assertLess(fps, 100.0)

    def test_reset_clears_history(self):
        fps_calc = FPSCalculator()
        fps_calc.tick()
        fps_calc.tick()
        fps_calc.reset()
        self.assertEqual(fps_calc.get_fps(), 0.0)


if __name__ == "__main__":
    unittest.main()
