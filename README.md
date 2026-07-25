<div align="center">

<img src="assets/logo_clean.png" alt="AirMouse AI Logo" width="128"/>

# AirMouse AI

### Touchless Desktop Mouse Controller & Hand-Gesture Automation for Windows

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows%2010%20%2F%2011%20(x64)-0078D6.svg)](https://www.microsoft.com/windows)
[![Offline](https://img.shields.io/badge/Privacy-100%25%20Offline-047857.svg)](#privacy--security)
[![Tests](https://img.shields.io/badge/Tests-48%2F48%20Passing-10B981.svg)](#development--testing)

**AirMouse AI** turns any standard webcam into a high-precision, low-latency touchless mouse controller. Move your cursor fluidly across your desktop, perform left clicks, right clicks, drag & drop operations, and scroll pages using intuitive, natural hand gestures.

Engineered to run **100% locally** on your computer with complete privacy, zero internet requirement, and no extra hardware.

</div>

---

## 🌟 Key Features

* **🖱️ Natural Motion Control**: Move your hand in front of your camera to guide your OS mouse cursor like a physical trackpad.
* **🎯 High-Precision Pinches**: Trigger single left-clicks, double clicks, and drag & drop operations with tight pinch hysteresis.
* **✌️ Two-Finger Scroll Mode**: Move two fingers up or down to scroll documents, web pages, and applications smoothly.
* **🔒 100% Local & Private**: All computer vision model inference executes on your local CPU. Zero webcam frames, data, or telemetry ever leave your device.
* **⚡ One Euro Tremor Filter**: Eliminates hand jitter at rest while keeping fast motion sweeps instant and lag-free.
* **🛡️ Clutch Safety & Fail-safes**: Automatic position freeze on tracking loss and instant PyAutoGUI screen-corner emergency stops.
* **⚙️ Customizable Settings**: Fine-tune gesture thresholds, cursor smoothing, motion deadzones, and workspace edge margins with instant persistence.
* **💻 Modern Desktop Interface**: Commercial-grade Tkinter/TTK UI with Dashboard telemetry, Settings panel, Illustrated Gesture Guide, and System Log Console.

---

## 🖐️ Hand Gesture Controls Cheat Sheet

| Gesture Icon | Hand Pose | Mapped Action | How to Perform |
| :---: | :--- | :--- | :--- |
| ☝️ | **Index Finger Alone** | **Point & Move** *(Hover Mode)* | Hold up your Index finger alone to move the cursor across the screen. |
| 👌 | **Thumb + Index Pinch Tap** | **Left Click** | Briefly pinch Thumb + Index fingertips together and release. |
| ✊ | **Thumb + Index Pinch & Hold** | **Drag & Drop** | Pinch Thumb + Index together and hold closed while moving your hand. |
| 🤞 | **Thumb + Middle Pinch** | **Right Click** | Pinch Thumb + Middle fingertips together to open context menus. |
| ✌️ | **Index + Middle Extended** | **Scroll Up & Down** | Move your hand up to scroll up, or down to scroll down. |
| 🖐️ | **Open Palm (5 Fingers)** | **Neutral / Pause Mode** | Spread all 5 fingers open to pause mouse movement safely. |
| 👊 | **Closed Fist** | **Emergency Safety Stop** | Close all fingers into a fist to instantly disable tracking. |

---

## 🖥️ System Requirements

* **Operating System**: Windows 10 or Windows 11 (64-bit)
* **Python Runtime**: Python 3.10 or higher
* **Webcam**: Any integrated laptop camera or standard USB webcam (720p or 1080p recommended)
* **CPU**: Intel Core i3 / AMD Ryzen 3 or higher (no GPU required)

---

## 🚀 Quick Start Guide

### 1. Clone Repository
```powershell
git clone https://github.com/your-username/AirMouse-AI.git
cd AirMouse-AI
```

### 2. Create Virtual Environment (Recommended)
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 4. Run Application
```powershell
python main.py
```

---

## 📁 Repository Structure

```text
AirMouse-AI/
├── main.py                  # Main application entry point
├── config.py                # Configuration dataclasses & baseline defaults
├── requirements.txt         # Python package dependencies
├── LICENSE                  # MIT Open Source License
├── README.md                # Project documentation & user guide
├── CHANGELOG.md             # Version history & release notes
├── assets/                  # High-resolution logos, icons, and gesture photos
│   ├── logo.png
│   ├── app_icon.ico
│   └── gestures/            # Custom gesture reference photos
├── models/
│   └── hand_landmarker.task # MediaPipe Hand Landmarker task bundle
├── data/
│   └── settings.json        # Persistent user preferences & configuration
├── app/                     # Core application source code
│   ├── core/                # State containers, logger, and SettingsManager
│   ├── vision/              # Camera manager, hand tracker, and gesture engine
│   ├── control/             # Win32 SendInput controller, mouse mapper, calibration
│   ├── ui/                  # Dashboard, Settings, Gesture Guide, Logs, Navigation
│   └── utils/               # File I/O, validation, geometry, smoothing filters
└── tests/                   # Complete unit test suite (48 tests)
```

---

## 🧪 Development & Testing

AirMouse AI includes a comprehensive test suite covering geometry, smoothing filters, state machines, calibration, and settings persistence.

Run unit tests:
```powershell
python -m unittest discover tests
```

---

## 🛡️ Privacy & Security Architecture

AirMouse AI was built with privacy as a foundational principle:

* **Zero Cloud Dependence**: Operates completely offline without external network calls.
* **No Video Persistence**: Camera frames are processed strictly in memory for landmark extraction and discarded immediately.
* **No Telemetry**: No user analytics, error reports, or telemetry metrics are collected or transmitted.

---

## 📜 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

## 🙏 Credits & Acknowledgments

* **[Google MediaPipe](https://developers.google.com/mediapipe)** — Hand Landmarker ML model.
* **[OpenCV](https://opencv.org/)** — Real-time computer vision and camera stream capture.
* **[PyAutoGUI](https://pyautogui.readthedocs.io/)** — OS mouse control & safety emergency stops.
* **[Python Software Foundation](https://www.python.org/)** — Python runtime ecosystem.

---

<div align="center">
  <sub>Made with ❤️ by the AirMouse AI Team</sub>
</div>
