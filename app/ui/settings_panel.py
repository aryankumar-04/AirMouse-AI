"""
AirMouse AI - Settings & Preferences View.

Provides interactive controls for tuning camera, gesture tracking, cursor smoothing,
display resolution, workspace margins, and persisting settings to JSON matching reference UI image 1.
"""

import re
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, Optional
import pyautogui

from config import AppConfig
from app.core.settings_state import SettingsManager
from app.control.mouse_controller import MouseController
from app.ui.custom_widgets import ModernSlider, ModernToggle


class SettingsPanel(ttk.Frame):
    """Settings view styled matching reference design."""

    def __init__(
        self,
        parent,
        config: AppConfig,
        settings_manager: SettingsManager,
        mouse_controller: MouseController,
        on_emergency_stop: Optional[Callable[[], None]] = None,
        on_update_resolution: Optional[Callable[[int, int], None]] = None,
        **kwargs
    ):
        super().__init__(parent, padding=20, style="Main.TFrame", **kwargs)

        self.config = config
        self.settings_manager = settings_manager
        self.mouse_controller = mouse_controller
        self.on_emergency_stop_cb = on_emergency_stop
        self.on_update_resolution_cb = on_update_resolution

        self._build_ui()

    def _build_ui(self):
        """Constructs settings panel widgets in auto-resizing scrollable light canvas."""
        self.canvas = tk.Canvas(self, bg="#F8FAFC", highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        scroll_frame = ttk.Frame(self.canvas, style="Main.TFrame")

        window_id = self.canvas.create_window((0, 0), window=scroll_frame, anchor="nw")

        def _on_canvas_configure(event):
            self.canvas.itemconfig(window_id, width=event.width)

        self.canvas.bind("<Configure>", _on_canvas_configure)
        scroll_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Mouse Wheel Scrolling
        self.bind_mouse_wheel()
        self.bind("<Enter>", lambda e: self.bind_mouse_wheel())

        # Page Header
        title_lbl = tk.Label(
            scroll_frame,
            text="Settings",
            font=("Segoe UI", 18, "bold"),
            fg="#0F172A",
            bg="#F8FAFC"
        )
        title_lbl.pack(anchor="w", pady=(0, 2))

        sub_lbl = tk.Label(
            scroll_frame,
            text="Configure tracking, gestures, display resolution, and mouse control preferences",
            font=("Segoe UI", 10),
            fg="#64748B",
            bg="#F8FAFC"
        )
        sub_lbl.pack(anchor="w", pady=(0, 15))

        # 1. Mouse Control Card
        mc_card = ttk.Frame(scroll_frame, style="Card.TFrame", padding=20)
        mc_card.pack(fill="x", pady=(0, 15))

        tk.Label(
            mc_card,
            text="Mouse Control",
            font=("Segoe UI", 11, "bold"),
            fg="#0F172A",
            bg="#FFFFFF"
        ).pack(anchor="w", pady=(0, 12))

        mc_row = ttk.Frame(mc_card, style="Card.TFrame")
        mc_row.pack(fill="x")

        self.enable_var = tk.BooleanVar(value=self.config.mouse.enabled)
        toggle_box = ttk.Frame(mc_row, style="Card.TFrame")
        toggle_box.pack(anchor="w")

        toggle = ModernToggle(toggle_box, variable=self.enable_var, command=self._on_toggle_mouse)
        toggle.pack(side="left", padx=(0, 12))

        lbl_box = ttk.Frame(toggle_box, style="Card.TFrame")
        lbl_box.pack(side="left")

        tk.Label(
            lbl_box,
            text="Enable OS Mouse Control (Master Switch)",
            font=("Segoe UI", 10, "bold"),
            fg="#0F172A",
            bg="#FFFFFF"
        ).pack(anchor="w")

        tk.Label(
            lbl_box,
            text="Allow AirMouse AI to control your mouse",
            font=("Segoe UI", 8),
            fg="#64748B",
            bg="#FFFFFF"
        ).pack(anchor="w", pady=(1, 0))

        # 2. Camera & Capture Settings Card
        cam_card = ttk.Frame(scroll_frame, style="Card.TFrame", padding=20)
        cam_card.pack(fill="x", pady=(0, 15))

        tk.Label(
            cam_card,
            text="Camera & Capture Settings",
            font=("Segoe UI", 11, "bold"),
            fg="#0F172A",
            bg="#FFFFFF"
        ).pack(anchor="w", pady=(0, 15))

        cam_grid = ttk.Frame(cam_card, style="Card.TFrame")
        cam_grid.pack(fill="x")

        # Camera Index
        col1 = ttk.Frame(cam_grid, style="Card.TFrame")
        col1.pack(side="left", fill="x", expand=True, padx=(0, 15))
        tk.Label(col1, text="Camera Index", font=("Segoe UI", 9, "bold"), fg="#0F172A", bg="#FFFFFF").pack(anchor="w", pady=(0, 2))
        tk.Label(col1, text="Select webcam device (0 = built-in laptop camera)", font=("Segoe UI", 8), fg="#64748B", bg="#FFFFFF").pack(anchor="w", pady=(0, 6))
        self.cam_index_var = tk.IntVar(value=self.config.camera.camera_index)
        cam_combo = ttk.Combobox(col1, textvariable=self.cam_index_var, values=[0, 1, 2, 3], state="readonly")
        cam_combo.pack(fill="x")

        # Target FPS
        col2 = ttk.Frame(cam_grid, style="Card.TFrame")
        col2.pack(side="left", fill="x", expand=True)
        tk.Label(col2, text="Target FPS", font=("Segoe UI", 9, "bold"), fg="#0F172A", bg="#FFFFFF").pack(anchor="w", pady=(0, 2))
        tk.Label(col2, text="Capture frame rate (60 FPS for smoother tracking)", font=("Segoe UI", 8), fg="#64748B", bg="#FFFFFF").pack(anchor="w", pady=(0, 6))
        self.fps_var = tk.IntVar(value=self.config.camera.target_fps)
        fps_combo = ttk.Combobox(col2, textvariable=self.fps_var, values=[15, 30, 60], state="readonly")
        fps_combo.pack(fill="x")

        # 3. Hand Tracking & Gesture Thresholds Card
        track_card = ttk.Frame(scroll_frame, style="Card.TFrame", padding=20)
        track_card.pack(fill="x", pady=(0, 15))

        tk.Label(
            track_card,
            text="Hand Tracking & Gesture Thresholds",
            font=("Segoe UI", 11, "bold"),
            fg="#0F172A",
            bg="#FFFFFF"
        ).pack(anchor="w", pady=(0, 15))

        track_grid = ttk.Frame(track_card, style="Card.TFrame")
        track_grid.pack(fill="x")

        # Row 1: Min Detection Conf & Pinch Distance Threshold
        t_row1 = ttk.Frame(track_grid, style="Card.TFrame")
        t_row1.pack(fill="x", pady=(0, 12))

        # Min Detection Confidence
        tc1 = ttk.Frame(t_row1, style="Card.TFrame")
        tc1.pack(side="left", fill="x", expand=True, padx=(0, 15))
        tk.Label(tc1, text="Min Detection Confidence", font=("Segoe UI", 9, "bold"), fg="#0F172A", bg="#FFFFFF").pack(anchor="w", pady=(0, 2))
        tk.Label(tc1, text="AI hand certainty threshold (higher = avoids false hands)", font=("Segoe UI", 8), fg="#64748B", bg="#FFFFFF").pack(anchor="w", pady=(0, 4))
        self.det_conf_var = tk.DoubleVar(value=self.config.tracking.min_detection_confidence)
        s1 = ModernSlider(tc1, from_=0.30, to=0.90, variable=self.det_conf_var, format_str="{:.2f}")
        s1.pack(fill="x")

        # Pinch Distance Threshold
        tc2 = ttk.Frame(t_row1, style="Card.TFrame")
        tc2.pack(side="left", fill="x", expand=True)
        tk.Label(tc2, text="Pinch Distance Threshold", font=("Segoe UI", 9, "bold"), fg="#0F172A", bg="#FFFFFF").pack(anchor="w", pady=(0, 2))
        tk.Label(tc2, text="Fingertip distance to click (larger = clicks earlier)", font=("Segoe UI", 8), fg="#64748B", bg="#FFFFFF").pack(anchor="w", pady=(0, 4))
        self.pinch_thresh_var = tk.DoubleVar(value=self.config.gesture.pinch_threshold)
        s2 = ModernSlider(tc2, from_=0.10, to=0.50, variable=self.pinch_thresh_var, format_str="{:.2f}")
        s2.pack(fill="x")

        # Row 2: Stability Frames
        t_row2 = ttk.Frame(track_grid, style="Card.TFrame")
        t_row2.pack(fill="x")
        tk.Label(t_row2, text="Stability Frames (Debounce Count)", font=("Segoe UI", 9, "bold"), fg="#0F172A", bg="#FFFFFF").pack(anchor="w", pady=(0, 2))
        tk.Label(t_row2, text="Consecutive video frames required to confirm a gesture", font=("Segoe UI", 8), fg="#64748B", bg="#FFFFFF").pack(anchor="w", pady=(0, 6))
        self.stability_var = tk.IntVar(value=self.config.gesture.stability_frames)
        stab_combo = ttk.Combobox(t_row2, textvariable=self.stability_var, values=[1, 2, 3, 4, 5], state="readonly")
        stab_combo.pack(fill="x")

        # 4. Cursor Motion & Calibration Card
        cal_card = ttk.Frame(scroll_frame, style="Card.TFrame", padding=20)
        cal_card.pack(fill="x", pady=(0, 20))

        tk.Label(
            cal_card,
            text="Cursor Motion & Calibration",
            font=("Segoe UI", 11, "bold"),
            fg="#0F172A",
            bg="#FFFFFF"
        ).pack(anchor="w", pady=(0, 15))

        cal_grid = ttk.Frame(cal_card, style="Card.TFrame")
        cal_grid.pack(fill="x")

        # Row 1: Preset & Motion Deadzone
        c_row1 = ttk.Frame(cal_grid, style="Card.TFrame")
        c_row1.pack(fill="x", pady=(0, 12))

        # Preset
        cc1 = ttk.Frame(c_row1, style="Card.TFrame")
        cc1.pack(side="left", fill="x", expand=True, padx=(0, 15))
        tk.Label(cc1, text="Smoothing Preset", font=("Segoe UI", 9, "bold"), fg="#0F172A", bg="#FFFFFF").pack(anchor="w", pady=(0, 2))
        tk.Label(cc1, text="Quick preset balancing response speed vs tremor filter", font=("Segoe UI", 8), fg="#64748B", bg="#FFFFFF").pack(anchor="w", pady=(0, 6))
        self.preset_var = tk.StringVar(value=self.config.mouse.smoothing_preset.capitalize())
        preset_combo = ttk.Combobox(cc1, textvariable=self.preset_var, values=["Low", "Medium", "High"], state="readonly")
        preset_combo.pack(fill="x")

        # Motion Deadzone
        cc2 = ttk.Frame(c_row1, style="Card.TFrame")
        cc2.pack(side="left", fill="x", expand=True)
        tk.Label(cc2, text="Motion Deadzone (px)", font=("Segoe UI", 9, "bold"), fg="#0F172A", bg="#FFFFFF").pack(anchor="w", pady=(0, 2))
        tk.Label(cc2, text="Ignores small hand shakes below this pixel threshold", font=("Segoe UI", 8), fg="#64748B", bg="#FFFFFF").pack(anchor="w", pady=(0, 4))
        self.deadzone_var = tk.DoubleVar(value=self.config.mouse.motion_deadzone_px)
        s3 = ModernSlider(cc2, from_=0.0, to=30.0, variable=self.deadzone_var, format_str="{:.0f}")
        s3.pack(fill="x")

        # Row 2: Smoothing Factor & Workspace Edge Margin
        c_row2 = ttk.Frame(cal_grid, style="Card.TFrame")
        c_row2.pack(fill="x", pady=(0, 12))

        # Cursor Smoothing Factor
        cc3 = ttk.Frame(c_row2, style="Card.TFrame")
        cc3.pack(side="left", fill="x", expand=True, padx=(0, 15))
        tk.Label(cc3, text="Cursor Smoothing Factor", font=("Segoe UI", 9, "bold"), fg="#0F172A", bg="#FFFFFF").pack(anchor="w", pady=(0, 2))
        tk.Label(cc3, text="Motion filter (lower = ultra-smooth, higher = faster response)", font=("Segoe UI", 8), fg="#64748B", bg="#FFFFFF").pack(anchor="w", pady=(0, 4))
        self.smooth_factor_var = tk.DoubleVar(value=self.config.mouse.smoothing_factor)
        s4 = ModernSlider(cc3, from_=0.05, to=0.95, variable=self.smooth_factor_var, format_str="{:.2f}")
        s4.pack(fill="x")

        # Workspace Edge Margin (%)
        cc4 = ttk.Frame(c_row2, style="Card.TFrame")
        cc4.pack(side="left", fill="x", expand=True)
        tk.Label(cc4, text="Workspace Edge Margin (%)", font=("Segoe UI", 9, "bold"), fg="#0F172A", bg="#FFFFFF").pack(anchor="w", pady=(0, 2))
        tk.Label(cc4, text="Screen border padding (reach corners without stretching)", font=("Segoe UI", 8), fg="#64748B", bg="#FFFFFF").pack(anchor="w", pady=(0, 4))
        self.pad_var = tk.DoubleVar(value=self.config.calibration.padding_x * 100)
        s5 = ModernSlider(cc4, from_=0.0, to=30.0, variable=self.pad_var, format_str="{:.0f}")
        s5.pack(fill="x")

        # Row 3: Click Freeze Window & Display Resolution Setting
        c_row3 = ttk.Frame(cal_grid, style="Card.TFrame")
        c_row3.pack(fill="x")

        # Click Freeze Window
        cc5 = ttk.Frame(c_row3, style="Card.TFrame")
        cc5.pack(side="left", fill="x", expand=True, padx=(0, 15))
        tk.Label(cc5, text="Click Freeze Window (ms)", font=("Segoe UI", 9, "bold"), fg="#0F172A", bg="#FFFFFF").pack(anchor="w", pady=(0, 2))
        tk.Label(cc5, text="Locks cursor on target during pinch to prevent target missing", font=("Segoe UI", 8), fg="#64748B", bg="#FFFFFF").pack(anchor="w", pady=(0, 4))
        self.freeze_var = tk.IntVar(value=self.config.mouse.click_freeze_duration_ms)
        freeze_combo = ttk.Combobox(cc5, textvariable=self.freeze_var, values=[50, 100, 150, 200, 300], state="readonly")
        freeze_combo.pack(fill="x")

        # Display Resolution Dropdown Setting
        cc6 = ttk.Frame(c_row3, style="Card.TFrame")
        cc6.pack(side="left", fill="x", expand=True)
        tk.Label(cc6, text="Display Resolution Target", font=("Segoe UI", 9, "bold"), fg="#0F172A", bg="#FFFFFF").pack(anchor="w", pady=(0, 2))
        tk.Label(cc6, text="Monitor resolution used to calculate cursor coordinates", font=("Segoe UI", 8), fg="#64748B", bg="#FFFFFF").pack(anchor="w", pady=(0, 4))

        # Detect primary display resolution dynamically
        detected_w, detected_h = 1920, 1080
        try:
            sw, sh = pyautogui.size()
            if sw > 0 and sh > 0:
                detected_w, detected_h = sw, sh
        except Exception:
            pass

        auto_opt = f"Auto-detect ({detected_w}x{detected_h} - Primary Display)"
        res_options = [
            auto_opt,
            "1920x1080 (Full HD)",
            "1920x1200 (WUXGA)",
            "2560x1440 (2K QHD)",
            "3840x2160 (4K UHD)",
            "1366x768 (Laptop HD)",
            "1280x720 (HD)"
        ]

        detected_str = f"{detected_w}x{detected_h}"
        if not any(detected_str in opt for opt in res_options):
            res_options.insert(1, f"{detected_str} (Primary Display)")

        curr_w = self.config.calibration.screen_width
        curr_h = self.config.calibration.screen_height
        if curr_w == 0 or curr_h == 0:
            initial_res_str = auto_opt
        else:
            matching = [opt for opt in res_options if f"{curr_w}x{curr_h}" in opt]
            initial_res_str = matching[0] if matching else f"{curr_w}x{curr_h} (Custom)"

        self.res_var = tk.StringVar(value=initial_res_str)
        self.res_combo = ttk.Combobox(cc6, textvariable=self.res_var, values=res_options, state="readonly")
        self.res_combo.pack(fill="x")
        self.res_combo.bind("<<ComboboxSelected>>", self._on_res_combo_changed)

        # 5. Bottom Action Bar (Save, Reset, Emergency Stop)
        action_bar = ttk.Frame(scroll_frame, style="Main.TFrame")
        action_bar.pack(fill="x", pady=(5, 10))

        # Save Preferences (Blue Filled)
        btn_save = tk.Button(
            action_bar,
            text="💾   Save Preferences",
            font=("Segoe UI", 10, "bold"),
            fg="#FFFFFF",
            bg="#2563EB",
            activebackground="#1D4ED8",
            activeforeground="#FFFFFF",
            bd=0,
            relief="flat",
            padx=18,
            pady=9,
            cursor="hand2",
            command=self._on_save_settings
        )
        btn_save.pack(side="left", padx=(0, 10))

        # Reset Defaults (White Outline)
        btn_reset = tk.Button(
            action_bar,
            text="🔄   Reset Defaults",
            font=("Segoe UI", 10, "bold"),
            fg="#475569",
            bg="#FFFFFF",
            activebackground="#F1F5F9",
            activeforeground="#0F172A",
            bd=1,
            relief="solid",
            highlightbackground="#E2E8F0",
            padx=18,
            pady=9,
            cursor="hand2",
            command=self._on_reset_defaults
        )
        btn_reset.pack(side="left", padx=(0, 10))

        # Emergency Stop (Red Outline)
        btn_emerg = tk.Button(
            action_bar,
            text="🔴   Emergency Stop",
            font=("Segoe UI", 10, "bold"),
            fg="#EF4444",
            bg="#FFFFFF",
            activebackground="#FEF2F2",
            activeforeground="#DC2626",
            bd=1,
            relief="solid",
            highlightbackground="#EF4444",
            padx=18,
            pady=9,
            cursor="hand2",
            command=self._on_emergency_stop
        )
        btn_emerg.pack(side="left")

    def _update_val_label(self, label: tk.Label, val: float, fmt: str):
        label.config(text=fmt.format(val))

    def _on_toggle_mouse(self):
        enabled = self.enable_var.get()
        self.mouse_controller.set_enabled(enabled)

    def _on_res_combo_changed(self, event=None):
        res_str = self.res_var.get()
        if "Auto-detect" in res_str:
            forced_w, forced_h = 0, 0
        else:
            match = re.search(r"(\d+)x(\d+)", res_str)
            if match:
                forced_w, forced_h = int(match.group(1)), int(match.group(2))
            else:
                forced_w, forced_h = 0, 0

        self.mouse_controller.transformer.update_screen_resolution(forced_w, forced_h)
        active_w = self.mouse_controller.transformer.screen_width
        active_h = self.mouse_controller.transformer.screen_height

        if self.on_update_resolution_cb:
            self.on_update_resolution_cb(active_w, active_h)

    def _on_save_settings(self):
        # Update config values from variables
        self.config.mouse.enabled = self.enable_var.get()
        self.config.camera.camera_index = self.cam_index_var.get()
        self.config.camera.target_fps = self.fps_var.get()
        self.config.tracking.min_detection_confidence = self.det_conf_var.get()
        self.config.gesture.pinch_threshold = self.pinch_thresh_var.get()
        self.config.gesture.stability_frames = self.stability_var.get()
        self.config.mouse.smoothing_preset = self.preset_var.get().lower()
        self.config.mouse.motion_deadzone_px = self.deadzone_var.get()
        self.config.mouse.smoothing_factor = self.smooth_factor_var.get()
        self.config.calibration.padding_x = self.pad_var.get() / 100.0
        self.config.calibration.padding_y = self.pad_var.get() / 100.0
        self.config.mouse.click_freeze_duration_ms = self.freeze_var.get()

        # Update resolution & notify status bar
        self._on_res_combo_changed()

        res_str = self.res_var.get()
        if "Auto-detect" in res_str:
            self.config.calibration.screen_width = 0
            self.config.calibration.screen_height = 0
        else:
            match = re.search(r"(\d+)x(\d+)", res_str)
            if match:
                self.config.calibration.screen_width = int(match.group(1))
                self.config.calibration.screen_height = int(match.group(2))

        # Save to JSON
        success = self.settings_manager.save_settings(self.config)
        if success:
            messagebox.showinfo("Settings Saved", "Your preference settings have been saved successfully!")

    def _on_reset_defaults(self):
        confirm = messagebox.askyesno("Reset Defaults", "Are you sure you want to reset all preferences to default settings?")
        if confirm:
            cfg = self.settings_manager.reset_to_defaults()
            self.config = cfg
            # Update UI vars
            self.enable_var.set(cfg.mouse.enabled)
            self.cam_index_var.set(cfg.camera.camera_index)
            self.fps_var.set(cfg.camera.target_fps)
            self.det_conf_var.set(cfg.tracking.min_detection_confidence)
            self.pinch_thresh_var.set(cfg.gesture.pinch_threshold)
            self.stability_var.set(cfg.gesture.stability_frames)
            self.preset_var.set(cfg.mouse.smoothing_preset.capitalize())
            self.deadzone_var.set(cfg.mouse.motion_deadzone_px)
            self.smooth_factor_var.set(cfg.mouse.smoothing_factor)
            self.pad_var.set(cfg.calibration.padding_x * 100)
            self.freeze_var.set(cfg.mouse.click_freeze_duration_ms)
            self.res_var.set("Auto-detect (System Resolution)")
            messagebox.showinfo("Defaults Restored", "All settings have been restored to factory defaults.")

    def _on_emergency_stop(self):
        if self.on_emergency_stop_cb:
            self.on_emergency_stop_cb()
        else:
            self.mouse_controller.emergency_stop()

    def bind_mouse_wheel(self):
        """Binds global mouse wheel scrolling to this panel's canvas when active."""
        def _on_mouse_wheel(event):
            if event.delta:
                self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            elif event.num == 4:
                self.canvas.yview_scroll(-1, "units")
            elif event.num == 5:
                self.canvas.yview_scroll(1, "units")

        if hasattr(self, 'canvas'):
            self.canvas.bind_all("<MouseWheel>", _on_mouse_wheel)
            self.canvas.bind_all("<Button-4>", _on_mouse_wheel)
            self.canvas.bind_all("<Button-5>", _on_mouse_wheel)
