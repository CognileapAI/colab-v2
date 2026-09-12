from __future__ import annotations
import hashlib, json, os, uuid
from pathlib import Path
from .events import canonical, validate

def append(directory: Path, record: dict) -> str:
    record = validate(record); directory = Path(directory); directory.mkdir(parents=True, exist_ok=True, mode=0o700); os.chmod(directory, 0o700)
    digest = hashlib.sha256(canonical(record)).hexdigest(); path = directory / (record["event_id"] + ".json")
    if path.exists():
        if hashlib.sha256(path.read_bytes()).hexdigest() != digest: raise ValueError("event id collision")
        return digest
    temp = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    fd = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as stream: stream.write(canonical(record)); stream.flush(); os.fsync(stream.fileno())
    os.replace(temp, path); parent = os.open(directory, os.O_RDONLY | os.O_DIRECTORY); os.fsync(parent); os.close(parent)
    return digest


def drain(directory: Path, store) -> int:
    """Remove a spool item only after the destination confirms durable acceptance."""
    directory = Path(directory)
    if not directory.is_dir(): raise ValueError("spool directory is not prepared")
    count = 0
    for path in sorted(directory.glob("*.json")):
        record = validate(json.loads(path.read_text()))
        store.put(record)
        saved = store.get(record["event_id"])["record"]
        comparable = lambda r: canonical({k:v for k,v in r.items() if k != "received_at"})
        if comparable(saved) != comparable(record): raise ValueError("durable receipt mismatch")
        path.unlink()
        fd = os.open(directory, os.O_RDONLY | os.O_DIRECTORY)
        try: os.fsync(fd)
        finally: os.close(fd)
        count += 1
    return count
