"""Event database — persistent storage for simulation events.

Provides an append-only store backed by JSON, with optional Parquet / HDF5
snapshots.  Designed to be called from the data pipeline after each
simulation run.
"""

from __future__ import annotations

import json
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from backend.data_pipeline.event_serializer import EventSerializer


@dataclass
class EventDatabase:
    """Thread-safe event store with multi-format persistence.

    Attributes:
        storage_dir: root directory for all persisted data.
        max_memory: maximum number of events to keep in memory.
    """

    storage_dir: str | Path = "data/events"
    max_memory: int = 50_000

    _events: list[dict[str, Any]] = field(default_factory=list, repr=False, init=False)
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False, init=False)

    def __post_init__(self) -> None:
        self._storage_dir = Path(self.storage_dir)
        self._storage_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def store(self, event: dict[str, Any]) -> None:
        """Append a single event to the in-memory buffer."""
        with self._lock:
            self._events.append(event)
            if len(self._events) > self.max_memory:
                self._events = self._events[-self.max_memory:]

    def store_batch(self, events: list[dict[str, Any]]) -> None:
        """Append multiple events at once."""
        for event in events:
            self.store(event)

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get_all(self) -> list[dict[str, Any]]:
        """Return a copy of all in-memory events."""
        with self._lock:
            return list(self._events)

    def get_latest(self, n: int = 100) -> list[dict[str, Any]]:
        """Return the *n* most recent events."""
        with self._lock:
            return list(self._events[-n:])

    def get_by_id(self, event_id: int) -> dict[str, Any] | None:
        """Lookup a single event by its ``event_id`` field."""
        with self._lock:
            for event in reversed(self._events):
                if event.get("event_id") == event_id:
                    return event
        return None

    def query(self, **filters: Any) -> list[dict[str, Any]]:
        """Filter events by key-value equality.

        Example::

            db.query(triggered=True, n_jets=2)
        """
        with self._lock:
            return [
                e for e in self._events
                if all(e.get(k) == v for k, v in filters.items())
            ]

    @property
    def count(self) -> int:
        with self._lock:
            return len(self._events)

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def flush_json(self, filename: str = "events.json") -> Path:
        """Persist all in-memory events to a JSON file."""
        dest = self._storage_dir / filename
        return EventSerializer.to_json(self.get_all(), dest)

    def flush_parquet(self, filename: str = "events.parquet") -> Path:
        """Persist all in-memory events to a Parquet file."""
        dest = self._storage_dir / filename
        return EventSerializer.to_parquet(self.get_all(), dest)

    def flush_hdf5(self, filename: str = "events.h5") -> Path:
        """Persist all in-memory events to an HDF5 file."""
        dest = self._storage_dir / filename
        return EventSerializer.to_hdf5(self.get_all(), dest)

    def load_json(self, filename: str = "events.json") -> int:
        """Load events from a JSON file into memory.  Returns count loaded."""
        src = self._storage_dir / filename
        if not src.exists():
            return 0
        events = EventSerializer.from_json(src)
        self.store_batch(events)
        return len(events)
