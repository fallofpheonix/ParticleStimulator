from __future__ import annotations

import json
from typing import Any


class SimulationWebSocketServer:
    def __init__(self, host: str = "localhost", port: int = 8000):
        self._host = host
        self._port = port
        self._clients: list = []

    def status(self) -> dict:
        return {
            "host": self._host,
            "port": self._port,
            "connected_clients": len(self._clients),
            "endpoint": f"ws://{self._host}:{self._port}/events",
        }

    def broadcast_event(self, event: dict) -> None:
        if not self._clients:
            return
        self._broadcast({"type": "event", "data": event})

    def broadcast_progress(self, progress: dict) -> None:
        if not self._clients:
            return
        self._broadcast({"type": "progress", "data": progress})

    def broadcast_detector(self, data: dict) -> None:
        if not self._clients:
            return
        self._broadcast({"type": "detector", "data": data})

    def _broadcast(self, message: Any) -> None:
        payload = json.dumps(message, default=str)
        for client in list(self._clients):
            try:
                client.send(payload)
            except Exception:
                self._clients.remove(client)

    def attach_to_app(self, app, path: str) -> None:
        from fastapi import WebSocket

        server = self

        @app.websocket(path)
        async def websocket_endpoint(websocket: WebSocket):
            await websocket.accept()
            server._clients.append(websocket)
            try:
                while True:
                    await websocket.receive_text()
            except Exception:
                pass
            finally:
                if websocket in server._clients:
                    server._clients.remove(websocket)
