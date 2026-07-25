"""
AirMouse AI - Gesture State Machine & Event Data Structures.

Defines the GestureState enum, GestureEvent output dataclass, and the state machine
managing debouncing, hysteresis, and clean state transitions.
"""

from dataclasses import dataclass, field
from enum import Enum, auto
import time
from typing import Optional, Tuple

from config import GestureConfig
from app.utils.timing import Debouncer, CooldownTimer


class GestureState(Enum):
    """Enumeration of recognizable hand gesture states."""
    NO_HAND = auto()
    OPEN_PALM = auto()
    POINTING = auto()
    PINCH_START = auto()
    PINCH_HOLD = auto()
    PINCH_RELEASE = auto()
    RIGHT_PINCH_START = auto()
    RIGHT_PINCH_HOLD = auto()
    RIGHT_PINCH_RELEASE = auto()
    TWO_FINGER = auto()
    THREE_FINGER = auto()
    FIST = auto()
    UNKNOWN = auto()


class TransitionType(Enum):
    """Gesture state transition type."""
    ENTER = auto()
    HOLD = auto()
    EXIT = auto()


@dataclass
class GestureEvent:
    """Structured event emitted by the gesture engine for downstream consumers."""
    state: GestureState
    handedness: str
    confidence: float
    pinch_distance: float
    index_tip_pos: Tuple[int, int]
    right_pinch_distance: float = 1.0
    hand_velocity: float = 0.0
    timestamp: float = field(default_factory=time.time)
    is_stable: bool = True
    transition_type: TransitionType = TransitionType.HOLD
    stability_count: int = 1


class GestureStateMachine:
    """State machine governing gesture transitions, debouncing, and pinch hysteresis."""

    def __init__(self, config: GestureConfig):
        self.config = config
        self.current_state = GestureState.NO_HAND
        self.previous_state = GestureState.NO_HAND

        self.debouncer = Debouncer(
            required_frames=config.stability_frames,
            default_value=GestureState.NO_HAND
        )
        self.cooldown_timer = CooldownTimer(cooldown_ms=config.cooldown_ms)

        self._in_pinch = False
        self._in_right_pinch = False

    def update(
        self,
        candidate_state: GestureState,
        pinch_distance: float,
        handedness: str,
        confidence: float,
        index_tip_pos: Tuple[int, int],
        right_pinch_distance: float = 1.0,
        hand_velocity: float = 0.0
    ) -> GestureEvent:
        """Processes candidate pose classification through state machine logic."""
        now = time.time()

        max_vel = getattr(self.config, 'max_click_velocity', 0.9)
        is_moving_too_fast = hand_velocity > max_vel

        # 1. Left Pinch (Thumb + Index) Hysteresis Logic
        #    Only applies when candidate is compatible with left-pinch AND right-pinch is NOT active
        if not self._in_right_pinch:
            if candidate_state in (GestureState.POINTING, GestureState.OPEN_PALM, GestureState.PINCH_START, GestureState.PINCH_HOLD):
                if not self._in_pinch and pinch_distance < self.config.pinch_threshold:
                    if not is_moving_too_fast:
                        candidate_state = GestureState.PINCH_START
                elif self._in_pinch:
                    if pinch_distance > self.config.pinch_release_threshold:
                        candidate_state = GestureState.PINCH_RELEASE
                        self._in_pinch = False
                    else:
                        candidate_state = GestureState.PINCH_HOLD

        # 2. Right Pinch (Thumb + Middle) Hysteresis Logic
        #    Only applies when left-pinch is NOT active
        right_thresh = getattr(self.config, 'right_pinch_threshold', 0.22)
        right_rel_thresh = getattr(self.config, 'right_pinch_release_threshold', 0.40)

        if not self._in_pinch:
            if candidate_state in (GestureState.POINTING, GestureState.OPEN_PALM, GestureState.TWO_FINGER,
                                   GestureState.UNKNOWN, GestureState.RIGHT_PINCH_START, GestureState.RIGHT_PINCH_HOLD,
                                   GestureState.THREE_FINGER):
                if not self._in_right_pinch and right_pinch_distance < right_thresh:
                    if not is_moving_too_fast:
                        candidate_state = GestureState.RIGHT_PINCH_START
                elif self._in_right_pinch:
                    if right_pinch_distance > right_rel_thresh:
                        candidate_state = GestureState.RIGHT_PINCH_RELEASE
                        self._in_right_pinch = False
                    else:
                        candidate_state = GestureState.RIGHT_PINCH_HOLD

        # Apply debouncing across N frames
        stable_state, state_changed = self.debouncer.update(candidate_state)
        stability_count = self.debouncer.get_stability_count()

        # State transition processing
        transition = TransitionType.HOLD

        if state_changed:
            if stable_state == GestureState.PINCH_START:
                self._in_pinch = True
            elif stable_state == GestureState.PINCH_RELEASE:
                self._in_pinch = False
            elif stable_state == GestureState.RIGHT_PINCH_START:
                self._in_right_pinch = True
            elif stable_state == GestureState.RIGHT_PINCH_RELEASE:
                self._in_right_pinch = False

            transition = TransitionType.ENTER
            self.previous_state = self.current_state
            self.current_state = stable_state
            self.cooldown_timer.trigger()

        elif self.current_state != stable_state:
            self.current_state = stable_state

        return GestureEvent(
            state=self.current_state,
            handedness=handedness,
            confidence=confidence,
            pinch_distance=pinch_distance,
            index_tip_pos=index_tip_pos,
            right_pinch_distance=right_pinch_distance,
            hand_velocity=hand_velocity,
            timestamp=now,
            is_stable=(stability_count >= self.config.stability_frames),
            transition_type=transition,
            stability_count=stability_count
        )

    def reset(self):
        """Resets state machine state."""
        self.current_state = GestureState.NO_HAND
        self.previous_state = GestureState.NO_HAND
        self._in_pinch = False
        self._in_right_pinch = False
        self.debouncer.reset(GestureState.NO_HAND)
        self.cooldown_timer.reset()

