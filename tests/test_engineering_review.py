"""MOSS real read-only review mission and HTTP contract tests."""
from pathlib import Path
import sys
import tempfile
import unittest
from threading import Thread
import http.client
import json

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "01_MOSS_KYVRAEL"))
from mission_store import MissionStore
from engineering_review import EngineeringReviews
from api_server import create_server


class ReviewUnitTests(unittest.TestCase):
    def test_mission_evidence_persists_with_zero_modified_files(self):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            journal = MissionStore(base / "missions.sqlite3")
            reviews = EngineeringReviews(journal, base / "reports.sqlite3")
            with self.assertRaises(PermissionError):
                reviews.execute("Refuse unapproved review")
            self.assertEqual(journal.list(), [])
            result = reviews.execute("Real read-only review", operator_approved=True)
            self.assertEqual(journal.get(result["mission_id"])["state"], "done")
            self.assertEqual(result["report"]["files_modified"], 0)
            self.assertEqual(result["report"]["tools_executed"],
                             ["inventory", "python_ast_audit"])
            self.assertGreater(result["report"]["inventory"]["total_source_files"], 0)
            self.assertEqual(EngineeringReviews(journal, base / "reports.sqlite3")
                             .get(result["mission_id"])["report"], result["report"])
            self.assertEqual(len(journal.events(result["mission_id"])), 3)

    def test_empty_title_rejected_without_mission(self):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            journal = MissionStore(base / "missions.sqlite3")
            reviews = EngineeringReviews(journal, base / "reports.sqlite3")
            with self.assertRaises(ValueError):
                reviews.execute("", operator_approved=True)
            self.assertEqual(journal.list(), [])


class ReviewHttpTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.server = create_server(data_dir=self.tmp.name, port=0, token="T" * 48)
        self.thread = Thread(target=self.server.serve_forever,
                             kwargs={"poll_interval": .02}, daemon=True)
        self.thread.start()
        self.addCleanup(self.close)

    def close(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)

    def request(self, method, url, data=None, auth=True):
        conn = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=25)
        headers = {}
        if auth:
            headers["Authorization"] = "Bearer " + "T" * 48
        body = None
        if data is not None:
            headers["Content-Type"] = "application/json"
            body = json.dumps(data).encode("utf-8")
        try:
            conn.request(method, url, body=body, headers=headers)
            response = conn.getresponse()
            return response.status, json.loads(response.read())
        finally:
            conn.close()

    def test_review_api_authorization_and_persistence(self):
        payload = {"title": "Verificar MOSS", "operator_approved": True}
        self.assertEqual(self.request("POST", "/api/v1/engineering/reviews",
                                       payload, auth=False)[0], 401)
        self.assertEqual(self.request("POST", "/api/v1/engineering/reviews",
                                       {"title": "Verificar MOSS",
                                        "operator_approved": False})[0], 403)
        status, record = self.request("POST", "/api/v1/engineering/reviews", payload)
        self.assertEqual(status, 201, record)
        self.assertEqual(record["report"]["files_modified"], 0)
        status, stored = self.request("GET", "/api/v1/engineering/reviews")
        self.assertEqual(status, 200)
        self.assertEqual(stored["reviews"][0]["mission_id"], record["mission_id"])
        status, mission = self.request("GET", "/api/v1/missions/" + record["mission_id"])
        self.assertEqual(status, 200)
        self.assertEqual(mission["state"], "done")


if __name__ == "__main__":
    unittest.main()
