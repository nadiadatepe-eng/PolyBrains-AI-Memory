from datetime import datetime, timezone
from unittest import TestCase

import polybrains
from polybrains import EpisodicStore, MemoryRecord
from polybrains.agent_adapter import AgentMemoryAdapter


NOW = datetime(2026, 8, 25, tzinfo=timezone.utc)


class AgentAdapterTests(TestCase):
    def test_adapter_is_equivalent_to_and_separate_from_core(self):
        adapter = AgentMemoryAdapter("a", "map-a")
        adapted = adapter.remember("a1", "bank means river edge", "agent-observation", NOW, NOW, 0.6)
        direct = MemoryRecord("a1", "a", "map-a", "agent-observation", NOW, NOW, 0.6, b"bank means river edge")
        direct_store = EpisodicStore("a", "map-a")
        direct_store.append(direct)

        self.assertEqual(adapted.to_bytes(), direct.to_bytes())
        self.assertEqual(adapter.recall("bank"), ("bank means river edge", adapted))
        self.assertEqual(direct_store.retrieve("a", "map-a", "bank").record_id, adapted.record_id)
        self.assertIsNone(adapter.recall("unmatched"))
        self.assertFalse(hasattr(polybrains, "AgentMemoryAdapter"))
        with self.assertRaisesRegex(ValueError, "text is required"):
            adapter.remember("empty", " ", "agent-observation", NOW, NOW, 0.5)
