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


if __name__ == "__main__":
    unittest.main()
