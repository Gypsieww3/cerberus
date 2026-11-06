"""Regression tests for supervised engineering execution and audit history."""
from __future__ import annotations
from pathlib import Path
import tempfile
import sys
import unittest
from unittest.mock import patch
import http.client
import json
from threading import Thread

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "01_MOSS_KYVRAEL"))
from engineering_tools import EngineeringRunner, EngineeringBusy
from api_server import create_server


class EngineeringUnitTests(unittest.TestCase):
    def test_real_moss_syntax_job_and_audit(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "engineering.sqlite3"
            runner = EngineeringRunner(path)
            self.assertIn("moss-syntax", [job["name"] for job in runner.jobs()])
            with self.assertRaises(PermissionError):
                runner.run("moss-syntax")
            with self.assertRaises(ValueError):
                runner.run("cmd.exe /c echo unsafe", operator_approved=True)
            self.assertEqual(runner.recent(), [])
            result = runner.run("moss-syntax", operator_approved=True, timeout=30)
            self.assertEqual(result["status"], "PASS", result)
            self.assertEqual(result["exit_code"], 0)
            # Completed results survive opening a new runner process.
            again = EngineeringRunner(path)
            self.assertEqual(again.recent()[0]["status"], "PASS")

    def test_engineering_inventory_is_source_based(self):
        with tempfile.TemporaryDirectory() as folder:
            runner = EngineeringRunner(Path(folder) / "engineering.db")
            result = runner.inventory()
            self.assertGreater(result["total_source_files"], 0)
            self.assertTrue(any(p["folder"] == "01_MOSS_KYVRAEL" for p in result["projects"]))

    def test_concurrent_requests_are_not_silently_queued(self):
        with tempfile.TemporaryDirectory() as folder:
            runner = EngineeringRunner(Path(folder) / "engineering.db")
            runner._lock.acquire()
            try:
                with self.assertRaises(EngineeringBusy):
                    runner.run("moss-syntax", operator_approved=True)
            finally:
                runner._lock.release()

    def test_reopen_interrupts_unfinished_runs(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "engineering.db"
            runner = EngineeringRunner(path)
            with runner.connection() as db:
                db.execute("INSERT INTO engineering_runs(name,status,requested_at) VALUES(?,?,?)",
                           ("moss-syntax", "RUNNING", "2026-01-01T00:00:00Z"))
            self.assertEqual(EngineeringRunner(path).recent()[0]["status"], "INTERRUPTED")


class EngineeringHttpTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.server = create_server(data_dir=self.temp.name, port=0, token="A" * 48)
        self.thread = Thread(target=self.server.serve_forever,
                             kwargs={"poll_interval": .02}, daemon=True)
        self.thread.start()
        self.addCleanup(self.close)

    def close(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)

    def request(self, method, path, body=None, authorized=True):
        conn = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=20)
        headers = {}
        if authorized:
            headers["Authorization"] = "Bearer " + "A" * 48
        payload = None
        if body is not None:
            payload = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = "application/json"
        try:
            conn.request(method, path, body=payload, headers=headers)
            res = conn.getresponse()
            return res.status, json.loads(res.read())
        finally:
            conn.close()

    def test_catalog_requires_auth(self):
        self.assertEqual(self.request("GET", "/api/v1/engineering/jobs", authorized=False)[0], 401)
        status, data = self.request("GET", "/api/v1/engineering/jobs")
        self.assertEqual(status, 200)
        self.assertIn("moss-syntax", [x["name"] for x in data["jobs"]])
        self.assertTrue(all(x["requires_approval"] for x in data["jobs"]))
        status, inventory = self.request("GET", "/api/v1/engineering/inventory")
        self.assertEqual(status, 200)
        self.assertGreater(inventory["total_source_files"], 0)

    def test_operator_confirmation_is_mandatory(self):
        status, _ = self.request("POST", "/api/v1/engineering/run",
                                 {"job": "moss-syntax", "operator_approved": False})
        self.assertEqual(status, 403)
        status, _ = self.request("POST", "/api/v1/engineering/run",
                                 {"job": "arbitrary-command", "operator_approved": True})
        self.assertEqual(status, 422)
        status, runs = self.request("GET", "/api/v1/engineering/runs")
        self.assertEqual(status, 200)
        self.assertEqual(runs["runs"], [])

    def test_real_syntax_job_over_http(self):
        status, completed = self.request("POST", "/api/v1/engineering/run",
                                         {"job": "moss-syntax", "operator_approved": True})
        self.assertEqual(status, 200)
        self.assertEqual(completed["status"], "PASS", completed)
        status, data = self.request("GET", "/api/v1/engineering/runs")
        self.assertEqual(status, 200)
        self.assertEqual(data["runs"][0]["id"], completed["id"])


if __name__ == "__main__":
    unittest.main()
