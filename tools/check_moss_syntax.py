"""AST-based syntax validation for source files in MOSS Lab; no imports or pycache."""
from __future__ import annotations
import ast
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1] / "01_MOSS_KYVRAEL"


def validate():
    files = sorted(ROOT.glob("*.py"))
    failures = []
    if not files:
        raise RuntimeError("No Python files found in MOSS directory")
    for file in files:
        try:
            ast.parse(file.read_text(encoding="utf-8"), filename=file.name)
        except (SyntaxError, UnicodeError) as exc:
            failures.append({"file": file.name, "error": type(exc).__name__})
    return {"source_files": len(files), "failures": failures,
            "scope": "AST syntax only; does not run modules or verify runtime behavior"}


def main():
    result = validate()
    print(json.dumps(result, ensure_ascii=False))
    return 0 if not result["failures"] else 1


if __name__ == "__main__":
    sys.exit(main())
