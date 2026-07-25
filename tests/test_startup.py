"""Headless smoke test validating full application module initialization."""

import unittest
from config import default_config
from app.core.logger import setup_logger
from app.core.app_state import AppStateManager
from app.core.settings_state import SettingsManager
from app.vision.camera import CameraManager
from app.vision.hand_tracker import HandTracker
from app.vision.gesture_engine import GestureEngine
from app.control.calibration import CoordinateTransformer
from app.control.mouse_controller import MouseController


class TestStartupSmoke(unittest.TestCase):

    def test_full_application_stack_initialization(self):
        # 1. Logger
        logger = setup_logger(name="AirMouseAI_SmokeTest", log_level="INFO", log_file=None)
        self.assertIsNotNone(logger)

        # 2. Settings Manager
        settings_mgr = SettingsManager(settings_filepath="data/settings.json", logger=logger)
        config = settings_mgr.get_config()
        self.assertIsNotNone(config)

        # 3. State Manager
        state_mgr = AppStateManager()
        self.assertTrue(state_mgr.is_stopped())

        # 4. Camera Manager
        cam_mgr = CameraManager(config=config.camera, state_manager=state_mgr, logger=logger)
        self.assertIsNotNone(cam_mgr)

        # 5. Hand Tracker
        hand_tracker = HandTracker(config=config.tracking, logger=logger)
        self.assertIsNotNone(hand_tracker)

        # 6. Gesture Engine
        gesture_engine = GestureEngine(config=config.gesture, logger=logger)
        self.assertIsNotNone(gesture_engine)

        # 7. Coordinate Transformer & Mouse Controller
        transformer = CoordinateTransformer(calibration_config=config.calibration, mouse_config=config.mouse, logger=logger)
        mouse_controller = MouseController(mouse_config=config.mouse, transformer=transformer, logger=logger)

        self.assertIsNotNone(mouse_controller)

        # Cleanup
        hand_tracker.close()


if __name__ == "__main__":
    unittest.main()
