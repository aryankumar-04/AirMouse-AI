<div align="center">

# AirMouse AI

**v1.0.0**

### AI-powered touchless desktop mouse controller for Windows

[![Version](https://img.shields.io/badge/version-v1.0.0-blue.svg)](https://github.com/aryankumar-04/AirMouse-AI)
[![Platform](https://img.shields.io/badge/platform-Windows%2010%2F11-0078D6.svg)](https://www.microsoft.com/windows)
[![Python](https://img.shields.io/badge/python-3.10%2B-3776AB.svg)](https://www.python.org/)
[![Privacy](https://img.shields.io/badge/privacy-100%25%20offline-16a34a.svg)](#privacy--security)
[![License](https://img.shields.io/badge/license-MIT-orange.svg)](LICENSE)

</div>

---

## Overview

**AirMouse AI** turns a standard webcam into a **real-time, touchless mouse controller** for Windows.

It lets you move the cursor, click, drag, right-click, and scroll using natural hand gestures — all running **fully locally** on your computer with **no paid APIs, no cloud services, no subscriptions, and no special hardware**.

Built with a focus on:
- clean UI
- low-latency interaction
- privacy-first processing
- safety and reliability
- beginner-friendly configuration
- professional desktop app structure

---

## Screenshots

### Dashboard
![Dashboard](assets/screenshots/dashboard.png)

### Gesture Guide
![Gesture Guide](assets/screenshots/gesture.png)

### Settings
![Settings](assets/screenshots/settings.png)

### About
![About](assets/screenshots/about.png)

---

## Key Features

- **Point & Move (Hover Mode)** — control the cursor naturally with your hand
- **Left Click (Pinch Tap)** — perform a clean single click
- **Drag & Drop (Pinch & Hold)** — click and hold for dragging files, text, and windows
- **Right Click (Thumb + Middle)** — open context menus reliably
- **Scroll Up & Down (Two-Finger Mode)** — scroll documents and pages
- **Neutral / Pause Mode (Open Palm)** — safely pause movement without closing the app
- **Emergency Safety Stop (Fist)** — instantly stop tracking and control
- **Fully Offline** — all processing stays on your device
- **Customizable Settings** — tune sensitivity, smoothing, thresholds, and behavior
- **Professional UI** — dashboard, gesture guide, settings, about page, and logs
- **Windows Desktop Ready** — designed for a clean local desktop experience

---

## How It Works

AirMouse AI uses a simple pipeline:

1. **Webcam captures the hand**
2. **MediaPipe detects landmarks**
3. **Gesture engine classifies the pose**
4. **Gesture mapper converts pose to action**
5. **Mouse controller moves/clicks/scrolls**
6. **UI updates status and feedback**

The system is designed to keep motion smooth, reduce jitter, and prevent accidental actions.

---

## Gesture Guide

| Gesture | Mode | Action |
|---|---|---|
| ☝️ Index finger up | **Point & Move** | Moves the cursor |
| 👌 Thumb + index pinch tap | **Left Click** | Single click |
| ✊ Thumb + index pinch and hold | **Drag & Drop** | Hold and drag |
| 🤞 Thumb + middle pinch | **Right Click** | Context menu click |
| ✌️ Index + middle fingers up | **Scroll Up & Down** | Scroll mode |
| 🖐️ Open palm | **Neutral / Pause Mode** | Pause movement |
| 👊 Fist | **Emergency Safety Stop** | Stop tracking immediately |

---

## Tech Stack

- **Python**
- **OpenCV**
- **MediaPipe**
- **NumPy**
- **Tkinter / TTK**
- **Windows native input backend**
- **PyAutoGUI** where applicable
- **PyInstaller** for packaging

---

## Project Structure

```text
AirMouse AI/
├── app/
│   ├── core/
│   ├── control/
│   ├── ui/
│   ├── utils/
│   └── vision/
├── assets/
│   ├── icons/
│   └── screenshots/
├── data/
├── logs/
├── models/
├── release/
├── scripts/
├── tests/
├── config.py
├── main.py
├── requirements.txt
├── README.md
├── CHANGELOG.md
├── LICENSE
└── airmouse_ai.spec
