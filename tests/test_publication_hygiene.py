"""Test that the repository publication hygiene gate rejects obvious accidents."""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from check_publication import forbidden

class PublicationHygieneTests(unittest.TestCase):
    def test_rejects_sensitive_artifacts(self):
        for path in (".env", ".env.production", "private.key", "data/users.sqlite3",
                     "logs/app.log", ".venv/Lib/site.py", "__pycache__/a.pyc",
                     "dist/app.exe", "credentials.json", "cert.pfx"):
            with self.subTest(path=path):
                self.assertTrue(forbidden(path))

    def test_allows_source_and_docs(self):
        for path in ("src/core.py", "docs/ROADMAP.md", ".github/workflows/engineering-smoke.yml",
                     "tests/test_api_server.py", "README.md", "docs/secret_handling.md"):
            with self.subTest(path=path):
                self.assertFalse(forbidden(path))
