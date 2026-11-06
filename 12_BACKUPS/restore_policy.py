"""Backup manifest verification without overwriting original files."""
from __future__ import annotations
from hashlib import sha256
from pathlib import Path


def verify_manifest(root, manifest):
    base = Path(root).resolve()
    results = []
    if not isinstance(manifest, list):
        raise ValueError("Manifest must be a list")
    for entry in manifest:
        name, expected = entry["path"], entry["sha256"]
        if not isinstance(name, str) or not isinstance(expected, str) or len(expected) != 64:
            raise ValueError("Invalid manifest entry")
        rel = Path(name)
        if rel.is_absolute() or ".." in rel.parts or not rel.parts:
            raise ValueError("Unsafe file path")
        destination = (base / rel).resolve()
        if not destination.is_relative_to(base):
            raise ValueError("Manifest contains path outside root or symlink escape")
        if not destination.is_file():
            results.append({"path": name, "status": "MISSING"})
            continue
        hasher = sha256()
        with destination.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                hasher.update(chunk)
        results.append({"path": name, "status": "OK" if hasher.hexdigest() == expected else "CHANGED"})
    return {"verified": all(item["status"] == "OK" for item in results), "files": results}
