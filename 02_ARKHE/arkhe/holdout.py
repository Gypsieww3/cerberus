"""Chronological holdout utilities; deterministic, without fitting or cherry-picking."""
from datetime import datetime
from hashlib import sha256
import json
import math

def _timestamp(value):
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise ValueError("Timezone-aware ISO timestamp required")
    return dt

def partition(rows, cutoff):
    """Split on a preregistered timestamp; reject duplicate identifiers."""
    boundary = _timestamp(cutoff)
    training, held_out, seen = [], [], set()
    for row in rows:
        identifier = row["id"]
        if not isinstance(identifier, str) or not identifier or identifier in seen:
            raise ValueError("Missing or duplicated observation id")
        seen.add(identifier)
        point = _timestamp(row["timestamp"])
        (training if point < boundary else held_out).append(dict(row))
    if not training or not held_out:
        raise ValueError("Non-empty chronological train and holdout sets required")
    return training, held_out

def frozen_signature(protocol):
    """Stable SHA-256 of explicitly supplied protocol and dataset provenance."""
    encoded = json.dumps(protocol, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    return sha256(encoded).hexdigest()

def evaluate(held_out, predictions):
    """Evaluate a supplied, unchanged prediction map against frozen observations."""
    if set(predictions) != {r["id"] for r in held_out}:
        raise ValueError("Predictions must match holdout ids exactly")
    errors = []
    for row in held_out:
        y, y_hat = row["target"], predictions[row["id"]]
        if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) for v in (y, y_hat)):
            raise ValueError("Finite numeric targets and predictions required")
        errors.append(y - y_hat)
    return {"count": len(errors), "mae": sum(abs(e) for e in errors) / len(errors),
            "rmse": math.sqrt(sum(e * e for e in errors) / len(errors)),
            "scope": "Holdout descriptive evaluation; no discovery or generalization claim"}
