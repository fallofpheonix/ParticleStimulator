from __future__ import annotations

import argparse
import asyncio
from http.server import ThreadingHTTPServer
from pathlib import Path
import threading
import sys


ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = Path(__file__).resolve().parent

if sys.path and Path(sys.path[0]).resolve() == BACKEND_DIR:
    sys.path.pop(0)
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.web.server import ParticleStimulatorHandler


def run_http_server(host: str, port: int) -> ThreadingHTTPServer:
    httpd = ThreadingHTTPServer((host, port), ParticleStimulatorHandler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True, name="particle-http")
    thread.start()
    return httpd


def main() -> None:
    try:
        from src.web.socket_server import run_websocket_server
    except ModuleNotFoundError as exc:  # pragma: no cover - runtime environment safeguard
        raise SystemExit(
            "websocket runtime dependency missing. Install project requirements or use `.venv/bin/python backend/server.py`."
        ) from exc

    parser = argparse.ArgumentParser(description="Particle Stimulator API + websocket server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000, help="HTTP API port")
    parser.add_argument("--ws-port", type=int, default=8001, help="WebSocket event stream port")
    args = parser.parse_args()

    httpd = run_http_server(args.host, args.port)
    print(f"HTTP API listening on http://{args.host}:{args.port}")
    print(f"Event stream listening on ws://{args.host}:{args.ws_port}/events")
    try:
        asyncio.run(run_websocket_server(args.host, args.ws_port))
    except KeyboardInterrupt:
        pass
    finally:
        httpd.shutdown()
        httpd.server_close()


if __name__ == "__main__":
    main()
