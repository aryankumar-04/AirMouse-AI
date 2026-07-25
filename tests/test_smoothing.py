"""Unit tests for anti-jitter smoothing filters."""

import unittest
from app.utils.smoothing import ExponentialSmoother, PointSmoother, LandmarkSmoother, OneEuroFilter, OneEuroFilter2D
from app.vision.hand_tracker import HandLandmark


class TestSmoothing(unittest.TestCase):

    def test_exponential_smoother_initial_value(self):
        smoother = ExponentialSmoother(alpha=0.5)
        res = smoother.update(10.0)
        self.assertEqual(res, 10.0)

    def test_exponential_smoother_filters_step_change(self):
        smoother = ExponentialSmoother(alpha=0.5)
        smoother.update(0.0)
        res2 = smoother.update(10.0)
        # Expected: 0.5 * 10 + 0.5 * 0 = 5.0
        self.assertAlmostEqual(res2, 5.0)

    def test_point_smoother_2d(self):
        smoother = PointSmoother(alpha=0.5)
        smoother.update_2d((0.0, 0.0))
        pt2 = smoother.update_2d((10.0, 20.0))
        self.assertEqual(pt2, (5.0, 10.0))

    def test_landmark_smoother(self):
        smoother = LandmarkSmoother(alpha=0.5, num_landmarks=21)
        raw_lms = [HandLandmark(id=i, x=0.0, y=0.0, z=0.0, px=0, py=0) for i in range(21)]
        
        # Frame 1
        smoother.smooth(raw_lms, width=640, height=480)
        
        # Frame 2 with step change to (1.0, 1.0)
        step_lms = [HandLandmark(id=i, x=1.0, y=1.0, z=1.0, px=640, py=480) for i in range(21)]
        smoothed_step = smoother.smooth(step_lms, width=640, height=480)

        # Expect x, y, z to be 0.5 and px, py to be 320, 240
        self.assertAlmostEqual(smoothed_step[0].x, 0.5)
        self.assertEqual(smoothed_step[0].px, 320)
        self.assertEqual(smoothed_step[0].py, 240)


    def test_one_euro_filter_rest_stability_and_motion(self):
        filter_1d = OneEuroFilter(min_cutoff=0.5, beta=0.01)
        # Seed initial value
        t0 = 1.0
        filter_1d.filter(100.0, timestamp=t0)

        # Micro jitter around 100.0 (rest condition)
        v1 = filter_1d.filter(100.2, timestamp=t0 + 0.033)
        self.assertAlmostEqual(v1, 100.0, delta=0.15)

        # Large fast movement (step change)
        t_fast = t0 + 0.066
        v2 = filter_1d.filter(150.0, timestamp=t_fast)
        # Should adapt cutoff frequency and follow fast motion rapidly
        self.assertGreater(v2, 110.0)

    def test_one_euro_filter_2d(self):
        filter_2d = OneEuroFilter2D(min_cutoff=0.5, beta=0.01)
        pt1 = filter_2d.filter((10.0, 20.0), timestamp=1.0)
        self.assertEqual(pt1, (10.0, 20.0))

        pt2 = filter_2d.filter((10.1, 20.1), timestamp=1.033)
        self.assertAlmostEqual(pt2[0], 10.0, delta=0.1)
        self.assertAlmostEqual(pt2[1], 20.0, delta=0.1)


if __name__ == "__main__":
    unittest.main()
