"""
AirMouse AI - Status Bar Widget.

Displays master mouse control status, active resolution, and safety state.
"""

import tkinter as tk
from tkinter import ttk
from app.core.mouse_state import MouseState, MouseStateMachine


class StatusBar(ttk.Frame):
    """Custom Status Bar widget."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)

        self.configure(padding=(15, 6, 15, 6), style="StatusBar.TFrame")

        self.mouse_status_lbl = ttk.Label(
            self,
            text="● MOUSE CONTROL: DISABLED",
            font=("Segoe UI", 9, "bold"),
            foreground="#64748B",
            background="#FFFFFF"
        )
        self.mouse_status_lbl.pack(side="left")

        self.screen_res_lbl = ttk.Label(
            self,
            text="Screen: 1920x1080",
            font=("Segoe UI", 9),
            foreground="#94A3B8",
            background="#FFFFFF"
        )
        self.screen_res_lbl.pack(side="right")

    def update_mouse_status(self, state: MouseState):
        """Updates mouse status label text and color."""
        color_map = {
            MouseState.IDLE: ("● MOUSE CONTROL: READY", "#22C55E"),
            MouseState.MOVE: ("● MOUSE CONTROL: MOVING", "#2563EB"),
            MouseState.DRAGGING: ("● MOUSE CONTROL: DRAGGING", "#8B5CF6"),
            MouseState.CLICKED: ("● MOUSE CONTROL: CLICKED", "#22C55E"),
            MouseState.PAUSED: ("● MOUSE CONTROL: PAUSED", "#F59E0B"),
            MouseState.DISABLED: ("● MOUSE CONTROL: DISABLED", "#64748B")
        }
        text, color = color_map.get(state, ("● MOUSE CONTROL: DISABLED", "#64748B"))
        self.mouse_status_lbl.config(text=text, foreground=color)

    def update_screen_res(self, width: int, height: int):
        """Updates screen resolution display."""
        self.screen_res_lbl.config(text=f"Screen: {width}x{height}")

