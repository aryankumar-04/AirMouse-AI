"""
AirMouse AI - Gesture Mapper Abstraction Module.

Maps high-level GestureEvents to abstract ActionIntents, establishing a clean,
decoupled contract for Mouse Automation with strict action priority.
"""

from dataclasses import dataclass, field
from enum import Enum, auto
import time
from typing import Optional

from app.core.gesture_state import GestureEvent, GestureState


class ActionIntent(Enum):
    """Abstract system actions mapped from gesture states."""
    ACTION_NONE = auto()
    ACTION_HOVER = auto()
    ACTION_PRIMARY_CLICK = auto()
    ACTION_SECONDARY_CLICK = auto()
    ACTION_SCROLL = auto()
    ACTION_DISABLE = auto()


@dataclass
class MappedAction:
    """Action intent wrapper containing gesture event context."""
    action: ActionIntent
    event: GestureEvent
    timestamp: float = field(default_factory=time.time)

    def is_active(self) -> bool:
        """Returns True if action is not NONE or DISABLE."""
        return self.action in (
            ActionIntent.ACTION_HOVER,
            ActionIntent.ACTION_PRIMARY_CLICK,
            ActionIntent.ACTION_SECONDARY_CLICK,
            ActionIntent.ACTION_SCROLL
        )


class GestureMapper:
    """Decouples gesture classification from physical system actions."""

    def __init__(self):
        self._current_action = ActionIntent.ACTION_NONE

    def map_event(self, event: GestureEvent) -> MappedAction:
        """Translates a GestureEvent into a high-level MappedAction intent with strict priority."""
        if not event or event.state in (GestureState.NO_HAND, GestureState.FIST):
            action = ActionIntent.ACTION_DISABLE
        elif event.state == GestureState.OPEN_PALM:
            action = ActionIntent.ACTION_NONE
        elif event.state in (GestureState.PINCH_START, GestureState.PINCH_HOLD):
            action = ActionIntent.ACTION_PRIMARY_CLICK
        elif event.state in (GestureState.RIGHT_PINCH_START, GestureState.RIGHT_PINCH_HOLD, GestureState.THREE_FINGER):
            action = ActionIntent.ACTION_SECONDARY_CLICK
        elif event.state == GestureState.TWO_FINGER:
            action = ActionIntent.ACTION_SCROLL
        elif event.state == GestureState.POINTING:
            action = ActionIntent.ACTION_HOVER
        else:
            action = ActionIntent.ACTION_NONE

        self._current_action = action
        return MappedAction(action=action, event=event, timestamp=time.time())

    def get_current_action(self) -> ActionIntent:
        """Returns current mapped action intent."""
        return self._current_action
