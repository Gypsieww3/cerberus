# C.E.R.B.E.R.U.S. — Integration Contract (Alpha 0.1)

Status: **implemented local read-only bridge**, not a remote-control agent or complete program integration.

## Start

On Windows, run `03_CERBERUS_CORE/ABRIR_CONTROL_PLANE.bat` (Python 3.11+ standard library).
Open `http://127.0.0.1:8890/` and enter the ephemeral access token shown in the terminal.
The token is not saved to browser storage. Never post it on GitHub.

Or run `py -3 03_CERBERUS_CORE/control_plane.py --once` for a one-off terminal snapshot.

## Contract

- `GET /healthz` — no authentication; reports the Control Plane process, **not** any downstream application.
- `GET /api/v1/services` — requires `Authorization: Bearer <token>`; responds with schema version 1 and an array of `id, name, kind, status`.
- `POST/PUT/PATCH/DELETE` — rejected (HTTP 405).
- Assets `/`, `/control_plane.js`, and `/control_plane.css` are served locally.
- Values: `reachable` (GET health responded 2xx), `unavailable` (could not confirm healthy endpoint), `not_integrated` (no probe exists).
- A service being reachable is **not** proof of secure operation, functional correctness, or commercial readiness.

## Known local probes

| Service | Probe | Limitation |
| --- | --- | --- |
| MOSS Lab | `127.0.0.1:8765/api/v1/health` | Historical MOSS engine is separate |
| Telemetry Studio | `127.0.0.1:8878/api/health` | CSV/SQLite app; does not read live industrial sensors |
| O Olho Que Tudo Vê | `127.0.0.1:8876/healthz` | **Set `OLHO_PORT=8876` before starting**, because MOSS Lab uses 8765 |
| Core Commander | Not integrated | No supported health adapter yet |
| Code Guard | Not integrated | Desktop product; no supported local API |
| TERRA VIVA | Not integrated | Public site is a static snapshot |

The probe targets are hard-coded reviewed loopback URLs: the API does not accept user-supplied URLs, paths or commands.

## Security constraints

Only binds to `127.0.0.1`. Local Bearer authentication uses a random token at each start, constant-time comparison, response `Cache-Control: no-store`, no wildcard CORS, CSP for static assets and no persistent log of tokens or queries. No filesystem writes, arbitrary scripts, plugin execution, cloud access or remote control. Anyone able to read the displayed token on the local computer can access the status list. Do not expose this development endpoint via reverse proxy or public tunnel.

## Next integration stages

1. Standardize opt-in health endpoints and API versions in desktop apps **without introducing PC command execution**.
2. Add durable, scoped capability permissions for individual agent actions.
3. Integrate event schema, audit log, sandbox execution, rollback and cancellation.
4. Validate on the owner's Windows environment and external test machines.
5. Consider a separate authenticated commercial API only after threat modelling.
