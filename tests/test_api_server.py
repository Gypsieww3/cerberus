"""MOSS Lab real HTTP tests. No Ollama service, network or external account needed."""
from __future__ import annotations

import http.client
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from threading import Thread
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "01_MOSS_KYVRAEL"))
from api_server import create_server


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.directory = TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.token = "a" * 48
        self.server = create_server(data_dir=self.directory.name, port=0, token=self.token)
        self.port = self.server.server_port
        self.thread = Thread(target=self.server.serve_forever,
                             kwargs={"poll_interval": 0.02}, daemon=True)
        self.thread.start()
        self.addCleanup(self.stop_server)

    def stop_server(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)

    def http(self, method, path, data=None, *, authorized=True, headers=None):
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=10)
        all_headers = dict(headers or {})
        if authorized:
            all_headers["Authorization"] = "Bearer " + self.token
        body = None
        if data is not None:
            body = json.dumps(data).encode("utf-8")
            all_headers["Content-Type"] = "application/json"
        try:
            conn.request(method, path, body=body, headers=all_headers)
            response = conn.getresponse()
            status, content_type = response.status, response.getheader("Content-Type", "")
            payload = response.read()
            if "application/json" in content_type:
                payload = json.loads(payload.decode("utf-8"))
            return status, payload
        finally:
            conn.close()

    def test_health_and_public_assets(self):
        status, health = self.http("GET", "/api/v1/health", authorized=False)
        self.assertEqual(status, 200)
        self.assertEqual(health["status"], "ok")
        for path in ["/", "/app.css", "/app.js"]:
            status, body = self.http("GET", path, authorized=False)
            self.assertEqual(status, 200, path)
            self.assertGreater(len(body), 100)

    def test_auth_is_required_and_checked(self):
        status, body = self.http("GET", "/api/v1/missions", authorized=False)
        self.assertEqual(status, 401)
        self.assertIn("Bearer", body["error"])
        status, body = self.http("GET", "/api/v1/missions",
                                 authorized=False, headers={"Authorization": "Bearer wrong"})
        self.assertEqual(status, 401)
        status, body = self.http("GET", "/api/v1/missions")
        self.assertEqual(status, 200)
        self.assertEqual(body["missions"], [])

    def test_origin_and_host_guard(self):
        status, _ = self.http("GET", "/api/v1/missions",
                              headers={"Origin": "https://hostile.example"})
        self.assertEqual(status, 403)
        status, _ = self.http("GET", "/api/v1/missions",
                              headers={"Host": "hostile.example"})
        self.assertEqual(status, 403)

    def test_mission_preview_and_events(self):
        status, mission = self.http("POST", "/api/v1/missions", {"title": "Rever RTL"})
        self.assertEqual(status, 201)
        self.assertEqual(mission["state"], "pending")
        status, preview = self.http("POST", "/api/v1/previews",
                                    {"title": "Plano seguro", "actions": ["inspect", "validate", "report"]})
        self.assertEqual(status, 201)
        self.assertEqual(preview["executed_actions"], 0)
        ident = preview["mission_id"]
        status, done = self.http("POST", "/api/v1/missions/" + ident + "/complete-preview", {})
        self.assertEqual(status, 200)
        self.assertEqual(done["order"], ["step-1", "step-2", "step-3"])
        status, events = self.http("GET", "/api/v1/missions/" + ident + "/events")
        self.assertEqual(status, 200)
        self.assertEqual(len(events["events"]), 3)
        status, listing = self.http("GET", "/api/v1/missions")
        self.assertEqual(status, 200)
        self.assertEqual(len(listing["missions"]), 2)

    def test_no_shell_actions_or_invalid_payload(self):
        status, obj = self.http("POST", "/api/v1/previews",
                                {"title": "Unsafe", "actions": ["shell"]})
        self.assertEqual(status, 422)
        status, obj = self.http("POST", "/api/v1/previews",
                                {"title": "Empty", "actions": []})
        self.assertEqual(status, 422)
        status, obj = self.http("GET", "/api/v1/missions/not-a-uuid")
        self.assertEqual(status, 400)
        status, obj = self.http("POST", "/api/v1/missions", {"title": "X", "unexpected": 1})
        self.assertEqual(status, 422)

    def test_notes_are_local_and_deletable(self):
        status, created = self.http("POST", "/api/v1/memory", {"text": "RISC V engineering note"})
        self.assertEqual(status, 201)
        status, found = self.http("GET", "/api/v1/memory?q=engineering")
        self.assertEqual(status, 200)
        self.assertEqual(found["results"][0]["id"], created["id"])
        status, deleted = self.http("DELETE", "/api/v1/memory/" + str(created["id"]))
        self.assertEqual(status, 200)
        self.assertTrue(deleted["deleted"])
        status, found = self.http("GET", "/api/v1/memory?q=engineering")
        self.assertEqual(found["results"], [])

    def test_ollama_adapter_contract(self):
        with patch("api_server.OllamaGateway") as gateway:
            gateway.return_value.list_models.return_value = ["qwen2.5:1.5b"]
            gateway.return_value.generate.return_value = "Resposta de teste"
            status, models = self.http("GET", "/api/v1/models")
            self.assertEqual(status, 200)
            self.assertEqual(models["models"], ["qwen2.5:1.5b"])
            status, answer = self.http("POST", "/api/v1/ask", {
                "model": "qwen2.5:1.5b", "prompt": "Ola MOSS", "max_tokens": 128})
            self.assertEqual(status, 200)
            self.assertEqual(answer["answer"], "Resposta de teste")
            self.assertEqual(answer["tools_executed"], 0)
            gateway.return_value.generate.assert_called_once_with(
                "qwen2.5:1.5b", "Ola MOSS", max_tokens=128)

    def test_api_is_loopback_only(self):
        self.assertEqual(self.server.server_address[0], "127.0.0.1")


if __name__ == "__main__":
    unittest.main()
