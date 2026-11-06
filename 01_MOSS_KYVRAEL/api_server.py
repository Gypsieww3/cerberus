"""MOSS Lab local REST API. No AI-generated code execution or OS control.

This server is intentionally loopback-only. It is not an Internet-facing
production deployment and does not replace the full legacy MOSS/KYVRAEL engine.
"""
from __future__ import annotations

import argparse
from collections import Counter
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import hmac
import json
import logging
import os
from pathlib import Path
from threading import Lock
import secrets
import sqlite3
import sys
from urllib.parse import parse_qs, urlsplit
from uuid import UUID

from lexical_memory import MemoryIndex
from chat_store import ChatStore
from engineering_tools import EngineeringBusy, EngineeringRunner
from moss_context import MODES, system_context
from model_identity import model_identity
from mission_preview import complete_preview, create_preview
from mission_recovery import recover_stale, request_retry
from mission_store import MissionStore
from safe_workflow import Step

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / "11_MODELOS_IA"))
from ollama_gateway import GatewayError, OllamaGateway

MAX_BODY = 16384
DEFAULT_DATA = Path.home() / ".cerberus" / "moss_lab"
READ_ONLY = frozenset({"inspect", "summarize", "validate", "report"})
LOGGER = logging.getLogger("moss.api")


class HttpFailure(Exception):
    def __init__(self, status, message):
        self.status = int(status)
        self.message = message
        super().__init__(message)


def checked_uuid(value):
    try:
        uid = UUID(value)
    except (ValueError, AttributeError) as exc:
        raise HttpFailure(400, "Invalid mission ID") from exc
    if str(uid) != value:
        raise HttpFailure(400, "Noncanonical mission ID")
    return value


def create_server(*, data_dir=DEFAULT_DATA, port=8765, token=None):
    """Create a bounded local service, allowing ephemeral ports for tests."""
    if type(port) is not int or not 0 <= port <= 65535:
        raise ValueError("Port outside 0..65535")
    secret = token if token is not None else (os.environ.get("MOSS_API_TOKEN") or secrets.token_urlsafe(32))
    if (not isinstance(secret, str) or not 32 <= len(secret) <= 512 or
        any(ord(ch) < 33 or ord(ch) > 126 for ch in secret)):
        raise ValueError("MOSS_API_TOKEN must be 32-512 printable ASCII characters without spaces")
    directory = Path(data_dir).expanduser().resolve()
    store = MissionStore(directory / "missions.sqlite3")
    memory = MemoryIndex(directory / "memory.sqlite3")
    server = ThreadingHTTPServer(("127.0.0.1", port), MOSSHandler)
    server.daemon_threads = True
    server.store = store
    server.memory = memory
    server.chat = ChatStore(directory / "chat.sqlite3")
    server.engineering = EngineeringRunner(directory / "engineering.sqlite3")
    server.chat_lock = Lock()
    server.auth_token = secret
    return server


class MOSSHandler(BaseHTTPRequestHandler):
    server_version = "MOSS-Lab/1.0"
    sys_version = ""
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):
        # Never include query strings, tokens, or private notes in access logs.
        return

    def reply(self, status, payload, content_type="application/json; charset=utf-8"):
        encoded = payload if isinstance(payload, bytes) else json.dumps(
            payload, ensure_ascii=False, allow_nan=False).encode("utf-8")
        self.send_response(int(status))
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("Cache-Control", "no-store, max-age=0")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Cross-Origin-Resource-Policy", "same-origin")
        self.send_header("Content-Security-Policy",
                         "default-src 'none'; script-src 'self'; style-src 'self'; "
                         "connect-src 'self'; base-uri 'none'; frame-ancestors 'none'; "
                         "form-action 'none'")
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(encoded)
        self.close_connection = True

    def validate_request_origin(self):
        port = self.server.server_address[1]
        hosts = {f"127.0.0.1:{port}", f"localhost:{port}"}
        if self.headers.get("Host") not in hosts:
            raise HttpFailure(403, "Invalid Host header")
        origin = self.headers.get("Origin")
        if origin and origin not in {f"http://{host}" for host in hosts}:
            raise HttpFailure(403, "Invalid Origin")

    def authenticate(self):
        values = self.headers.get_all("Authorization", [])
        if len(values) != 1 or not values[0].startswith("Bearer "):
            raise HttpFailure(401, "Bearer token required")
        supplied = values[0][7:]
        if len(supplied) > 512 or not hmac.compare_digest(supplied, self.server.auth_token):
            raise HttpFailure(401, "Invalid bearer token")

    def read_json(self):
        raw_len = self.headers.get("Content-Length")
        if raw_len is None or not raw_len.isascii() or not raw_len.isdecimal():
            raise HttpFailure(411, "JSON Content-Length required")
        length = int(raw_len)
        if length > MAX_BODY:
            raise HttpFailure(413, "Request exceeds 16 KiB limit")
        if self.headers.get("Content-Type", "").split(";", 1)[0].strip().lower() != "application/json":
            raise HttpFailure(415, "Expected application/json")
        data = self.rfile.read(length)
        if len(data) != length:
            raise HttpFailure(400, "Incomplete request body")
        try:
            obj = json.loads(data.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise HttpFailure(400, "Invalid JSON") from exc
        if not isinstance(obj, dict):
            raise HttpFailure(400, "JSON object required")
        return obj

    def dispatch(self, method):
        try:
            self.validate_request_origin()
            parts = urlsplit(self.path)
            path = parts.path
            if len(self.path) > 2048 or len(parts.query) > 1000:
                raise HttpFailure(414, "URL too long")
            assets = {
                "/": (ROOT / "web" / "index.html", "text/html; charset=utf-8"),
                "/app.js": (ROOT / "web" / "app.js", "application/javascript; charset=utf-8"),
                "/app.css": (ROOT / "web" / "app.css", "text/css; charset=utf-8"),
            }
            if method == "GET" and path in assets:
                asset, mime = assets[path]
                self.reply(200, asset.read_bytes(), mime)
                return
            if method == "GET" and path == "/api/v1/health":
                self.reply(200, {"service": "MOSS Lab", "status": "ok",
                                  "scope": "loopback only", "tools_executed": 0})
                return
            if not path.startswith("/api/v1/"):
                raise HttpFailure(404, "Not found")
            self.authenticate()
            self.api(method, parts)
        except HttpFailure as exc:
            self.reply(exc.status, {"status": exc.status, "error": exc.message})
        except KeyError:
            self.reply(404, {"status": 404, "error": "Requested record not found"})
        except PermissionError as exc:
            self.reply(403, {"status": 403, "error": str(exc)})
        except EngineeringBusy as exc:
            self.reply(409, {"status": 409, "error": str(exc)})
        except (ValueError, TypeError) as exc:
            self.reply(422, {"status": 422, "error": str(exc)})
        except (GatewayError, TimeoutError):
            self.reply(502, {"status": 502, "error": "Local Ollama unavailable or invalid response"})
        except sqlite3.Error:
            LOGGER.exception("Local database failure")
            self.reply(503, {"status": 503, "error": "Local database operation failed"})
        except Exception:
            LOGGER.exception("Unexpected API failure")
            self.reply(500, {"status": 500, "error": "Internal server error"})

    def api(self, method, parts):
        path = parts.path
        store, memory = self.server.store, self.server.memory
        if method == "GET" and path == "/api/v1/missions":
            records = store.list(limit=100)
            self.reply(200, {"missions": records, "states": dict(Counter(r["state"] for r in records))})
            return
        if method == "POST" and path == "/api/v1/missions":
            data = self.read_json()
            if set(data) != {"title"}:
                raise ValueError("Only title is accepted")
            identifier = store.add(data["title"])
            self.reply(201, store.get(identifier))
            return
        if method == "POST" and path == "/api/v1/previews":
            data = self.read_json()
            if set(data) != {"title", "actions"}:
                raise ValueError("title and actions required")
            actions = data["actions"]
            if (not isinstance(actions, list) or not 1 <= len(actions) <= 128 or
                any(not isinstance(a, str) or a not in READ_ONLY for a in actions)):
                raise ValueError("Actions must be 1..128 read-only step names")
            steps = [Step(f"step-{i+1}", action, (f"step-{i}",) if i else ())
                     for i, action in enumerate(actions)]
            self.reply(201, create_preview(store, data["title"], steps))
            return
        if method == "POST" and path == "/api/v1/recover":
            data = self.read_json()
            if set(data) != {"older_than_seconds"}:
                raise ValueError("older_than_seconds required")
            self.reply(200, {"marked_failed": recover_stale(store, data["older_than_seconds"]),
                             "automatic_retry": False})
            return
        if path.startswith("/api/v1/missions/"):
            segments = path.split("/")
            if len(segments) not in (5, 6):
                raise HttpFailure(404, "Not found")
            identifier = checked_uuid(segments[4])
            if method == "GET" and len(segments) == 5:
                self.reply(200, store.get(identifier))
                return
            if method == "GET" and len(segments) == 6 and segments[5] == "events":
                self.reply(200, {"events": store.events(identifier)})
                return
            if method == "POST" and len(segments) == 6 and segments[5] == "complete-preview":
                if self.read_json():
                    raise ValueError("Empty JSON object expected")
                self.reply(200, complete_preview(store, identifier))
                return
            if method == "POST" and len(segments) == 6 and segments[5] == "retry":
                if self.read_json() != {"operator_approved": True}:
                    raise PermissionError("Explicit operator approval required")
                self.reply(200, request_retry(store, identifier, operator_approved=True))
                return
        if method == "GET" and path == "/api/v1/memory":
            params = parse_qs(parts.query, keep_blank_values=True)
            if set(params) != {"q"} or len(params["q"]) != 1:
                raise ValueError("Exactly one q parameter required")
            self.reply(200, {"results": memory.search(params["q"][0], k=20)})
            return
        if method == "POST" and path == "/api/v1/memory":
            data = self.read_json()
            if set(data) != {"text"}:
                raise ValueError("text required")
            self.reply(201, {"id": memory.insert(data["text"], source="local_web_ui")})
            return
        if method == "DELETE" and path.startswith("/api/v1/memory/"):
            identifier = path.rsplit("/", 1)[1]
            if not identifier.isascii() or not identifier.isdecimal():
                raise ValueError("Invalid note ID")
            if not memory.delete(int(identifier)):
                raise HttpFailure(404, "Note not found")
            self.reply(200, {"deleted": True})
            return
        if method == "GET" and path == "/api/v1/engineering/jobs":
            self.reply(200, {"jobs": self.server.engineering.jobs(),
                             "policy": "Explicit operator approval, fixed scripts, shell=False"})
            return
        if method == "GET" and path == "/api/v1/engineering/inventory":
            self.reply(200, self.server.engineering.inventory())
            return
        if method == "GET" and path == "/api/v1/engineering/runs":
            self.reply(200, {"runs": self.server.engineering.recent(limit=20)})
            return
        if method == "POST" and path == "/api/v1/engineering/run":
            data = self.read_json()
            if set(data) != {"job", "operator_approved"}:
                raise ValueError("job and operator_approved fields required")
            if data["operator_approved"] is not True:
                raise PermissionError("Operator approval required")
            result = self.server.engineering.run(
                data["job"], operator_approved=True, timeout=120)
            self.reply(200, result)
            return
        if method == "GET" and path == "/api/v1/chat":
            self.reply(200, {"messages": self.server.chat.history(limit=60),
                             "scope": "local SQLite conversation"})
            return
        if method == "DELETE" and path == "/api/v1/chat":
            with self.server.chat_lock:
                self.server.chat.clear()
            self.reply(200, {"cleared": True})
            return
        if method == "POST" and path == "/api/v1/chat":
            data = self.read_json()
            if (not {"prompt", "model"} <= set(data) or
                set(data) - {"prompt", "model", "mode", "max_tokens"}):
                raise ValueError("model and prompt required")
            prompt, model = data["prompt"], data["model"]
            mode = data.get("mode", "engineering")
            max_tokens = data.get("max_tokens", 256)
            if not isinstance(prompt, str) or not 1 <= len(prompt) <= 4000:
                raise ValueError("Chat prompt must have 1..4000 characters")
            if mode not in MODES:
                raise ValueError("Unsupported conversation mode")
            if type(max_tokens) is not int or not 1 <= max_tokens <= 512:
                raise ValueError("max_tokens must be between 1 and 512")
            system = system_context(model, mode)
            # Serialize each local conversation turn to preserve chronological order.
            with self.server.chat_lock:
                context = self.server.chat.context(max_messages=12, char_budget=12000)
                messages = [{"role": "system", "content": system}]
                messages.extend(context)
                messages.append({"role": "user", "content": prompt})
                answer = OllamaGateway(timeout=90).chat(
                    model, messages, max_tokens=max_tokens)
                self.server.chat.append_exchange(prompt, answer, model=model, mode=mode)
            self.reply(200, {"model": model, "mode": mode, "answer": answer,
                             "tools_executed": 0, "history_saved": True,
                             "scope": "MOSS Lab local Ollama chat",
                             "model_identity": model_identity(model)})
            return
        if method == "GET" and path == "/api/v1/models":
            models = OllamaGateway(timeout=8).list_models()
            self.reply(200, {"models": models, "provider": "local_ollama",
                             "model_details": {name: model_identity(name) for name in models}})
            return
        if method == "POST" and path == "/api/v1/ask":
            data = self.read_json()
            if not {"prompt", "model"} <= set(data) or set(data) - {"prompt", "model", "max_tokens"}:
                raise ValueError("model and prompt required")
            answer = OllamaGateway(timeout=90).generate(
                data["model"], data["prompt"], max_tokens=data.get("max_tokens", 256))
            self.reply(200, {"model": data["model"], "answer": answer,
                             "scope": "Local text generation", "tools_executed": 0})
            return
        raise HttpFailure(404, "Unknown API endpoint")

    def do_GET(self):
        self.dispatch("GET")

    def do_POST(self):
        self.dispatch("POST")

    def do_DELETE(self):
        self.dispatch("DELETE")


def main(argv=None):
    parser = argparse.ArgumentParser(description="MOSS Lab localhost API and dashboard")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA)
    args = parser.parse_args(argv)
    with create_server(data_dir=args.data_dir, port=args.port) as server:
        print(f"MOSS Lab: http://127.0.0.1:{server.server_port}/")
        print(f"Access token (do not share): {server.auth_token}")
        print("Local only. Press Ctrl+C to stop.", flush=True)
        try:
            server.serve_forever(poll_interval=0.2)
        except KeyboardInterrupt:
            print("\nServer stopped.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
