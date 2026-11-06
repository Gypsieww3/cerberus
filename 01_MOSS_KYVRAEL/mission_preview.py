"""Bounded MOSS mission previews with an auditable journal.

No shell, network, file-writing or external tool executor is provided.
"""
from dataclasses import asdict
from safe_workflow import Step, plan

PREVIEW_ACTIONS = frozenset({"inspect", "summarize", "validate", "report"})

def create_preview(store, title, steps):
    items = list(steps)
    result = plan(items, dry_run=True)
    payload = []
    for step in items:
        if step.action not in PREVIEW_ACTIONS or step.requires_approval:
            raise PermissionError("Read-only plan descriptors only")
        record = asdict(step)
        record["dependencies"] = list(record["dependencies"])
        payload.append(record)
    identifier = store.add(title, {"mode": "preview", "steps": payload, "order": result.order})
    return {"mission_id": identifier, "state": "pending", "order": result.order,
            "executed_actions": 0, "dry_run": True}

def complete_preview(store, mission_id):
    mission = store.get(mission_id)
    if mission["state"] != "pending" or mission["details"].get("mode") != "preview":
        raise ValueError("Only pending previews may be completed")
    store.transition(mission_id, "running", "Evaluating plan, no external actions")
    try:
        steps = [Step(identifier=s["identifier"], action=s["action"],
                      dependencies=tuple(s["dependencies"]),
                      requires_approval=s["requires_approval"])
                 for s in mission["details"]["steps"]]
        result = plan(steps, dry_run=True)
        store.transition(mission_id, "done", "Preview completed without external actions")
        return {"mission_id": mission_id, "order": result.order,
                "preview_complete": True, "dry_run": True, "executed_actions": 0}
    except Exception:
        store.transition(mission_id, "failed", "Preview validation failed")
        raise
