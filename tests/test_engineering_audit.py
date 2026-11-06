"""Verifiable syntax/heuristic audit and local UI contract tests."""
from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
import re
import sys
import tempfile
import unittest
from threading import Thread
import http.client
import json

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "01_MOSS_KYVRAEL"))
from engineering_audit import audit_sources
from api_server import create_server


class AuditorTests(unittest.TestCase):
    def test_detects_syntax_errors_and_risky_primitives_without_execution(self):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            (base / "safe.py").write_text("def square(x):\n    return x * x\n", encoding="utf-8")
            (base / "unsafe.py").write_text(
                "import subprocess\n"
                "def bad(x):\n"
                "    eval(x)\n"
                "    subprocess.run('echo hi', shell=True)\n"
                "    try:\n        pass\n    except:\n        pass\n",
                encoding="utf-8")
            (base / "broken.py").write_text("def broken(:\n    pass", encoding="utf-8")
            result = audit_sources(base)
            self.assertEqual(result["analyzed"], 2)
            self.assertEqual(result["syntax_errors"], 1)
            self.assertEqual(result["status"], "ERRORS_FOUND")
            rules = {x["rule"] for x in result["findings"]}
            self.assertTrue({"PARSE_FAILURE", "DYNAMIC_EXECUTION", "SHELL_TRUE",
                             "BARE_EXCEPT"} <= rules)

    def test_safe_code_reports_no_finding(self):
        with tempfile.TemporaryDirectory() as folder:
            (Path(folder) / "hello.py").write_text("value = sum(range(3))\n", encoding="utf-8")
            result = audit_sources(folder)
            self.assertEqual(result["syntax_errors"], 0)
            self.assertEqual(result["warnings"], 0)
            self.assertEqual(result["status"], "SCAN_COMPLETE")


class ElementIds(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
    def handle_starttag(self, tag, attrs):
        self.ids.extend(v for k,v in attrs if k == "id")


class FrontendContractTests(unittest.TestCase):
    def test_html_ids_match_script_references(self):
        markup = (ROOT / "01_MOSS_KYVRAEL" / "web" / "index.html").read_text(encoding="utf-8")
        script = (ROOT / "01_MOSS_KYVRAEL" / "web" / "app.js").read_text(encoding="utf-8")
        parser = ElementIds()
        parser.feed(markup)
        self.assertEqual(len(parser.ids), len(set(parser.ids)), "Duplicate HTML IDs")
        refs = set(re.findall(r'\$\("([a-z][\w-]*)"\)', script))
        self.assertFalse(refs - set(parser.ids), f"UI references missing IDs: {refs - set(parser.ids)}")
        for key in ("engineering-job", "engineering-audit", "engineering-runs"):
            self.assertIn(key, parser.ids)

    def test_ast_audit_requires_bearer_token(self):
        with tempfile.TemporaryDirectory() as folder:
            server = create_server(data_dir=folder, port=0, token="R" * 48)
            thread = Thread(target=server.serve_forever, kwargs={"poll_interval": .02}, daemon=True)
            thread.start()
            try:
                conn = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=20)
                conn.request("GET", "/api/v1/engineering/audit")
                response = conn.getresponse()
                self.assertEqual(response.status, 401)
                response.read()
                conn.close()
                conn = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=20)
                conn.request("GET", "/api/v1/engineering/audit",
                             headers={"Authorization": "Bearer " + "R" * 48})
                response = conn.getresponse()
                self.assertEqual(response.status, 200)
                result = json.loads(response.read())
                self.assertGreater(result["analyzed"], 0)
                self.assertIn("findings", result)
                conn.close()
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=5)


if __name__ == "__main__":
    unittest.main()
