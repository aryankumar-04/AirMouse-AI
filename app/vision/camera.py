"""
AirMouse AI - Camera Manager Module.

Provides threaded OpenCV webcam capture to avoid freezing the UI thread.
"""

import logging
import threading
import time
from typing import Optional, Tuple
import cv2
import numpy as np

from config import CameraConfig
from app.core.app_state import AppState, AppStateManager


class CameraManager:
    """Manages OpenCV webcam initialization, threaded frame capture, and safe release."""

    def __init__(
        self,
        config: CameraConfig,
        state_manager: Optional[AppStateManager] = None,
        logger: Optional[logging.Logger] = None
    ):
        self.config = config
        self.state_manager = state_manager
        self.logger = logger or logging.getLogger("AirMouseAI.Camera")

        self._cap: Optional[cv2.VideoCapture] = None
        self._thread: Optional[threading.Thread] = None
        self._running = False
        self._lock = threading.Lock()

        self._latest_frame: Optional[np.ndarray] = None
        self._frame_count = 0
        self._error_msg = ""

    def start(self) -> bool:
        """Opens the webcam and launches the background capture thread.

        Returns:
            bool: True if camera started successfully, False otherwise.
        """
        if self._running:
            self.logger.warning("Camera is already running.")
            return True

        self.logger.debug(f"Opening camera index {self.config.camera_index}...")
        
        # On Windows, cv2.CAP_DSHOW provides fast startup and reliable direct show bindings
        cap = cv2.VideoCapture(self.config.camera_index, cv2.CAP_DSHOW)
        
        if not cap.isOpened():
            # Fallback to default backend
            self.logger.debug("CAP_DSHOW failed, falling back to default OpenCV backend...")
            cap = cv2.VideoCapture(self.config.camera_index)

        if not cap.isOpened():
            self._error_msg = "Camera could not be opened."
            self.logger.error(self._error_msg)
            if self.state_manager:
                self.state_manager.set_state(AppState.ERROR, self._error_msg)
            return False

        # Configure camera capture properties
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.config.frame_width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config.frame_height)
        cap.set(cv2.CAP_PROP_FPS, self.config.target_fps)

        self._cap = cap
        self._running = True

        if self.state_manager:
            self.state_manager.set_state(AppState.RUNNING)

        # Launch worker thread
        self._thread = threading.Thread(
            target=self._capture_loop,
            name="AirMouse_CameraThread",
            daemon=True
        )
        self._thread.start()
        self.logger.debug("Camera capture thread started successfully.")
        return True

    def _capture_loop(self):
        """Worker loop running in a background thread to read frames continuously."""
        consecutive_failures = 0

        while self._running and self._cap and self._cap.isOpened():
            ret, frame = self._cap.read()

            if not ret or frame is None:
                consecutive_failures += 1
                self.logger.debug(
                    f"Frame read failure ({consecutive_failures}/{self.config.max_reconnect_attempts})"
                )
                if consecutive_failures >= self.config.max_reconnect_attempts:
                    self._error_msg = "Camera disconnected unexpectedly."
                    self.logger.error(self._error_msg)
                    if self.state_manager:
                        self.state_manager.set_state(AppState.ERROR, self._error_msg)
                    self._running = False
                    break
                time.sleep(0.05)
                continue

            consecutive_failures = 0

            # Mirror frame horizontally for natural selfie view so text overlays render left-to-right
            mirrored_frame = cv2.flip(frame, 1)
            with self._lock:
                self._latest_frame = mirrored_frame
                self._frame_count += 1

            # Cap loop iteration rate lightly to avoid high CPU spin while maintaining lowest latency
            time.sleep(0.001)

    def read_frame(self) -> Tuple[bool, Optional[np.ndarray]]:
        """Retrieves the latest available frame from the camera buffer.

        Returns:
            Tuple[bool, Optional[np.ndarray]]: (Success flag, BGR frame array)
        """
        with self._lock:
            if self._latest_frame is None:
                return False, None
            # Return a copy to prevent race conditions during array operations
            return True, self._latest_frame.copy()

    def is_running(self) -> bool:
        """Returns True if the camera loop is actively running."""
        return self._running

    def get_frame_count(self) -> int:
        """Returns total frames read since start."""
        with self._lock:
            return self._frame_count

    def get_error_message(self) -> str:
        """Returns error message if camera failed."""
        return self._error_msg

    def stop(self):
        """Stops the capture thread and safely releases camera hardware resources."""
        if not self._running and self._cap is None:
            return

        self.logger.debug("Stopping camera manager...")
        self._running = False

        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
            self._thread = None

        if self._cap:
            try:
                self._cap.release()
            except Exception as e:
                self.logger.warning(f"Error releasing VideoCapture: {e}")
            self._cap = None

        with self._lock:
            self._latest_frame = None

        if self.state_manager and not self.state_manager.is_error():
            self.state_manager.set_state(AppState.STOPPED)

        self.logger.debug("Camera manager stopped cleanly.")
