"""
AirMouse AI - Application State Manager.

Maintains thread-safe execution status across background camera threads and main UI.
"""

from enum import Enum, auto
import threading
from typing import Tuple


class AppState(Enum):
    """Execution states for the application."""
    STOPPED = auto()
    STARTING = auto()
    RUNNING = auto()
    ERROR = auto()


class AppStateManager:
    """Thread-safe state manager for AirMouse AI."""

    def __init__(self, initial_state: AppState = AppState.STOPPED):
        self._state = initial_state
        self._lock = threading.Lock()
        self._error_message = ""

    def get_state(self) -> AppState:
        """Returns current application state."""
        with self._lock:
            return self._state

    def set_state(self, new_state: AppState, error_message: str = ""):
        """Sets application state with optional error detail."""
        with self._lock:
            self._state = new_state
            if error_message:
                self._error_message = error_message
            elif new_state != AppState.ERROR:
                self._error_message = ""

    def get_error_message(self) -> str:
        """Returns the current error message if state is ERROR."""
        with self._lock:
            return self._error_message

    def is_running(self) -> bool:
        """Returns True if state is RUNNING."""
        with self._lock:
            return self._state == AppState.RUNNING

    def is_stopped(self) -> bool:
        """Returns True if state is STOPPED."""
        with self._lock:
            return self._state == AppState.STOPPED

    def is_error(self) -> bool:
        """Returns True if state is ERROR."""
        with self._lock:
            return self._state == AppState.ERROR
