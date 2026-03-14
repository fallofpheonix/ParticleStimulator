"""Event stream — accumulates and provides access to simulation events."""

from __future__ import annotations
import json
from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class EventStream:
    """Stores and streams simulation events.

    Attributes:
        max_buffer: maximum events to keep in memory.
    """

    max_buffer: int = 10_000
    _events: list[dict[str, Any]] = field(default_factory=list, repr=False)

    def push(self, event: dict[str, Any]) -> None:
        """Add an event to the stream."""
        self._events.append(event)
        if len(self._events) > self.max_buffer:
            self._events = self._events[-self.max_buffer:]

    def get_latest(self, n: int = 10) -> list[dict[str, Any]]:
        return self._events[-n:]

    def get_by_id(self, event_id: int) -> dict[str, Any] | None:
        for e in reversed(self._events):
            if e.get("event_id") == event_id:
                return e
        return None

    @property
    def count(self) -> int:
        return len(self._events)

    def export_json(self, path: str) -> None:
        with open(path, "w") as f:
            json.dump(self._events, f, indent=2, default=str)
