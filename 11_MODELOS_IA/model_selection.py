"""Pure, offline Ollama model selector by local constraints.

Estimates are heuristics, not benchmark or hardware capability guarantees.
"""
from __future__ import annotations


def choose_model(models, available_ram_gb, *, task="general"):
    if task not in {"general", "code", "reasoning"}:
        raise ValueError("Unsupported task")
    if isinstance(available_ram_gb, bool) or not isinstance(available_ram_gb, (float, int)) or not 0 < available_ram_gb <= 1024:
        raise ValueError("Invalid available RAM")
    ranked = []
    for item in models:
        name, footprint, tags = item["name"], item["disk_gb"], item.get("tags", [])
        if not isinstance(name, str) or not name or isinstance(footprint, bool) or not isinstance(footprint, (float, int)) or not 0 < footprint <= 1000:
            raise ValueError("Invalid model entry")
        if not isinstance(tags, list) or any(not isinstance(x, str) for x in tags):
            raise ValueError("Invalid model tags")
        # Runtime overhead/headroom is highly device-specific; use conservative filter.
        if available_ram_gb < footprint * 1.5 + 1.0:
            continue
        preference = 1 if task in tags else 0
        ranked.append((preference, footprint, name))
    ranked.sort(key=lambda r: (-r[0], -r[1], r[2]))
    return {"recommended": ranked[0][2] if ranked else None,
            "eligible": [x[2] for x in ranked],
            "note": "Disk size is not runtime RAM usage; verify with real measurements."}
