"""
AirMouse AI - Anti-Jitter & Smoothing Utilities Module.

Implements Exponential Moving Average (EMA), One Euro Adaptive Filters (Casiez et al. 2012),
and landmark spatial smoothing to eliminate tremor at rest and maintain low latency during motion.
"""

import math
import time
from typing import List, Optional, Tuple, Any
from app.vision.hand_tracker import HandLandmark


class OneEuroFilter:
    """Adaptive Low-Pass Filter for 1D signal smoothing (Casiez et al. 2012).

    Dynamically adjusts cutoff frequency based on input velocity:
    - Low velocity -> low cutoff (heavy filtering, zero jitter at rest)
    - High velocity -> high cutoff (low latency, instant response during fast motion)
    """

    def __init__(
        self,
        min_cutoff: float = 0.6,
        beta: float = 0.015,
        d_cutoff: float = 1.0
    ):
        self.min_cutoff = float(min_cutoff)
        self.beta = float(beta)
        self.d_cutoff = float(d_cutoff)

        self.x_prev: Optional[float] = None
        self.dx_prev: Optional[float] = None
        self.t_prev: Optional[float] = None

    def _smoothing_factor(self, dt: float, cutoff: float) -> float:
        r = 2.0 * math.pi * cutoff * dt
        return r / (r + 1.0)

    def filter(self, x: float, timestamp: Optional[float] = None) -> float:
        if timestamp is None:
            timestamp = time.perf_counter()

        if self.t_prev is None or self.x_prev is None:
            self.t_prev = timestamp
            self.x_prev = x
            self.dx_prev = 0.0
            return x

        dt = timestamp - self.t_prev
        if dt <= 1e-6:
            return self.x_prev

        # Calculate rate of change (velocity)
        dx = (x - self.x_prev) / dt
        edx = self.dx_prev + self._smoothing_factor(dt, self.d_cutoff) * (dx - self.dx_prev)

        # Dynamic cutoff frequency calculation
        cutoff = self.min_cutoff + self.beta * abs(edx)
        alpha = self._smoothing_factor(dt, cutoff)

        x_hat = self.x_prev + alpha * (x - self.x_prev)

        self.x_prev = x_hat
        self.dx_prev = edx
        self.t_prev = timestamp
        return x_hat

    def reset(self):
        """Resets filter state."""
        self.x_prev = None
        self.dx_prev = None
        self.t_prev = None


class OneEuroFilter2D:
    """Adaptive 2D point filter combining two One Euro filters."""

    def __init__(
        self,
        min_cutoff: float = 0.6,
        beta: float = 0.015,
        d_cutoff: float = 1.0
    ):
        self.x_filter = OneEuroFilter(min_cutoff, beta, d_cutoff)
        self.y_filter = OneEuroFilter(min_cutoff, beta, d_cutoff)

    def filter(self, point: Tuple[float, float], timestamp: Optional[float] = None) -> Tuple[float, float]:
        if timestamp is None:
            timestamp = time.perf_counter()
        fx = self.x_filter.filter(point[0], timestamp)
        fy = self.y_filter.filter(point[1], timestamp)
        return (fx, fy)

    def reset(self):
        self.x_filter.reset()
        self.y_filter.reset()


class AdaptiveLandmarkSmoother:
    """Adaptive One Euro Filter applied across all 21 3D hand landmarks."""

    def __init__(
        self,
        min_cutoff: float = 0.8,
        beta: float = 0.02,
        d_cutoff: float = 1.0,
        num_landmarks: int = 21
    ):
        self.num_landmarks = num_landmarks
        self.filters = [
            (
                OneEuroFilter(min_cutoff, beta, d_cutoff),
                OneEuroFilter(min_cutoff, beta, d_cutoff),
                OneEuroFilter(min_cutoff, beta, d_cutoff)
            )
            for _ in range(num_landmarks)
        ]

    def smooth(
        self,
        raw_landmarks: List[HandLandmark],
        width: int,
        height: int,
        timestamp: Optional[float] = None
    ) -> List[HandLandmark]:
        if not raw_landmarks or len(raw_landmarks) != self.num_landmarks:
            return raw_landmarks

        if timestamp is None:
            timestamp = time.perf_counter()

        smoothed_list: List[HandLandmark] = []

        for idx, lm in enumerate(raw_landmarks):
            fx_filter, fy_filter, fz_filter = self.filters[idx]
            sx = fx_filter.filter(lm.x, timestamp)
            sy = fy_filter.filter(lm.y, timestamp)
            sz = fz_filter.filter(lm.z, timestamp)

            spx = int(sx * width)
            spy = int(sy * height)

            smoothed_list.append(HandLandmark(
                id=lm.id,
                x=sx,
                y=sy,
                z=sz,
                px=spx,
                py=spy
            ))

        return smoothed_list

    def reset(self):
        for fx, fy, fz in self.filters:
            fx.reset()
            fy.reset()
            fz.reset()


class ExponentialSmoother:
    """Single-value Exponential Moving Average (EMA) filter."""

    def __init__(self, alpha: float = 0.45):
        self.alpha = max(0.01, min(1.0, alpha))
        self.state: Optional[float] = None

    def update(self, val: float) -> float:
        if self.state is None:
            self.state = val
        else:
            self.state = self.alpha * val + (1.0 - self.alpha) * self.state
        return self.state

    def get_value(self) -> float:
        return self.state if self.state is not None else 0.0

    def reset(self):
        self.state = None


class PointSmoother:
    """Smoother for 2D or 3D coordinate tuples."""

    def __init__(self, alpha: float = 0.45):
        self.x_smoother = ExponentialSmoother(alpha)
        self.y_smoother = ExponentialSmoother(alpha)
        self.z_smoother = ExponentialSmoother(alpha)

    def update_2d(self, point: Tuple[float, float]) -> Tuple[float, float]:
        sx = self.x_smoother.update(point[0])
        sy = self.y_smoother.update(point[1])
        return (sx, sy)

    def update_3d(self, point: Tuple[float, float, float]) -> Tuple[float, float, float]:
        sx = self.x_smoother.update(point[0])
        sy = self.y_smoother.update(point[1])
        sz = self.z_smoother.update(point[2])
        return (sx, sy, sz)

    def reset(self):
        self.x_smoother.reset()
        self.y_smoother.reset()
        self.z_smoother.reset()


class LandmarkSmoother:
    """Smoother for a full set of 21 3D hand landmarks (EMA wrapper for backward compatibility)."""

    def __init__(self, alpha: float = 0.45, num_landmarks: int = 21):
        self.alpha = alpha
        self.num_landmarks = num_landmarks
        self.adaptive_smoother = AdaptiveLandmarkSmoother(min_cutoff=0.8, beta=0.02)
        self.smoothers = [PointSmoother(alpha) for _ in range(num_landmarks)]

    def smooth(self, raw_landmarks: List[HandLandmark], width: int, height: int) -> List[HandLandmark]:
        if not raw_landmarks or len(raw_landmarks) != self.num_landmarks:
            return raw_landmarks

        smoothed_list: List[HandLandmark] = []

        for idx, lm in enumerate(raw_landmarks):
            sx, sy, sz = self.smoothers[idx].update_3d((lm.x, lm.y, lm.z))
            spx = int(sx * width)
            spy = int(sy * height)

            smoothed_list.append(HandLandmark(
                id=lm.id,
                x=sx,
                y=sy,
                z=sz,
                px=spx,
                py=spy
            ))

        return smoothed_list

    def reset(self):
        for smoother in self.smoothers:
            smoother.reset()
        self.adaptive_smoother.reset()

