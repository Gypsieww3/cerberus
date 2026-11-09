"""Keep the public product showcase honest, accessible and separate from private source."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

class PublicCatalogTests(unittest.TestCase):
    def test_new_public_products_are_linked(self):
        html = (ROOT / "projects.html").read_text(encoding="utf-8")
        self.assertIn('id="novos-produtos"', html)
        self.assertIn("cerberus-terra-viva-demo", html)
        self.assertIn("docs/TELEMETRY_STUDIO_PUBLIC.md", html)
        self.assertIn("docs/CORE_COMMANDER_PUBLIC.md", html)
        self.assertIn("Code Guard", html)

    def test_private_source_not_linked_as_public_download(self):
        html = (ROOT / "projects.html").read_text(encoding="utf-8")
        self.assertNotIn("cerberus-code-guard-private", html)
        self.assertNotIn("cerberus-core-commander-private", html)

    def test_public_documents_exist(self):
        self.assertTrue((ROOT / "docs" / "TELEMETRY_STUDIO_PUBLIC.md").is_file())
        self.assertTrue((ROOT / "docs" / "CORE_COMMANDER_PUBLIC.md").is_file())

if __name__ == "__main__":
    unittest.main()
