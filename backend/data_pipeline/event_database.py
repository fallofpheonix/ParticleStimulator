from __future__ import annotations

import json
from pathlib import Path
from typing import Optional


class EventDatabase:
    def __init__(self, storage_dir: Optional[str] = None):
        self._storage_dir = Path(storage_dir) if storage_dir else None
        self._events: list[dict] = []

    def store(self, event: dict) -> None:
        self._events.append(event)

    def store_batch(self, events: list[dict]) -> None:
        self._events.extend(events)

    @property
    def count(self) -> int:
        return len(self._events)

    def get_by_id(self, event_id) -> Optional[dict]:
        for e in self._events:
            if e.get("event_id") == event_id:
                return e
        return None

    def query(self, **kwargs) -> list[dict]:
        results = []
        for e in self._events:
            if all(e.get(k) == v for k, v in kwargs.items()):
                results.append(e)
        return results

    def get_latest(self, n: int) -> list[dict]:
        return self._events[-n:] if n <= len(self._events) else list(self._events)

    def flush_json(self, filename: str) -> Path:
        if self._storage_dir is None:
            raise RuntimeError("No storage_dir configured")
        path = self._storage_dir / filename
        path.write_text(json.dumps(self._events, default=str))
        return path

    def load_json(self, filename: str) -> int:
        if self._storage_dir is None:
            raise RuntimeError("No storage_dir configured")
        path = self._storage_dir / filename
        self._events = json.loads(path.read_text())
        return len(self._events)
