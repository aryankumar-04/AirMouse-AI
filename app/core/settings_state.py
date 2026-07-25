"""
AirMouse AI - Settings Manager Module.

Provides JSON persistence, configuration loading/saving, and default restoration.
"""

from dataclasses import asdict
import logging
import os
from typing import Any, Dict, Optional

from config import (
    AppConfig,
    CameraConfig,
    HandTrackingConfig,
    GestureConfig,
    CalibrationConfig,
    MouseConfig,
    UIConfig
)
from app.utils.file_io import safe_load_json, safe_save_json
from app.utils.validation import validate_settings_dict


class SettingsManager:
    """Manages application settings persistence to data/settings.json."""

    def __init__(
        self,
        settings_filepath: str = "data/settings.json",
        logger: Optional[logging.Logger] = None
    ):
        self.filepath = settings_filepath
        self.logger = logger or logging.getLogger("AirMouseAI.Settings")
        self.config: AppConfig = AppConfig()

        self.load_settings()

    def load_settings(self) -> AppConfig:
        """Loads and validates settings from JSON file."""
        default_dict = self._config_to_dict(AppConfig())
        raw_dict = safe_load_json(self.filepath, default_data=default_dict)
        clean_dict = validate_settings_dict(raw_dict)

        self.config = self._dict_to_config(clean_dict)
        self.logger.info("Settings loaded")
        return self.config

    def get_config(self) -> AppConfig:
        """Returns the active application config."""
        return self.config

    def save_settings(self, config: Optional[AppConfig] = None) -> bool:
        """Saves active configuration to JSON file."""
        target_config = config or self.config
        data_dict = self._config_to_dict(target_config)
        clean_dict = validate_settings_dict(data_dict)

        success = safe_save_json(self.filepath, clean_dict)
        if success:
            self.config = target_config
            self.logger.debug("Settings saved successfully")
        return success

    def reset_to_defaults(self) -> AppConfig:
        """Resets configuration to factory defaults and overwrites settings file."""
        self.config = AppConfig()
        self.save_settings(self.config)
        self.logger.debug("Reset settings to default baseline.")
        return self.config

    def _config_to_dict(self, cfg: AppConfig) -> Dict[str, Any]:
        """Converts AppConfig dataclass hierarchy into a dictionary."""
        return asdict(cfg)

    def _dict_to_config(self, d: Dict[str, Any]) -> AppConfig:
        """Converts a validated dictionary into an AppConfig instance."""
        return AppConfig(
            camera=CameraConfig(**d["camera"]),
            tracking=HandTrackingConfig(**d["tracking"]),
            gesture=GestureConfig(**d["gesture"]),
            calibration=CalibrationConfig(**d["calibration"]),
            mouse=MouseConfig(**d["mouse"]),
            ui=UIConfig(**d["ui"]),
            debug_mode=d.get("debug_mode", False),
            log_mode=d.get("log_mode", "RELEASE"),
            log_level=d.get("log_level", "RELEASE"),
            log_filename=d.get("log_filename", "logs/airmouse.log")
        )
