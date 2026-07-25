"""
AirMouse AI - Timing, Debouncing, and Cooldown Utilities Module.

Provides timing helpers to prevent gesture flickering and debounce state changes.
"""

from collections import deque
import time
from typing import Any, Optional


class CooldownTimer:
    """Timer helper ensuring minimum elapsed time between triggered actions."""

    def __init__(self, cooldown_ms: int = 150):
        self.cooldown_seconds = cooldown_ms / 1000.0
        self.last_trigger_time: float = 0.0

    def is_ready(self) -> bool:
        """Returns True if the cooldown period has elapsed."""
        return (time.time() - self.last_trigger_time) >= self.cooldown_seconds

    def trigger(self):
        """Registers a trigger event, resetting the timer."""
        self.last_trigger_time = time.time()

    def reset(self):
        """Clears timer state."""
        self.last_trigger_time = 0.0


class Debouncer:
    """N-frame stability debouncer.

    Requires N consecutive identical input evaluations before emitting a state change.
    """

    def __init__(self, required_frames: int = 3, default_value: Any = None):
        self.required_frames = max(1, required_frames)
        self.history = deque(maxlen=self.required_frames)
        self.current_stable_value: Any = default_value

        if default_value is not None:
            for _ in range(self.required_frames):
                self.history.append(default_value)

    def update(self, candidate_value: Any) -> Tuple[Any, bool]:
        """Evaluates candidate value against recent history.

        Args:
            candidate_value: Newly evaluated gesture or state candidate.

        Returns:
            Tuple[Any, bool]: (Current stable value, Flag indicating if state changed on this update)
        """
        self.history.append(candidate_value)

        # Check if all N frames in history are identical
        if len(self.history) == self.required_frames and len(set(self.history)) == 1:
            stable_candidate = self.history[0]
            if stable_candidate != self.current_stable_value:
                self.current_stable_value = stable_candidate
                return (self.current_stable_value, True)

        return (self.current_stable_value, False)

    def get_stability_count(self) -> int:
        """Returns number of consecutive trailing identical frames matching candidate."""
        if not self.history:
            return 0
        last_val = self.history[-1]
        count = 0
        for val in reversed(self.history):
            if val == last_val:
                count += 1
            else:
                break
        return count

    def reset(self, initial_value: Any = None):
        """Resets debouncer history."""
        self.history.clear()
        self.current_stable_value = initial_value
        if initial_value is not None:
            for _ in range(self.required_frames):
                self.history.append(initial_value)
