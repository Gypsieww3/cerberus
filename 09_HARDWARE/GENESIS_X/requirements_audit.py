"""GENESIS X requirements audit: no assumptions about physical prototypes."""
from __future__ import annotations
from collections import Counter

STATES = frozenset({"concept", "specified", "prototype", "verified", "blocked"})
EVIDENCE_REQUIRED = frozenset({"prototype", "verified"})


def audit_requirements(requirements):
    if not isinstance(requirements, list) or not requirements:
        raise ValueError("Nonempty list of requirements required")
    seen, issues, stats = set(), [], Counter()
    for i, req in enumerate(requirements):
        if not isinstance(req, dict):
            raise ValueError("Requirement must be a mapping")
        code, state = req.get("id"), req.get("state")
        if not isinstance(code, str) or not code.strip() or code in seen:
            raise ValueError("Requirement IDs must be unique nonempty strings")
        if state not in STATES:
            raise ValueError("Unknown requirement state")
        seen.add(code)
        stats[state] += 1
        evidence = req.get("evidence", [])
        if not isinstance(evidence, list) or any(not isinstance(x, str) for x in evidence):
            raise ValueError("Evidence must be a list of text references")
        if state in EVIDENCE_REQUIRED and not any(e.strip() for e in evidence):
            issues.append({"id": code, "problem": "MISSING_EVIDENCE"})
        if state == "verified" and not req.get("acceptance_test"):
            issues.append({"id": code, "problem": "MISSING_ACCEPTANCE_TEST"})
    return {"count": len(requirements), "states": dict(stats),
            "issues": issues, "auditable": not issues,
            "scope": "Documentation consistency only; does not validate device hardware"}
