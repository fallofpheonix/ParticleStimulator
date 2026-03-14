from __future__ import annotations

from http.server import ThreadingHTTPServer
import json
import threading
import unittest
from urllib import request

from web.server import ParticleStimulatorHandler
from web.service import simulate_payload


class WebServiceTests(unittest.TestCase):
    def test_simulate_payload_contains_frontend_fields(self) -> None:
        payload = simulate_payload({"beam_particles_per_side": 4, "steps": 80, "seed": 11})
        self.assertIn("summary", payload)
        self.assertIn("initial_particles", payload)
        self.assertIn("final_particles", payload)
        self.assertIn("timeline", payload)
        self.assertGreaterEqual(len(payload["collisions"]), 1)
        self.assertTrue(all("product_ids" in event for event in payload["collisions"]))

    def test_http_server_serves_api_and_static_assets(self) -> None:
        server = ThreadingHTTPServer(("127.0.0.1", 0), ParticleStimulatorHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        host, port = server.server_address

        try:
            with request.urlopen(f"http://{host}:{port}/api/health", timeout=5) as response:
                health = json.load(response)
            self.assertEqual(health["status"], "ok")

            simulate_request = request.Request(
                f"http://{host}:{port}/api/simulate",
                data=json.dumps({"beam_particles_per_side": 4, "steps": 40, "seed": 3}).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with request.urlopen(simulate_request, timeout=5) as response:
                payload = json.load(response)
            self.assertIn("summary", payload)
            self.assertIn("collisions", payload)

            with request.urlopen(f"http://{host}:{port}/", timeout=5) as response:
                index = response.read().decode("utf-8")
            self.assertIn("Particle Stimulator Control Surface", index)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)


if __name__ == "__main__":
    unittest.main()
