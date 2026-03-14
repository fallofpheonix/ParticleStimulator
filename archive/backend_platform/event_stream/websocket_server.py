"""WebSocket event streaming server.

Serves a WebSocket endpoint at ``ws://localhost:8001/events`` and
broadcasts simulation events, detector data, and progress updates to
all connected clients in real time.

Usage (standalone)::

    from backend.event_stream.websocket_server import SimulationWebSocketServer
    server = SimulationWebSocketServer(host="0.0.0.0", port=8001)
    asyncio.run(server.start())

Usage (embedded in FastAPI)::

    from fastapi import FastAPI
    from backend.event_stream.websocket_server import SimulationWebSocketServer

    server = SimulationWebSocketServer()
    app = FastAPI()
    server.attach_to_app(app, path="/events")
"""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class SimulationWebSocketServer:
    """Manages WebSocket connections and event broadcasting.

    Attributes:
        host: bind address for the standalone server.
        port: port for the standalone server (default 8001).
        max_queue: maximum events held in the broadcast queue per client.
    """

    host: str = "127.0.0.1"
    port: int = 8001
    max_queue: int = 1_000

    _connections: dict[str, Any] = field(default_factory=dict, repr=False, init=False)
    _broadcast_queue: asyncio.Queue | None = field(default=None, repr=False, init=False)

    # ------------------------------------------------------------------
    # FastAPI integration
    # ------------------------------------------------------------------

    def attach_to_app(self, app: Any, path: str = "/events") -> None:
        """Register a WebSocket route on an existing FastAPI *app*.

        Args:
            app: FastAPI application instance.
            path: URL path for the WebSocket endpoint.
        """
        from fastapi import WebSocket, WebSocketDisconnect  # type: ignore

        server = self  # capture for closure

        @app.websocket(path)
        async def ws_endpoint(websocket: WebSocket) -> None:
            await websocket.accept()
            client_id = str(id(websocket))
            server._connections[client_id] = websocket
            logger.info("WebSocket client connected: %s (total=%d)",
                        client_id, len(server._connections))
            try:
                # Keep the connection alive; handle pings / client messages.
                while True:
                    try:
                        msg = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                        # Echo any client messages back as acknowledgements.
                        await websocket.send_text(
                            json.dumps({"type": "ack", "received": msg})
                        )
                    except asyncio.TimeoutError:
                        # Send a heartbeat to keep the connection alive.
                        await websocket.send_text(json.dumps({"type": "ping"}))
            except WebSocketDisconnect:
                pass
            finally:
                server._connections.pop(client_id, None)
                logger.info("WebSocket client disconnected: %s (total=%d)",
                            client_id, len(server._connections))

    # ------------------------------------------------------------------
    # Broadcasting
    # ------------------------------------------------------------------

    def broadcast_event(self, event: dict[str, Any]) -> None:
        """Queue a simulation event for broadcast to all connected clients.

        This method is safe to call from synchronous code (e.g. from the
        simulation controller) and will schedule the async send on the
        running event loop if one is available.
        """
        message = json.dumps({"type": "event", "data": event}, default=str)
        self._send_to_all(message)

    def broadcast_progress(self, progress: dict[str, Any]) -> None:
        """Broadcast a simulation progress update."""
        message = json.dumps({"type": "progress", "data": progress}, default=str)
        self._send_to_all(message)

    def broadcast_detector(self, detector_data: dict[str, Any]) -> None:
        """Broadcast detector response data."""
        message = json.dumps({"type": "detector", "data": detector_data}, default=str)
        self._send_to_all(message)

    def _send_to_all(self, message: str) -> None:
        """Internal: send *message* to every connected WebSocket client."""
        if not self._connections:
            return
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            return  # No event loop running.

        disconnected = []
        for client_id, ws in list(self._connections.items()):
            try:
                if loop.is_running():
                    asyncio.ensure_future(ws.send_text(message), loop=loop)
                else:
                    loop.run_until_complete(ws.send_text(message))
            except Exception:  # noqa: BLE001
                disconnected.append(client_id)

        for client_id in disconnected:
            self._connections.pop(client_id, None)

    # ------------------------------------------------------------------
    # Standalone server
    # ------------------------------------------------------------------

    async def start(self) -> None:
        """Run a standalone WebSocket server (requires ``websockets`` package).

        Serves the ``ws://{host}:{port}/events`` endpoint.
        """
        try:
            import websockets  # type: ignore
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError(
                "websockets is required for the standalone server: pip install websockets"
            ) from exc

        logger.info("Starting WebSocket server on ws://%s:%d/events", self.host, self.port)

        async def handler(websocket: Any, path: str) -> None:
            client_id = str(id(websocket))
            self._connections[client_id] = websocket
            logger.info("Client connected: %s", client_id)
            try:
                async for message in websocket:
                    await websocket.send(
                        json.dumps({"type": "ack", "received": message})
                    )
            except Exception:  # noqa: BLE001
                pass
            finally:
                self._connections.pop(client_id, None)
                logger.info("Client disconnected: %s", client_id)

        async with websockets.serve(handler, self.host, self.port):
            await asyncio.Future()  # run forever

    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------

    @property
    def connected_clients(self) -> int:
        return len(self._connections)

    def status(self) -> dict[str, Any]:
        return {
            "host": self.host,
            "port": self.port,
            "connected_clients": self.connected_clients,
            "endpoint": f"ws://{self.host}:{self.port}/events",
        }
