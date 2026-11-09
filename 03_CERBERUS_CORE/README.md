# CERBERUS Core / ecosystem

Source archive located: `CERBERUS_ECOSYSTEM_v0_6_PILOTOS.zip` (696 entries, many duplicates of independent projects and generated state).

The independent projects remain the canonical source. This folder is reserved for orchestration, cross-project APIs and reproducible pilot metrics; do not dump duplicate versions of MOSS/ARKHÉ/KIM here.

The archive describes 390 tests in a Linux validation environment. This is **not yet** proof of Windows readiness or live hardware/market operation.

## Control Plane Alpha 0.2 (operational subset)

- `control_plane.py`: HTTP interface at `127.0.0.1:8890` with random session token.
- `mission_engine.py`: fixed allowlist of three engineering tasks, **two-step approval**, Docker isolation, cancellation, SQLite audit log and restart recovery for interrupted task records.
- `control_plane.html/js/css`: local dashboard, including explicit approval and manual results refresh.
- `ABRIR_CONTROL_PLANE.bat`: local Windows launcher.

**Prerequisites:** Python 3.11+; Docker Desktop and a pre-cached `python:3.12-alpine` image for mission execution. Status checks work without Docker. No shell commands, custom paths, URL targets or package installations are accepted from the browser.

The Control Plane is **not** the separate proprietary desktop Core Commander, not a replacement for MOSS, and does not provide permission for autonomous changes to files. See [integration and security contract](../docs/INTEGRATION_CONTRACT.md).
