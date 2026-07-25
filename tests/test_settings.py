"""Unit tests for SettingsManager, JSON persistence, and schema validation."""

import os
import tempfile
import unittest
from config import AppConfig
from app.core.settings_state import SettingsManager
from app.utils.validation import validate_settings_dict


class TestSettings(unittest.TestCase):

    def setUp(self):
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
        self.temp_file.close()

    def tearDown(self):
        if os.path.exists(self.temp_file.name):
            os.remove(self.temp_file.name)

    def test_save_and_load_settings(self):
        mgr = SettingsManager(settings_filepath=self.temp_file.name)
        cfg = AppConfig()
        cfg.mouse.smoothing_factor = 0.55
        cfg.camera.camera_index = 2

        # Save settings
        saved = mgr.save_settings(cfg)
        self.assertTrue(saved)

        # Load settings in new manager
        mgr2 = SettingsManager(settings_filepath=self.temp_file.name)
        cfg2 = mgr2.get_config()

        self.assertAlmostEqual(cfg2.mouse.smoothing_factor, 0.55)
        self.assertEqual(cfg2.camera.camera_index, 2)

    def test_validate_settings_dict_clamping(self):
        invalid_data = {
            "camera": {"camera_index": -5, "target_fps": 999},
            "mouse": {"smoothing_factor": 1.5}
        }
        clean = validate_settings_dict(invalid_data)

        self.assertEqual(clean["camera"]["camera_index"], 0)
        self.assertEqual(clean["camera"]["target_fps"], 120)
        self.assertAlmostEqual(clean["mouse"]["smoothing_factor"], 0.95)

    def test_reset_to_defaults(self):
        mgr = SettingsManager(settings_filepath=self.temp_file.name)
        mgr.config.mouse.smoothing_factor = 0.9
        mgr.reset_to_defaults()

        self.assertAlmostEqual(mgr.config.mouse.smoothing_factor, 0.21)


if __name__ == "__main__":
    unittest.main()
