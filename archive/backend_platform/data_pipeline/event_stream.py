"""Data pipeline event stream — bridges the simulation event buffer to storage and WebSocket.

This module acts as the glue between the real-time event buffer and the
persistent ``EventDatabase``.  It also drives WebSocket broadcasts when
a ``SimulationWebSocketServer`` is registered.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import Any


@dataclass
class DataPipelineEventStream:
    """Pipeline stage that consumes events from the simulation and fans them out.

    Responsibilities:
    - Buffer events in memory (circular buffer).
    - Persist events to ``EventDatabase`` if configured.
    - Broadcast events over WebSocket if a server is registered.

    Attributes:
        max_buffer: maximum events kept in the circular buffer.
    """

    max_buffer: int = 10_000

    _events: list[dict[str, Any]] = field(default_factory=list, repr=False, init=False)
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False, init=False)
    _database: Any = field(default=None, repr=False, init=False)  # EventDatabase | None
    _ws_server: Any = field(default=None, repr=False, init=False)  # SimulationWebSocketServer | None

    # ------------------------------------------------------------------
    # Configuration
    # ------------------------------------------------------------------

    def attach_database(self, database: Any) -> None:
        """Register an ``EventDatabase`` for persistent storage."""
        self._database = database

    def attach_websocket_server(self, server: Any) -> None:
        """Register a WebSocket server for live broadcasts."""
        self._ws_server = server

    # ------------------------------------------------------------------
    # Ingestion
    # ------------------------------------------------------------------

    def push(self, event: dict[str, Any]) -> None:
        """Accept a simulation event and fan it out to all sinks.

        Args:
            event: event dict produced by the simulation controller.
        """
        with self._lock:
            self._events.append(event)
            if len(self._events) > self.max_buffer:
                self._events = self._events[-self.max_buffer:]

        if self._database is not None:
            self._database.store(event)

        if self._ws_server is not None:
            self._ws_server.broadcast_event(event)

    def push_batch(self, events: list[dict[str, Any]]) -> None:
        """Push multiple events in one call."""
        for event in events:
            self.push(event)

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------

    def get_latest(self, n: int = 10) -> list[dict[str, Any]]:
        """Return the *n* most recently pushed events."""
        with self._lock:
            return list(self._events[-n:])

    def get_by_id(self, event_id: int) -> dict[str, Any] | None:
        """Find a buffered event by ``event_id``."""
        with self._lock:
            for e in reversed(self._events):
                if e.get("event_id") == event_id:
                    return e
        return None

    @property
    def count(self) -> int:
        with self._lock:
            return len(self._events)

    def clear(self) -> None:
        """Discard all buffered events."""
        with self._lock:
            self._events.clear()
