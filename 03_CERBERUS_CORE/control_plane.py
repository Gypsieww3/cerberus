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

def make_server(port=8890, token=None, probe=probe_service):
    if not isinstance(port, int) or not 0 <= port <= 65535:
        raise ValueError("port must be 0..65535")
    secret = token if token is not None else secrets.token_urlsafe(32)
    if not isinstance(secret, str) or len(secret) < 32 or len(secret) > 512:
        raise ValueError("token must contain 32..512 characters")
    if any(c.isspace() or ord(c) < 33 or ord(c) > 126 for c in secret):
        raise ValueError("token must be printable ASCII without spaces")

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

        def do_GET(self):
            if self.path == "/":
                return self.send_asset("control_plane.html", "text/html; charset=utf-8")
            if self.path == "/control_plane.js":
                return self.send_asset("control_plane.js", "text/javascript; charset=utf-8")
            if self.path == "/control_plane.css":
                return self.send_asset("control_plane.css", "text/css; charset=utf-8")
            if self.path == "/healthz":
                return self.send_json(200, {"service": "cerberus-control-plane", "status": "ok", "mode": "read-only"})
            supplied = self.headers.get("Authorization", "")
            prefix = "Bearer "
            if not supplied.startswith(prefix) or not hmac.compare_digest(supplied[len(prefix):], secret):
                return self.send_json(401, {"error": "authentication required"})
            if self.path == "/api/v1/services":
                return self.send_json(200, {"schema": 1, "services": snapshot(probe)})
            return self.send_json(404, {"error": "route not found"})

        def do_POST(self):
            return self.send_json(405, {"error": "read-only API"})
        do_PUT = do_POST
        do_DELETE = do_POST
        do_PATCH = do_POST

    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    server.auth_token = secret
    return server

def main():
    parser = argparse.ArgumentParser(description="CERBERUS local, read-only control plane")
    parser.add_argument("--port", type=int, default=8890)
    parser.add_argument("--once", action="store_true", help="Print a one-time status snapshot; no HTTP server")
    args = parser.parse_args()
    if args.once:
        print(json.dumps({"services": snapshot()}, ensure_ascii=False, indent=2))
        return
    with make_server(port=args.port) as server:
        print("CERBERUS Control Plane: http://127.0.0.1:%d/" % server.server_port)
        print("Access token (do not share): " + server.auth_token)
        server.serve_forever(poll_interval=0.25)

if __name__ == "__main__":
    main()
