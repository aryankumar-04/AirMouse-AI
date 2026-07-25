"""
AirMouse AI - Application Configuration Module.

Holds structured configuration settings using Python dataclasses.
All parameters can be tuned via this module without hardcoding values in business logic.
"""

from dataclasses import dataclass, field
from typing import Tuple


@dataclass
class CameraConfig:
    """Webcam capture configuration settings."""
    camera_index: int = 0
    frame_width: int = 640
    frame_height: int = 480
    target_fps: int = 60
    auto_reconnect: bool = True
    max_reconnect_attempts: int = 3


@dataclass
class HandTrackingConfig:
    """MediaPipe hand tracking configuration settings."""
    max_num_hands: int = 2
    min_detection_confidence: float = 0.90
    min_tracking_confidence: float = 0.4
    model_complexity: int = 1
    model_path: str = "models/hand_landmarker.task"
    model_url: str = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"


@dataclass
class GestureConfig:
    """Gesture recognition, hysteresis, and anti-jitter configuration settings."""
    pinch_threshold: float = 0.40          # Normalized distance to trigger left PINCH_START
    pinch_release_threshold: float = 0.55  # Hysteresis threshold to exit left PINCH_HOLD
    right_pinch_threshold: float = 0.22    # Normalized distance to trigger right PINCH_START (thumb-middle)
    right_pinch_release_threshold: float = 0.40 # Hysteresis threshold to exit right PINCH_HOLD
    max_click_velocity: float = 0.9        # Suppress new click triggers if hand speed > threshold
    smoothing_alpha: float = 0.45          # EMA alpha factor (fallback / legacy)
    stability_frames: int = 2              # Number of consecutive frames required for state change
    cooldown_ms: int = 120                 # Minimum time (ms) between gesture re-triggers
    finger_extension_ratio: float = 1.0    # Tip-to-wrist / MCP-to-wrist ratio threshold
    palm_open_min_fingers: int = 4         # Minimum extended fingers to classify as OPEN_PALM
    scroll_speed_factor: float = 0.5       # Scales scroll delta by hand motion speed (0.0=fixed, 1.0=fully adaptive)


@dataclass
class CalibrationConfig:
    """Screen coordinate transformer and calibration settings."""
    padding_x: float = 0.20                # 20% horizontal workspace margin
    padding_y: float = 0.20                # 20% vertical workspace margin
    screen_width: int = 1920               # Auto-detected on launch if 0
    screen_height: int = 1080              # Auto-detected on launch if 0
    flip_horizontal: bool = False          # Mirroring handled at camera level


@dataclass
class MouseConfig:
    """Physical OS Mouse Controller configuration settings."""
    enabled: bool = True                   # Master mouse control toggle (default True)
    smoothing_factor: float = 0.21         # Cursor motion EMA factor (0.21)
    smoothing_preset: str = "medium"       # Presets: "low" (0.55), "medium" (0.35), "high" (0.18)
    one_euro_min_cutoff: float = 0.5       # One Euro Filter min cutoff frequency (Hz)
    one_euro_beta: float = 0.012           # One Euro Filter speed coefficient
    one_euro_d_cutoff: float = 1.0         # One Euro Filter derivative cutoff frequency (Hz)
    motion_deadzone_px: float = 6.0        # Motion deadzone (6 px)
    max_cursor_step_px: float = 180.0      # Maximum per-frame cursor displacement cap
    click_freeze_duration_ms: int = 300    # Freeze cursor at target during pinch transition (300 ms)
    click_cooldown_ms: int = 220           # Minimum time (ms) between click triggers
    right_click_cooldown_ms: int = 350     # Dedicated cooldown for right clicks
    right_click_hold_duration_ms: int = 150 # Minimum hold time for right click gesture
    drag_hold_duration_ms: int = 280       # Hold threshold (ms) to engage drag & drop
    motion_cancel_threshold_px: float = 75.0 # Max pixel movement during click decision before cancelling click
    double_click_interval_ms: int = 350    # Maximum interval for double-click detection
    scroll_sensitivity: float = 8.0        # Scroll speed factor
    scroll_min_delta_px: int = 8           # Minimum vertical pixel delta before scroll registers
    speed_acceleration: float = 1.15       # Dynamic acceleration exponent
    failsafe: bool = True                  # PyAutoGUI failsafe



@dataclass
class UIConfig:
    """Tkinter Desktop UI configuration settings."""
    window_title: str = "AirMouse AI - Phase 3 Mouse Controller"
    window_width: int = 1080
    window_height: int = 680
    preview_width: int = 640
    preview_height: int = 480
    dark_mode: bool = True
    update_interval_ms: int = 16  # ~60 FPS UI polling loop


@dataclass
class LogConfig:
    """Production & Development logging configuration settings."""
    log_mode: str = "RELEASE"              # Modes: RELEASE (default production - clean console), INFO, DEBUG
    debug_mode: bool = False               # False = Production Mode (RELEASE), True = Development Mode (DEBUG)
    log_level: str = "RELEASE"             # RELEASE, INFO, DEBUG, WARNING, ERROR, CRITICAL
    log_to_file: bool = True               # Enable writing logs to file
    log_to_console: bool = True            # Enable console log output
    log_filename: str = "logs/airmouse.log"# Log file path
    max_file_size_mb: int = 5              # Max size in MB before rotating
    backup_count: int = 5                  # Number of rotated log backup files to keep


@dataclass
class AppConfig:
    """Master application configuration container."""
    camera: CameraConfig = field(default_factory=CameraConfig)
    tracking: HandTrackingConfig = field(default_factory=HandTrackingConfig)
    gesture: GestureConfig = field(default_factory=GestureConfig)
    calibration: CalibrationConfig = field(default_factory=CalibrationConfig)
    mouse: MouseConfig = field(default_factory=MouseConfig)
    ui: UIConfig = field(default_factory=UIConfig)
    log: LogConfig = field(default_factory=LogConfig)
    debug_mode: bool = False
    log_mode: str = "RELEASE"
    log_level: str = "RELEASE"
    log_filename: str = "logs/airmouse.log"


# Global default configuration instance
default_config = AppConfig()

