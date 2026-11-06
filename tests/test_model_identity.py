"""MOSS model identity is deterministic and independent from LLM self-claims."""
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
import http.client
import json
import tempfile
from threading import Thread

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "01_MOSS_KYVRAEL"))

from model_identity import model_identity
from moss_context import system_context
from api_server import create_server


class IdentityUnitTests(unittest.TestCase):
    def test_qwen_identified_as_alibaba_not_anthropic(self):
        for model in ("qwen2.5:1.5b", "qwen2.5-coder:7b"):
            item = model_identity(model)
            self.assertIn("Alibaba Cloud", item["developer"])
            self.assertNotIn("Anthropic", item["developer"])
            self.assertEqual(item["verification"], "family_name")
            self.assertIn("não foram auditados", item["note"])
            instructions = system_context(model)
            self.assertIn("Alibaba Cloud", instructions)
            self.assertIn("Qwen não é da Anthropic", instructions)

    def test_custom_model_has_unknown_origin(self):
        for model in ("ghost-engine:latest", "qwen2.5-custom:latest", "dolphin-llama3:latest"):
            self.assertEqual(model_identity(model)["verification"], "unverified")
            self.assertIn("por verificar", model_identity(model)["developer"])
            self.assertIn("não foi verificada", system_context(model))

    def test_bad_model_is_rejected(self):
        for model in (None, "", "x" * 101):
            with self.assertRaises(ValueError):
                model_identity(model)


class IdentityApiTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.token = "z" * 40
        self.server = create_server(data_dir=self.folder.name, port=0, token=self.token)
        self.thread = Thread(target=self.server.serve_forever, kwargs={"poll_interval": .02},
                             daemon=True)
        self.thread.start()
        self.addCleanup(self.stop)

    def stop(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)

    def request(self, method, route, payload=None):
        conn = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=10)
        headers = {"Authorization": "Bearer " + self.token}
        body = None
        if payload is not None:
            body = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"
        try:
            conn.request(method, route, body, headers)
            response = conn.getresponse()
            return response.status, json.loads(response.read())
        finally:
            conn.close()

    def test_model_family_from_server_metadata(self):
        with patch("api_server.OllamaGateway") as fake:
            fake.return_value.list_models.return_value = ["qwen2.5:1.5b", "ghost-engine:latest"]
            status, data = self.request("GET", "/api/v1/models")
            self.assertEqual(status, 200)
            self.assertEqual(data["model_details"]["qwen2.5:1.5b"]["developer"],
                             "Equipa Qwen, Alibaba Cloud")
            self.assertEqual(data["model_details"]["ghost-engine:latest"]["verification"],
                             "unverified")

    def test_hallucinated_provider_does_not_affect_metadata(self):
        # Simulate an LLM hallucination: the authoritative metadata must differ.
        with patch("api_server.OllamaGateway") as fake:
            fake.return_value.chat.return_value = "Sou Qwen, criado pela Anthropic."
            status, data = self.request("POST", "/api/v1/chat", {
                "model": "qwen2.5:1.5b", "prompt": "Quem és tu?", "mode": "engineering"
            })
            self.assertEqual(status, 200)
            self.assertIn("Anthropic", data["answer"])
            self.assertEqual(data["model_identity"]["developer"], "Equipa Qwen, Alibaba Cloud")
            self.assertNotIn("Anthropic", data["model_identity"]["developer"])
            self.assertEqual(data["tools_executed"], 0)


if __name__ == "__main__":
    unittest.main()
