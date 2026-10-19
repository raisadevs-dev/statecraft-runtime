import json
import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tigress.engine import TigressEngine
from tigress.models import CharacterState, Event, EventType
from tigress.storage import save_state, load_state


class TigressEngineTests(unittest.TestCase):
    def test_unclear_event_does_not_change_trust(self):
        engine = TigressEngine()
        before = engine.state.trust
        result = engine.respond(Event(EventType.UNCLEAR, context_known=False))
        self.assertEqual(result.action, "ASK_FOR_CONTEXT")
        self.assertEqual(engine.state.trust, before)

    def test_unjustified_restriction_sets_boundary_and_changes_state(self):
        engine = TigressEngine()
        before = engine.state.trust
        result = engine.respond(Event(EventType.UNJUSTIFIED_RESTRICTION))
        self.assertEqual(result.action, "CHALLENGE_AND_SET_BOUNDARY")
        self.assertLess(engine.state.trust, before)

    def test_apology_does_not_automatically_restore_trust(self):
        engine = TigressEngine()
        engine.respond(Event(EventType.REPEATED_HARM))
        after_harm = engine.state.trust
        engine.respond(Event(EventType.GENUINE_APOLOGY))
        self.assertLessEqual(engine.state.trust, after_harm)

    def test_accountability_with_change_can_rebuild_trust_gradually(self):
        engine = TigressEngine()
        engine.respond(Event(EventType.REPEATED_HARM, evidence_strength=1.0))
        after_harm = engine.state.trust
        engine.respond(Event(EventType.ACCOUNTABILITY_WITH_CHANGE, evidence_strength=1.0))
        self.assertGreater(engine.state.trust, after_harm)
        self.assertLess(engine.state.trust, 0.75)

    def test_honest_mistake_is_not_counted_as_repeated_harm(self):
        engine = TigressEngine()
        engine.respond(Event(EventType.HONEST_MISTAKE))
        self.assertEqual(engine.state.harmful_pattern_count, 0)

    def test_state_is_clamped(self):
        state = CharacterState(trust=9, hurt=-4)
        state.clamp()
        self.assertEqual(state.trust, 1.0)
        self.assertEqual(state.hurt, 0.0)

    def test_save_and_load_round_trip(self):
        state = CharacterState(trust=0.42, harmful_pattern_count=2)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state.json"
            save_state(state, path)
            loaded = load_state(path)
            self.assertAlmostEqual(loaded.trust, 0.42)
            self.assertEqual(loaded.harmful_pattern_count, 2)


if __name__ == "__main__":
    unittest.main()
