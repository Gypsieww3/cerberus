"""Isolated cross-project regression tests; no live actions or third-party packages."""
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
for folder in ("01_MOSS_KYVRAEL", "02_ARKHE", "02_ARKHE/arkhe",
               "05_TRADING", "07_ROBOTICA", "08_PROMETHEUS",
               "09_HARDWARE/GENESIS_X", "11_MODELOS_IA", "12_BACKUPS"):
    sys.path.insert(0, str(ROOT / folder))

from safe_workflow import Step, plan
from mission_store import MissionStore
from mission_preview import create_preview, complete_preview
from mission_recovery import recover_stale, request_retry
from lexical_memory import MemoryIndex
from experiment_protocol import ExperimentProtocol
from holdout import partition, evaluate
from paper_risk import PaperLimits
from trajectory_envelope import estimate_dynamic
from dataset_audit import audit
from requirements_audit import audit_requirements
from model_selection import choose_model
from restore_policy import verify_manifest

class MossTests(unittest.TestCase):
    def test_plan_topology(self):
        self.assertEqual(plan([Step("b","report",("a",)), Step("a","inspect")]).order, ["a","b"])
        with self.assertRaises(ValueError):
            plan([Step("a","inspect",("b",)),Step("b","inspect",("a",))])

    def test_requires_approval_for_unknown_action(self):
        self.assertEqual(plan([Step("x","shell")]).pending_approval, ["x"])

    def test_preview_journal(self):
        with tempfile.TemporaryDirectory() as folder:
            db = MissionStore(Path(folder)/"missions.db")
            preview = create_preview(db,"Review project",[Step("a","inspect"),Step("b","report",("a",))])
            completed = complete_preview(db,preview["mission_id"])
            self.assertEqual(completed["order"],["a","b"])
            self.assertEqual(completed["executed_actions"],0)
            self.assertEqual(db.get(preview["mission_id"])["state"],"done")

    def test_preview_blocks_mutation(self):
        with tempfile.TemporaryDirectory() as folder:
            db = MissionStore(Path(folder)/"missions.db")
            with self.assertRaises(PermissionError):
                create_preview(db,"Unsafe",[Step("x","shell")])

    def test_recovery_requires_operator(self):
        with tempfile.TemporaryDirectory() as folder:
            db = MissionStore(Path(folder)/"missions.db")
            identifier=db.add("Aborted")
            db.transition(identifier,"running")
            later=datetime.now(timezone.utc)+timedelta(hours=2)
            self.assertEqual(recover_stale(db,60,now=later),[identifier])
            with self.assertRaises(PermissionError):
                request_retry(db,identifier)
            request_retry(db,identifier,operator_approved=True)
            self.assertEqual(db.get(identifier)["state"],"pending")

    def test_memory_index(self):
        with tempfile.TemporaryDirectory() as folder:
            index=MemoryIndex(Path(folder)/"notes.db")
            identifier=index.insert("test of RISC V processor")
            self.assertEqual(index.search("processor")[0]["id"],identifier)
            self.assertTrue(index.delete(identifier))

class ResearchTests(unittest.TestCase):
    def test_holdout(self):
        points=[{"id":"a","timestamp":"2026-01-01T00:00:00Z","target":1},
                {"id":"b","timestamp":"2026-02-01T00:00:00Z","target":3}]
        train,held=partition(points,"2026-01-15T00:00:00Z")
        self.assertEqual(len(train),1)
        self.assertEqual(evaluate(held,{"b":2})["mae"],1)

    def test_protocol(self):
        p=ExperimentProtocol("question","hypothesis","MAE","2026-02-01T00:00:00Z",
                             "a"*64,"mean baseline")
        self.assertEqual(len(p.digest()),64)
        self.assertEqual(p.digest(),p.digest())

class OtherTests(unittest.TestCase):
    def test_trading_is_paper_and_bounded(self):
        risk=PaperLimits(Decimal(1000),Decimal(30),Decimal(60))
        self.assertTrue(risk.check(equity=1000,daily_open_equity=1000,proposed_risk=10)["permitted"])
        self.assertFalse(risk.check(equity=1000,daily_open_equity=1000,proposed_risk=50)["permitted"])

    def test_robotics_envelope(self):
        result=estimate_dynamic(2,0.25,0.1,
            [{"angle_rad":1.57,"acceleration_rad_s2":0}],gear_ratio=10,efficiency=0.8)
        self.assertGreater(result["peak_motor_nm"],0)

    def test_prometheus_split_leakage(self):
        pixel=[[1,2],[3,4]]
        outcome=audit([{"id":"a","image":pixel,"defective":False}],
                      [{"id":"b","image":pixel,"defective":True}])
        self.assertTrue(outcome["leakage_detected"])

    def test_genesis_evidence(self):
        result=audit_requirements([{"id":"wifi","state":"verified","evidence":[]}])
        self.assertFalse(result["auditable"])
        self.assertEqual(len(result["issues"]),2)

    def test_model_ranking(self):
        result=choose_model([{"name":"small","disk_gb":1,"tags":["general"]},
                             {"name":"coder","disk_gb":4,"tags":["code"]}],8,task="code")
        self.assertEqual(result["recommended"],"coder")

    def test_backup_checksum(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/"a.txt"
            p.write_text("stable",encoding="utf-8")
            entry=[{"path":"a.txt","sha256":sha256(p.read_bytes()).hexdigest()}]
            self.assertTrue(verify_manifest(folder,entry)["verified"])
            p.write_text("modified",encoding="utf-8")
            self.assertFalse(verify_manifest(folder,entry)["verified"])
            with self.assertRaises(ValueError):
                verify_manifest(folder,[{"path":"../escape","sha256":"a"*64}])

if __name__=="__main__":
    unittest.main()
