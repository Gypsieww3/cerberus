"""Deterministic plan validator: no system calls, files modified or tool execution."""
from dataclasses import dataclass, field

READ_ONLY = frozenset({"inspect", "summarize", "validate", "report"})
MAX_STEPS = 128

@dataclass(frozen=True)
class Step:
    identifier: str
    action: str
    dependencies: tuple[str, ...] = ()
    requires_approval: bool = False

@dataclass
class PlanResult:
    order: list[str] = field(default_factory=list)
    pending_approval: list[str] = field(default_factory=list)
    executable: bool = False
    dry_run: bool = True

def plan(steps, approvals=(), *, dry_run=True):
    """Topologically order bounded plans; never perform planned actions.

    Unknown/mutating actions are *always* marked for separate approval.
    Approvals are only metadata; no executor is provided.
    """
    steps = list(steps)
    if not 1 <= len(steps) <= MAX_STEPS:
        raise ValueError("Plan length must be between 1 and 128")
    ids = [s.identifier for s in steps]
    if any(not isinstance(s.identifier, str) or not s.identifier.strip() for s in steps):
        raise ValueError("Invalid step identifier")
    if len(set(ids)) != len(ids):
        raise ValueError("Duplicate step identifiers")
    by_id = {s.identifier: s for s in steps}
    for s in steps:
        if not isinstance(s.action, str) or not isinstance(s.dependencies, tuple):
            raise ValueError("Invalid step")
        if s.identifier in s.dependencies:
            raise ValueError("Self-dependency")
        if any(d not in by_id for d in s.dependencies):
            raise ValueError("Unknown dependency")
    order = []
    unresolved = set(ids)
    while unresolved:
        available = [i for i in ids if i in unresolved and all(d in order for d in by_id[i].dependencies)]
        if not available:
            raise ValueError("Cyclic plan dependency")
        order.extend(available)
        unresolved.difference_update(available)
    approved = set(approvals)
    needed = [i for i in order if by_id[i].requires_approval or by_id[i].action not in READ_ONLY]
    pending = [i for i in needed if i not in approved]
    return PlanResult(order, pending, executable=(not pending and not dry_run), dry_run=bool(dry_run))
