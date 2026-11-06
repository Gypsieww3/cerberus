"""Smartphone requirements traceability; claim-evidence validation only."""
STAGES={"concept","designed","bench_tested","prototype_verified","certified"}

def validate(requirements):
    seen=set()
    report=[]
    for item in requirements:
        identifier=item["id"]
        if not isinstance(identifier,str) or not identifier or identifier in seen:
            raise ValueError("Duplicate or missing requirement ID")
        seen.add(identifier)
        if not isinstance(item["description"],str) or not item["description"].strip():
            raise ValueError("Requirement description is required")
        stage=item.get("stage","concept")
        if stage not in STAGES:
            raise ValueError("Invalid stage")
        evidence=item.get("evidence",[])
        if not isinstance(evidence,list) or any(not isinstance(x,str) for x in evidence):
            raise ValueError("Invalid evidence references")
        if stage in {"prototype_verified","certified"} and not evidence:
            raise ValueError("Verification claims must cite evidence")
        report.append(dict(id=identifier,stage=stage,evidence_count=len(evidence)))
    return dict(count=len(report),requirements=report)
