"""Supervised mission engine tests, including adversarial and race behaviours."""
from __future__ import annotations

import json
from contextlib import closing
from pathlib import Path
import sqlite3
import sys
import tempfile
import time
from threading import Event
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "03_CERBERUS_CORE"))
from mission_engine import JobSupervisor, Result, TASKS, catalog

class MissionEngineTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.db = Path(self.tmp.name) / "missions.sqlite3"

    def supervisor(self, runner=None):
        return JobSupervisor(db_path=self.db, runner=runner or
                             (lambda task, mid, stop: Result("PASSED", 0, "CHECK OK")))

    @staticmethod
    def await_terminal(sup, mission_id, seconds=3):
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            item = sup.get(mission_id)
            if item["state"] not in ("RUNNING", "CANCELLING"):
                return item
            time.sleep(.02)
        raise AssertionError("job did not finish")

    def test_catalog_is_fixed_and_constrained(self):
        self.assertEqual(len(catalog()), 3)
        for task in TASKS.values():
            self.assertIn(task["args"][0], ("python",))
            self.assertLessEqual(task["limit"], 60)
        self.assertRaises(ValueError, self.supervisor().prepare, "../../etc/passwd")
        self.assertRaises(ValueError, self.supervisor().prepare, {"task_id": "robotics_static"})

    def test_approval_is_one_time_and_persisted(self):
        sup = self.supervisor()
        ticket = sup.prepare("riscv_reference")["ticket"]
        self.assertRaises(ValueError, sup.start, ticket, False)
        started = sup.start(ticket, True)
        final = self.await_terminal(sup, started["id"])
        self.assertEqual(final["state"], "PASSED")
        self.assertEqual(final["output"], "CHECK OK")
        self.assertEqual(final["exit_code"], 0)
        self.assertRaises(ValueError, sup.start, ticket, True)
        self.assertEqual(self.supervisor().get(started["id"])["state"], "PASSED")

    def test_second_parallel_job_is_rejected(self):
        release = Event()
        def blocker(task, mid, cancelled):
            release.wait(timeout=3)
            return Result("PASSED", 0, "DONE")
        sup = self.supervisor(blocker)
        first = sup.start(sup.prepare("engineering_tests")["ticket"], True)
        second = sup.prepare("riscv_reference")["ticket"]
        try:
            with self.assertRaises(RuntimeError):
                sup.start(second, True)
        finally:
            release.set()
        self.assertEqual(self.await_terminal(sup, first["id"])["state"], "PASSED")
        # The busy attempt consumes its ticket rather than silently executing later.
        with self.assertRaises(ValueError):
            sup.start(second, True)

    def test_cancellation_sets_final_state(self):
        def blocked(task, mid, stopped):
            stopped.wait(timeout=2)
            return Result("PASSED", 0, "CANCELLED BY USER")
        sup = self.supervisor(blocked)
        mission = sup.start(sup.prepare("robotics_static")["ticket"], True)
        response = sup.cancel(mission["id"])
        self.assertEqual(response["state"], "CANCELLING")
        self.assertEqual(self.await_terminal(sup, mission["id"])["state"], "CANCELLED")
        self.assertRaises(ValueError, sup.cancel, mission["id"])

    def test_ticket_expiry(self):
        sup = self.supervisor()
        ticket = sup.prepare("riscv_reference")["ticket"]
        with sup._lock:
            sup._tickets[ticket] = ("riscv_reference", time.monotonic() - 1)
        self.assertRaises(ValueError, sup.start, ticket, True)

    def test_graceful_shutdown_requests_cancellation(self):
        def slow(task, mid, stopped):
            stopped.wait(timeout=2)
            return Result("PASSED", 0, "FINISHED")
        sup = self.supervisor(slow)
        item = sup.start(sup.prepare("riscv_reference")["ticket"], True)
        sup.shutdown(timeout=2)
        self.assertEqual(self.await_terminal(sup, item["id"])["state"], "CANCELLED")

    def test_restart_marks_unfinished_as_interrupted(self):
        sup = self.supervisor()
        mid = "97b4bfbe-45a1-42c3-8db1-bd3932646b16"
        with closing(sqlite3.connect(str(self.db))) as conn:
            with conn:
                conn.execute("INSERT INTO missions(id,task_id,state,created) VALUES(?,?,?,?)",
                             (mid, "riscv_reference", "RUNNING", "2026-01-01T00:00:00Z"))
        later = self.supervisor()
        self.assertEqual(later.get(mid)["state"], "INTERRUPTED")

    def test_bounded_audit_history(self):
        sup = self.supervisor(lambda t, mid, stop: Result("FAILED", 7, "x" * 7000))
        for _ in range(17):
            task = sup.start(sup.prepare("riscv_reference")["ticket"], True)
            self.await_terminal(sup, task["id"])
        self.assertEqual(len(sup.recent()), 15)
        self.assertLessEqual(len(sup.recent()[0]["output"]), 5000)
        self.assertRaises(ValueError, sup.get, "not-a-uuid")

if __name__ == "__main__":
    unittest.main()
