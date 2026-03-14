from __future__ import annotations

import asyncio
from collections import deque
from dataclasses import dataclass, field
from threading import Lock
from typing import Any


@dataclass(slots=True)
class EventBroker:
    max_events: int = 256
    _events: deque[dict[str, Any]] = field(default_factory=lambda: deque(maxlen=256), repr=False)
    _snapshot: dict[str, Any] | None = field(default=None, repr=False)
    _subscribers: list[tuple[asyncio.AbstractEventLoop, asyncio.Queue[dict[str, Any]]]] = field(default_factory=list, repr=False)
    _lock: Lock = field(default_factory=Lock, repr=False)

    def register(self, loop: asyncio.AbstractEventLoop, queue: asyncio.Queue[dict[str, Any]]) -> None:
        with self._lock:
            self._subscribers.append((loop, queue))

    def unregister(self, queue: asyncio.Queue[dict[str, Any]]) -> None:
        with self._lock:
            self._subscribers = [(loop, current) for loop, current in self._subscribers if current is not queue]

    def publish_event(self, event: dict[str, Any]) -> None:
        with self._lock:
            self._events.append(event)
            subscribers = list(self._subscribers)
        self._fan_out(subscribers, event)

    def publish_snapshot(self, snapshot: dict[str, Any]) -> None:
        with self._lock:
            self._snapshot = snapshot
            subscribers = list(self._subscribers)
        self._fan_out(subscribers, snapshot)

    def latest_snapshot(self) -> dict[str, Any] | None:
        with self._lock:
            if self._snapshot is None:
                return None
            return dict(self._snapshot)

    def recent_events(self) -> list[dict[str, Any]]:
        with self._lock:
            return list(self._events)

    def _fan_out(
        self,
        subscribers: list[tuple[asyncio.AbstractEventLoop, asyncio.Queue[dict[str, Any]]]],
        payload: dict[str, Any],
    ) -> None:
        for loop, queue in subscribers:
            try:
                loop.call_soon_threadsafe(queue.put_nowait, payload)
            except RuntimeError:
                continue


event_broker = EventBroker()
