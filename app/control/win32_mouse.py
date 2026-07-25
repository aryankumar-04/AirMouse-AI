"""
AirMouse AI - Low-Latency Windows Native Mouse Backend.

Uses Windows ctypes (user32.dll) SendInput API for sub-millisecond low-latency
mouse cursor motion, button press/release events, right clicks, and scrolling.
"""

import ctypes
import os
import sys
from typing import Tuple
import pyautogui

# Win32 Constants
INPUT_MOUSE = 0
MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_ABSOLUTE = 0x8000
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010
MOUSEEVENTF_MIDDLEDOWN = 0x0020
MOUSEEVENTF_MIDDLEUP = 0x0040
MOUSEEVENTF_WHEEL = 0x0800
MOUSEEVENTF_VIRTUALDESK = 0x4000

# Ctypes Structure Definitions for SendInput
class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", ctypes.c_long),
        ("dy", ctypes.c_long),
        ("mouseData", ctypes.c_ulong),
        ("dwFlags", ctypes.c_ulong),
        ("time", ctypes.c_ulong),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]

class _INPUT_UNION(ctypes.Union):
    _fields_ = [("mi", MOUSEINPUT)]

class INPUT(ctypes.Structure):
    _fields_ = [
        ("type", ctypes.c_ulong),
        ("u", _INPUT_UNION),
    ]


class Win32MouseBackend:
    """Ultra low-latency Windows SendInput API backend."""

    def __init__(self):
        self.is_windows = sys.platform == "win32"
        if self.is_windows:
            try:
                self.user32 = ctypes.windll.user32
                self.user32.SetProcessDPIAware()
            except Exception:
                self.user32 = None

    def move_to(self, x: int, y: int):
        """Moves cursor directly to (x, y) desktop pixel coordinate."""
        if self.is_windows and self.user32:
            try:
                self.user32.SetCursorPos(int(x), int(y))
                return
            except Exception:
                pass
        pyautogui.moveTo(x, y)

    def mouse_down(self, button: str = 'left'):
        """Sends physical mouse down event."""
        if self.is_windows and self.user32:
            try:
                flags = MOUSEEVENTF_LEFTDOWN if button == 'left' else MOUSEEVENTF_RIGHTDOWN
                inp = INPUT()
                inp.type = INPUT_MOUSE
                inp.u.mi.dwFlags = flags
                self.user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))
                return
            except Exception:
                pass
        pyautogui.mouseDown(button=button)

    def mouse_up(self, button: str = 'left'):
        """Sends physical mouse up event."""
        if self.is_windows and self.user32:
            try:
                flags = MOUSEEVENTF_LEFTUP if button == 'left' else MOUSEEVENTF_RIGHTUP
                inp = INPUT()
                inp.type = INPUT_MOUSE
                inp.u.mi.dwFlags = flags
                self.user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))
                return
            except Exception:
                pass
        pyautogui.mouseUp(button=button)

    def click(self, button: str = 'left'):
        """Sends physical single click (down + up)."""
        self.mouse_down(button)
        self.mouse_up(button)

    def scroll(self, clicks: int):
        """Sends vertical wheel scroll event."""
        if self.is_windows and self.user32:
            try:
                # Wheel delta: 120 per notch
                wheel_delta = int(clicks * 120)
                inp = INPUT()
                inp.type = INPUT_MOUSE
                inp.u.mi.dwFlags = MOUSEEVENTF_WHEEL
                inp.u.mi.mouseData = ctypes.c_ulong(wheel_delta & 0xFFFFFFFF)
                self.user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))
                return
            except Exception:
                pass
        pyautogui.scroll(clicks)
