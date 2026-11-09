"""Manual end-to-end localhost HTTP + Docker execution check.

Starts a temporary Control Plane instance on an ephemeral port, authorizes
one fixed robotics check, inspects its audited completion, and exits.
No production DB, secrets, network service or arbitrary user commands.
"""
from contextlib import closing
import http.client
import json
from pathlib import Path
import secrets
import sys
from tempfile import TemporaryDirectory
from threading import Thread
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "03_CERBERUS_CORE"))
from control_plane import make_server

def main():
    with TemporaryDirectory() as tmp:
        token = secrets.token_urlsafe(32)
        server = make_server(port=0, token=token, mission_db=Path(tmp) / "audit.sqlite3")
        server_thread = Thread(target=server.serve_forever, daemon=True)
        server_thread.start()
        host = "127.0.0.1"
        port = server.server_port
        def request(method, path, data=None):
            headers = {"Authorization": "Bearer " + token,
                       "Origin": "http://127.0.0.1:" + str(port)}
            encoded = None
            if data is not None:
                encoded = json.dumps(data).encode()
                headers["Content-Type"] = "application/json"
            with closing(http.client.HTTPConnection(host, port, timeout=5)) as conn:
                conn.request(method, path, body=encoded, headers=headers)
                response = conn.getresponse()
                return response.status, json.loads(response.read())
        try:
            status, plan = request("POST", "/api/v1/missions/prepare", {"task_id": "robotics_static"})
            if status != 200:
                raise RuntimeError("prepare failed: " + repr(plan))
            status, mission = request("POST", "/api/v1/missions/start",
                                      {"ticket": plan["ticket"], "approve": True})
            if status != 202:
                raise RuntimeError("start failed: " + repr(mission))
            deadline = time.monotonic() + 30
            while time.monotonic() < deadline:
                status, item = request("GET", "/api/v1/missions/" + mission["id"])
                if status == 200 and item["state"] not in ("RUNNING", "CANCELLING"):
                    print("HTTP -> Docker -> SQLite:", item["state"],
                          "exit", item["exit_code"])
                    print("Evidence tail:", item["output"][-500:])
                    return 0 if item["state"] == "PASSED" else 1
                time.sleep(.2)
            print("Mission did not finish before smoke deadline")
            return 1
        finally:
            server.shutdown()
            server.server_close()
            server_thread.join(timeout=2)

if __name__ == "__main__":
    sys.exit(main())
