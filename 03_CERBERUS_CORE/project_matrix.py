"""Describe source actually present in the repo; do not imply placeholder projects are built."""
from __future__ import annotations
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_EXT = frozenset({".py", ".sv", ".v", ".cpp", ".c", ".h", ".hpp", ".js", ".ts", ".html"})
EXCLUDE = frozenset({".git", "__pycache__", ".venv", "node_modules", ".pytest_cache"})

def inventory(root=ROOT):
    root = Path(root)
    projects = []
    for directory in sorted(root.iterdir()):
        if not directory.is_dir() or not (len(directory.name) >= 3 and directory.name[:2].isdigit() and directory.name[2] == "_"):
            continue
        files = [path for path in directory.rglob("*")
                 if path.is_file() and not any(p in EXCLUDE for p in path.relative_to(directory).parts)]
        code = [p for p in files if p.suffix.lower() in SOURCE_EXT]
        projects.append({"folder": directory.name, "files": len(files),
                         "source_files": len(code),
                         "stage": "SOURCE_PRESENT" if code else "DOCUMENTATION_ONLY",
                         "note": "Source existence is not proof of functional readiness"})
    return {"projects": projects,
            "total_source_files": sum(p["source_files"] for p in projects),
            "scope": "Files currently present in this directory tree"}

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    print(json.dumps(inventory(args.root), indent=2, ensure_ascii=False))
