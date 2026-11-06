"""Import a hash-verified, source-only MOSS legacy ZIP into an ignored folder.

The importer does not execute imported files and does not overwrite existing data.
Only archives with the reviewed-source layout and an SHA-256 manifest are accepted.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path, PurePosixPath
import shutil
import stat
from tempfile import TemporaryDirectory
from zipfile import ZipFile, BadZipFile

REPO = Path(__file__).resolve().parents[1]
DEST = REPO / "01_MOSS_KYVRAEL" / "legacy_v5_25_4"
PREFIX = "MOSS_ORIGINAL_5_25_4/"
MAX_FILES = 300
MAX_TOTAL_BYTES = 20_000_000
MAX_ONE_BYTES = 2_000_000
ALLOWED_DIRS = frozenset({"moss", "tests", "testes_independentes", "validation"})


def allowed_source(rel):
    path = PurePosixPath(rel)
    if not path.parts or path.is_absolute() or ".." in path.parts or "\\" in rel:
        return False
    return path.suffix == ".py" and (len(path.parts) == 1 or path.parts[0] in ALLOWED_DIRS)


def inspect_archive(zip_path):
    zip_path = Path(zip_path)
    if not zip_path.is_file():
        raise ValueError("Source ZIP was not found")
    try:
        with ZipFile(zip_path) as z:
            lookup = {info.filename: info for info in z.infolist() if not info.is_dir()}
            if len(lookup) != len([i for i in z.infolist() if not i.is_dir()]):
                raise ValueError("Duplicate filenames in ZIP")
            manifest_name = PREFIX + "MANIFEST.json"
            if manifest_name not in lookup:
                raise ValueError("Missing SHA-256 manifest")
            if lookup[manifest_name].file_size > MAX_ONE_BYTES:
                raise ValueError("Manifest too large")
            manifest = json.loads(z.read(manifest_name))
            if manifest.get("version") != "5.25.4":
                raise ValueError("Wrong source version")
            expected = manifest.get("sha256")
            if not isinstance(expected, dict) or not 1 <= len(expected) <= MAX_FILES:
                raise ValueError("Invalid manifest")
            actual = {}
            total = 0
            for info in z.infolist():
                if info.is_dir():
                    continue
                if not info.filename.startswith(PREFIX):
                    raise ValueError("Unexpected archive root")
                rel = info.filename[len(PREFIX):]
                if rel in ("MANIFEST.json", "LEIA_PRIMEIRO.md"):
                    continue
                if not allowed_source(rel):
                    raise ValueError("Forbidden source path: " + rel)
                unix_mode = (info.external_attr >> 16) & 0o170000
                if unix_mode == stat.S_IFLNK:
                    raise ValueError("Symlinks are not imported")
                if info.file_size > MAX_ONE_BYTES:
                    raise ValueError("Source file exceeds size limit")
                total += info.file_size
                if total > MAX_TOTAL_BYTES:
                    raise ValueError("Total uncompressed size exceeds limit")
                body = z.read(info)
                checksum = sha256(body).hexdigest()
                if checksum != expected.get(rel):
                    raise ValueError("SHA-256 mismatch: " + rel)
                actual[rel] = body
            if set(actual) != set(expected):
                raise ValueError("Manifest file list mismatch")
            if not any(key.startswith("moss/") for key in actual):
                raise ValueError("No MOSS package found")
    except (BadZipFile, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("Unreadable source ZIP or manifest") from exc
    return actual


def import_archive(zip_path, *, apply=False, destination=DEST):
    destination = Path(destination).resolve()
    sources = inspect_archive(zip_path)
    if destination.exists():
        raise FileExistsError("Target already exists; refusing to overwrite: " + str(destination))
    summary = {"source_files": len(sources), "target": str(destination),
               "status": "PREVIEW", "code_executed": False}
    if not apply:
        return summary
    destination.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix=".moss-import-", dir=destination.parent) as tmp:
        staged = Path(tmp) / "source"
        staged.mkdir()
        for name, body in sources.items():
            target = staged / PurePosixPath(name)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(body)
        # Rename on the same volume; never replace existing sources.
        staged.rename(destination)
    return {**summary, "status": "IMPORTED"}


def main(argv=None):
    parser = argparse.ArgumentParser(description="Stage reviewed MOSS 5.25.4 source offline")
    parser.add_argument("zip", type=Path)
    parser.add_argument("--apply", action="store_true",
                        help="Explicitly import code after preview, without executing it")
    args = parser.parse_args(argv)
    try:
        report = import_archive(args.zip, apply=args.apply)
    except (ValueError, FileExistsError, OSError) as exc:
        parser.exit(2, f"IMPORT ERROR: {exc}\n")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
