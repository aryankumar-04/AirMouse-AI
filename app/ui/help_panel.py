"""
AirMouse AI - Gesture Guide View.

Provides clean, visual, card-based gesture references with custom vector hand drawings,
responsive grid reflow (1, 2, 3, or 4 columns), and soft rounded styling matching reference UI.
"""

import os
import tkinter as tk
from tkinter import ttk
from typing import List


# Gesture Card Data Definitions
GESTURE_CARDS_DATA = [
    {
        "num": "1",
        "num_bg": "#2563EB",
        "gesture_id": 1,
        "circle_bg": "#EFF6FF",
        "stroke_color": "#2563EB",
        "title": "Point & Move",
        "subtitle": "(Hover Mode)",
        "sub_color": "#2563EB",
        "desc": "Hold up your Index finger alone (keep other fingers folded).",
        "what": "Smoothly moves the mouse cursor across your screen like a physical trackpad."
    },
    {
        "num": "2",
        "num_bg": "#10B981",
        "gesture_id": 2,
        "circle_bg": "#DCFCE7",
        "stroke_color": "#16A34A",
        "title": "Left Click",
        "subtitle": "(Pinch Tap)",
        "sub_color": "#10B981",
        "desc": "Briefly pinch your Thumb + Index finger together and release.",
        "what": "Triggers a single left-click right on your target without moving or slipping off the button."
    },
    {
        "num": "3",
        "num_bg": "#8B5CF6",
        "gesture_id": 3,
        "circle_bg": "#F3E8FF",
        "stroke_color": "#9333EA",
        "title": "Drag & Drop",
        "subtitle": "(Pinch & Hold)",
        "sub_color": "#8B5CF6",
        "desc": "Pinch your Thumb + Index finger together and hold them closed while moving your hand.",
        "what": "Presses down the left mouse button so you can drag windows, move files, or select text. Releasing your pinch drops the item."
    },
    {
        "num": "4",
        "num_bg": "#F59E0B",
        "gesture_id": 4,
        "circle_bg": "#FEF3C7",
        "stroke_color": "#D97706",
        "title": "Right Click",
        "subtitle": "(Thumb + Middle)",
        "sub_color": "#F59E0B",
        "desc": "Pinch your Thumb + Middle finger together.",
        "what": "Triggers a reliable right-click to open context menus."
    },
    {
        "num": "5",
        "num_bg": "#2563EB",
        "gesture_id": 5,
        "circle_bg": "#EFF6FF",
        "stroke_color": "#2563EB",
        "title": "Scroll Up & Down",
        "subtitle": "(Two-Finger Mode)",
        "sub_color": "#2563EB",
        "desc": "Hold up your Index + Middle fingers together.",
        "what": "Enters Scroll Mode! Move your hand up to scroll up, or down to scroll down."
    },
    {
        "num": "6",
        "num_bg": "#10B981",
        "gesture_id": 6,
        "circle_bg": "#DCFCE7",
        "stroke_color": "#16A34A",
        "title": "Neutral / Pause Mode",
        "subtitle": "(Open Palm)",
        "sub_color": "#10B981",
        "desc": "Show an Open Palm (all 5 fingers spread open).",
        "what": "Pauses mouse movement safely so you can rest your hand without accidentally clicking anything."
    },
    {
        "num": "7",
        "num_bg": "#EF4444",
        "gesture_id": 7,
        "circle_bg": "#FEE2E2",
        "stroke_color": "#DC2626",
        "title": "Emergency Safety Stop",
        "subtitle": "(Fist)",
        "sub_color": "#EF4444",
        "desc": "Make a Fist (all fingers closed into your palm).",
        "what": "Instantly stops mouse tracking for total safety whenever you want to use your physical mouse or keyboard."
    }
]


class GestureCard(ttk.Frame):
    """Reusable card component for displaying individual hand gesture instructions with custom image overlays."""

    def __init__(self, parent, data: dict, **kwargs):
        super().__init__(parent, style="Card.TFrame", padding=15, **kwargs)
        self.data = data
        self.gesture_img = None
        self._build_card()

    def _build_card(self):
        # Card Header: Circular Number Badge + Title & Mode Subtitle
        hdr = ttk.Frame(self, style="Card.TFrame")
        hdr.pack(fill="x", pady=(0, 8))

        # Circular Badge
        badge = tk.Canvas(hdr, width=26, height=26, bg="#FFFFFF", highlightthickness=0)
        badge.pack(side="left", padx=(0, 8))
        badge.create_oval(1, 1, 25, 25, fill=self.data["num_bg"], outline="")
        badge.create_text(13, 13, text=self.data["num"], fill="#FFFFFF", font=("Segoe UI", 9, "bold"))

        t_box = ttk.Frame(hdr, style="Card.TFrame")
        t_box.pack(side="left", fill="x", expand=True)

        tk.Label(t_box, text=self.data["title"], font=("Segoe UI", 9, "bold"), fg="#0F172A", bg="#FFFFFF").pack(anchor="w")
        tk.Label(t_box, text=self.data["subtitle"], font=("Segoe UI", 8, "bold"), fg=self.data["sub_color"], bg="#FFFFFF").pack(anchor="w")

        # Large Illustration Canvas (80x80)
        cv = tk.Canvas(self, width=80, height=80, bg="#FFFFFF", highlightthickness=0)
        cv.pack(pady=(4, 8))

        # Background Circle
        cv.create_oval(4, 4, 76, 76, fill=self.data["circle_bg"], outline="")

        # Check for custom image overlay in assets/gestures/gesture_{id}.png
        g_id = self.data["gesture_id"]
        img_path = f"assets/gestures/gesture_{g_id}.png"
        has_custom_img = False

        if os.path.exists(img_path):
            try:
                from PIL import Image, ImageTk, ImageDraw
                pil_img = Image.open(img_path).convert("RGBA")
                # Resize keeping aspect ratio to fit inside 72x72 circle
                pil_img.thumbnail((72, 72), Image.Resampling.LANCZOS)
                
                # Apply smooth circular mask
                mask = Image.new("L", pil_img.size, 0)
                draw = ImageDraw.Draw(mask)
                draw.ellipse((0, 0, pil_img.size[0], pil_img.size[1]), fill=255)

                composite = Image.new("RGBA", pil_img.size, (255, 255, 255, 0))
                composite.paste(pil_img, (0, 0), mask)

                self.gesture_img = ImageTk.PhotoImage(composite)
                cv.create_image(40, 40, image=self.gesture_img)
                has_custom_img = True
            except Exception:
                has_custom_img = False

        if not has_custom_img:
            self._draw_vector_hand(cv, g_id, self.data["stroke_color"])

        # Description
        tk.Label(
            self,
            text=self.data["desc"],
            font=("Segoe UI", 8),
            fg="#475569",
            bg="#FFFFFF",
            wraplength=170,
            justify="center"
        ).pack(pady=(0, 10))

        # What it does Box
        what_box = tk.Frame(
            self,
            bg="#F8FAFC",
            highlightbackground="#E2E8F0",
            highlightthickness=1,
            relief="flat"
        )
        what_box.pack(fill="both", expand=True)

        tk.Label(what_box, text="What it does:", font=("Segoe UI", 8, "bold"), fg=self.data["sub_color"], bg="#F8FAFC").pack(anchor="w", padx=10, pady=(8, 2))
        tk.Label(
            what_box,
            text=self.data["what"],
            font=("Segoe UI", 8),
            fg="#475569",
            bg="#F8FAFC",
            wraplength=150,
            justify="left"
        ).pack(anchor="w", padx=10, pady=(0, 10))

    def _draw_vector_hand(self, cv: tk.Canvas, gesture_id: int, color: str):
        c = color
        if gesture_id == 1:  # Pointing Index Finger
            cv.create_line(40, 42, 40, 18, fill=c, width=4, capstyle="round")
            cv.create_rectangle(30, 42, 50, 58, fill=c, outline=c)
            cv.create_line(24, 46, 30, 50, fill=c, width=4, capstyle="round")
        elif gesture_id == 2:  # Pinch Tap
            cv.create_oval(25, 22, 45, 42, outline=c, width=3)
            cv.create_line(44, 28, 56, 18, fill=c, width=3, capstyle="round")
            cv.create_line(48, 34, 60, 26, fill=c, width=3, capstyle="round")
            cv.create_line(50, 40, 62, 34, fill=c, width=3, capstyle="round")
            cv.create_rectangle(32, 42, 48, 58, fill=c, outline=c)
        elif gesture_id == 3:  # Pinch Hold / Drag
            cv.create_oval(28, 24, 46, 42, fill=c, outline=c)
            cv.create_rectangle(30, 42, 50, 58, fill=c, outline=c)
            cv.create_line(24, 46, 30, 50, fill=c, width=3, capstyle="round")
        elif gesture_id == 4:  # Thumb + Middle Pinch
            cv.create_oval(32, 22, 52, 42, outline=c, width=3)
            cv.create_line(26, 38, 24, 18, fill=c, width=3, capstyle="round")
            cv.create_rectangle(32, 42, 50, 58, fill=c, outline=c)
        elif gesture_id == 5:  # Two Finger Scroll
            cv.create_line(34, 42, 34, 18, fill=c, width=4, capstyle="round")
            cv.create_line(46, 42, 46, 18, fill=c, width=4, capstyle="round")
            cv.create_rectangle(28, 42, 52, 58, fill=c, outline=c)
        elif gesture_id == 6:  # Open Palm (5 fingers)
            cv.create_line(22, 38, 14, 26, fill=c, width=3, capstyle="round")
            cv.create_line(28, 38, 22, 16, fill=c, width=3, capstyle="round")
            cv.create_line(36, 38, 36, 12, fill=c, width=3, capstyle="round")
            cv.create_line(44, 38, 48, 16, fill=c, width=3, capstyle="round")
            cv.create_line(52, 40, 58, 26, fill=c, width=3, capstyle="round")
            cv.create_oval(25, 36, 52, 58, fill=c, outline=c)
        elif gesture_id == 7:  # Closed Fist
            cv.create_rectangle(26, 28, 54, 56, fill=c, outline=c)
            cv.create_line(20, 36, 26, 40, fill=c, width=4, capstyle="round")


class QuickTipsCard(ttk.Frame):
    """Card 8 widget displaying Quick Tips for optimal gesture experience."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, style="Card.TFrame", padding=15, **kwargs)
        self._build_card()

    def _build_card(self):
        tk.Label(
            self,
            text="💡 Quick Tips for the Best Experience",
            font=("Segoe UI", 10, "bold"),
            fg="#2563EB",
            bg="#FFFFFF"
        ).pack(anchor="w", pady=(0, 10))

        tips = [
            ("🎯", "Natural Movement", "Move slowly for precise pixel targeting, or sweep fast to cover your whole screen."),
            ("⏱️", "Click Precision", "Pause briefly before pinching. Avoid clicking while moving quickly."),
            ("💡", "Lighting", "Use good lighting and avoid dark environments."),
            ("📷", "Camera Distance", "Keep your entire hand inside the camera frame."),
            ("🛡️", "Safety", "If tracking is lost, cursor movement pauses automatically.")
        ]

        for icon, title, desc in tips:
            t_hdr = ttk.Frame(self, style="Card.TFrame")
            t_hdr.pack(fill="x", pady=(3, 1))
            tk.Label(t_hdr, text=icon, font=("Segoe UI", 9), bg="#FFFFFF").pack(side="left", padx=(0, 4))
            tk.Label(t_hdr, text=title, font=("Segoe UI", 9, "bold"), fg="#0F172A", bg="#FFFFFF").pack(side="left")

            tk.Label(
                self,
                text=desc,
                font=("Segoe UI", 8),
                fg="#475569",
                bg="#FFFFFF",
                wraplength=170,
                justify="left"
            ).pack(anchor="w", padx=(18, 0), pady=(0, 5))


class HelpPanel(ttk.Frame):
    """Fully responsive Gesture Guide page component with dynamic card reflow."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, padding=20, style="Main.TFrame", **kwargs)
        self.current_cols = -1
        self.card_widgets: List[ttk.Frame] = []
        self._build_ui()

    def _build_ui(self):
        """Constructs gesture guide card grid in auto-resizing canvas."""
        self.canvas = tk.Canvas(self, bg="#F8FAFC", highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        scroll_frame = ttk.Frame(self.canvas, style="Main.TFrame")

        window_id = self.canvas.create_window((0, 0), window=scroll_frame, anchor="nw")

        def _on_canvas_configure(event):
            self.canvas.itemconfig(window_id, width=event.width)
            self._relayout_grid(event.width)

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
            text="Gesture Guide",
            font=("Segoe UI", 18, "bold"),
            fg="#0F172A",
            bg="#F8FAFC"
        )
        title_lbl.pack(anchor="w", pady=(0, 2))

        sub_lbl = tk.Label(
            scroll_frame,
            text="Learn all hand gestures and their actions",
            font=("Segoe UI", 10),
            fg="#64748B",
            bg="#F8FAFC"
        )
        sub_lbl.pack(anchor="w", pady=(0, 15))

        # Dynamic Grid Container
        self.grid_frame = ttk.Frame(scroll_frame, style="Main.TFrame")
        self.grid_frame.pack(fill="x")

        # Instantiate 7 Gesture Cards + 1 Quick Tips Card
        for data in GESTURE_CARDS_DATA:
            card = GestureCard(self.grid_frame, data)
            self.card_widgets.append(card)

        tips_card = QuickTipsCard(self.grid_frame)
        self.card_widgets.append(tips_card)

        # Trigger initial grid layout
        self._relayout_grid(800)

    def _relayout_grid(self, width: int):
        """Dynamically calculates grid column reflow (1, 2, 3, or 4 columns) based on width."""
        if not hasattr(self, 'grid_frame') or not self.grid_frame:
            return

        if width < 500:
            cols = 1
        elif width < 850:
            cols = 2
        elif width < 1150:
            cols = 3
        else:
            cols = 4

        if cols == self.current_cols:
            return

        self.current_cols = cols

        # Configure uniform column weights
        for c_idx in range(4):
            self.grid_frame.columnconfigure(c_idx, weight=0, uniform="")
        for c_idx in range(cols):
            self.grid_frame.columnconfigure(c_idx, weight=1, uniform="card_col")

        # Re-grid all card widgets
        for idx, card in enumerate(self.card_widgets):
            r = idx // cols
            c = idx % cols
            card.grid(row=r, column=c, padx=6, pady=6, sticky="nsew")

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

