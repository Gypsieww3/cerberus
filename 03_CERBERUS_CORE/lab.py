"""CERBERUS engineering lab: strict allowlist of local offline verification jobs."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
JOBS={
    "engineering-tests":"tools/test_engineering.py",
    "rv32i-reference":"09_HARDWARE/RV32I_TRACE/tools/verify_reference.py",
    "alu-reference":"09_HARDWARE/RV32I_TRACE/tools/alu_reference.py",
}

def run_job(name, timeout=60):
    if name not in JOBS:
        raise ValueError("Only predefined jobs allowed")
    if isinstance(timeout,bool) or not isinstance(timeout,(int,float)) or not 1<=timeout<=120:
        raise ValueError("Invalid timeout")
    target=(ROOT/JOBS[name]).resolve()
    if not target.is_relative_to(ROOT.resolve()) or not target.is_file():
        return dict(name=name,status="NOT_INSTALLED",exit_code=None)
    started=time.monotonic()
    try:
        result=subprocess.run([sys.executable,str(target)],cwd=ROOT,shell=False,
                              capture_output=True,text=True,timeout=timeout,check=False)
        return dict(name=name,status="PASS" if result.returncode==0 else "FAIL",
                    exit_code=result.returncode,duration_s=round(time.monotonic()-started,3),
                    stdout=result.stdout[-5000:],stderr=result.stderr[-5000:])
    except subprocess.TimeoutExpired:
        return dict(name=name,status="TIMEOUT",exit_code=None)

def main(argv=None):
    parser=argparse.ArgumentParser()
    parser.add_argument("--job",choices=["all",*JOBS],default="all")
    parser.add_argument("--json",action="store_true")
    args=parser.parse_args(argv)
    names=list(JOBS) if args.job=="all" else [args.job]
    result=[run_job(name) for name in names]
    if args.json: print(json.dumps(result,indent=2))
    else:
        for r in result: print(f"{r['name']}: {r['status']}")
    return int(any(r["status"]!="PASS" for r in result))

if __name__=="__main__":
    raise SystemExit(main())
