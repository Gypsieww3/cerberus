"""Explicit recovery of stale missions; never restarts arbitrary actions."""
from __future__ import annotations
from datetime import datetime, timezone
import math


def recover_stale(store, older_than_seconds=3600, *, now=None):
    """Mark stale 'running' missions as failed; operator decides if retried.

    Only the mission journal changes. No tool or agent action is executed.
    """
    if (isinstance(older_than_seconds, bool) or
        not isinstance(older_than_seconds, (int, float)) or
        not math.isfinite(older_than_seconds) or older_than_seconds <= 0):
        raise ValueError("older_than_seconds must be finite and positive")
    moment = now or datetime.now(timezone.utc)
    if not isinstance(moment, datetime) or moment.tzinfo is None or moment.utcoffset() is None:
        raise ValueError("now must be a timezone-aware datetime")
    recovered = []
    for mission in store.list(state="running", limit=1000):
        changed = datetime.fromisoformat(mission["updated_at"])
        if changed.tzinfo is None or changed.utcoffset() is None:
            raise ValueError("Stored timestamp has no timezone")
        elapsed = (moment - changed).total_seconds()
        if elapsed >= older_than_seconds:
            try:
                store.transition(mission["id"], "failed", "Marked stale by explicit recovery scan")
                recovered.append(mission["id"])
            except ValueError:
                # Another worker may have completed it concurrently.
                continue
    return recovered


def request_retry(store, mission_id, *, operator_approved=False):
    """Explicitly move a failed mission back to pending; does not run it."""
    if operator_approved is not True:
        raise PermissionError("Explicit operator approval required")
    return store.transition(mission_id, "pending", "Operator-authorized retry request")
