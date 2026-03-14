from __future__ import annotations

import argparse
import json
import logging
import mimetypes
import time
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from web.event_stream import event_broker
from web.ml_service import ml_service
from web.rate_limiter import RateLimiter
from web.service import SimulationRequest, simulate_payload

_LOG = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parents[2]
FRONTEND_DIST_DIR = ROOT_DIR / "frontend" / "dist"
STATIC_DIR = Path(__file__).resolve().parent / "static"
ACTIVE_STATIC_DIR = FRONTEND_DIST_DIR if (FRONTEND_DIST_DIR / "index.html").exists() else STATIC_DIR

# Maximum request body accepted from any single POST request (1 MiB).
# Requests larger than this are rejected with 413 to prevent DoS via
# oversized payloads filling server memory.
MAX_REQUEST_BYTES: int = 1 * 1024 * 1024

# Monotonic timestamp recorded at module import time, used for uptime reporting.
_START_TIME: float = time.monotonic()

_SERVER_VERSION: str = "0.1.0"

# Per-IP sliding-window rate limiters.
# General API (all endpoints): 120 requests / 60 s.
_api_limiter: RateLimiter = RateLimiter(max_requests=120, window_seconds=60.0)
# Simulation endpoint is CPU-intensive: 10 requests / 60 s.
_simulate_limiter: RateLimiter = RateLimiter(max_requests=10, window_seconds=60.0)
# ML training is very expensive: 2 requests / 60 s.
_ml_train_limiter: RateLimiter = RateLimiter(max_requests=2, window_seconds=60.0)

# Security headers added to every HTTP response.
_SECURITY_HEADERS: dict[str, str] = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    # Allow browser frontends served from any origin to reach this API.
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
}


def _json_bytes(payload: dict[str, object]) -> bytes:
    return json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")


class ParticleStimulatorHandler(BaseHTTPRequestHandler):
    server_version = "ParticleStimulatorHTTP/0.1"

    def log_message(self, fmt: str, *args: object) -> None:  # noqa: N802
        _LOG.info(fmt, *args)

    def _client_ip(self) -> str:
        return self.client_address[0] if self.client_address else "unknown"

    def do_OPTIONS(self) -> None:  # noqa: N802
        """Handle CORS preflight requests without rate-limiting."""
        self.send_response(HTTPStatus.NO_CONTENT)
        for header, value in _SECURITY_HEADERS.items():
            self.send_header(header, value)
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        client_ip = self._client_ip()

        if not _api_limiter.is_allowed(client_ip):
            self._write_json(HTTPStatus.TOO_MANY_REQUESTS, {"error": "rate limit exceeded"})
            return

        if parsed.path == "/api/health":
            uptime_s = time.monotonic() - _START_TIME
            self._write_json(
                HTTPStatus.OK,
                {
                    "status": "ok",
                    "version": _SERVER_VERSION,
                    "uptime_s": round(uptime_s, 1),
                    "components": {
                        "simulation": "ok",
                        "ml_service": ml_service.status().get("status", "unknown"),
                        "event_broker": "ok",
                    },
                },
            )
            return
        if parsed.path == "/api/defaults":
            defaults = SimulationRequest()
            self._write_json(
                HTTPStatus.OK,
                {
                    "beam_energy_gev": defaults.beam_energy_gev,
                    "beam_intensity": defaults.beam_intensity,
                    "magnetic_field_t": defaults.magnetic_field_t,
                    "rf_field_v_m": defaults.rf_field_v_m,
                    "quadrupole_gradient_t_per_m": defaults.quadrupole_gradient_t_per_m,
                    "beam_particles_per_side": defaults.beam_particles_per_side,
                    "beam_spread_m": defaults.beam_spread_m,
                    "longitudinal_spacing_m": defaults.longitudinal_spacing_m,
                    "interaction_radius_m": defaults.interaction_radius_m,
                    "event_probability": defaults.event_probability,
                    "aperture_radius_m": defaults.aperture_radius_m,
                    "steps": defaults.steps,
                    "seed": defaults.seed,
                },
            )
            return
        if parsed.path == "/api/ml/status":
            self._write_json(HTTPStatus.OK, ml_service.status())
            return
        if parsed.path == "/api/events/recent":
            self._write_json(HTTPStatus.OK, {"events": event_broker.recent_events()})
            return
        self._serve_static(parsed.path)

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        client_ip = self._client_ip()

        if parsed.path not in {"/api/simulate", "/api/ml/train", "/api/ml/predict"}:
            self._write_json(HTTPStatus.NOT_FOUND, {"error": "unknown endpoint"})
            return

        # Apply general rate limit first, then endpoint-specific limits.
        if not _api_limiter.is_allowed(client_ip):
            self._write_json(HTTPStatus.TOO_MANY_REQUESTS, {"error": "rate limit exceeded"})
            return
        if parsed.path == "/api/simulate" and not _simulate_limiter.is_allowed(client_ip):
            self._write_json(HTTPStatus.TOO_MANY_REQUESTS, {"error": "simulate rate limit exceeded"})
            return
        if parsed.path == "/api/ml/train" and not _ml_train_limiter.is_allowed(client_ip):
            self._write_json(HTTPStatus.TOO_MANY_REQUESTS, {"error": "ml train rate limit exceeded"})
            return

        # Require application/json content type to prevent CSRF-style injection
        # and to ensure the body can be parsed as JSON.
        content_type = self.headers.get("Content-Type", "")
        if not content_type.startswith("application/json"):
            self._write_json(
                HTTPStatus.UNSUPPORTED_MEDIA_TYPE,
                {"error": "Content-Type must be application/json"},
            )
            return

        # Enforce maximum body size to prevent memory exhaustion DoS.
        length = int(self.headers.get("Content-Length", "0"))
        if length > MAX_REQUEST_BYTES:
            self._write_json(
                HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
                {"error": f"request body exceeds {MAX_REQUEST_BYTES} bytes"},
            )
            return

        raw_body = self.rfile.read(length) if length else b"{}"
        try:
            payload = json.loads(raw_body.decode("utf-8"))
            if not isinstance(payload, dict):
                raise ValueError("payload must be an object")
            if parsed.path == "/api/simulate":
                response = simulate_payload(payload)
                status = HTTPStatus.OK
            elif parsed.path == "/api/ml/train":
                response = ml_service.start_training(payload)
                status = HTTPStatus.ACCEPTED
            else:
                response = ml_service.predict(payload)
                status = HTTPStatus.OK
        except (json.JSONDecodeError, UnicodeDecodeError, ValueError) as exc:
            self._write_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
            return
        except RuntimeError as exc:
            self._write_json(HTTPStatus.CONFLICT, {"error": str(exc)})
            return
        except Exception:  # pragma: no cover - top-level server safety
            _LOG.exception("Unhandled error processing %s", parsed.path)
            self._write_json(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": "internal server error"})
            return

        self._write_json(status, response)

    def _write_json(self, status: HTTPStatus, payload: dict[str, object]) -> None:
        body = _json_bytes(payload)
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        for header, value in _SECURITY_HEADERS.items():
            self.send_header(header, value)
        self.end_headers()
        self.wfile.write(body)

    def _serve_static(self, raw_path: str) -> None:
        relative = raw_path.lstrip("/") or "index.html"
        candidate = (ACTIVE_STATIC_DIR / relative).resolve()
        if ACTIVE_STATIC_DIR.resolve() not in candidate.parents and candidate != ACTIVE_STATIC_DIR.resolve():
            self._write_json(HTTPStatus.FORBIDDEN, {"error": "invalid path"})
            return
        if candidate.is_dir():
            candidate = candidate / "index.html"
        if not candidate.exists():
            candidate = ACTIVE_STATIC_DIR / "index.html"
        content = candidate.read_bytes()
        content_type, _ = mimetypes.guess_type(str(candidate))
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", f"{content_type or 'text/plain'}; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        for header, value in _SECURITY_HEADERS.items():
            self.send_header(header, value)
        self.end_headers()
        self.wfile.write(content)


def main() -> None:
    parser = argparse.ArgumentParser(description="Particle Stimulator web server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    httpd = ThreadingHTTPServer((args.host, args.port), ParticleStimulatorHandler)
    print(f"Serving Particle Stimulator on http://{args.host}:{args.port}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()


if __name__ == "__main__":
    main()
