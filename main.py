"""
AirMouse AI - Phase 4 Main Entry Point.

Initializes logging, persistent settings manager, camera worker, hand tracking,
gesture engine, coordinate transformer, physical mouse controller, and launches
the professional tabbed Tkinter desktop GUI.
"""

import sys
import os

from app.core.settings_state import SettingsManager
from app.core.logger import setup_logger
from app.core.app_state import AppStateManager
from app.vision.camera import CameraManager
from app.vision.hand_tracker import HandTracker
from app.vision.gesture_engine import GestureEngine
from app.control.calibration import CoordinateTransformer
from app.control.mouse_controller import MouseController
from app.ui.main_window import MainWindow


import ctypes

def main():
    """Main application setup and execution function."""
    # Set Windows AppUserModelID so taskbar displays custom logo instead of python default icon
    try:
        if sys.platform == 'win32':
            myappid = 'AirMouseAI.DesktopApp.1.0'
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except Exception:
        pass

    # 1. Initialize Persistent Settings Manager & Load data/settings.json
    settings_manager = SettingsManager(settings_filepath="data/settings.json")
    config = settings_manager.get_config()

    # 2. Setup centralized production logger
    log_mode = getattr(config.log, 'log_mode', getattr(config, 'log_mode', 'RELEASE'))
    logger = setup_logger(
        name="AirMouseAI",
        log_mode=log_mode,
        log_level=config.log.log_level if hasattr(config, 'log') else config.log_level,
        log_file=config.log.log_filename if hasattr(config, 'log') else config.log_filename,
        debug_mode=getattr(config.log, 'debug_mode', config.debug_mode),
        max_file_size_mb=getattr(config.log, 'max_file_size_mb', 5),
        backup_count=getattr(config.log, 'backup_count', 5)
    )

    logger.info("Application started")

    try:
        # 3. Initialize App State Container
        state_manager = AppStateManager()

        # 4. Initialize Camera Manager
        camera_manager = CameraManager(
            config=config.camera,
            state_manager=state_manager,
            logger=logger
        )

        # 5. Initialize Hand Tracker
        hand_tracker = HandTracker(
            config=config.tracking,
            logger=logger
        )

        # 6. Initialize Gesture Engine
        gesture_engine = GestureEngine(
            config=config.gesture,
            logger=logger
        )

        # 7. Initialize Coordinate Transformer & Mouse Controller
        transformer = CoordinateTransformer(
            calibration_config=config.calibration,
            mouse_config=config.mouse,
            logger=logger
        )

        mouse_controller = MouseController(
            mouse_config=config.mouse,
            transformer=transformer,
            logger=logger
        )

        # 8. Launch Tkinter User Interface Control Center
        app_window = MainWindow(
            config=config,
            state_manager=state_manager,
            settings_manager=settings_manager,
            camera_manager=camera_manager,
            hand_tracker=hand_tracker,
            gesture_engine=gesture_engine,
            mouse_controller=mouse_controller,
            logger=logger
        )

        # Run application event loop
        app_window.run()

    except Exception as err:
        logger.critical(f"Fatal unhandled exception during main startup: {err}", exc_info=True)
        sys.exit(1)
    finally:
        logger.info("Application closed")


if __name__ == "__main__":
    main()
