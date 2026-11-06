"""SHA-256 file manifest / local verification. No upload or archive deletion."""
from hashlib import sha256
from pathlib import Path

def digest_file(path):
    value=sha256()
    with Path(path).open("rb") as file:
        while True:
            chunk=file.read(1024*1024)
            if not chunk: break
            value.update(chunk)
    return value.hexdigest()

def make_manifest(root, exclude=(".git",".venv","__pycache__")):
    base=Path(root).resolve()
    entries=[]
    for path in sorted(base.rglob("*")):
        if not path.is_file() or path.is_symlink() or any(x in exclude for x in path.relative_to(base).parts):
            continue
        entries.append(dict(path=path.relative_to(base).as_posix(),
                            sha256=digest_file(path),bytes=path.stat().st_size))
    return entries

def verify_manifest(root, entries):
    base=Path(root).resolve()
    results=[]
    for item in entries:
        relative=Path(item["path"])
        candidate=base/relative
        target=candidate.resolve()
        linked=any(x.is_symlink() for x in [candidate,*candidate.parents] if x!=base and x.is_relative_to(base))
        if relative.is_absolute() or ".." in relative.parts or not target.is_relative_to(base) or linked or not target.is_file():
            results.append(dict(path=str(relative),ok=False,reason="missing_or_unsafe"))
            continue
        good=digest_file(target)==item["sha256"] and target.stat().st_size==item["bytes"]
        results.append(dict(path=str(relative),ok=good,reason="match" if good else "changed"))
    return results
