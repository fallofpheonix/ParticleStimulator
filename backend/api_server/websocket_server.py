"""WebSocket server — real-time event streaming to frontends."""

from __future__ import annotations
import json
from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class WebSocketConnection:
    """Represents a connected WebSocket client (stub)."""
    client_id: str
    connected: bool = True


@dataclass(slots=True)
class WebSocketServer:
    """Simplified WebSocket server for event streaming.

    In production this would use the websockets library or FastAPI WebSockets.
    This stub maintains a list of connected clients and message queue.
    """

    host: str = "0.0.0.0"
    port: int = 8765
    clients: list[WebSocketConnection] = field(default_factory=list)
    _message_queue: list[str] = field(default_factory=list, repr=False)

    def connect(self, client_id: str) -> WebSocketConnection:
        conn = WebSocketConnection(client_id=client_id)
        self.clients.append(conn)
        return conn

    def disconnect(self, client_id: str) -> None:
        self.clients = [c for c in self.clients if c.client_id != client_id]

    def broadcast(self, data: dict[str, Any]) -> int:
        """Broadcast a message to all connected clients.

        Returns: number of clients that received the message.
        """
        msg = json.dumps(data)
        self._message_queue.append(msg)
        count = sum(1 for c in self.clients if c.connected)
        return count

    def send_event(self, event_data: dict[str, Any]) -> None:
        """Stream a simulation event to all clients."""
        self.broadcast({"type": "event", "data": event_data})

    def send_metrics(self, metrics: dict[str, Any]) -> None:
        """Stream performance metrics."""
        self.broadcast({"type": "metrics", "data": metrics})
