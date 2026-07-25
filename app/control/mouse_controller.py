"""
AirMouse AI - Physical Mouse Controller Module.

Executes system cursor movement, clicks, dragging, and scrolling using Win32 native SendInput API.
Includes click-freeze target preservation, palm tremor suppression, safety fail-safes,
click cooldowns, edge-triggered clicks, and automatic drag state cleanup.
"""

import logging
import math
import time
from typing import Optional, Tuple
import pyautogui

from config import MouseConfig
from app.core.gesture_state import GestureState, TransitionType
from app.core.mouse_state import MouseState, MouseStateMachine
from app.control.gesture_mapper import ActionIntent, MappedAction
from app.control.calibration import CoordinateTransformer
from app.control.win32_mouse import Win32MouseBackend
from app.vision.gesture_engine import GestureEngineOutput
from app.utils.timing import CooldownTimer


class MouseController:
    """Executes physical Windows mouse commands based on gesture pipeline outputs."""

    def __init__(
        self,
        mouse_config: MouseConfig,
        transformer: CoordinateTransformer,
        state_machine: Optional[MouseStateMachine] = None,
        logger: Optional[logging.Logger] = None
    ):
        self.config = mouse_config
        self.transformer = transformer
        self.state_machine = state_machine or MouseStateMachine(initial_enabled=mouse_config.enabled)
        self.logger = logger or logging.getLogger("AirMouseAI.MouseController")

        self.win32_backend = Win32MouseBackend()
        self.click_cooldown = CooldownTimer(cooldown_ms=mouse_config.click_cooldown_ms)
        self.right_click_cooldown = CooldownTimer(cooldown_ms=getattr(mouse_config, 'right_click_cooldown_ms', 400))
        self._last_scroll_y: Optional[int] = None
        self._pinch_start_time: float = 0.0
        self._pinch_active: bool = False
        self._pinch_cancelled: bool = False

        # Click-Freeze Target Preservation state variables
        self._click_freeze_pos: Optional[Tuple[int, int]] = None
        self._click_freeze_time: float = 0.0

        # Right-Click Hold State
        self._right_click_start_time: float = 0.0
        self._right_pinch_active: bool = False

        # Configure PyAutoGUI settings for safety fallback
        pyautogui.PAUSE = 0.001
        pyautogui.FAILSAFE = mouse_config.failsafe

    def set_enabled(self, enabled: bool):
        """Enables or disables master mouse control."""
        if enabled:
            self.logger.debug("Master Mouse Control ENABLED.")
            self.state_machine.enable()
        else:
            self.logger.debug("Master Mouse Control DISABLED.")
            self.emergency_stop()

    def is_enabled(self) -> bool:
        """Returns True if master mouse control is enabled."""
        return self.state_machine.is_enabled()

    def process(self, gesture_output: GestureEngineOutput, frame_dimensions: Tuple[int, int]):
        """Processes frame gesture output into physical mouse action execution using Click Decision State Machine."""
        if not self.state_machine.is_enabled():
            return

        event = gesture_output.event
        action = gesture_output.mapped_action.action
        now = time.time()

        # Handle tracking loss or disable gesture immediately
        if event.state in (GestureState.NO_HAND, GestureState.FIST) or action == ActionIntent.ACTION_DISABLE:
            if self.state_machine.is_dragging():
                self._release_drag()
            self._last_scroll_y = None
            self._pinch_active = False
            self._pinch_cancelled = False
            self._click_freeze_pos = None
            self._right_click_start_time = 0.0
            self._right_pinch_active = False
            self.transformer.reset()
            self.state_machine.set_state(MouseState.PAUSED)
            return

        # Extract rigid palm-backed control anchor (cx, cy)
        anchor_pos = getattr(gesture_output, 'anchor_pos', (0.5, 0.5))

        # 1. Transform camera anchor coordinates to screen pixel coordinates
        raw_screen_x, raw_screen_y = self.transformer.transform(anchor_pos, frame_dimensions)

        # 2. Check Click-Freeze Target Preservation status
        freeze_duration_ms = getattr(self.config, 'click_freeze_duration_ms', 250)
        is_freeze_active = (
            self._click_freeze_pos is not None and
            ((now - self._click_freeze_time) * 1000.0) < freeze_duration_ms
        )

        if is_freeze_active:
            screen_x, screen_y = self._click_freeze_pos
        else:
            screen_x, screen_y = raw_screen_x, raw_screen_y
            if not self._pinch_active and event.state not in (GestureState.PINCH_START, GestureState.PINCH_HOLD):
                self._click_freeze_pos = None

        try:
            # 3. Execute Mouse Actions via Click Decision State Machine

            # --- LEFT CLICK / DRAG (Click Decision State Machine) ---
            if action == ActionIntent.ACTION_PRIMARY_CLICK:
                self._last_scroll_y = None
                self._right_click_start_time = 0.0
                self._right_pinch_active = False

                if event.state in (GestureState.PINCH_START, GestureState.PINCH_HOLD):
                    if not self._pinch_active:
                        # Rising edge of pinch candidate: Lock hover target to prevent drift during pinch closure
                        self._pinch_active = True
                        self._pinch_cancelled = False
                        self._pinch_start_time = now
                        self._click_freeze_pos = (raw_screen_x, raw_screen_y)
                        self._click_freeze_time = now
                        self.state_machine.set_state(MouseState.CLICK_CANDIDATE)

                    pinch_duration_ms = (now - self._pinch_start_time) * 1000.0
                    drag_duration_threshold = getattr(self.config, 'drag_hold_duration_ms', 280)
                    cancel_threshold = getattr(self.config, 'motion_cancel_threshold_px', 75.0)

                    # Movement-based Click Cancellation check
                    if self._click_freeze_pos is not None and not self.state_machine.is_dragging():
                        freeze_x, freeze_y = self._click_freeze_pos
                        movement_from_target = math.hypot(raw_screen_x - freeze_x, raw_screen_y - freeze_y)
                        if movement_from_target > cancel_threshold:
                            # Large hand displacement during candidate window -> cancel click decision!
                            self._pinch_cancelled = True
                            self._click_freeze_pos = None

                    if self._pinch_cancelled:
                        # Candidate cancelled by large motion -> move cursor normally without clicking/dragging
                        self.win32_backend.move_to(raw_screen_x, raw_screen_y)
                        self.state_machine.set_state(MouseState.MOVE)
                        self.state_machine.update_cursor_pos(raw_screen_x, raw_screen_y)

                    elif pinch_duration_ms >= drag_duration_threshold:
                        # Pinch held longer than hold threshold -> Engage Drag & Drop & un-freeze cursor motion
                        self._click_freeze_pos = None
                        if not self.state_machine.is_dragging():
                            self.win32_backend.move_to(raw_screen_x, raw_screen_y)
                            self.win32_backend.mouse_down('left')
                            self.state_machine.set_state(MouseState.DRAG_ACTIVE)
                        else:
                            self.win32_backend.move_to(raw_screen_x, raw_screen_y)
                            self.state_machine.update_cursor_pos(raw_screen_x, raw_screen_y)
                    else:
                        # During initial candidate window, hold cursor strictly frozen at initial target
                        target_x, target_y = self._click_freeze_pos if self._click_freeze_pos else (raw_screen_x, raw_screen_y)
                        self.win32_backend.move_to(target_x, target_y)
                        self.state_machine.set_state(MouseState.CLICK_FROZEN)

            # --- RIGHT CLICK INITIATION ---
            elif action == ActionIntent.ACTION_SECONDARY_CLICK:
                if self.state_machine.is_dragging():
                    self._release_drag()
                self._last_scroll_y = None
                self._pinch_active = False

                if event.state in (GestureState.RIGHT_PINCH_START, GestureState.RIGHT_PINCH_HOLD, GestureState.THREE_FINGER):
                    if not self._right_pinch_active:
                        self._right_pinch_active = True
                        self._right_click_start_time = now
                        # Freeze cursor during right-pinch / three-finger to prevent drift
                        self._click_freeze_pos = (raw_screen_x, raw_screen_y)
                        self._click_freeze_time = now

                    # Freeze cursor position while holding right click gesture
                    target_x, target_y = self._click_freeze_pos if self._click_freeze_pos else (raw_screen_x, raw_screen_y)
                    self.win32_backend.move_to(target_x, target_y)

            # --- SCROLL ---
            elif action == ActionIntent.ACTION_SCROLL:
                if self.state_machine.is_dragging():
                    self._release_drag()
                self._pinch_active = False
                self._click_freeze_pos = None
                self._right_click_start_time = 0.0
                self._right_pinch_active = False

                self.win32_backend.move_to(screen_x, screen_y)
                self.state_machine.update_cursor_pos(screen_x, screen_y)

                if self._last_scroll_y is not None:
                    dy = screen_y - self._last_scroll_y
                    scroll_min_delta = getattr(self.config, 'scroll_min_delta_px', 8)
                    if abs(dy) >= scroll_min_delta:
                        # Adaptive scroll: scale sensitivity by hand speed
                        scroll_clicks = int(-dy * (self.config.scroll_sensitivity / 18.0))
                        if scroll_clicks != 0:
                            self.win32_backend.scroll(scroll_clicks)
                            self.state_machine.set_state(MouseState.SCROLLING)

                self._last_scroll_y = screen_y

            # Handle pinch release -> decide between tap-click vs drag release
            if self._pinch_active and event.state not in (GestureState.PINCH_START, GestureState.PINCH_HOLD):
                pinch_duration_ms = (now - self._pinch_start_time) * 1000.0
                drag_duration_threshold = getattr(self.config, 'drag_hold_duration_ms', 280)

                if self.state_machine.is_dragging():
                    # Release drag & drop
                    self._release_drag()
                elif not self._pinch_cancelled and pinch_duration_ms < drag_duration_threshold and self.click_cooldown.is_ready():
                    # Quick pinch tap (< hold threshold) -> execute single left click AT frozen hover target
                    click_x, click_y = self._click_freeze_pos if self._click_freeze_pos else (screen_x, screen_y)
                    self.win32_backend.move_to(click_x, click_y)
                    self.win32_backend.click('left')
                    self.logger.info(f"LEFT CLICK executed at ({click_x}, {click_y})")
                    self.state_machine.set_state(MouseState.CLICKED)
                    self.state_machine.register_click()
                    self.click_cooldown.trigger()

                self._pinch_active = False
                self._pinch_cancelled = False
                self._click_freeze_pos = None

            # Handle right pinch release -> fire right click
            if self._right_pinch_active and event.state not in (GestureState.RIGHT_PINCH_START, GestureState.RIGHT_PINCH_HOLD, GestureState.THREE_FINGER):
                if self.right_click_cooldown.is_ready():
                    click_x, click_y = self._click_freeze_pos if self._click_freeze_pos else (screen_x, screen_y)
                    self.win32_backend.move_to(click_x, click_y)
                    self.win32_backend.click('right')
                    self.logger.info(f"RIGHT CLICK executed at ({click_x}, {click_y})")
                    self.state_machine.set_state(MouseState.CLICKED)
                    self.state_machine.register_click()
                    self.right_click_cooldown.trigger()
                self._right_pinch_active = False
                self._click_freeze_pos = None

            # --- HOVER / POINTING (executed when no pinch/right-pinch is actively holding or releasing) ---
            if action in (ActionIntent.ACTION_HOVER, ActionIntent.ACTION_NONE) and not self._pinch_active and not self._right_pinch_active:
                if self.state_machine.is_dragging():
                    self._release_drag()
                self._last_scroll_y = None

                if not is_freeze_active:
                    self._click_freeze_pos = None
                    self.win32_backend.move_to(screen_x, screen_y)
                    self.state_machine.set_state(MouseState.MOVE)
                    self.state_machine.update_cursor_pos(screen_x, screen_y)

        except pyautogui.FailSafeException:
            self.logger.critical("PyAutoGUI Failsafe triggered! Screen corner hit. Disabling mouse control.")
            self.emergency_stop()
        except Exception as err:
            self.logger.error(f"Error executing mouse command: {err}")
            self.emergency_stop()

    def _release_drag(self):
        """Safely releases left mouse button."""
        try:
            self.win32_backend.mouse_up('left')
            self.state_machine.set_state(MouseState.IDLE)
        except Exception as err:
            self.logger.warning(f"Error releasing mouse button: {err}")

    def emergency_stop(self):
        """Instantly stops mouse control and releases any active drag states."""
        self.logger.info("Emergency Stop triggered!")
        try:
            self.win32_backend.mouse_up('left')
            self.win32_backend.mouse_up('right')
        except Exception:
            pass
        self._last_scroll_y = None
        self._pinch_active = False
        self._click_freeze_pos = None
        self._right_click_start_time = 0.0
        self._right_pinch_active = False
        self.state_machine.disable()
        self.transformer.reset()

