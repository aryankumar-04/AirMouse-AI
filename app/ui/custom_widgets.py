"""
AirMouse AI - Custom UI Widgets Module.

Provides pixel-perfect custom canvas widgets including two-tone progress track sliders
with value badge boxes and pill toggle switches matching the reference UI mockup.
"""

import tkinter as tk
from typing import Callable, Optional


class ModernToggle(tk.Canvas):
    """Modern pill toggle switch widget matching reference UI design."""

    def __init__(
        self,
        parent,
        variable: Optional[tk.BooleanVar] = None,
        command: Optional[Callable[[], None]] = None,
        bg: str = "#FFFFFF",
        **kwargs
    ):
        super().__init__(parent, width=46, height=24, bg=bg, highlightthickness=0, bd=0, cursor="hand2", **kwargs)
        self.var = variable or tk.BooleanVar(value=True)
        self.command = command

        self.bind("<Button-1>", self._toggle)
        self.var.trace_add("write", lambda *args: self._redraw())
        self._redraw()

    def _toggle(self, event=None):
        new_val = not self.var.get()
        self.var.set(new_val)
        if self.command:
            self.command()

    def _redraw(self):
        self.delete("all")
        is_on = self.var.get()
        bg_color = "#2563EB" if is_on else "#CBD5E1"
        knob_x = 33 if is_on else 13

        # Pill background track
        self.create_line(13, 12, 33, 12, fill=bg_color, width=22, capstyle="round")
        # White circular knob
        r = 8
        self.create_oval(knob_x - r, 12 - r, knob_x + r, 12 + r, fill="#FFFFFF", outline="")


class ModernSlider(tk.Frame):
    """Custom slider widget with two-tone blue progress track, white handle, and value badge box."""

    def __init__(
        self,
        parent,
        from_: float = 0.0,
        to: float = 1.0,
        variable: Optional[tk.DoubleVar] = None,
        command: Optional[Callable[[float], None]] = None,
        format_str: str = "{:.2f}",
        bg: str = "#FFFFFF",
        **kwargs
    ):
        super().__init__(parent, bg=bg, **kwargs)
        self.from_ = from_
        self.to = to
        self.var = variable or tk.DoubleVar(value=from_)
        self.command = command
        self.format_str = format_str

        # Canvas for two-tone slider track & handle
        self.canvas = tk.Canvas(self, height=28, bg=bg, highlightthickness=0, bd=0, cursor="hand2")
        self.canvas.pack(side="left", fill="x", expand=True, padx=(0, 12))

        # Value Display Badge Box
        self.val_badge = tk.Label(
            self,
            text=self.format_str.format(self.var.get()),
            font=("Segoe UI", 9),
            fg="#0F172A",
            bg="#F8FAFC",
            bd=1,
            relief="solid",
            highlightbackground="#E2E8F0",
            width=6,
            pady=3
        )
        self.val_badge.pack(side="right")

        self.canvas.bind("<Configure>", self._redraw)
        self.canvas.bind("<Button-1>", self._on_click)
        self.canvas.bind("<B1-Motion>", self._on_drag)

        # Sync variable writes
        self.var.trace_add("write", lambda *args: self._update_from_var())
        self._update_from_var()

    def _update_from_var(self):
        try:
            val = self.var.get()
            self.val_badge.config(text=self.format_str.format(val))
            self._redraw()
        except Exception:
            pass

    def _redraw(self, event=None):
        self.canvas.delete("all")
        w = max(50, self.canvas.winfo_width())
        cy = 14
        pad_x = 10
        track_w = w - 2 * pad_x

        try:
            val = max(self.from_, min(self.to, self.var.get()))
        except Exception:
            val = self.from_

        ratio = (val - self.from_) / (self.to - self.from_) if self.to > self.from_ else 0
        handle_x = pad_x + ratio * track_w

        # Inactive Gray Track
        self.canvas.create_line(pad_x, cy, pad_x + track_w, cy, fill="#E2E8F0", width=6, capstyle="round")

        # Active Blue Progress Track
        if handle_x > pad_x:
            self.canvas.create_line(pad_x, cy, handle_x, cy, fill="#2563EB", width=6, capstyle="round")

        # White Circular Thumb Handle with Blue Accent Ring
        r = 7
        self.canvas.create_oval(handle_x - r - 1, cy - r - 1, handle_x + r + 1, cy + r + 1, fill="#CBD5E1", outline="")
        self.canvas.create_oval(handle_x - r, cy - r, handle_x + r, cy + r, fill="#FFFFFF", outline="#2563EB", width=2)

    def _on_click(self, event):
        self._set_val_from_x(event.x)

    def _on_drag(self, event):
        self._set_val_from_x(event.x)

    def _set_val_from_x(self, x_pos):
        w = self.canvas.winfo_width()
        pad_x = 10
        track_w = w - 2 * pad_x
        if track_w <= 0:
            return
        ratio = max(0.0, min(1.0, (x_pos - pad_x) / track_w))
        val = self.from_ + ratio * (self.to - self.from_)
        self.var.set(val)
        if self.command:
            self.command(val)
