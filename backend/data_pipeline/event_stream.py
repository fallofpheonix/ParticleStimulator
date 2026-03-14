from __future__ import annotations

from collections import deque
from typing import Optional

from backend.data_pipeline.event_database import EventDatabase


class DataPipelineEventStream:
    def __init__(self, max_buffer: Optional[int] = None):
        self._max_buffer = max_buffer
        self._buffer: deque = deque(maxlen=max_buffer)
        self._db: Optional[EventDatabase] = None

    def push(self, event: dict) -> None:
        self._buffer.append(event)
        if self._db is not None:
            self._db.store(event)

    @property
    def count(self) -> int:
        return len(self._buffer)

    def get_latest(self, n: int) -> list[dict]:
        buf = list(self._buffer)
        return buf[-n:] if n <= len(buf) else buf

    def attach_database(self, db: EventDatabase) -> None:
        self._db = db
