"""MOSS mission preview with bounded plans and an auditable journal.

No shell access, file editing, network calls or external actions are exposed.
"""
from __future__ import annotations
from dataclasses import asdict
import json
from safe_workflow import Step, plan

ALLOWED_PREVIEW_ACTIONS = frozenset({"inspect", "summarize", "validate", "report"})


def create_preview(store, title, steps):
    """Persist a plan preview. Only read-only action descriptors are allowed."""
    items = list(steps)
    result = plan(items, dry_run=True)
    payload = []
    for step in items:
        if step.action not in ALLOWED_PREVIEW_ACTIONS or step.requires_approval:
            raise PermissionError("Only read-only, non-privileged previews can be queued")
        payload.append(asdict(step))
    # Journal stores JSON-serializable data, not runnable code.
    mission_id = store.add(title, {"mode": "preview", "steps": payload, "order": result.order})
    return {"mission_id": mission_id, "state": "pending", "order": result.order,
            "executed_actions": 0, "dry_run": True}


def complete_preview(store, mission_id):
    """Complete the *preview*, not the actions described by the plan."""
    mission = store.get(mission_id)
    if mission["state"] != "pending" or mission["details"].get("mode") != "preview":
        raise ValueError("Only pending previews may be completed")
    store.transition(mission_id, "running", "Preview evaluation started; no external actions")
    try:
        steps = [Step(**s) for s in mission["details"]["steps"]]
        result = plan(steps, dry_run=True)
        store.transition(mission_id, "done", "Plan preview validated; executed actions: 0")
        return {"mission_id": mission_id, "preview_complete": True, "order": result.order,
                "executed_actions": 0, "dry_run": True}
    except Exception:
        store.transition(mission_id, "failed", "Preview validation failed")
        raise
