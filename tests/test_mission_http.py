"""HTTP contract tests for strict approvals, authentication, origin and bounded payloads."""
from __future__ import annotations
from contextlib import closing
import http.client
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from threading import Thread
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "03_CERBERUS_CORE"))
from mission_engine import JobSupervisor, Result
from control_plane import make_server

class MissionHttpTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.supervisor = JobSupervisor(Path(self.temp.name) / "audit.sqlite3",
                                        runner=lambda t, mid, cancel: Result("PASSED", 0, "HTTP_TEST_OK"))
        self.server = make_server(port=0, token="z" * 44, mission_engine=self.supervisor)
        self.thread = Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.shutdown)

    def shutdown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=3)

    def request(self, method, path, body=None, *, token=None, headers=None):
        hs = dict(headers or {})
        if token is not False:
            hs["Authorization"] = "Bearer " + (token if token is not None else "z" * 44)
        payload = json.dumps(body).encode() if body is not None else None
        if payload is not None:
            hs.setdefault("Content-Type", "application/json")
        with closing(http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=4)) as conn:
            conn.request(method, path, body=payload, headers=hs)
            resp = conn.getresponse()
            raw = resp.read()
            return resp.status, json.loads(raw), dict(resp.getheaders())

    def test_catalog_and_run_after_two_explicit_steps(self):
        status, body, headers = self.request("GET", "/api/v1/missions/catalog")
        self.assertEqual(status, 200)
        self.assertEqual(len(body["tasks"]), 3)
        self.assertEqual(headers["Cache-Control"], "no-store")
        status, pending, _ = self.request("POST", "/api/v1/missions/prepare", {"task_id": "engineering_tests"})
        self.assertEqual(status, 200)
        ticket = pending["ticket"]
        self.assertEqual(self.request("POST", "/api/v1/missions/start", {"ticket": ticket, "approve": False})[0], 400)
        status, active, _ = self.request("POST", "/api/v1/missions/start", {"ticket": ticket, "approve": True})
        self.assertEqual(status, 202)
        self.assertEqual(self.request("POST", "/api/v1/missions/start", {"ticket": ticket, "approve": True})[0], 400)
        for _ in range(60):
            status, item, _ = self.request("GET", "/api/v1/missions/" + active["id"])
            self.assertEqual(status, 200)
            if item["state"] == "PASSED":
                break
            time.sleep(.02)
        self.assertEqual(item["state"], "PASSED")
        self.assertEqual(self.request("GET", "/api/v1/missions")[1]["missions"][0]["id"], active["id"])

    def test_auth_host_origin_and_methods(self):
        self.assertEqual(self.request("GET", "/api/v1/missions", token=False)[0], 401)
        self.assertEqual(self.request("POST", "/api/v1/missions/prepare", {"task_id": "riscv_reference"},token="wrong")[0], 401)
        self.assertEqual(self.request("POST", "/api/v1/missions/prepare", {"task_id": "riscv_reference"},
                                      headers={"Origin": "https://evil.example"})[0], 403)
        self.assertEqual(self.request("GET", "/api/v1/missions", headers={"Host": "evil.example"})[0], 403)
        self.assertEqual(self.request("POST", "/api/v1/services", {})[0], 405)
        self.assertEqual(self.request("PUT", "/api/v1/missions/prepare", {})[0], 405)
        self.assertEqual(self.request("POST", "/api/v1/missions/prepare",
                                      {"task_id": "not-a-task"})[0], 400)
        self.assertEqual(self.request("POST", "/api/v1/missions/prepare",
                                      {"task_id": "riscv_reference", "shell": "cmd"})[0], 400)

    def test_invalid_json_content_type_and_cancel(self):
        self.assertEqual(self.request("POST", "/api/v1/missions/prepare",
                                      {"task_id": "robotics_static"},
                                      headers={"Content-Type":"text/plain"})[0], 400)
        self.assertEqual(self.request("POST", "/api/v1/missions/start",
                                      {"ticket": "random", "approve": True})[0], 400)
        self.assertEqual(self.request("POST", "/api/v1/missions/cancel", {"id": "wrong"})[0], 400)
        self.assertEqual(self.request("GET", "/api/v1/missions/97b4bfbe-45a1-42c3-8db1-bd3932646b16")[0], 404)

if __name__ == "__main__":
    unittest.main()
