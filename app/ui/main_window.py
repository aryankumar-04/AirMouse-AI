"""
AirMouse AI - Main Application GUI Control Center.

Desktop window featuring a clean productivity Light Theme, Left Sidebar Navigation
(Dashboard, Settings, Gesture Guide, About), rounded white card view containers, and Status Bar.
"""

import logging
import os
import time
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional
from PIL import Image, ImageTk

from config import AppConfig
from app.core.app_state import AppState, AppStateManager
from app.core.settings_state import SettingsManager
from app.core.mouse_state import MouseState
from app.vision.camera import CameraManager
from app.vision.hand_tracker import HandTracker, DetectionResult
from app.vision.gesture_engine import GestureEngine, GestureEngineOutput
from app.control.mouse_controller import MouseController
from app.ui.dashboard import Dashboard
from app.ui.settings_panel import SettingsPanel
from app.ui.help_panel import HelpPanel
from app.ui.about_panel import AboutPanel
from app.ui.status_bar import StatusBar


class MainWindow:
    """Tkinter Desktop Application Control Center with Light Theme and Sidebar Navigation."""

    def __init__(
        self,
        config: AppConfig,
        state_manager: AppStateManager,
        settings_manager: SettingsManager,
        camera_manager: CameraManager,
        hand_tracker: HandTracker,
        gesture_engine: GestureEngine,
        mouse_controller: MouseController,
        logger: Optional[logging.Logger] = None
    ):
        self.config = config
        self.state_manager = state_manager
        self.settings_manager = settings_manager
        self.camera_manager = camera_manager
        self.hand_tracker = hand_tracker
        self.gesture_engine = gesture_engine
        self.mouse_controller = mouse_controller
        self.logger = logger or logging.getLogger("AirMouseAI.UI")

        # Tkinter Root Setup
        self.root = tk.Tk()
        self.root.title(self.config.ui.window_title)
        self.root.geometry(f"{self.config.ui.window_width}x{self.config.ui.window_height}")
        self.root.minsize(1024, 680)

        # Active page tracking
        self.active_page = "dashboard"
        self.nav_buttons = {}

        # Apply Light Theme Styling
        self._configure_styles()

        # Build Main App Container (Sidebar + Page Stack)
        self._build_layout()
        self._build_status_bar()

        # Default page display
        self._switch_page("dashboard")

        # Window closing handler
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

        # Start periodic UI polling loop
        self.root.after(self.config.ui.update_interval_ms, self._ui_tick)

    def _configure_styles(self):
        """Sets Light color scheme and TTK widget styles."""
        bg_app = "#F8FAFC"       # Light gray-white
        bg_card = "#FFFFFF"      # Pure white
        accent_blue = "#2563EB"  # Primary blue

        self.root.configure(bg=bg_app)
        style = ttk.Style()
        style.theme_use("clam")

        # Global TTK Defaults
        style.configure(".", background=bg_app, foreground="#0F172A", font=("Segoe UI", 10))
        style.configure("Main.TFrame", background=bg_app)
        style.configure("Card.TFrame", background=bg_card, relief="flat", borderwidth=0)
        style.configure("Sidebar.TFrame", background="#F8FAFC")
        style.configure("StatusBar.TFrame", background=bg_card)

        style.configure("Header.TLabel", font=("Segoe UI", 16, "bold"), foreground="#0F172A", background=bg_app)
        style.configure("SubHeader.TLabel", font=("Segoe UI", 9), foreground="#64748B", background=bg_app)
        style.configure("CardTitle.TLabel", font=("Segoe UI", 11, "bold"), foreground=accent_blue, background=bg_card)

    def _build_layout(self):
        """Constructs left sidebar and main page view stack."""
        self.main_container = ttk.Frame(self.root, style="Main.TFrame")
        self.main_container.pack(fill="both", expand=True)

        # 1. Left Sidebar
        self.sidebar = tk.Frame(self.main_container, bg="#F8FAFC", width=260, bd=0)
        self.sidebar.pack(side="left", fill="y", expand=False)
        self.sidebar.pack_propagate(False)

        # Sidebar Right Border Separator Line
        sep_line = tk.Frame(self.main_container, bg="#E2E8F0", width=1)
        sep_line.pack(side="left", fill="y")

        # Sidebar Top Logo & Title Box
        logo_box = tk.Frame(self.sidebar, bg="#F8FAFC")
        logo_box.pack(fill="x", pady=(18, 20), padx=12)

        logo_hdr = tk.Frame(logo_box, bg="#F8FAFC")
        logo_hdr.pack(fill="x", anchor="w")

        # Load high-quality app logo PNGs
        self.logo_img = None
        if os.path.exists("assets/logo_36.png"):
            try:
                pil_logo = Image.open("assets/logo_36.png").convert("RGBA")
                self.logo_img = ImageTk.PhotoImage(pil_logo)
            except Exception:
                pass
        if os.path.exists("assets/logo_64.png"):
            try:
                icon_pil = Image.open("assets/logo_64.png").convert("RGBA")
                self.icon_img = ImageTk.PhotoImage(icon_pil)
                self.root.iconphoto(True, self.icon_img)
            except Exception:
                pass

        if self.logo_img:
            tk.Label(
                logo_hdr,
                image=self.logo_img,
                bg="#F8FAFC"
            ).pack(side="left", padx=(0, 8))
        else:
            tk.Label(
                logo_hdr,
                text="🖐️",
                font=("Segoe UI", 18),
                bg="#F8FAFC"
            ).pack(side="left", padx=(0, 6))

        tk.Label(
            logo_hdr,
            text="AirMouse AI",
            font=("Segoe UI", 16, "bold"),
            fg="#0F172A",
            bg="#F8FAFC"
        ).pack(side="left")

        tk.Label(
            logo_box,
            text="AI Hand Gesture Mouse Controller",
            font=("Segoe UI", 8),
            fg="#64748B",
            bg="#F8FAFC"
        ).pack(anchor="w", pady=(3, 0))

        # Sidebar Navigation Item List
        nav_items = [
            ("dashboard", "🏠   Dashboard"),
            ("settings", "⚙️   Settings"),
            ("guide", "📖   Gesture Guide"),
            ("about", "ℹ️   About")
        ]

        nav_box = tk.Frame(self.sidebar, bg="#F8FAFC")
        nav_box.pack(fill="x", padx=12)

        for page_key, label_text in nav_items:
            btn = tk.Button(
                nav_box,
                text=label_text,
                font=("Segoe UI", 10, "bold"),
                anchor="w",
                padx=15,
                pady=10,
                bd=0,
                relief="flat",
                cursor="hand2",
                command=lambda k=page_key: self._switch_page(k)
            )
            btn.pack(fill="x", pady=4)
            self.nav_buttons[page_key] = btn

        # 2. Right Main View Content Stack
        self.view_stack = ttk.Frame(self.main_container, style="Main.TFrame")
        self.view_stack.pack(side="right", fill="both", expand=True)

        # Page View 1: Dashboard
        self.dashboard_view = Dashboard(
            self.view_stack,
            config=self.config,
            state_manager=self.state_manager,
            camera_manager=self.camera_manager,
            hand_tracker=self.hand_tracker,
            gesture_engine=self.gesture_engine,
            mouse_controller=self.mouse_controller,
            on_start_camera=self._start_camera,
            on_stop_camera=self._stop_camera,
            on_emergency_stop=self._on_emergency_stop_triggered
        )

        # Page View 2: Settings & Calibration
        self.settings_view = SettingsPanel(
            self.view_stack,
            config=self.config,
            settings_manager=self.settings_manager,
            mouse_controller=self.mouse_controller,
            on_emergency_stop=self._on_emergency_stop_triggered,
            on_update_resolution=self._on_update_resolution_cb
        )

        # Page View 3: Gesture Guide
        self.guide_view = HelpPanel(self.view_stack)

        # Page View 4: About
        self.about_view = AboutPanel(self.view_stack, config=self.config)

    def _switch_page(self, target_page: str):
        """Switches active page in the main view stack and updates sidebar highlighting."""
        self.active_page = target_page

        # Update sidebar button styling
        for page_key, btn in self.nav_buttons.items():
            if page_key == target_page:
                btn.config(
                    bg="#2563EB",
                    fg="#FFFFFF",
                    activebackground="#1D4ED8",
                    activeforeground="#FFFFFF"
                )
            else:
                btn.config(
                    bg="#F8FAFC",
                    fg="#475569",
                    activebackground="#F1F5F9",
                    activeforeground="#0F172A"
                )

        # Hide all views
        self.dashboard_view.pack_forget()
        self.settings_view.pack_forget()
        self.guide_view.pack_forget()
        self.about_view.pack_forget()

        # Show target view & activate mouse wheel scrolling for visible active page
        if target_page == "dashboard":
            self.root.unbind_all("<MouseWheel>")
            self.root.unbind_all("<Button-4>")
            self.root.unbind_all("<Button-5>")
            self.dashboard_view.pack(fill="both", expand=True)
        elif target_page == "settings":
            self.settings_view.pack(fill="both", expand=True)
            self.settings_view.bind_mouse_wheel()
        elif target_page == "guide":
            self.guide_view.pack(fill="both", expand=True)
            self.guide_view.bind_mouse_wheel()
        elif target_page == "about":
            self.about_view.pack(fill="both", expand=True)
            self.about_view.bind_mouse_wheel()

    def _build_status_bar(self):
        """Builds bottom status bar."""
        self.status_bar = StatusBar(self.root)
        self.status_bar.pack(fill="x", side="bottom")
        self.status_bar.update_screen_res(
            self.mouse_controller.transformer.screen_width,
            self.mouse_controller.transformer.screen_height
        )

    def _on_emergency_stop_triggered(self):
        """Callback when Emergency Stop is triggered."""
        self.logger.warning("Emergency Stop triggered by user")
        self.mouse_controller.emergency_stop()
        if hasattr(self, 'settings_view') and hasattr(self.settings_view, 'enable_var'):
            self.settings_view.enable_var.set(False)
        self.status_bar.update_mouse_status(MouseState.DISABLED)

    def _on_update_resolution_cb(self, width: int, height: int):
        """Callback to update active resolution display in bottom status bar and Dashboard Performance card."""
        if hasattr(self, 'status_bar') and self.status_bar:
            self.status_bar.update_screen_res(width, height)
        if hasattr(self, 'dashboard_view') and self.dashboard_view:
            self.dashboard_view.update_screen_resolution(width, height)

    def _start_camera(self):
        """Starts webcam capture and updates control state."""
        self.dashboard_view.set_camera_transitioning("Starting...")
        success = self.camera_manager.start()

        if success:
            # Sync mouse controller state with user config preference
            self.mouse_controller.set_enabled(self.config.mouse.enabled)
            self.dashboard_view.set_camera_running_state(True)
            self.dashboard_view.fps_calculator.reset()
            self.logger.info("Tracking started")
        else:
            err_msg = self.camera_manager.get_error_message() or "Camera could not be opened."
            self.dashboard_view.set_camera_running_state(False)
            messagebox.showerror("Camera Error", err_msg)
            self.logger.error("Camera could not be opened")

    def _stop_camera(self):
        """Stops webcam capture and resets preview."""
        self.dashboard_view.set_camera_transitioning("Stopping...")
        self.mouse_controller.emergency_stop()
        self.camera_manager.stop()

        self.dashboard_view.reset_preview()
        self.status_bar.update_mouse_status(MouseState.DISABLED)
        self.logger.info("Tracking stopped")

    def _ui_tick(self):
        """Periodic UI update loop called via root.after()."""
        try:
            if self.state_manager.is_error():
                err_msg = self.state_manager.get_error_message()
                self._stop_camera()
                messagebox.showerror("Camera Failure", err_msg)

            elif self.camera_manager.is_running():
                ret, frame = self.camera_manager.read_frame()

                if ret and frame is not None:
                    h, w, _ = frame.shape

                    # 1. Update FPS calculation
                    fps = self.dashboard_view.fps_calculator.tick()

                    # 2. Run hand tracking
                    detection_result: DetectionResult = self.hand_tracker.process_frame(
                        frame, draw_overlay=True
                    )

                    # 3. Run gesture engine & state machine
                    gesture_output: GestureEngineOutput = self.gesture_engine.process(
                        detection_result, draw_debug_overlay=True
                    )

                    # 4. Run Physical Mouse Controller
                    self.mouse_controller.process(gesture_output, (w, h))

                    # 5. Update Dashboard View Telemetry
                    self.dashboard_view.update_telemetry(gesture_output, fps)

                    # 6. Update Status Bar
                    mouse_state = self.mouse_controller.state_machine.get_state()
                    self.status_bar.update_mouse_status(mouse_state)

        except Exception as err:
            self.logger.error(f"Unexpected exception in UI tick loop: {err}", exc_info=True)

        finally:
            if self.root.winfo_exists():
                self.root.after(self.config.ui.update_interval_ms, self._ui_tick)

    def _on_closing(self):
        """Gracefully saves preferences, cleans up vision worker thread, and destroys window."""
        try:
            self.mouse_controller.emergency_stop()
            self.camera_manager.stop()
            self.hand_tracker.close()
            # Save active preferences to file on exit
            self.settings_manager.save_settings(self.config)
        except Exception as e:
            self.logger.warning(f"Error during cleanup on window close: {e}")
        finally:
            self.root.destroy()

    def run(self):
        """Launches the Tkinter event loop."""
        self.logger.debug("Launching Tkinter main application loop.")
        self.root.mainloop()
