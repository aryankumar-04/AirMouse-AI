"""Unit tests for CameraManager module."""

import unittest
from config import CameraConfig
from app.core.app_state import AppStateManager, AppState
from app.vision.camera import CameraManager


class TestCameraManager(unittest.TestCase):

    def test_invalid_camera_index_fails_gracefully(self):
        # Index 9999 is invalid on standard hardware
        invalid_config = CameraConfig(camera_index=9999, max_reconnect_attempts=1)
        state_mgr = AppStateManager()
        cam = CameraManager(config=invalid_config, state_manager=state_mgr)

        started = cam.start()
        self.assertFalse(started)
        self.assertFalse(cam.is_running())
        self.assertEqual(state_mgr.get_state(), AppState.ERROR)
        self.assertIn("Camera could not be opened", state_mgr.get_error_message())
        cam.stop()


if __name__ == "__main__":
    unittest.main()
