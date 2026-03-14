from __future__ import annotations

import argparse
import asyncio
import json

from websockets.asyncio.server import serve
from websockets.exceptions import ConnectionClosed

from src.web.event_stream import event_broker


async def _handle_connection(websocket) -> None:
    if websocket.request.path != "/events":
        await websocket.close(code=1008, reason="unknown path")
        return

    queue: asyncio.Queue[dict[str, object]] = asyncio.Queue()
    loop = asyncio.get_running_loop()
    event_broker.register(loop, queue)

    snapshot = event_broker.latest_snapshot()
    if snapshot is not None:
        await websocket.send(json.dumps(snapshot))
    for event in event_broker.recent_events():
        await websocket.send(json.dumps(event))

    sender = asyncio.create_task(_sender_loop(websocket, queue))
    try:
        await websocket.wait_closed()
    finally:
        sender.cancel()
        event_broker.unregister(queue)


async def _sender_loop(websocket, queue: asyncio.Queue[dict[str, object]]) -> None:
    try:
        while True:
            payload = await queue.get()
            await websocket.send(json.dumps(payload))
    except (asyncio.CancelledError, ConnectionClosed):
        return


async def run_websocket_server(host: str = "127.0.0.1", port: int = 8001) -> None:
    async with serve(_handle_connection, host, port, ping_interval=20, ping_timeout=20):
        await asyncio.Future()


def main() -> None:
    parser = argparse.ArgumentParser(description="Particle Stimulator websocket server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8001)
    args = parser.parse_args()
    asyncio.run(run_websocket_server(args.host, args.port))


if __name__ == "__main__":
    main()
