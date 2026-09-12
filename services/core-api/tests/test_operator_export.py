import json, os
from pathlib import Path
from colab_core.kernel.ids import Ulid

def test_jsonl_spool_is_private_and_deterministic(tmp_path):
    from ops.operator_audit_export import _write_jsonl
    path=tmp_path/"private"/"events.jsonl"
    rows=[{"source_id":str(Ulid.generate()),"action":"dataset.updated"}]
    first=_write_jsonl(path,rows)
    assert len(first)==64
    assert (path.stat().st_mode & 0o777)==0o600
    assert json.loads(path.read_text())["action"]=="dataset.updated"
