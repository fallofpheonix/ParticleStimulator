from __future__ import annotations

import json
import threading
import unittest
from http.server import ThreadingHTTPServer
from urllib import request
from urllib.error import HTTPError

from web.server import (
    MAX_REQUEST_BODY_BYTES,
    RATE_LIMIT_BURST,
    RATE_LIMIT_WINDOW_S,
    ParticleStimulatorHandler,
    _check_rate_limit,
    _RATE_LIMIT_BUCKETS,
    _RATE_LIMIT_LOCK,
)
from web.ml_service import (
    _MAX_DEPTH,
    _MAX_ESTIMATORS,
    _MAX_SAMPLE_SIZE,
    _ARTIFACT_REQUIRED_KEYS,
    _sanitize_training_payload,
    _validate_artifact,
    FEATURE_NAMES,
)


def _start_server() -> tuple[ThreadingHTTPServer, str, int]:
    server = ThreadingHTTPServer(("127.0.0.1", 0), ParticleStimulatorHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    return server, host, port


class SecurityHeaderTests(unittest.TestCase):
    """Verify that security-related HTTP response headers are present."""

    def setUp(self) -> None:
        self.server, self.host, self.port = _start_server()

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()

    def _get(self, path: str):
        return request.urlopen(f"http://{self.host}:{self.port}{path}", timeout=5)

    def test_health_response_has_security_headers(self) -> None:
        with self._get("/api/health") as resp:
            self.assertEqual(resp.headers.get("X-Content-Type-Options"), "nosniff")
            self.assertEqual(resp.headers.get("X-Frame-Options"), "DENY")
            self.assertIn("default-src", resp.headers.get("Content-Security-Policy", ""))

    def test_static_response_has_security_headers(self) -> None:
        with self._get("/") as resp:
            self.assertEqual(resp.headers.get("X-Content-Type-Options"), "nosniff")
            self.assertEqual(resp.headers.get("X-Frame-Options"), "DENY")

    def test_simulate_response_has_security_headers(self) -> None:
        req = request.Request(
            f"http://{self.host}:{self.port}/api/simulate",
            data=json.dumps({"particleCount": 4, "simulationSteps": 40, "beamEnergy": 6100, "seed": 1}).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with request.urlopen(req, timeout=10) as resp:
            self.assertEqual(resp.headers.get("X-Content-Type-Options"), "nosniff")
            self.assertEqual(resp.headers.get("X-Frame-Options"), "DENY")


class RequestBodySizeLimitTests(unittest.TestCase):
    """Verify that oversized request bodies are rejected."""

    def setUp(self) -> None:
        self.server, self.host, self.port = _start_server()

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()

    def test_oversized_body_is_rejected_with_413(self) -> None:
        oversized = b"x" * (MAX_REQUEST_BODY_BYTES + 1)
        req = request.Request(
            f"http://{self.host}:{self.port}/api/simulate",
            data=oversized,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        # The server rejects the request based on Content-Length before the body
        # is fully transmitted, so the client may raise HTTPError(413) or a
        # BrokenPipeError / RemoteDisconnected depending on timing.
        try:
            with request.urlopen(req, timeout=5):
                pass
            self.fail("expected request to be rejected")
        except HTTPError as exc:
            self.assertEqual(exc.code, 413)
        except OSError:
            # BrokenPipeError or RemoteDisconnected: server closed connection
            # after sending 413 — this is acceptable behaviour.
            pass

    def test_invalid_content_length_is_rejected_with_400(self) -> None:
        req = request.Request(
            f"http://{self.host}:{self.port}/api/simulate",
            data=b"{}",
            headers={"Content-Type": "application/json", "Content-Length": "not-a-number"},
            method="POST",
        )
        with self.assertRaises(HTTPError) as ctx:
            request.urlopen(req, timeout=5)
        self.assertEqual(ctx.exception.code, 400)

    def test_body_at_exact_limit_is_accepted_or_fails_with_valid_json_error(self) -> None:
        # A body exactly at the limit should pass the size check (though it may be invalid JSON).
        at_limit = b"x" * MAX_REQUEST_BODY_BYTES
        req = request.Request(
            f"http://{self.host}:{self.port}/api/simulate",
            data=at_limit,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with request.urlopen(req, timeout=5):
                pass
        except HTTPError as exc:
            # Invalid JSON body → 400, not 413.
            self.assertNotEqual(exc.code, 413)


class RateLimitTests(unittest.TestCase):
    """Verify per-IP rate-limiting logic."""

    def setUp(self) -> None:
        # Clear rate-limit buckets before each test.
        with _RATE_LIMIT_LOCK:
            _RATE_LIMIT_BUCKETS.clear()

    def test_requests_within_burst_are_allowed(self) -> None:
        for _ in range(RATE_LIMIT_BURST):
            self.assertTrue(_check_rate_limit("10.0.0.1"))

    def test_requests_exceeding_burst_are_denied(self) -> None:
        for _ in range(RATE_LIMIT_BURST):
            _check_rate_limit("10.0.0.2")
        self.assertFalse(_check_rate_limit("10.0.0.2"))

    def test_different_ips_have_independent_buckets(self) -> None:
        for _ in range(RATE_LIMIT_BURST):
            _check_rate_limit("10.0.0.3")
        # Exhausted bucket for .3 should not affect .4.
        self.assertTrue(_check_rate_limit("10.0.0.4"))

    def test_rate_limit_endpoint_returns_429(self) -> None:
        """Fill the bucket via the real HTTP server and expect HTTP 429."""
        server, host, port = _start_server()
        try:
            for _ in range(RATE_LIMIT_BURST):
                req = request.Request(
                    f"http://{host}:{port}/api/simulate",
                    data=json.dumps({"particleCount": 4, "simulationSteps": 10, "seed": 1}).encode(),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                try:
                    request.urlopen(req, timeout=10)
                except HTTPError:
                    pass
            req = request.Request(
                f"http://{host}:{port}/api/simulate",
                data=json.dumps({"particleCount": 4, "simulationSteps": 10, "seed": 1}).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with self.assertRaises(HTTPError) as ctx:
                request.urlopen(req, timeout=5)
            self.assertEqual(ctx.exception.code, 429)
        finally:
            server.shutdown()
            server.server_close()


class MLTrainingPayloadSanitizationTests(unittest.TestCase):
    """Verify that ML training hyper-parameters are clamped to safe limits."""

    def test_sample_size_is_capped(self) -> None:
        result = _sanitize_training_payload({"sample_size": _MAX_SAMPLE_SIZE * 10})
        self.assertEqual(result["sample_size"], _MAX_SAMPLE_SIZE)

    def test_estimators_is_capped(self) -> None:
        result = _sanitize_training_payload({"estimators": _MAX_ESTIMATORS * 10})
        self.assertEqual(result["estimators"], _MAX_ESTIMATORS)

    def test_max_depth_is_capped(self) -> None:
        result = _sanitize_training_payload({"max_depth": _MAX_DEPTH * 10})
        self.assertEqual(result["max_depth"], _MAX_DEPTH)

    def test_values_below_cap_are_unchanged(self) -> None:
        result = _sanitize_training_payload({"sample_size": 1000, "estimators": 10, "max_depth": 3})
        self.assertEqual(result["sample_size"], 1000)
        self.assertEqual(result["estimators"], 10)
        self.assertEqual(result["max_depth"], 3)

    def test_invalid_numeric_values_are_dropped(self) -> None:
        result = _sanitize_training_payload({"sample_size": "bad", "estimators": None})
        self.assertNotIn("sample_size", result)
        self.assertNotIn("estimators", result)

    def test_dataset_path_is_stripped(self) -> None:
        result = _sanitize_training_payload({"dataset": "/etc/passwd"})
        self.assertNotIn("dataset", result)

    def test_empty_payload_is_unchanged(self) -> None:
        result = _sanitize_training_payload({})
        self.assertEqual(result, {})


class ArtifactValidationTests(unittest.TestCase):
    """Verify that only well-formed model artifacts are accepted after deserialization."""

    def _make_valid_artifact(self) -> dict:
        return {
            "model": object(),
            "scaler": object(),
            "feature_names": list(FEATURE_NAMES),
            "metrics": {},
        }

    def test_valid_artifact_passes(self) -> None:
        self.assertTrue(_validate_artifact(self._make_valid_artifact()))

    def test_non_dict_is_rejected(self) -> None:
        self.assertFalse(_validate_artifact("string"))
        self.assertFalse(_validate_artifact(42))
        self.assertFalse(_validate_artifact(None))

    def test_missing_required_key_is_rejected(self) -> None:
        for key in _ARTIFACT_REQUIRED_KEYS:
            artifact = self._make_valid_artifact()
            del artifact[key]
            self.assertFalse(_validate_artifact(artifact), f"should reject artifact missing '{key}'")

    def test_wrong_feature_names_are_rejected(self) -> None:
        artifact = self._make_valid_artifact()
        artifact["feature_names"] = ["wrong_feature"]
        self.assertFalse(_validate_artifact(artifact))

    def test_non_list_feature_names_are_rejected(self) -> None:
        artifact = self._make_valid_artifact()
        artifact["feature_names"] = "lepton_pt"
        self.assertFalse(_validate_artifact(artifact))


if __name__ == "__main__":
    unittest.main()
