"""Real loopback HTTP tests for the read-only CERBERUS control plane."""
from __future__ import annotations

import http.client
from contextlib import closing
import json
from pathlib import Path
import sys
from threading import Thread
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "03_CERBERUS_CORE"))
from control_plane import CATALOG, make_server, probe_service

class ControlPlaneTests(unittest.TestCase):
    def setUp(self):
        self.server = make_server(port=0, token="x" * 40, probe=lambda _: "not_integrated")
        self.worker = Thread(target=self.server.serve_forever, daemon=True)
        self.worker.start()
        self.addCleanup(self.close)

    def close(self):
        self.server.shutdown()
        self.server.server_close()
        self.worker.join(timeout=5)

    def call(self, method, path, token=None):
        with closing(http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=5)) as client:
            headers = {"Authorization": "Bearer " + token} if token else {}
            client.request(method, path, headers=headers)
            response = client.getresponse()
            return response.status, response.read(), dict(response.getheaders())

    def test_health_is_loopback_and_read_only(self):
        self.assertEqual(self.server.server_address[0], "127.0.0.1")
        status, body, headers = self.call("GET", "/healthz")
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)["mode"], "read-only")
        self.assertEqual(headers["Cache-Control"], "no-store")
        self.assertEqual(self.call("POST", "/api/v1/services", "x" * 40)[0], 405)

    def test_api_needs_valid_token(self):
        self.assertEqual(self.call("GET", "/api/v1/services")[0], 401)
        self.assertEqual(self.call("GET", "/api/v1/services", "bad")[0], 401)
        self.assertEqual(self.call("GET", "/api/v1/services", "x" * 40)[0], 200)

    def test_catalog_and_explicit_not_integrated(self):
        _, body, _ = self.call("GET", "/api/v1/services", "x" * 40)
        data = json.loads(body)
        self.assertEqual(len(data["services"]), len(CATALOG))
        self.assertEqual(data["schema"], 1)
        self.assertTrue(all(s["status"] == "not_integrated" for s in data["services"]))

    def test_local_assets_and_unexpected_routes(self):
        for path in ("/", "/control_plane.js", "/control_plane.css"):
            status, body, headers = self.call("GET", path)
            self.assertEqual(status, 200)
            self.assertGreater(len(body), 100)
            self.assertIn("Content-Security-Policy", headers)
        self.assertEqual(self.call("GET", "/missing", "x" * 40)[0], 404)

    def test_probe_absent_and_unreachable(self):
        self.assertEqual(probe_service({"health_url": None}), "not_integrated")
        self.assertEqual(probe_service({"health_url": "http://127.0.0.1:1/healthz"}, timeout=.1), "unavailable")
        with self.assertRaises(ValueError):
            make_server(port=0, token="short")

if __name__ == "__main__":
    unittest.main()
