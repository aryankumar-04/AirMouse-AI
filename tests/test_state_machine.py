"""Unit tests for GestureStateMachine and debouncer stability."""

import unittest
from config import GestureConfig
from app.core.gesture_state import GestureState, GestureStateMachine, TransitionType


class TestStateMachine(unittest.TestCase):

    def setUp(self):
        self.config = GestureConfig(
            stability_frames=3,
            pinch_threshold=0.25,
            pinch_release_threshold=0.38
        )
        self.state_machine = GestureStateMachine(config=self.config)

    def test_initial_state_is_no_hand(self):
        self.assertEqual(self.state_machine.current_state, GestureState.NO_HAND)

    def test_debouncer_requires_consecutive_frames(self):
        # Frame 1: Candidate = POINTING
        evt1 = self.state_machine.update(
            candidate_state=GestureState.POINTING,
            pinch_distance=0.6,
            handedness="Right",
            confidence=0.9,
            index_tip_pos=(320, 240)
        )
        # Should stay NO_HAND until 3 consecutive frames are evaluated
        self.assertEqual(evt1.state, GestureState.NO_HAND)
        self.assertFalse(evt1.is_stable)

        # Frame 2
        evt2 = self.state_machine.update(
            candidate_state=GestureState.POINTING,
            pinch_distance=0.6,
            handedness="Right",
            confidence=0.9,
            index_tip_pos=(320, 240)
        )
        self.assertEqual(evt2.state, GestureState.NO_HAND)

        # Frame 3 (3rd frame -> confirms POINTING)
        evt3 = self.state_machine.update(
            candidate_state=GestureState.POINTING,
            pinch_distance=0.6,
            handedness="Right",
            confidence=0.9,
            index_tip_pos=(320, 240)
        )
        self.assertEqual(evt3.state, GestureState.POINTING)
        self.assertTrue(evt3.is_stable)
        self.assertEqual(evt3.transition_type, TransitionType.ENTER)

    def test_pinch_hysteresis_enter_and_exit(self):
        # Stabilize in POINTING first
        for _ in range(3):
            self.state_machine.update(
                candidate_state=GestureState.POINTING,
                pinch_distance=0.6,
                handedness="Right",
                confidence=0.9,
                index_tip_pos=(320, 240)
            )
        self.assertEqual(self.state_machine.current_state, GestureState.POINTING)

        # Bring pinch distance below pinch_threshold (0.20 < 0.25)
        for _ in range(3):
            evt = self.state_machine.update(
                candidate_state=GestureState.POINTING,
                pinch_distance=0.20,
                handedness="Right",
                confidence=0.9,
                index_tip_pos=(320, 240)
            )
        # State should switch to PINCH_START / PINCH_HOLD
        self.assertIn(evt.state, (GestureState.PINCH_START, GestureState.PINCH_HOLD))

        # Intermediate distance (0.30) - between 0.25 and 0.38 - should hold pinch (hysteresis!)
        for _ in range(3):
            evt_hold = self.state_machine.update(
                candidate_state=GestureState.POINTING,
                pinch_distance=0.30,
                handedness="Right",
                confidence=0.9,
                index_tip_pos=(320, 240)
            )
        self.assertEqual(evt_hold.state, GestureState.PINCH_HOLD)

        # Increase distance above pinch_release_threshold (0.40 > 0.38)
        for _ in range(4):
            evt_rel = self.state_machine.update(
                candidate_state=GestureState.POINTING,
                pinch_distance=0.40,
                handedness="Right",
                confidence=0.9,
                index_tip_pos=(320, 240)
            )
        self.assertEqual(evt_rel.state, GestureState.POINTING)


if __name__ == "__main__":
    unittest.main()
