"""Unit tests for GUILogHandler and thread-safe log queue emission."""

import logging
import queue
import unittest
from app.core.logger import GUILogHandler, setup_logger


class TestLogging(unittest.TestCase):

    def test_gui_log_handler_pushes_to_queue(self):
        test_queue = queue.Queue()
        handler = GUILogHandler(test_queue)
        handler.setFormatter(logging.Formatter("%(message)s"))

        logger = logging.getLogger("TestLogger")
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

        logger.info("Test log message")

        self.assertFalse(test_queue.empty())
        level, msg = test_queue.get_nowait()
        self.assertEqual(level, "INFO")
        self.assertIn("Test log message", msg)

    def test_setup_logger_returns_logger(self):
        logger = setup_logger(name="AirMouseAI_Test", log_level="DEBUG", log_file=None, debug_mode=True)
        self.assertIsNotNone(logger)
        self.assertTrue(logger.hasHandlers())

    def test_sanitize_message(self):
        from app.core.logger import sanitize_message
        dirty_msg = "Loaded settings from C:\\Users\\HP\\AppData\\Local\\Temp\\settings.json"
        clean = sanitize_message(dirty_msg)
        self.assertNotIn("C:\\Users\\HP\\", clean)
        self.assertIn("~/AppData", clean)


if __name__ == "__main__":
    unittest.main()
