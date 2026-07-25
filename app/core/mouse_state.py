"""
AirMouse AI - Mouse Execution State Machine.

Maintains physical cursor control state, drag tracking, and click timing.
"""

from enum import Enum, auto
import threading
import time
from typing import Tuple


class MouseState(Enum):
    """Enumeration of physical mouse controller states."""
    IDLE = auto()
    MOVE = auto()
    CLICK_CANDIDATE = auto()
    CLICK_FROZEN = auto()
    CLICKED = auto()
    HOLD_CANDIDATE = auto()
    DRAG_ACTIVE = auto()
    DRAGGING = auto()  # Backwards-compatible alias for DRAG_ACTIVE
    SCROLLING = auto()
    PAUSED = auto()
    DISABLED = auto()


class MouseStateMachine:
    """Thread-safe state manager for physical mouse execution."""

    def __init__(self, initial_enabled: bool = False):
        self._enabled = initial_enabled
        self._state = MouseState.DISABLED if not initial_enabled else MouseState.IDLE
        self._lock = threading.Lock()

        self._is_dragging = False
        self._last_click_time = 0.0
        self._last_cursor_pos: Tuple[int, int] = (0, 0)

    def is_enabled(self) -> bool:
        """Returns True if master mouse control is enabled."""
        with self._lock:
            return self._enabled

    def enable(self):
        """Enables master mouse control."""
        with self._lock:
            self._enabled = True
            if self._state == MouseState.DISABLED:
                self._state = MouseState.IDLE

    def disable(self):
        """Disables master mouse control (emergency stop / pause)."""
        with self._lock:
            self._enabled = False
            self._is_dragging = False
            self._state = MouseState.DISABLED

    def get_state(self) -> MouseState:
        """Returns current mouse state."""
        with self._lock:
            return self._state

    def set_state(self, new_state: MouseState):
        """Updates current mouse state if control is enabled."""
        with self._lock:
            if not self._enabled:
                self._state = MouseState.DISABLED
                return
            self._state = new_state
            if new_state in (MouseState.DRAG_ACTIVE, MouseState.DRAGGING):
                self._is_dragging = True
            elif new_state in (MouseState.IDLE, MouseState.MOVE, MouseState.CLICKED, MouseState.DISABLED, MouseState.PAUSED):
                self._is_dragging = False

    def is_dragging(self) -> bool:
        """Returns True if currently holding mouse button in drag state."""
        with self._lock:
            return self._is_dragging

    def register_click(self):
        """Registers a click timestamp."""
        with self._lock:
            self._last_click_time = time.time()

    def get_last_click_time(self) -> float:
        """Returns timestamp of last click event."""
        with self._lock:
            return self._last_click_time

    def get_last_cursor_pos(self) -> Tuple[int, int]:
        """Returns last executed desktop cursor position."""
        with self._lock:
            return self._last_cursor_pos

    def update_cursor_pos(self, x: int, y: int):
        """Updates last recorded cursor position."""
        with self._lock:
            self._last_cursor_pos = (x, y)
