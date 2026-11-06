"""Bounded, read-only Python AST audit for the local CERBERUS code repository.

This scanner does NOT execute files or infer that a warning is a vulnerability.
Outputs evidence with file paths and line numbers for human review.
"""
from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP = frozenset({".git", "__pycache__", ".venv", "venv", "node_modules", ".pytest_cache"})
MAX_FILES = 2000
MAX_BYTES = 2_000_000
MAX_FINDINGS = 200


class SafetyVisitor(ast.NodeVisitor):
    def __init__(self, filename):
        self.filename = filename
        self.findings = []

    def mark(self, node, rule, detail, severity="warning"):
        if len(self.findings) < MAX_FINDINGS:
            self.findings.append({
                "file": self.filename, "line": node.lineno, "rule": rule,
                "severity": severity, "detail": detail
            })

    def visit_ExceptHandler(self, node):
        if node.type is None:
            self.mark(node, "BARE_EXCEPT", "Bare except catches BaseException and may hide shutdown signals.")
        self.generic_visit(node)

    def visit_Call(self, node):
        f = node.func
        if isinstance(f, ast.Name) and f.id in {"eval", "exec"}:
            self.mark(node, "DYNAMIC_EXECUTION", "Dynamic Python execution requires a careful security review.")
        if isinstance(f, ast.Attribute) and isinstance(f.value, ast.Name):
            if f.value.id == "os" and f.attr == "system":
                self.mark(node, "OS_SYSTEM", "Shell command via os.system should be reviewed.")
            if f.value.id == "subprocess" and f.attr in {"run", "Popen", "call", "check_output", "check_call"}:
                for kw in node.keywords:
                    if kw.arg == "shell" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                        self.mark(node, "SHELL_TRUE", "subprocess shell=True raises injection risk.")
        self.generic_visit(node)


def audit_sources(root=ROOT):
    base = Path(root).resolve()
    if not base.is_dir():
        raise ValueError("Project root directory does not exist")
    candidates = []
    for file in base.rglob("*.py"):
        if any(piece in SKIP for piece in file.relative_to(base).parts):
            continue
        if file.is_symlink() or not file.resolve().is_relative_to(base):
            continue
        candidates.append(file)
    candidates.sort()
    if len(candidates) > MAX_FILES:
        return {"files": len(candidates), "analyzed": 0, "findings": [],
                "status": "LIMIT_EXCEEDED", "truncated": True,
                "scope": "Source audit is incomplete; too many Python files"}
    counts = {"files": len(candidates), "analyzed": 0,
              "syntax_errors": 0, "warnings": 0, "functions": 0, "classes": 0}
    findings = []
    for file in candidates:
        relative = file.relative_to(base).as_posix()
        if file.stat().st_size > MAX_BYTES:
            findings.append({"file": relative, "line": 0, "rule": "LARGE_FILE",
                             "severity": "info", "detail": "Skipped file larger than 2 MB"})
            continue
        try:
            text = file.read_text(encoding="utf-8")
            tree = ast.parse(text, filename=relative)
        except (SyntaxError, UnicodeError) as exc:
            counts["syntax_errors"] += 1
            findings.append({"file": relative, "line": getattr(exc, "lineno", 0) or 0,
                             "rule": "PARSE_FAILURE", "severity": "error",
                             "detail": type(exc).__name__})
            continue
        counts["analyzed"] += 1
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                counts["functions"] += 1
            elif isinstance(node, ast.ClassDef):
                counts["classes"] += 1
        visitor = SafetyVisitor(relative)
        visitor.visit(tree)
        counts["warnings"] += len(visitor.findings)
        if len(findings) < MAX_FINDINGS:
            findings.extend(visitor.findings[:MAX_FINDINGS - len(findings)])
    return {**counts, "findings": findings,
            "truncated": len(findings) >= MAX_FINDINGS,
            "status": "ERRORS_FOUND" if counts["syntax_errors"] else "SCAN_COMPLETE",
            "scope": "Static AST heuristic only; no execution, dependency audit or security certification"}


if __name__ == "__main__":
    import json
    print(json.dumps(audit_sources(), indent=2, ensure_ascii=False))
