# AirMouse AI - Version History & Release Notes

## [v1.0.0] - Production Release

### Initial Release Highlights

- **Webcam Capture Foundation (Phase 1)**:
  - Non-blocking threaded OpenCV camera acquisition (`cv2.CAP_DSHOW` optimized for Windows).
  - Graceful reconnection, camera error logging, and resource cleanup.

- **Hand Landmark Tracking & Gesture Engine (Phase 2)**:
  - 21-point 3D landmark tracking powered by MediaPipe.
  - Scale-invariant geometry calculations (invariant to hand distance from webcam).
  - Anti-jitter Exponential Moving Average (EMA) landmark filtering.
  - State machine with $N$-frame debouncing and pinch hysteresis.
  - Recognized pose vocabulary: `OPEN_PALM`, `POINTING`, `PINCH_START`/`HOLD`/`RELEASE`, `TWO_FINGER`, `FIST`, `NO_HAND`.

- **Real OS Mouse Control & Calibration (Phase 3)**:
  - PyAutoGUI integration for zero-lag cursor movement (`moveTo`), left clicks, drag-and-drop (`mouseDown`/`mouseUp`), and right clicks (`rightClick`).
  - Screen coordinate transformer with 15% workspace edge margins and horizontal coordinate mirroring.
  - Emergency safety stop button and PyAutoGUI corner failsafes.

- **Production Control Center UI & Settings (Phase 4)**:
  - Tabbed interface: 📊 Dashboard, ⚙️ Settings & Calibration, 📘 Help & Onboarding Guide, 📜 Real-Time System Diagnostics Log View.
  - Persistent JSON settings (`data/settings.json`) saving user preferences automatically.
  - Live status bar displaying resolution, FPS, and mouse state.

- **Packaging & Delivery (Phase 5)**:
  - PyAutoGUI, OpenCV, Pillow, MediaPipe, and NumPy bundled into a standalone Windows executable.
  - 41 automated unit and integration tests passing cleanly.
  - Standalone versioned release directory generated at `release/AirMouseAI-v1.0.0/`.
