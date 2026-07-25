"""
AirMouse AI - Coordinate Transformer & Calibration Module.

Maps normalized camera hand coordinates to desktop screen resolution with
workspace edge padding, max step clamping, One Euro adaptive smoothing,
velocity-based pointer acceleration, and clutch re-engage safety.
"""

from enum import Enum, auto
import logging
import math
import time
from typing import Optional, Tuple
import pyautogui

from config import CalibrationConfig, MouseConfig
from app.utils.smoothing import PointSmoother, OneEuroFilter2D
from app.utils.geometry import math_clamp


class TrackingState(Enum):
    """Tracking continuity state for clutch mechanism."""
    ACTIVE = auto()
    LOST = auto()
    RE_ENGAGING = auto()


class CoordinateTransformer:
    """Transforms 2D normalized camera coordinates to screen pixel space with velocity acceleration & clutch safety."""

    PRESETS = {
        "low": (1.2, 0.03),     # Responsive / lower latency (min_cutoff, beta)
        "medium": (0.6, 0.015), # Balanced smoothing (default)
        "high": (0.3, 0.005)    # Ultra-smooth / zero micro-jitter
    }

    def __init__(
        self,
        calibration_config: CalibrationConfig,
        mouse_config: MouseConfig,
        logger: Optional[logging.Logger] = None
    ):
        self.cal_config = calibration_config
        self.mouse_config = mouse_config
        self.logger = logger or logging.getLogger("AirMouseAI.Calibration")

        # Auto-detect screen resolution if not specified
        self.screen_width = self.cal_config.screen_width
        self.screen_height = self.cal_config.screen_height

        self._auto_detect_screen_size()

        # One Euro Adaptive 2D Filter for cursor motion
        min_cutoff = getattr(self.mouse_config, 'one_euro_min_cutoff', 0.6)
        beta = getattr(self.mouse_config, 'one_euro_beta', 0.015)
        d_cutoff = getattr(self.mouse_config, 'one_euro_d_cutoff', 1.0)
        self.one_euro_filter = OneEuroFilter2D(min_cutoff=min_cutoff, beta=beta, d_cutoff=d_cutoff)
        self.legacy_smoother = PointSmoother(alpha=self.mouse_config.smoothing_factor)

        self._last_screen_pos: Optional[Tuple[int, int]] = None
        self._last_timestamp: Optional[float] = None
        self.tracking_state: TrackingState = TrackingState.LOST
        self._reengage_counter: int = 0

    def _auto_detect_screen_size(self):
        """Auto-detects primary display resolution using PyAutoGUI."""
        try:
            sw, sh = pyautogui.size()
            if sw > 0 and sh > 0:
                self.screen_width = sw
                self.screen_height = sh
                self.cal_config.screen_width = sw
                self.cal_config.screen_height = sh
                self.logger.debug(f"Auto-detected display resolution: {sw}x{sh}")
        except Exception as err:
            self.logger.warning(f"Could not auto-detect screen size: {err}")
            if self.screen_width == 0 or self.screen_height == 0:
                self.screen_width = 1920
                self.screen_height = 1080

    def update_screen_resolution(self, forced_width: int = 0, forced_height: int = 0):
        """Updates or auto-detects active target screen resolution."""
        if forced_width > 0 and forced_height > 0:
            self.screen_width = forced_width
            self.screen_height = forced_height
            self.cal_config.screen_width = forced_width
            self.cal_config.screen_height = forced_height
            self.logger.info(f"Target display resolution set to: {forced_width}x{forced_height}")
        else:
            self._auto_detect_screen_size()

    def auto_detect_resolution(self, forced_width: int = 0, forced_height: int = 0):
        """Alias for update_screen_resolution."""
        self.update_screen_resolution(forced_width, forced_height)

    def set_smoothing_preset(self, preset_name: str):
        """Sets smoothing preset ('low', 'medium', 'high')."""
        preset_clean = preset_name.lower()
        if preset_clean in self.PRESETS:
            min_cutoff, beta = self.PRESETS[preset_clean]
            self.mouse_config.smoothing_preset = preset_clean
            self.mouse_config.one_euro_min_cutoff = min_cutoff
            self.mouse_config.one_euro_beta = beta
            self.one_euro_filter = OneEuroFilter2D(
                min_cutoff=min_cutoff,
                beta=beta,
                d_cutoff=getattr(self.mouse_config, 'one_euro_d_cutoff', 1.0)
            )
            self.logger.info(f"Set cursor smoothing preset to '{preset_clean}' (min_cutoff={min_cutoff}, beta={beta})")

    def transform(
        self,
        normalized_pos: Tuple[float, float],
        frame_dimensions: Optional[Tuple[int, int]] = None
    ) -> Tuple[int, int]:
        """Transforms camera coordinate (norm_x, norm_y) to screen pixel coordinate (screen_x, screen_y)."""
        now = time.perf_counter()
        cx, cy = normalized_pos

        # 1. Apply horizontal mirroring if enabled
        if self.cal_config.flip_horizontal:
            cx = 1.0 - cx

        # 2. Apply Workspace Padding Margins
        pad_x = self.cal_config.padding_x
        pad_y = self.cal_config.padding_y

        mapped_x = (cx - pad_x) / max(0.01, (1.0 - 2 * pad_x))
        mapped_y = (cy - pad_y) / max(0.01, (1.0 - 2 * pad_y))

        clamped_x = max(0.0, min(1.0, mapped_x))
        clamped_y = max(0.0, min(1.0, mapped_y))

        # 3. Target Screen Pixel Coordinates
        target_sx = clamped_x * (self.screen_width - 1)
        target_sy = clamped_y * (self.screen_height - 1)

        # 4. Handle Clutch / Tracking Continuity State Transitions
        if self.tracking_state == TrackingState.LOST:
            self.tracking_state = TrackingState.RE_ENGAGING
            self._reengage_counter = 2
            self.one_euro_filter.reset()
            self.legacy_smoother.reset()

        if self.tracking_state == TrackingState.RE_ENGAGING:
            self._reengage_counter -= 1
            if self._reengage_counter <= 0:
                self.tracking_state = TrackingState.ACTIVE

            # Re-seed filter and hold cursor still during re-engagement
            filtered_sx, filtered_sy = self.one_euro_filter.filter((target_sx, target_sy), now)
            final_x = int(math_clamp(int(filtered_sx), 0, self.screen_width - 1))
            final_y = int(math_clamp(int(filtered_sy), 0, self.screen_height - 1))

            self._last_screen_pos = (final_x, final_y)
            self._last_timestamp = now
            return (final_x, final_y)

        # 5. One Euro Filter Adaptive Smoothing
        smoothed_sx, smoothed_sy = self.one_euro_filter.filter((target_sx, target_sy), now)

        final_sx = int(math_clamp(int(smoothed_sx), 0, self.screen_width - 1))
        final_sy = int(math_clamp(int(smoothed_sy), 0, self.screen_height - 1))

        if self._last_screen_pos is not None:
            last_x, last_y = self._last_screen_pos
            dx = final_sx - last_x
            dy = final_sy - last_y
            dist = math.hypot(dx, dy)

            # 6. Apply Movement Deadzone (ignore tiny sub-pixel tremor)
            deadzone = self.mouse_config.motion_deadzone_px
            if dist < deadzone:
                return self._last_screen_pos

            # 7. Apply Velocity-Based Pointer Acceleration Curve
            #    Softer gain scaling for natural feel: gain = 1.0 + k * (v/v_ref)^1.1, capped at 2.0x
            accel_exponent = getattr(self.mouse_config, 'speed_acceleration', 1.15)
            if accel_exponent > 1.0 and dist > deadzone:
                dt = (now - self._last_timestamp) if (self._last_timestamp and (now - self._last_timestamp) > 1e-4) else 0.033
                velocity_px_per_sec = dist / dt
                ref_velocity = 600.0  # Lower reference for earlier but softer acceleration

                gain = 1.0 + (accel_exponent - 1.0) * min(2.0, (velocity_px_per_sec / ref_velocity) ** 1.1)
                accelerated_dx = dx * gain
                accelerated_dy = dy * gain

                final_sx = int(math_clamp(int(last_x + accelerated_dx), 0, self.screen_width - 1))
                final_sy = int(math_clamp(int(last_y + accelerated_dy), 0, self.screen_height - 1))
                dist = math.hypot(final_sx - last_x, final_sy - last_y)

            # 8. Apply Max Step Displacement Cap to prevent erratic jumps
            max_step = self.mouse_config.max_cursor_step_px
            if max_step > 0 and dist > max_step:
                scale = max_step / max(1.0, dist)
                final_sx = int(math_clamp(int(last_x + (final_sx - last_x) * scale), 0, self.screen_width - 1))
                final_sy = int(math_clamp(int(last_y + (final_sy - last_y) * scale), 0, self.screen_height - 1))

        self._last_screen_pos = (final_sx, final_sy)
        self._last_timestamp = now
        return (final_sx, final_sy)

    def update_smoothing_factor(self, alpha: float):
        """Updates smoothing alpha factor on the fly."""
        self.mouse_config.smoothing_factor = max(0.01, min(1.0, alpha))
        self.legacy_smoother = PointSmoother(alpha=self.mouse_config.smoothing_factor)

    def update_padding(self, padding_x: float, padding_y: float):
        """Updates workspace padding margins on the fly."""
        self.cal_config.padding_x = max(0.0, min(0.35, padding_x))
        self.cal_config.padding_y = max(0.0, min(0.35, padding_y))

    def reset(self):
        """Resets smoother state and triggers clutch tracking loss."""
        self.one_euro_filter.reset()
        self.legacy_smoother.reset()
        self._last_screen_pos = None
        self._last_timestamp = None
        self.tracking_state = TrackingState.LOST

