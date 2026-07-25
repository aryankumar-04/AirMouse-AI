"""
AirMouse AI - Dashboard Tab View.

Combines live camera preview canvas with real-time telemetry cards and quick action controls matching the reference UI design.
"""

import logging
import time
import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional
import cv2
from PIL import Image, ImageTk

from config import AppConfig
from app.core.app_state import AppStateManager
from app.core.mouse_state import MouseState
from app.vision.camera import CameraManager
from app.vision.hand_tracker import HandTracker
from app.vision.gesture_engine import GestureEngine, GestureEngineOutput
from app.control.mouse_controller import MouseController
from app.utils.fps_calculator import FPSCalculator


class Dashboard(ttk.Frame):
    """Main Dashboard tab view styled in clean modern light theme."""

    def __init__(
        self,
        parent,
        config: AppConfig,
        state_manager: AppStateManager,
        camera_manager: CameraManager,
        hand_tracker: HandTracker,
        gesture_engine: GestureEngine,
        mouse_controller: MouseController,
        on_start_camera: Callable[[], None],
        on_stop_camera: Callable[[], None],
        on_emergency_stop: Callable[[], None],
        **kwargs
    ):
        super().__init__(parent, padding=20, style="Main.TFrame", **kwargs)

        self.config = config
        self.state_manager = state_manager
        self.camera_manager = camera_manager
        self.hand_tracker = hand_tracker
        self.gesture_engine = gesture_engine
        self.mouse_controller = mouse_controller

        self.on_start_camera_cb = on_start_camera
        self.on_stop_camera_cb = on_stop_camera
        self.on_emergency_stop_cb = on_emergency_stop

        self.fps_calculator = FPSCalculator()
        self._current_photo_image: Optional[ImageTk.PhotoImage] = None

        self._build_ui()

    def _build_ui(self):
        """Constructs responsive dashboard split layout matching reference image."""
        # Top Container Split
        main_split = ttk.Frame(self, style="Main.TFrame")
        main_split.pack(fill="both", expand=True)

        # 1. Right Column: Stacked Telemetry Cards (Packed FIRST so it never collapses on resize)
        right_col = ttk.Frame(main_split, width=280, style="Main.TFrame")
        right_col.pack(side="right", fill="y", expand=False)
        right_col.pack_propagate(False)

        # 2. Left Column: Video Preview & Quick Actions (Takes remaining space on left)
        left_col = ttk.Frame(main_split, style="Main.TFrame")
        left_col.pack(side="left", fill="both", expand=True, padx=(0, 20))

        # 2A. Quick Actions Card (Packed at BOTTOM of left_col first so it never gets pushed off screen)
        quick_card = ttk.Frame(left_col, style="Card.TFrame", padding=15)
        quick_card.pack(side="bottom", fill="x", pady=(15, 0))

        tk.Label(
            quick_card,
            text="Quick Actions",
            font=("Segoe UI", 11, "bold"),
            fg="#0F172A",
            bg="#FFFFFF"
        ).pack(anchor="w", pady=(0, 10))

        btn_row = ttk.Frame(quick_card, style="Card.TFrame")
        btn_row.pack(fill="x")

        self.btn_start = tk.Button(
            btn_row,
            text="▶   Start Tracking",
            font=("Segoe UI", 10, "bold"),
            fg="#FFFFFF",
            bg="#2563EB",
            activebackground="#1D4ED8",
            activeforeground="#FFFFFF",
            bd=0,
            relief="flat",
            padx=20,
            pady=10,
            cursor="hand2",
            command=self.on_start_camera_cb
        )
        self.btn_start.pack(side="left")

        self.btn_stop = tk.Button(
            btn_row,
            text="⏹   Stop Tracking",
            font=("Segoe UI", 10, "bold"),
            fg="#EF4444",
            bg="#FFFFFF",
            activebackground="#FEF2F2",
            activeforeground="#DC2626",
            bd=1,
            relief="solid",
            highlightbackground="#E2E8F0",
            padx=20,
            pady=10,
            cursor="hand2",
            command=self.on_stop_camera_cb
        )
        # Initially hide stop button until camera starts
        self.btn_stop.pack_forget()

        # 2B. Live Camera Card (Packs in top remaining space of left_col)
        camera_card = ttk.Frame(left_col, style="Card.TFrame", padding=15)
        camera_card.pack(side="top", fill="both", expand=True)

        # Camera Header
        cam_hdr = ttk.Frame(camera_card, style="Card.TFrame")
        cam_hdr.pack(fill="x", pady=(0, 10))

        tk.Label(
            cam_hdr,
            text="📹  Live Camera",
            font=("Segoe UI", 12, "bold"),
            fg="#0F172A",
            bg="#FFFFFF"
        ).pack(side="left")

        # Camera Video Canvas Label Container
        self.preview_frame_container = ttk.Frame(camera_card, style="Card.TFrame")
        self.preview_frame_container.pack(fill="both", expand=True)

        self.preview_label = tk.Label(
            self.preview_frame_container,
            text="Camera Inactive\nClick 'Start Tracking' below to launch camera feed",
            bg="#F1F5F9",
            fg="#94A3B8",
            font=("Segoe UI", 11),
            bd=0,
            relief="flat"
        )
        self.preview_label.pack(fill="both", expand=True)

        # Telemetry Card Helper
        def make_telemetry_card(parent, icon_symbol: str, icon_bg: str, icon_fg: str, title: str):
            card = ttk.Frame(parent, style="Card.TFrame", padding=15)
            card.pack(fill="x", pady=(0, 15))

            hdr = ttk.Frame(card, style="Card.TFrame")
            hdr.pack(fill="x", pady=(0, 6))

            # Icon badge
            icon_lbl = tk.Label(
                hdr,
                text=icon_symbol,
                font=("Segoe UI", 11, "bold"),
                fg=icon_fg,
                bg=icon_bg,
                width=3,
                height=1
            )
            icon_lbl.pack(side="left", padx=(0, 8))

            tk.Label(
                hdr,
                text=title,
                font=("Segoe UI", 10, "bold"),
                fg="#0F172A",
                bg="#FFFFFF"
            ).pack(side="left")

            val_lbl = tk.Label(
                card,
                text="--",
                font=("Segoe UI", 15, "bold"),
                fg="#0F172A",
                bg="#FFFFFF"
            )
            val_lbl.pack(anchor="w")

            sub_lbl = tk.Label(
                card,
                text="--",
                font=("Segoe UI", 9),
                fg="#64748B",
                bg="#FFFFFF"
            )
            sub_lbl.pack(anchor="w", pady=(2, 0))

            return val_lbl, sub_lbl

        # 1. Performance Card
        self.fps_val_lbl, self.res_sub_lbl = make_telemetry_card(
            right_col, "⚡", "#EFF6FF", "#2563EB", "Performance"
        )
        self.fps_val_lbl.config(text="0.0 FPS")
        active_w = self.mouse_controller.transformer.screen_width
        active_h = self.mouse_controller.transformer.screen_height
        self.res_sub_lbl.config(text=f"Resolution: {active_w}x{active_h}")

        # 2. Gesture Card
        self.gesture_val_lbl, self.stability_sub_lbl = make_telemetry_card(
            right_col, "🖐", "#DCFCE7", "#16A34A", "Gesture"
        )
        self.gesture_val_lbl.config(text="NO_HAND", fg="#64748B")
        self.stability_sub_lbl.config(text="Stability: 0/2")

        # 3. Action Card
        self.action_val_lbl, self.pos_sub_lbl = make_telemetry_card(
            right_col, "🖱", "#F3E8FF", "#9333EA", "Action"
        )
        self.action_val_lbl.config(text="ACTION_DISABLE", fg="#9333EA")
        self.pos_sub_lbl.config(text="Cursor Pos: (0, 0)")

        # 4. Camera Card
        self.cam_status_lbl, self.cam_health_sub_lbl = make_telemetry_card(
            right_col, "📹", "#FEF3C7", "#D97706", "Camera"
        )
        self.cam_status_lbl.config(text="Inactive", fg="#64748B")
        self.cam_health_sub_lbl.config(text="Click Start Tracking to begin")

    def update_telemetry(self, gesture_output: GestureEngineOutput, fps: float):
        """Updates dashboard metric cards and renders preview video frame."""
        # 1. Update FPS & Preview Frame
        self.fps_val_lbl.config(text=f"{fps:.1f} FPS")

        display_frame = gesture_output.processed_frame
        if display_frame is not None:
            rgb_img = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(rgb_img)

            # Fit into preview container dynamically while preserving video aspect ratio
            container_w = self.preview_frame_container.winfo_width()
            container_h = self.preview_frame_container.winfo_height()

            if container_w < 50 or container_h < 50:
                container_w = self.config.ui.preview_width
                container_h = self.config.ui.preview_height

            img_h, img_w, _ = display_frame.shape
            aspect = img_w / float(img_h) if img_h > 0 else (4.0 / 3.0)

            target_w = container_w
            target_h = int(target_w / aspect)

            if target_h > container_h and container_h > 50:
                target_h = container_h
                target_w = int(target_h * aspect)

            target_w = max(160, target_w)
            target_h = max(120, target_h)

            pil_img = pil_img.resize((target_w, target_h), Image.Resampling.BILINEAR)

            photo = ImageTk.PhotoImage(image=pil_img)
            self.preview_label.config(image=photo, text="")
            self._current_photo_image = photo

        # 2. Update Telemetry Cards
        evt = gesture_output.event
        action = gesture_output.mapped_action.action
        last_pos = self.mouse_controller.state_machine.get_last_cursor_pos()

        # Format action display name cleanly
        action_name_map = {
            "ACTION_HOVER": "HOVER",
            "ACTION_PRIMARY_CLICK": "LEFT CLICK",
            "ACTION_SECONDARY_CLICK": "RIGHT CLICK",
            "ACTION_SCROLL": "SCROLL",
            "ACTION_DISABLE": "PAUSED",
            "ACTION_NONE": "PAUSED"
        }
        display_action = action_name_map.get(action.name, action.name.replace("ACTION_", ""))

        # Gesture Card
        self.gesture_val_lbl.config(
            text=f"{evt.state.name}",
            fg="#10B981" if evt.is_stable and evt.state.name != "NO_HAND" else "#F59E0B"
        )
        self.stability_sub_lbl.config(
            text=f"Stability: {evt.stability_count}/{self.config.gesture.stability_frames} ({'Stable' if evt.is_stable else 'Transition'})"
        )

        # Action Card
        self.action_val_lbl.config(text=display_action, fg="#8B5CF6")
        self.pos_sub_lbl.config(text=f"Cursor Pos: ({last_pos[0]}, {last_pos[1]})")

        # Camera Card
        self.cam_status_lbl.config(text="Active", fg="#0F172A")
        self.cam_health_sub_lbl.config(text="Camera is working properly")

    def reset_preview(self):
        """Resets preview label on camera stop."""
        self.preview_label.config(
            image="",
            text="Camera Inactive\nClick 'Start Tracking' below to launch camera feed"
        )
        self._current_photo_image = None
        self.fps_val_lbl.config(text="0.0 FPS")
        self.gesture_val_lbl.config(text="NO_HAND", fg="#64748B")
        self.stability_sub_lbl.config(text="Stability: 0/2")
        self.action_val_lbl.config(text="PAUSED", fg="#8B5CF6")
        self.pos_sub_lbl.config(text="Cursor Pos: (0, 0)")
        self.cam_status_lbl.config(text="Inactive", fg="#64748B")
        self.cam_health_sub_lbl.config(text="Click Start Tracking to begin")
        self.set_camera_running_state(False)

    def set_camera_running_state(self, running: bool):
        """Updates camera action button visibility so only one button is visible at a time."""
        if running:
            self.btn_start.pack_forget()
            self.btn_stop.config(text="⏹   Stop Tracking", state="normal")
            self.btn_stop.pack(side="left")
        else:
            self.btn_stop.pack_forget()
            self.btn_start.config(text="▶   Start Tracking", state="normal")
            self.btn_start.pack(side="left")

    def set_camera_transitioning(self, text: str):
        """Sets temporary transitioning state on active button."""
        if "Start" in text or "Starting" in text:
            self.btn_stop.pack_forget()
            self.btn_start.config(text=text, state="disabled")
            self.btn_start.pack(side="left")
        else:
            self.btn_start.pack_forget()
            self.btn_stop.config(text=text, state="disabled")
            self.btn_stop.pack(side="left")

    def update_screen_resolution(self, width: int, height: int):
        """Updates active screen display resolution label in Performance card."""
        self.res_sub_lbl.config(text=f"Resolution: {width}x{height}")
