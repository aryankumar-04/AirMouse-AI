"""Integration tests for MouseController."""

import unittest
from config import MouseConfig, CalibrationConfig
from app.control.calibration import CoordinateTransformer
from app.control.mouse_controller import MouseController
from app.core.mouse_state import MouseState, MouseStateMachine
from app.core.gesture_state import GestureEvent, GestureState
from app.control.gesture_mapper import MappedAction, ActionIntent
from app.vision.gesture_engine import GestureEngineOutput


class TestMouseControllerIntegration(unittest.TestCase):

    def setUp(self):
        self.mouse_cfg = MouseConfig(enabled=False)
        self.cal_cfg = CalibrationConfig(screen_width=1000, screen_height=1000)
        self.transformer = CoordinateTransformer(self.cal_cfg, self.mouse_cfg)
        self.state_machine = MouseStateMachine(initial_enabled=False)
        self.controller = MouseController(
            mouse_config=self.mouse_cfg,
            transformer=self.transformer,
            state_machine=self.state_machine
        )

    def test_process_ignores_when_disabled(self):
        evt = GestureEvent(
            state=GestureState.POINTING,
            handedness="Right",
            confidence=0.9,
            pinch_distance=0.5,
            index_tip_pos=(320, 240)
        )
        action = MappedAction(action=ActionIntent.ACTION_HOVER, event=evt)
        output = GestureEngineOutput(event=evt, mapped_action=action)

        # Process should do nothing physical when disabled
        self.controller.process(output, (640, 480))
        self.assertEqual(self.state_machine.get_state(), MouseState.DISABLED)

    def test_right_click_execution(self):
        from unittest.mock import MagicMock
        self.controller.set_enabled(True)
        self.controller.win32_backend.click = MagicMock()
        self.controller.win32_backend.move_to = MagicMock()

        # Step 1: Right Pinch Start gesture
        evt1 = GestureEvent(
            state=GestureState.RIGHT_PINCH_START,
            handedness="Right",
            confidence=0.9,
            pinch_distance=0.5,
            index_tip_pos=(320, 240)
        )
        action1 = MappedAction(action=ActionIntent.ACTION_SECONDARY_CLICK, event=evt1)
        output1 = GestureEngineOutput(event=evt1, mapped_action=action1, anchor_pos=(0.5, 0.5))

        self.controller.process(output1, (640, 480))
        self.assertTrue(self.controller._right_pinch_active)

        # Step 2: Release right pinch -> should trigger right click
        evt2 = GestureEvent(
            state=GestureState.RIGHT_PINCH_RELEASE,
            handedness="Right",
            confidence=0.9,
            pinch_distance=0.5,
            index_tip_pos=(320, 240)
        )
        action2 = MappedAction(action=ActionIntent.ACTION_HOVER, event=evt2)
        output2 = GestureEngineOutput(event=evt2, mapped_action=action2, anchor_pos=(0.5, 0.5))

        self.controller.process(output2, (640, 480))
        self.assertFalse(self.controller._right_pinch_active)
        self.controller.win32_backend.click.assert_called_with('right')


if __name__ == "__main__":
    unittest.main()
