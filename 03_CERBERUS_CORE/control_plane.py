"""C.E.R.B.E.R.U.S. Control Plane — read-only local service status bridge.

This bridge never executes external programs or accepts arbitrary probe URLs.
It only performs bounded GET health checks against reviewed loopback targets.
"""
from __future__ import annotations

import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import hmac
import json
import secrets
from pathlib import Path
from mission_engine import JobSupervisor, DEFAULT_DB, catalog
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

BASE = Path(__file__).resolve().parent
CATALOG = (
    {"id": "moss", "name": "MOSS Lab", "health_url": "http://127.0.0.1:8765/api/v1/health", "kind": "local_api"},
    {"id": "telemetry", "name": "Telemetry Studio", "health_url": "http://127.0.0.1:8878/api/health", "kind": "local_api"},
    {"id": "olho", "name": "O Olho Que Tudo Vê", "health_url": "http://127.0.0.1:8876/healthz", "kind": "local_api"},
    {"id": "commander", "name": "Core Commander", "health_url": None, "kind": "desktop_not_integrated"},
    {"id": "code_guard", "name": "Code Guard", "health_url": None, "kind": "desktop_not_integrated"},
    {"id": "terra_viva", "name": "TERRA VIVA", "health_url": None, "kind": "simulation_not_integrated"},
)

class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

_LOCAL_OPENER = build_opener(ProxyHandler({}), _NoRedirect())

def probe_service(service, timeout=0.4):
    """Return only observed reachability, never infer application readiness."""
    url = service["health_url"]
    if url is None:
        return "not_integrated"
    try:
        with _LOCAL_OPENER.open(Request(url, headers={"Accept": "application/json"}), timeout=timeout) as response:
            return "reachable" if 200 <= response.status < 300 else "unavailable"
    except (HTTPError, URLError, TimeoutError, OSError, ValueError):
        return "unavailable"

def snapshot(probe=probe_service):
    return [
        {"id": s["id"], "name": s["name"], "kind": s["kind"], "status": probe(s)}
        for s in CATALOG
    ]

def make_server(port=8890, token=None, probe=probe_service, mission_engine=None, mission_db=None):
    if not isinstance(port, int) or not 0 <= port <= 65535:
        raise ValueError("port must be 0..65535")
    secret = token if token is not None else secrets.token_urlsafe(32)
    if not isinstance(secret, str) or len(secret) < 32 or len(secret) > 512:
        raise ValueError("token must contain 32..512 characters")
    if any(c.isspace() or ord(c) < 33 or ord(c) > 126 for c in secret):
        raise ValueError("token must be printable ASCII without spaces")

    missions = mission_engine if mission_engine is not None else JobSupervisor(db_path=mission_db or DEFAULT_DB)

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):
            # Do not log URLs, headers, private notes or bearer tokens.
            return

        def send_json(self, status, payload):
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("X-Frame-Options", "DENY")
            self.send_header("Referrer-Policy", "no-referrer")
            self.end_headers()
            self.wfile.write(body)

        def send_asset(self, filename, mime):
            content = (BASE / filename).read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", mime)
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Security-Policy", "default-src 'none'; script-src 'self'; style-src 'self'; connect-src 'self'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'")
            self.end_headers()
            self.wfile.write(content)

        def authorized(self):
            values = self.headers.get_all("Authorization", [])
            prefix = "Bearer "
            return (len(values) == 1 and values[0].startswith(prefix)
                    and hmac.compare_digest(values[0][len(prefix):], secret))

        def same_origin(self):
            port_str = str(self.server.server_port)
            allowed = {"127.0.0.1:" + port_str, "localhost:" + port_str}
            host = self.headers.get("Host", "")
            origin = self.headers.get("Origin")
            return host in allowed and (origin is None or origin == "http://" + host)

        def read_json(self):
            if self.headers.get("Transfer-Encoding"):
                raise ValueError("Transferência não suportada")
            if self.headers.get("Content-Type", "").split(";")[0].strip().lower() != "application/json":
                raise ValueError("Content-Type deve ser application/json")
            try:
                size = int(self.headers.get("Content-Length", "-1"))
            except ValueError:
                raise ValueError("Content-Length inválido") from None
            if not 1 <= size <= 2048:
                raise ValueError("Corpo JSON deve ter entre 1 e 2048 bytes")
            raw = self.rfile.read(size)
            try:
                data = json.loads(raw.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                raise ValueError("JSON inválido") from None
            if type(data) is not dict:
                raise ValueError("Esperado objeto JSON")
            return data

        def do_GET(self):
            if self.path == "/":
                return self.send_asset("control_plane.html", "text/html; charset=utf-8")
            if self.path == "/control_plane.js":
                return self.send_asset("control_plane.js", "text/javascript; charset=utf-8")
            if self.path == "/control_plane.css":
                return self.send_asset("control_plane.css", "text/css; charset=utf-8")
            if self.path == "/healthz":
                return self.send_json(200, {"service": "cerberus-control-plane", "status": "ok", "mode": "supervised-docker"})
            if not self.same_origin():
                return self.send_json(403, {"error": "invalid host or origin"})
            if not self.authorized():
                return self.send_json(401, {"error": "authentication required"})
            if self.path == "/api/v1/services":
                return self.send_json(200, {"schema": 1, "services": snapshot(probe)})
            if self.path == "/api/v1/missions/catalog":
                return self.send_json(200, {"schema": 1, "tasks": catalog()})
            if self.path == "/api/v1/missions":
                return self.send_json(200, {"schema": 1, "missions": missions.recent()})
            if self.path.startswith("/api/v1/missions/"):
                mid = self.path[len("/api/v1/missions/"):]
                try:
                    item = missions.get(mid)
                except ValueError:
                    return self.send_json(400, {"error": "invalid mission ID"})
                return self.send_json(200, item) if item else self.send_json(404, {"error": "unknown mission"})
            return self.send_json(404, {"error": "route not found"})

        def do_POST(self):
            routes = ("/api/v1/missions/prepare", "/api/v1/missions/start", "/api/v1/missions/cancel")
            if self.path not in routes:
                return self.send_json(405, {"error": "method not allowed"})
            if not self.same_origin():
                return self.send_json(403, {"error": "invalid host or origin"})
            if not self.authorized():
                return self.send_json(401, {"error": "authentication required"})
            try:
                data = self.read_json()
                if self.path == routes[0]:
                    if set(data) != {"task_id"}:
                        raise ValueError("Payload não permitido")
                    return self.send_json(200, missions.prepare(data["task_id"]))
                if self.path == routes[1]:
                    if set(data) != {"ticket", "approve"}:
                        raise ValueError("Payload não permitido")
                    return self.send_json(202, missions.start(data["ticket"], data["approve"]))
                if set(data) != {"id"}:
                    raise ValueError("Payload não permitido")
                return self.send_json(202, missions.cancel(data["id"]))
            except ValueError as err:
                return self.send_json(400, {"error": str(err)})
            except RuntimeError as err:
                return self.send_json(409, {"error": str(err)})
        def method_not_allowed(self):
            return self.send_json(405, {"error": "method not allowed"})
        do_PUT = method_not_allowed
        do_DELETE = method_not_allowed
        do_PATCH = method_not_allowed

    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    server.auth_token = secret
    server.missions = missions
    return server

def main():
    parser = argparse.ArgumentParser(description="CERBERUS local, supervised engineering control plane")
    parser.add_argument("--port", type=int, default=8890)
    parser.add_argument("--once", action="store_true", help="Print a one-time status snapshot; no HTTP server")
    args = parser.parse_args()
    if args.once:
        print(json.dumps({"services": snapshot()}, ensure_ascii=False, indent=2))
        return
    with make_server(port=args.port) as server:
        print("CERBERUS Control Plane (Docker supervised): http://127.0.0.1:%d/" % server.server_port)
        print("Access token (do not share): " + server.auth_token)
        try:
            server.serve_forever(poll_interval=0.25)
        except KeyboardInterrupt:
            print("Encerramento solicitado")
        finally:
            server.missions.shutdown()

if __name__ == "__main__":
    main()
