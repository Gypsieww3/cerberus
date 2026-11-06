"""Offline Ollama gateway contract tests; no running Ollama is required."""
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "11_MODELOS_IA"))
from ollama_gateway import OllamaGateway, GatewayError


class DummyResponse:
    def __init__(self, value):
        self.data = json.dumps(value).encode("utf-8")
    def __enter__(self):
        return self
    def __exit__(self, *_args):
        return False
    def read(self, amount):
        return self.data[:amount]


class Tests(unittest.TestCase):
    def test_remote_endpoint_is_forbidden(self):
        with self.assertRaises(ValueError):
            OllamaGateway("https://example.org:11434")

    def test_list_models_offline(self):
        gateway = OllamaGateway()
        with patch("ollama_gateway.request.OpenerDirector.open",
                   return_value=DummyResponse({"models": [
                       {"name": "phi3:latest"}, {"name": "qwen2.5:1.5b"},
                       {"name": "phi3:latest"}]})) as mock_open:
            result = gateway.list_models()
            self.assertEqual(result, ["phi3:latest", "qwen2.5:1.5b"])
            self.assertEqual(mock_open.call_args.args[0].full_url,
                             "http://127.0.0.1:11434/api/tags")

    def test_generate_offline(self):
        gateway = OllamaGateway()
        with patch("ollama_gateway.request.OpenerDirector.open",
                   return_value=DummyResponse({"response": "Ola!"})) as mock_open:
            answer = gateway.generate("qwen2.5:1.5b", "Diz ola")
            self.assertEqual(answer, "Ola!")
            req = mock_open.call_args.args[0]
            self.assertEqual(req.full_url, "http://127.0.0.1:11434/api/generate")
            payload = json.loads(req.data)
            self.assertEqual(payload["stream"], False)
            self.assertEqual(payload["options"]["num_predict"], 256)

    def test_bad_model_name(self):
        with self.assertRaises(ValueError):
            OllamaGateway().generate("model /invalid", "hello")

    def test_invalid_models_response(self):
        with patch("ollama_gateway.request.OpenerDirector.open",
                   return_value=DummyResponse({"models": None})):
            with self.assertRaises(GatewayError):
                OllamaGateway().list_models()


if __name__ == "__main__":
    unittest.main()
