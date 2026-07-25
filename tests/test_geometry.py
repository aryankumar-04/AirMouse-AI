"""Unit tests for geometry calculations and finger extension rules."""

import unittest
from app.vision.hand_tracker import HandLandmark
from app.utils.geometry import (
    euclidean_distance_2d,
    euclidean_distance_3d,
    calculate_hand_size,
    calculate_normalized_distance,
    is_finger_extended,
    get_finger_extension_states
)


class TestGeometry(unittest.TestCase):

    def test_euclidean_distance_2d(self):
        p1 = (0.0, 0.0)
        p2 = (3.0, 4.0)
        self.assertAlmostEqual(euclidean_distance_2d(p1, p2), 5.0)

    def test_euclidean_distance_3d(self):
        p1 = (0.0, 0.0, 0.0)
        p2 = (1.0, 2.0, 2.0)
        self.assertAlmostEqual(euclidean_distance_3d(p1, p2), 3.0)

    def test_calculate_hand_size(self):
        # Create dummy 21 landmarks
        landmarks = [HandLandmark(id=i, x=0.5, y=0.5, z=0.0, px=320, py=240) for i in range(21)]
        # Set Wrist (0) and Middle MCP (9)
        landmarks[0] = HandLandmark(id=0, x=0.5, y=0.8, z=0.0, px=320, py=400)
        landmarks[9] = HandLandmark(id=9, x=0.5, y=0.5, z=0.0, px=320, py=250)

        hand_size = calculate_hand_size(landmarks)
        self.assertAlmostEqual(hand_size, 0.3)

    def test_calculate_normalized_distance(self):
        p1 = (100.0, 100.0)
        p2 = (100.0, 150.0)
        hand_size = 100.0

        norm_dist = calculate_normalized_distance(p1, p2, hand_size)
        self.assertAlmostEqual(norm_dist, 0.5)

    def test_is_finger_extended_true(self):
        landmarks = [HandLandmark(id=i, x=0.5, y=0.5, z=0.0, px=320, py=240) for i in range(21)]
        # Wrist at (0.5, 0.9)
        landmarks[0] = HandLandmark(id=0, x=0.5, y=0.9, z=0.0, px=320, py=450)
        # Index MCP (5) at (0.5, 0.7)
        landmarks[5] = HandLandmark(id=5, x=0.5, y=0.7, z=0.0, px=320, py=350)
        # Index PIP (6) at (0.5, 0.5)
        landmarks[6] = HandLandmark(id=6, x=0.5, y=0.5, z=0.0, px=320, py=250)
        # Index TIP (8) extended high at (0.5, 0.1)
        landmarks[8] = HandLandmark(id=8, x=0.5, y=0.1, z=0.0, px=320, py=50)

        self.assertTrue(is_finger_extended(landmarks, tip_id=8, pip_id=6, mcp_id=5, wrist_id=0))


if __name__ == "__main__":
    unittest.main()
