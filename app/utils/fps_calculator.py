"""
AirMouse AI - FPS Calculator Utility.

Calculates smooth moving-average frames per second.
"""

from collections import deque
import time


class FPSCalculator:
    """Calculates frame rates over a rolling window of frames."""

    def __init__(self, buffer_size: int = 30):
        self.buffer_size = max(2, buffer_size)
        self.timestamps = deque(maxlen=self.buffer_size)

    def tick(self) -> float:
        """Records a new frame timestamp and returns current calculated FPS."""
        now = time.time()
        self.timestamps.append(now)
        return self.get_fps()

    def get_fps(self) -> float:
        """Calculates current FPS without registering a tick."""
        if len(self.timestamps) < 2:
            return 0.0
        elapsed = self.timestamps[-1] - self.timestamps[0]
        if elapsed <= 0:
            return 0.0
        return (len(self.timestamps) - 1) / elapsed

    def reset(self):
        """Clears timestamp history."""
        self.timestamps.clear()
