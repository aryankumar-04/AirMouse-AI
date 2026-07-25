"""
AirMouse AI - File I/O Helper Module.

Provides safe JSON loading, saving, and directory creation functions.
"""

import json
import logging
import os
from typing import Any, Dict, Optional

logger = logging.getLogger("AirMouseAI.FileIO")


def safe_load_json(file_path: str, default_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Safely loads data from a JSON file, returning default_data if missing or corrupted."""
    if default_data is None:
        default_data = {}

    abs_path = os.path.abspath(file_path)

    if not os.path.exists(abs_path):
        logger.debug("Configuration file missing. Initializing baseline file.")
        safe_save_json(abs_path, default_data)
        return default_data.copy()

    try:
        with open(abs_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else default_data.copy()
    except Exception as err:
        logger.error(f"Error reading configuration file: {err}. Reverting to default baseline settings.")
        return default_data.copy()


def safe_save_json(file_path: str, data: Dict[str, Any]) -> bool:
    """Safely writes a dictionary to a JSON file, creating parent directories if necessary."""
    abs_path = os.path.abspath(file_path)
    parent_dir = os.path.dirname(abs_path)

    try:
        if parent_dir and not os.path.exists(parent_dir):
            os.makedirs(parent_dir, exist_ok=True)

        with open(abs_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        logger.debug("Configuration settings saved cleanly.")
        return True
    except Exception as err:
        logger.error(f"Failed to write configuration settings: {err}")
        return False
