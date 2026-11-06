"""Pre-registered experiment metadata: freeze protocol before evaluating."""
from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json


@dataclass(frozen=True)
class ExperimentProtocol:
    question: str
    hypothesis: str
    metric: str
    cutoff_utc: str
    dataset_sha256: str
    baseline: str

    def __post_init__(self):
        if any(not isinstance(v, str) or not v.strip() for v in vars(self).values()):
            raise ValueError("All protocol fields are required")
        if len(self.dataset_sha256) != 64 or any(ch not in "0123456789abcdef" for ch in self.dataset_sha256):
            raise ValueError("dataset_sha256 must be lowercase SHA256 hex")
        from datetime import datetime
        moment = datetime.fromisoformat(self.cutoff_utc.replace("Z", "+00:00"))
        if moment.tzinfo is None or moment.utcoffset() is None:
            raise ValueError("Chronological cutoff must include a timezone")

    def digest(self):
        body = json.dumps(vars(self), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return sha256(body.encode("utf-8")).hexdigest()
