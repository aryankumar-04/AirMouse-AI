"""Unit tests for state management interactions."""

import unittest
from app.core.app_state import AppStateManager, AppState
from app.core.mouse_state import MouseStateMachine, MouseState


class TestUIState(unittest.TestCase):

    def test_app_state_transitions(self):
        state_mgr = AppStateManager()
        self.assertEqual(state_mgr.get_state(), AppState.STOPPED)

        state_mgr.set_state(AppState.RUNNING)
        self.assertTrue(state_mgr.is_running())

        state_mgr.set_state(AppState.ERROR, "Camera failure")
        self.assertTrue(state_mgr.is_error())
        self.assertEqual(state_mgr.get_error_message(), "Camera failure")

    def test_mouse_state_transitions(self):
        mouse_mgr = MouseStateMachine(initial_enabled=False)
        self.assertEqual(mouse_mgr.get_state(), MouseState.DISABLED)
        self.assertFalse(mouse_mgr.is_enabled())

        mouse_mgr.enable()
        self.assertTrue(mouse_mgr.is_enabled())
        self.assertEqual(mouse_mgr.get_state(), MouseState.IDLE)

        mouse_mgr.disable()
        self.assertFalse(mouse_mgr.is_enabled())
        self.assertEqual(mouse_mgr.get_state(), MouseState.DISABLED)


if __name__ == "__main__":
    unittest.main()
