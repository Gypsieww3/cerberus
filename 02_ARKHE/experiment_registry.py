"""Preregister test hypotheses with reproducible protocol digests."""
import json
from datetime import datetime,timezone
from hashlib import sha256
from pathlib import Path

REQUIRED={"hypothesis","dataset_id","split_cutoff","metric","analysis_plan"}
def canonical(protocol):
    return json.dumps(protocol,sort_keys=True,ensure_ascii=False,separators=(",",":"),allow_nan=False).encode("utf-8")
def preregister(protocol):
    if not isinstance(protocol,dict) or not REQUIRED<=set(protocol):
        raise ValueError("Missing protocol fields")
    if any(not isinstance(protocol[key],str) or not protocol[key].strip() for key in REQUIRED):
        raise ValueError("Protocol fields must be nonempty strings")
    data=canonical(protocol)
    if len(data)>50000: raise ValueError("Protocol too large")
    return dict(protocol=protocol,sha256=sha256(data).hexdigest(),
                recorded_at=datetime.now(timezone.utc).isoformat(),
                caveat="Digest does not prove a trusted timestamp or scientific discovery")
def verify(record):
    try: return sha256(canonical(record["protocol"])).hexdigest()==record["sha256"]
    except (KeyError,TypeError,ValueError): return False
def write_once(record,path):
    if not verify(record): raise ValueError("Unverifiable record")
    target=Path(path)
    target.parent.mkdir(parents=True,exist_ok=True)
    with target.open("x",encoding="utf-8") as output:
        json.dump(record,output,ensure_ascii=False,indent=2)
    return str(target)
