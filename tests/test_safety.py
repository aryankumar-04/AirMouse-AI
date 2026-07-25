"""Unit tests for MouseController safety fail-safes and state management."""

import unittest
from config import MouseConfig, CalibrationConfig
from app.core.mouse_state import MouseState, MouseStateMachine
from app.control.calibration import CoordinateTransformer
from app.control.mouse_controller import MouseController


class TestSafety(unittest.TestCase):

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

    def test_default_mouse_control_disabled(self):
        self.assertFalse(self.controller.is_enabled())
        self.assertEqual(self.state_machine.get_state(), MouseState.DISABLED)

    def test_emergency_stop(self):
        self.controller.set_enabled(True)
        self.assertTrue(self.controller.is_enabled())

        # Trigger emergency stop
        self.controller.emergency_stop()
        self.assertFalse(self.controller.is_enabled())
        self.assertEqual(self.state_machine.get_state(), MouseState.DISABLED)

    def test_drag_release_on_disable(self):
        self.controller.set_enabled(True)
        self.state_machine.set_state(MouseState.DRAGGING)
        self.assertTrue(self.state_machine.is_dragging())

        self.controller.emergency_stop()
        self.assertFalse(self.state_machine.is_dragging())


if __name__ == "__main__":
    unittest.main()
