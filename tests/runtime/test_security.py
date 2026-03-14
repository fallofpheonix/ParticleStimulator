"""Tests for security controls added to the HTTP API.

Covers:
- Per-IP rate limiting (RateLimiter unit tests)
- HTTP 413 when request body exceeds MAX_REQUEST_BYTES
- HTTP 415 when Content-Type is not application/json
- Security headers present on every response
- Health endpoint returns version and uptime
- CORS preflight (OPTIONS) returns correct headers
"""
from __future__ import annotations

import json
import threading
import time
import unittest
from http.server import ThreadingHTTPServer
from urllib import request as urllib_request
from urllib.error import HTTPError

from web.rate_limiter import RateLimiter
from web.server import MAX_REQUEST_BYTES, ParticleStimulatorHandler, _SECURITY_HEADERS


class RateLimiterUnitTests(unittest.TestCase):
    def test_allows_requests_within_limit(self) -> None:
        limiter = RateLimiter(max_requests=3, window_seconds=60.0)
        self.assertTrue(limiter.is_allowed("client"))
        self.assertTrue(limiter.is_allowed("client"))
        self.assertTrue(limiter.is_allowed("client"))

    def test_blocks_request_exceeding_limit(self) -> None:
        limiter = RateLimiter(max_requests=2, window_seconds=60.0)
        self.assertTrue(limiter.is_allowed("client"))
        self.assertTrue(limiter.is_allowed("client"))
        self.assertFalse(limiter.is_allowed("client"))

    def test_independent_clients_do_not_interfere(self) -> None:
        limiter = RateLimiter(max_requests=1, window_seconds=60.0)
        self.assertTrue(limiter.is_allowed("alice"))
        self.assertTrue(limiter.is_allowed("bob"))
        self.assertFalse(limiter.is_allowed("alice"))

    def test_window_expiry_resets_counter(self) -> None:
        limiter = RateLimiter(max_requests=1, window_seconds=0.05)
        self.assertTrue(limiter.is_allowed("client"))
        self.assertFalse(limiter.is_allowed("client"))
        time.sleep(0.1)
        # After the window expires the slot should be reclaimed.
        self.assertTrue(limiter.is_allowed("client"))

    def test_purge_stale_removes_inactive_clients(self) -> None:
        limiter = RateLimiter(max_requests=5, window_seconds=0.05)
        limiter.is_allowed("ghost")
        time.sleep(0.1)
        limiter.purge_stale()
        # The internal bucket for 'ghost' should be removed.
        self.assertNotIn("ghost", limiter._buckets)

    def test_invalid_max_requests_raises(self) -> None:
        with self.assertRaises(ValueError):
            RateLimiter(max_requests=0)

    def test_invalid_window_raises(self) -> None:
        with self.assertRaises(ValueError):
            RateLimiter(max_requests=10, window_seconds=0.0)


class SecurityHeaderTests(unittest.TestCase):
    """Integration tests that spin up a real ThreadingHTTPServer."""

    def setUp(self) -> None:
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), ParticleStimulatorHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        host, port = self.server.server_address
        self.base_url = f"http://{host}:{port}"

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)

    def _get(self, path: str):
        return urllib_request.urlopen(f"{self.base_url}{path}", timeout=5)

    def _post(self, path: str, body: bytes, content_type: str = "application/json"):
        req = urllib_request.Request(
            f"{self.base_url}{path}",
            data=body,
            headers={"Content-Type": content_type},
            method="POST",
        )
        return urllib_request.urlopen(req, timeout=5)

    def test_security_headers_present_on_json_response(self) -> None:
        with self._get("/api/health") as resp:
            self.assertEqual(resp.headers.get("X-Content-Type-Options"), "nosniff")
            self.assertEqual(resp.headers.get("X-Frame-Options"), "DENY")
            self.assertEqual(resp.headers.get("X-XSS-Protection"), "1; mode=block")

    def test_security_headers_present_on_static_response(self) -> None:
        with self._get("/") as resp:
            self.assertEqual(resp.headers.get("X-Content-Type-Options"), "nosniff")
            self.assertEqual(resp.headers.get("X-Frame-Options"), "DENY")

    def test_health_endpoint_returns_version_and_uptime(self) -> None:
        with self._get("/api/health") as resp:
            data = json.load(resp)
        self.assertEqual(data["status"], "ok")
        self.assertIn("version", data)
        self.assertIn("uptime_s", data)
        self.assertIn("components", data)
        self.assertIsInstance(data["uptime_s"], float)

    def test_cors_access_control_header_present(self) -> None:
        with self._get("/api/health") as resp:
            self.assertIn("Access-Control-Allow-Origin", resp.headers)

    def test_options_preflight_returns_204(self) -> None:
        req = urllib_request.Request(
            f"{self.base_url}/api/simulate",
            method="OPTIONS",
        )
        with urllib_request.urlopen(req, timeout=5) as resp:
            self.assertEqual(resp.status, 204)
            self.assertIn("Access-Control-Allow-Origin", resp.headers)
            self.assertIn("Access-Control-Allow-Methods", resp.headers)

    def test_post_with_wrong_content_type_returns_415(self) -> None:
        req = urllib_request.Request(
            f"{self.base_url}/api/simulate",
            data=b'{"seed": 1}',
            headers={"Content-Type": "text/plain"},
            method="POST",
        )
        try:
            urllib_request.urlopen(req, timeout=5)
            self.fail("Expected HTTPError 415")
        except HTTPError as exc:
            self.assertEqual(exc.code, 415)

    def test_post_with_oversized_body_returns_413(self) -> None:
        import http.client

        host, port = self.server.server_address
        conn = http.client.HTTPConnection(str(host), port, timeout=5)
        try:
            # Announce an oversized Content-Length so the server can reject
            # based on the header alone, before reading the request body.
            conn.request(
                "POST",
                "/api/simulate",
                body=b"",
                headers={
                    "Content-Type": "application/json",
                    "Content-Length": str(MAX_REQUEST_BYTES + 1),
                },
            )
            resp = conn.getresponse()
            self.assertEqual(resp.status, 413)
        finally:
            conn.close()


if __name__ == "__main__":
    unittest.main()
