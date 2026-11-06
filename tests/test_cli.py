"""Local executable tests of the MOSS Lab CLI."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
MOSS = ROOT / "01_MOSS_KYVRAEL" / "cli.py"
MATRIX = ROOT / "03_CERBERUS_CORE" / "project_matrix.py"

class TestCli(unittest.TestCase):
    def call_cli(self, folder, *args):
        return subprocess.run([sys.executable, str(MOSS), "--data-dir", str(folder), *args],
                              capture_output=True, text=True, timeout=20)

    def test_explicit_preview(self):
        with tempfile.TemporaryDirectory() as folder:
            result = self.call_cli(folder, "preview", "Inspection", "--actions", "inspect,report")
            self.assertEqual(result.returncode, 0, result.stderr)
            obj = json.loads(result.stdout)
            self.assertEqual(obj["executed_actions"], 0)
            second = self.call_cli(folder, "complete-preview", obj["mission_id"])
            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertEqual(json.loads(second.stdout)["order"], ["step-1", "step-2"])

    def test_reject_command_execution(self):
        with tempfile.TemporaryDirectory() as folder:
            result = self.call_cli(folder, "preview", "Unsafe", "--actions", "shell")
            self.assertEqual(result.returncode, 2)

    def test_private_memory(self):
        with tempfile.TemporaryDirectory() as folder:
            self.assertEqual(self.call_cli(folder,"memory-add","RISC V test").returncode,0)
            result = self.call_cli(folder,"memory-search","RISC")
            self.assertEqual(result.returncode,0)
            self.assertEqual(len(json.loads(result.stdout)),1)

    def test_source_inventory(self):
        command = subprocess.run([sys.executable, str(MATRIX)], capture_output=True,text=True,timeout=20)
        self.assertEqual(command.returncode,0,command.stderr)
        obj=json.loads(command.stdout)
        self.assertGreaterEqual(len(obj["projects"]),10)
        self.assertGreater(obj["total_source_files"],0)

if __name__=="__main__":
    unittest.main()
