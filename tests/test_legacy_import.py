"""MOSS legacy importer invariants using entirely synthetic ZIP archives."""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from import_legacy_moss import import_archive, inspect_archive, PREFIX


def archive_at(path, *, tamper=False, bad_path=False, version="5.25.4"):
    files = {
        "moss/__init__.py": b"",
        "moss/core.py": b"class MossCore:\n    pass\n",
        "tests/test_placeholder.py": b"import unittest\n",
    }
    manifest = {
        "version": version,
        "sha256": {name: sha256(data).hexdigest() for name, data in files.items()},
    }
    with ZipFile(path, "w") as z:
        z.writestr(PREFIX + "MANIFEST.json", json.dumps(manifest))
        z.writestr(PREFIX + "LEIA_PRIMEIRO.md", "test")
        for name, data in files.items():
            z.writestr(PREFIX + name, data + (b"# changed" if tamper and name == "moss/core.py" else b""))
        if bad_path:
            z.writestr(PREFIX + "../credentials.txt", "secret")


class ImportTests(unittest.TestCase):
    def test_preview_does_not_write_and_import_is_explicit(self):
        with TemporaryDirectory() as folder:
            base = Path(folder)
            zip_path, dest = base / "source.zip", base / "legacy"
            archive_at(zip_path)
            preview = import_archive(zip_path, destination=dest)
            self.assertEqual(preview["status"], "PREVIEW")
            self.assertFalse(dest.exists())
            report = import_archive(zip_path, apply=True, destination=dest)
            self.assertEqual(report["status"], "IMPORTED")
            self.assertTrue((dest / "moss" / "core.py").exists())
            with self.assertRaises(FileExistsError):
                import_archive(zip_path, apply=True, destination=dest)

    def test_checksums_checked_before_writing(self):
        with TemporaryDirectory() as folder:
            base = Path(folder)
            zip_path, dest = base / "source.zip", base / "legacy"
            archive_at(zip_path, tamper=True)
            with self.assertRaises(ValueError):
                import_archive(zip_path, apply=True, destination=dest)
            self.assertFalse(dest.exists())

    def test_traversal_is_forbidden(self):
        with TemporaryDirectory() as folder:
            zip_path = Path(folder) / "source.zip"
            archive_at(zip_path, bad_path=True)
            with self.assertRaises(ValueError):
                inspect_archive(zip_path)

    def test_wrong_version_is_rejected(self):
        with TemporaryDirectory() as folder:
            zip_path = Path(folder) / "source.zip"
            archive_at(zip_path, version="5.25.3")
            with self.assertRaises(ValueError):
                inspect_archive(zip_path)

    def test_missing_archive(self):
        with TemporaryDirectory() as folder:
            with self.assertRaises(ValueError):
                inspect_archive(Path(folder) / "missing.zip")


if __name__ == "__main__":
    unittest.main()
