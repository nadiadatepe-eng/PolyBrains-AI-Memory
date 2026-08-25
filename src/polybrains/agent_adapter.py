"""Optional framework-neutral adapter from agent text to the memory core."""

from datetime import datetime

from .memory import EpisodicStore, MemoryRecord


class AgentMemoryAdapter:
    def __init__(self, owner: str, frame: str) -> None:
        self.store = EpisodicStore(owner, frame)

    def remember(
        self,
        record_id: str,
        text: str,
        source: str,
        event_time: datetime,
        write_time: datetime,
        confidence: float,
    ) -> MemoryRecord:
        if not text.strip():
            raise ValueError("observation text is required")
        record = MemoryRecord(
            record_id,
            self.store.owner,
            self.store.frame,
            source,
            event_time,
            write_time,
            confidence,
            text.encode(),
        )
        self.store.append(record)
        return record

    def recall(self, query: str) -> tuple[str, MemoryRecord] | None:
        record = self.store.retrieve(self.store.owner, self.store.frame, query)
        return None if record is None else (record.payload.decode(), record)
