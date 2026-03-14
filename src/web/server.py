from __future__ import annotations

import argparse
import json
import mimetypes
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from web.event_stream import event_broker
from web.ml_service import ml_service
from web.service import SimulationRequest, simulate_payload


ROOT_DIR = Path(__file__).resolve().parents[2]
FRONTEND_DIST_DIR = ROOT_DIR / "frontend" / "dist"
STATIC_DIR = Path(__file__).resolve().parent / "static"
ACTIVE_STATIC_DIR = FRONTEND_DIST_DIR if (FRONTEND_DIST_DIR / "index.html").exists() else STATIC_DIR


def _json_bytes(payload: dict[str, object]) -> bytes:
    return json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")


class ParticleStimulatorHandler(BaseHTTPRequestHandler):
    server_version = "ParticleStimulatorHTTP/0.1"

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/api/health":
            self._write_json(HTTPStatus.OK, {"status": "ok"})
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
        if parsed.path not in {"/api/simulate", "/api/ml/train", "/api/ml/predict"}:
            self._write_json(HTTPStatus.NOT_FOUND, {"error": "unknown endpoint"})
            return

        length = int(self.headers.get("Content-Length", "0"))
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
        except Exception as exc:  # pragma: no cover - top-level server safety
            self._write_json(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": f"simulation failure: {exc}"})
            return

        self._write_json(status, response)

    def _write_json(self, status: HTTPStatus, payload: dict[str, object]) -> None:
        body = _json_bytes(payload)
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
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
