"""
AirMouse AI - Production About Page View.

Designed to commercial product standards (inspired by Microsoft PowerToys, VS Code, Logitech Options+).
Presents product value, key features, privacy model, technology stack, and interactive support options.
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox
import webbrowser
from PIL import Image, ImageTk
from config import AppConfig


class AboutPanel(ttk.Frame):
    """Production-grade About page styled in clean modern product presentation."""

    def __init__(self, parent, config: AppConfig, **kwargs):
        super().__init__(parent, padding=20, style="Main.TFrame", **kwargs)
        self.config = config
        self.about_logo_img = None
        self._build_ui()

    def _build_ui(self):
        """Constructs about page cards in auto-resizing scrollable canvas."""
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

        # ----------------------------------------------------
        # SECTION 1: HERO CARD
        # ----------------------------------------------------
        hero_card = ttk.Frame(scroll_frame, style="Card.TFrame", padding=24)
        hero_card.pack(fill="x", pady=(0, 15))

        hero_hdr = ttk.Frame(hero_card, style="Card.TFrame")
        hero_hdr.pack(fill="x", anchor="w", pady=(0, 10))

        # Logo Icon
        if os.path.exists("assets/logo_64.png"):
            try:
                pil_logo = Image.open("assets/logo_64.png").convert("RGBA")
                self.about_logo_img = ImageTk.PhotoImage(pil_logo)
            except Exception:
                pass

        if self.about_logo_img:
            tk.Label(hero_hdr, image=self.about_logo_img, bg="#FFFFFF").pack(side="left", padx=(0, 12))

        title_box = ttk.Frame(hero_hdr, style="Card.TFrame")
        title_box.pack(side="left")

        title_row = ttk.Frame(title_box, style="Card.TFrame")
        title_row.pack(anchor="w")

        tk.Label(
            title_row,
            text="AirMouse AI",
            font=("Segoe UI", 18, "bold"),
            fg="#0F172A",
            bg="#FFFFFF"
        ).pack(side="left", padx=(0, 8))

        # Version Pill Badge
        ver_badge = tk.Label(
            title_row,
            text=" v1.0.0 ",
            font=("Segoe UI", 9, "bold"),
            fg="#2563EB",
            bg="#EFF6FF",
            padx=6,
            pady=2
        )
        ver_badge.pack(side="left")

        tk.Label(
            title_box,
            text="Control your Windows PC naturally using only your hand.",
            font=("Segoe UI", 11, "bold"),
            fg="#2563EB",
            bg="#FFFFFF"
        ).pack(anchor="w", pady=(2, 0))

        # Product Benefit Description
        hero_desc = (
            "AirMouse AI turns any standard webcam into a high-precision, low-latency touchless mouse controller. "
            "Operate your PC seamlessly using natural hand movement and intuitive pinch gestures. "
            "Engineered to run 100% locally on your computer with complete privacy, zero internet requirement, and no extra hardware."
        )
        tk.Label(
            hero_card,
            text=hero_desc,
            font=("Segoe UI", 10),
            fg="#475569",
            bg="#FFFFFF",
            wraplength=720,
            justify="left"
        ).pack(anchor="w", pady=(0, 15))

        # Badges Row
        badge_row = ttk.Frame(hero_card, style="Card.TFrame")
        badge_row.pack(anchor="w")

        badges = [
            ("🔒 100% Offline", "#ECFDF5", "#047857"),
            ("🛡️ Privacy First", "#EFF6FF", "#1D4ED8"),
            ("⚡ Ultra-Low Latency", "#FEF3C7", "#B45309"),
            ("💻 Windows Native", "#F3E8FF", "#6B21A8"),
            ("⭐ Open Source", "#F1F5F9", "#334155")
        ]

        for text, bg_col, fg_col in badges:
            tk.Label(
                badge_row,
                text=f" {text} ",
                font=("Segoe UI", 8, "bold"),
                fg=fg_col,
                bg=bg_col,
                padx=8,
                pady=4
            ).pack(side="left", padx=(0, 8))

        # ----------------------------------------------------
        # SECTION 2: KEY FEATURES GRID
        # ----------------------------------------------------
        feat_card = ttk.Frame(scroll_frame, style="Card.TFrame", padding=24)
        feat_card.pack(fill="x", pady=(0, 15))

        tk.Label(
            feat_card,
            text="Key Product Capabilities",
            font=("Segoe UI", 12, "bold"),
            fg="#0F172A",
            bg="#FFFFFF"
        ).pack(anchor="w", pady=(0, 15))

        feat_grid = ttk.Frame(feat_card, style="Card.TFrame")
        feat_grid.pack(fill="x")

        features_data = [
            ("🖱️", "Natural Mouse Control", "Fluidly guide your cursor across your display with smooth hand motion."),
            ("🎯", "Precise Pinch Click & Drag", "Execute left clicks, right clicks, and drag operations with high accuracy."),
            ("🔒", "100% Local & Private", "Zero cloud processing or network calls. Video frames never leave your device."),
            ("⚡", "Adaptive Tremor Filter", "One Euro filtering eliminates rest jitter while keeping fast sweeps instant."),
            ("🛡️", "Safety & Emergency Clutch", "Automatic position freeze on tracking loss and instant PyAutoGUI failsafes."),
            ("⚙️", "Customizable Sensitivity", "Tailor pinch distance thresholds, smoothing factors, and deadzones to your style.")
        ]

        for idx, (icon, f_title, f_desc) in enumerate(features_data):
            r = idx // 2
            c = idx % 2

            f_box = ttk.Frame(feat_grid, style="Card.TFrame", padding=10)
            f_box.grid(row=r, column=c, sticky="nsew", padx=6, pady=6)
            feat_grid.columnconfigure(c, weight=1)

            f_hdr = ttk.Frame(f_box, style="Card.TFrame")
            f_hdr.pack(anchor="w", pady=(0, 4))

            tk.Label(f_hdr, text=icon, font=("Segoe UI", 12), bg="#FFFFFF").pack(side="left", padx=(0, 6))
            tk.Label(f_hdr, text=f_title, font=("Segoe UI", 10, "bold"), fg="#0F172A", bg="#FFFFFF").pack(side="left")
            tk.Label(f_box, text=f_desc, font=("Segoe UI", 9), fg="#64748B", bg="#FFFFFF", wraplength=320, justify="left").pack(anchor="w")

        # ----------------------------------------------------
        # SECTION 3: WHY AIRMOUSE AI? (PHILOSOPHY)
        # ----------------------------------------------------
        phil_card = ttk.Frame(scroll_frame, style="Card.TFrame", padding=24)
        phil_card.pack(fill="x", pady=(0, 15))

        tk.Label(
            phil_card,
            text="Why AirMouse AI?",
            font=("Segoe UI", 12, "bold"),
            fg="#0F172A",
            bg="#FFFFFF"
        ).pack(anchor="w", pady=(0, 12))

        principles = [
            ("No Special Hardware Required", "Works out-of-the-box with your laptop's integrated webcam or standard USB camera."),
            ("No Subscriptions or Paywalls", "100% free and open-source software built for performance and accessibility."),
            ("Privacy by Design", "Camera frames are processed in memory and discarded immediately. No video is recorded or sent anywhere."),
            ("Native Windows Performance", "Direct Win32 SendInput integration delivers sub-millisecond physical mouse execution.")
        ]

        for p_title, p_desc in principles:
            p_row = ttk.Frame(phil_card, style="Card.TFrame")
            p_row.pack(fill="x", pady=4)
            tk.Label(p_row, text="• ", font=("Segoe UI", 10, "bold"), fg="#2563EB", bg="#FFFFFF").pack(side="left")
            tk.Label(p_row, text=f"{p_title}: ", font=("Segoe UI", 9, "bold"), fg="#0F172A", bg="#FFFFFF").pack(side="left")
            tk.Label(p_row, text=p_desc, font=("Segoe UI", 9), fg="#64748B", bg="#FFFFFF").pack(side="left")

        # ----------------------------------------------------
        # SECTION 4: PRIVACY & SECURITY STATEMENT
        # ----------------------------------------------------
        priv_card = ttk.Frame(scroll_frame, style="Card.TFrame", padding=24)
        priv_card.pack(fill="x", pady=(0, 15))

        p_hdr = ttk.Frame(priv_card, style="Card.TFrame")
        p_hdr.pack(anchor="w", pady=(0, 8))

        tk.Label(p_hdr, text="🛡️", font=("Segoe UI", 14), bg="#FFFFFF").pack(side="left", padx=(0, 8))
        tk.Label(p_hdr, text="Privacy & Security Guarantee", font=("Segoe UI", 12, "bold"), fg="#0F172A", bg="#FFFFFF").pack(side="left")

        p_text = (
            "Your privacy is fully protected. AirMouse AI operates completely offline. "
            "No webcam images, personal data, or telemetry metrics ever leave your local computer. "
            "All vision models execute locally on your CPU."
        )
        tk.Label(priv_card, text=p_text, font=("Segoe UI", 9), fg="#475569", bg="#FFFFFF", wraplength=700, justify="left").pack(anchor="w")

        # ----------------------------------------------------
        # SECTION 5: TECHNOLOGY STACK
        # ----------------------------------------------------
        tech_card = ttk.Frame(scroll_frame, style="Card.TFrame", padding=24)
        tech_card.pack(fill="x", pady=(0, 15))

        tk.Label(
            tech_card,
            text="Technology Stack",
            font=("Segoe UI", 12, "bold"),
            fg="#0F172A",
            bg="#FFFFFF"
        ).pack(anchor="w", pady=(0, 10))

        tech_items = [
            "Python 3.10+",
            "MediaPipe Tasks API",
            "OpenCV Vision",
            "Win32 Native SendInput",
            "PyAutoGUI",
            "NumPy Engine",
            "Tkinter / TTK"
        ]

        tech_row = ttk.Frame(tech_card, style="Card.TFrame")
        tech_row.pack(anchor="w")

        for item in tech_items:
            tk.Label(
                tech_row,
                text=f" {item} ",
                font=("Segoe UI", 8, "bold"),
                fg="#2563EB",
                bg="#EFF6FF",
                padx=8,
                pady=4
            ).pack(side="left", padx=(0, 8), pady=2)

        # ----------------------------------------------------
        # SECTION 6: APPLICATION INFORMATION TABLE
        # ----------------------------------------------------
        info_card = ttk.Frame(scroll_frame, style="Card.TFrame", padding=24)
        info_card.pack(fill="x", pady=(0, 15))

        tk.Label(
            info_card,
            text="System & Build Information",
            font=("Segoe UI", 12, "bold"),
            fg="#0F172A",
            bg="#FFFFFF"
        ).pack(anchor="w", pady=(0, 12))

        sys_info_data = [
            ("Product Version", "v1.0.0 (Release Build)"),
            ("Target OS", "Windows 10 / Windows 11 (x64)"),
            ("License", "MIT Open Source License"),
            ("Python Runtime", f"Python {sys.version.split()[0]}"),
            ("Author & Maintainers", "AirMouse AI Core Team")
        ]

        info_grid = ttk.Frame(info_card, style="Card.TFrame")
        info_grid.pack(fill="x")

        for k, v in sys_info_data:
            r_frame = ttk.Frame(info_grid, style="Card.TFrame")
            r_frame.pack(fill="x", pady=3)
            tk.Label(r_frame, text=f"{k}:", font=("Segoe UI", 9, "bold"), fg="#475569", bg="#FFFFFF", width=22, anchor="w").pack(side="left")
            tk.Label(r_frame, text=v, font=("Segoe UI", 9), fg="#0F172A", bg="#FFFFFF").pack(side="left")

        # ----------------------------------------------------
        # SECTION 7: SUPPORT & RESOURCES (ACTION BUTTONS)
        # ----------------------------------------------------
        supp_card = ttk.Frame(scroll_frame, style="Card.TFrame", padding=24)
        supp_card.pack(fill="x", pady=(0, 15))

        tk.Label(
            supp_card,
            text="Resources & Support",
            font=("Segoe UI", 12, "bold"),
            fg="#0F172A",
            bg="#FFFFFF"
        ).pack(anchor="w", pady=(0, 12))

        btn_bar = ttk.Frame(supp_card, style="Card.TFrame")
        btn_bar.pack(anchor="w")

        # GitHub Repo Button
        tk.Button(
            btn_bar,
            text="⭐   GitHub Repository",
            font=("Segoe UI", 9, "bold"),
            fg="#FFFFFF",
            bg="#2563EB",
            activebackground="#1D4ED8",
            activeforeground="#FFFFFF",
            bd=0,
            relief="flat",
            padx=14,
            pady=8,
            cursor="hand2",
            command=lambda: webbrowser.open("https://github.com")
        ).pack(side="left", padx=(0, 10))

        # Report Issue Button
        tk.Button(
            btn_bar,
            text="🐛   Report Issue",
            font=("Segoe UI", 9, "bold"),
            fg="#475569",
            bg="#FFFFFF",
            activebackground="#F1F5F9",
            activeforeground="#0F172A",
            bd=1,
            relief="solid",
            highlightbackground="#E2E8F0",
            padx=14,
            pady=8,
            cursor="hand2",
            command=lambda: webbrowser.open("https://github.com")
        ).pack(side="left", padx=(0, 10))

        # Copy System Info Button
        tk.Button(
            btn_bar,
            text="📋   Copy System Info",
            font=("Segoe UI", 9, "bold"),
            fg="#475569",
            bg="#FFFFFF",
            activebackground="#F1F5F9",
            activeforeground="#0F172A",
            bd=1,
            relief="solid",
            highlightbackground="#E2E8F0",
            padx=14,
            pady=8,
            cursor="hand2",
            command=self._copy_system_info
        ).pack(side="left")

        # ----------------------------------------------------
        # SECTION 8: CREDITS
        # ----------------------------------------------------
        cred_card = ttk.Frame(scroll_frame, style="Card.TFrame", padding=20)
        cred_card.pack(fill="x", pady=(0, 15))

        tk.Label(cred_card, text="Credits & Acknowledgments", font=("Segoe UI", 11, "bold"), fg="#0F172A", bg="#FFFFFF").pack(anchor="w", pady=(0, 6))
        c_text = "Built with gratitude using Google MediaPipe Tasks API, OpenCV, Python Software Foundation, PyAutoGUI, and the open-source computer vision community."
        tk.Label(cred_card, text=c_text, font=("Segoe UI", 9), fg="#64748B", bg="#FFFFFF", wraplength=700, justify="left").pack(anchor="w")

        # ----------------------------------------------------
        # SECTION 9: LICENSE & LEGAL NOTICE
        # ----------------------------------------------------
        lic_card = ttk.Frame(scroll_frame, style="Card.TFrame", padding=20)
        lic_card.pack(fill="x", pady=(0, 15))

        tk.Label(lic_card, text="License & Legal", font=("Segoe UI", 11, "bold"), fg="#0F172A", bg="#FFFFFF").pack(anchor="w", pady=(0, 6))
        l_text = "Released under the MIT License. Copyright © 2026 AirMouse AI Team. All rights reserved."
        tk.Label(lic_card, text=l_text, font=("Segoe UI", 9), fg="#64748B", bg="#FFFFFF").pack(anchor="w")

        # ----------------------------------------------------
        # SECTION 10: FOOTER
        # ----------------------------------------------------
        footer = ttk.Frame(scroll_frame, style="Main.TFrame")
        footer.pack(fill="x", pady=(10, 20))

        tk.Label(
            footer,
            text="Made with Python • AirMouse AI v1.0.0 • © 2026 AirMouse AI Team",
            font=("Segoe UI", 8),
            fg="#94A3B8",
            bg="#F8FAFC"
        ).pack(anchor="center")

    def _copy_system_info(self):
        """Copies formatted system information to the Windows clipboard."""
        info_str = (
            f"AirMouse AI Version: v1.0.0 (Release Build)\n"
            f"Python Runtime: Python {sys.version.split()[0]}\n"
            f"Target OS: {sys.platform} (x64)\n"
            f"License: MIT Open Source License"
        )
        self.clipboard_clear()
        self.clipboard_append(info_str)
        messagebox.showinfo("Copied", "System information copied to clipboard!")

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

