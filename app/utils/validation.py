"""
AirMouse AI - Settings Validation Module.

Validates parameter types, bounds, and fallback defaults for loaded configuration settings.
"""

from typing import Any, Dict


def validate_settings_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """Sanitizes and clamps raw settings dictionary to valid ranges."""
    clean = {}

    # Camera section
    cam = data.get("camera", {})
    clean["camera"] = {
        "camera_index": max(0, int(cam.get("camera_index", 0))),
        "frame_width": max(320, int(cam.get("frame_width", 640))),
        "frame_height": max(240, int(cam.get("frame_height", 480))),
        "target_fps": max(10, min(120, int(cam.get("target_fps", 30)))),
        "auto_reconnect": bool(cam.get("auto_reconnect", True)),
        "max_reconnect_attempts": max(1, int(cam.get("max_reconnect_attempts", 3)))
    }

    # Tracking section
    tr = data.get("tracking", {})
    clean["tracking"] = {
        "max_num_hands": max(1, min(4, int(tr.get("max_num_hands", 2)))),
        "min_detection_confidence": max(0.1, min(1.0, float(tr.get("min_detection_confidence", 0.7)))),
        "min_tracking_confidence": max(0.1, min(1.0, float(tr.get("min_tracking_confidence", 0.5)))),
        "model_complexity": max(0, min(1, int(tr.get("model_complexity", 1)))),
        "model_path": str(tr.get("model_path", "models/hand_landmarker.task")),
        "model_url": str(tr.get("model_url", "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"))
    }

    # Gesture section
    gest = data.get("gesture", {})
    clean["gesture"] = {
        "pinch_threshold": max(0.05, min(0.6, float(gest.get("pinch_threshold", 0.25)))),
        "pinch_release_threshold": max(0.1, min(0.8, float(gest.get("pinch_release_threshold", 0.38)))),
        "right_pinch_threshold": max(0.05, min(0.6, float(gest.get("right_pinch_threshold", 0.25)))),
        "right_pinch_release_threshold": max(0.1, min(0.8, float(gest.get("right_pinch_release_threshold", 0.38)))),
        "max_click_velocity": max(0.2, min(5.0, float(gest.get("max_click_velocity", 1.2)))),
        "smoothing_alpha": max(0.05, min(1.0, float(gest.get("smoothing_alpha", 0.45)))),
        "stability_frames": max(1, min(15, int(gest.get("stability_frames", 2)))),
        "cooldown_ms": max(50, min(2000, int(gest.get("cooldown_ms", 150)))),
        "finger_extension_ratio": max(0.8, min(2.0, float(gest.get("finger_extension_ratio", 1.0))))
    }

    # Calibration section
    cal = data.get("calibration", {})
    clean["calibration"] = {
        "padding_x": max(0.0, min(0.35, float(cal.get("padding_x", 0.15)))),
        "padding_y": max(0.0, min(0.35, float(cal.get("padding_y", 0.15)))),
        "screen_width": max(0, int(cal.get("screen_width", 1920))),
        "screen_height": max(0, int(cal.get("screen_height", 1080))),
        "flip_horizontal": bool(cal.get("flip_horizontal", False))
    }

    # Mouse section
    m = data.get("mouse", {})
    clean["mouse"] = {
        "enabled": bool(m.get("enabled", False)),  # Safety default OFF
        "smoothing_factor": max(0.05, min(0.95, float(m.get("smoothing_factor", 0.35)))),
        "smoothing_preset": str(m.get("smoothing_preset", "medium")),
        "one_euro_min_cutoff": max(0.01, min(10.0, float(m.get("one_euro_min_cutoff", 0.6)))),
        "one_euro_beta": max(0.0001, min(1.0, float(m.get("one_euro_beta", 0.015)))),
        "one_euro_d_cutoff": max(0.1, min(10.0, float(m.get("one_euro_d_cutoff", 1.0)))),
        "motion_deadzone_px": max(0.0, min(20.0, float(m.get("motion_deadzone_px", 3.0)))),
        "max_cursor_step_px": max(10.0, min(500.0, float(m.get("max_cursor_step_px", 150.0)))),
        "click_freeze_duration_ms": max(0, min(1000, int(m.get("click_freeze_duration_ms", 150)))),
        "click_cooldown_ms": max(50, min(1000, int(m.get("click_cooldown_ms", 250)))),
        "right_click_cooldown_ms": max(50, min(1000, int(m.get("right_click_cooldown_ms", 400)))),
        "right_click_hold_duration_ms": max(50, min(1000, int(m.get("right_click_hold_duration_ms", 200)))),
        "drag_hold_duration_ms": max(50, min(1000, int(m.get("drag_hold_duration_ms", 250)))),
        "double_click_interval_ms": max(100, min(1000, int(m.get("double_click_interval_ms", 350)))),
        "scroll_sensitivity": max(1.0, min(50.0, float(m.get("scroll_sensitivity", 15.0)))),
        "speed_acceleration": max(1.0, min(3.0, float(m.get("speed_acceleration", 1.2)))),
        "failsafe": bool(m.get("failsafe", True))
    }

    # UI section
    ui = data.get("ui", {})
    clean["ui"] = {
        "window_title": str(ui.get("window_title", "AirMouse AI Control Center")),
        "window_width": max(800, int(ui.get("window_width", 1080))),
        "window_height": max(550, int(ui.get("window_height", 680))),
        "preview_width": max(320, int(ui.get("preview_width", 640))),
        "preview_height": max(240, int(ui.get("preview_height", 480))),
        "dark_mode": bool(ui.get("dark_mode", True)),
        "update_interval_ms": max(10, min(100, int(ui.get("update_interval_ms", 16))))
    }

    # App section
    clean["debug_mode"] = bool(data.get("debug_mode", True))
    clean["log_level"] = str(data.get("log_level", "INFO"))
    clean["log_filename"] = str(data.get("log_filename", "airmouse_ai.log"))

    return clean
