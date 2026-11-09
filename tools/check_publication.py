"""Fail CI when obviously sensitive local artefacts are accidentally tracked.

This is a hygiene gate, not a comprehensive secret scanner.
"""
from __future__ import annotations

from pathlib import PurePosixPath
import subprocess
import sys

BANNED_NAMES = {
    ".env", "id_rsa", "id_ed25519", "credentials.json",
    "secrets.json", ".netrc", "token.txt", "private.key",
}
BANNED_SUFFIXES = (".sqlite", ".sqlite3", ".db", ".p12", ".pfx", ".pem", ".key", ".log", ".exe", ".dll")
BANNED_PARTS = {"__pycache__", ".venv", "venv", "node_modules", ".pytest_cache"}

def forbidden(path):
    normalized = PurePosixPath(path.replace("\\", "/"))
    parts = normalized.parts
    name = normalized.name.lower()
    return (
        name in BANNED_NAMES
        or name.startswith(".env.")
        or name.endswith(BANNED_SUFFIXES)
        or any(part.lower() in BANNED_PARTS for part in parts)
    )

def main():
    result = subprocess.run(["git", "ls-files", "-z"], capture_output=True, check=True)
    paths = [p.decode("utf-8", "replace") for p in result.stdout.split(b"\0") if p]
    bad = [p for p in paths if forbidden(p)]
    if bad:
        print("Publication gate failed: review tracked paths (content not displayed).")
        for path in bad:
            print("  " + path)
        return 1
    print("Publication hygiene passed for %d tracked paths (not a secret audit)." % len(paths))
    return 0

if __name__ == "__main__":
    sys.exit(main())
