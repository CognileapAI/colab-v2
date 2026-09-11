from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timedelta, timezone

import pytest

from colab_viz.domains.d7_visualization import ownership_snapshot

D3 = "01ARZ3NDEKTSV4RRFFQ69G5FAV"
D5 = "01BX5ZZKBKACTAV9WEVGEMMVRZ"


def _write(path, *, observed_at=None, d3=None, d5=None, scope="all-tenants"):
    payload = {
        "schema": "colab-preview-ownership-snapshot/1",
        "observed_at": observed_at or datetime.now(timezone.utc).isoformat(),
        "scope": scope,
        "database_role": "colab_backup",
        "role_evidence": {"superuser": False, "bypassrls": True, "read_all_data": True},
        "d3_file_ids": d3 if d3 is not None else [D3],
        "d5_upload_file_ids": d5 if d5 is not None else [D5],
        "counts": {"d3_file": len(d3 if d3 is not None else [D3]),
                   "d5_upload_file": len(d5 if d5 is not None else [D5])},
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    payload["content_sha256"] = hashlib.sha256(canonical).hexdigest()
    path.write_text(json.dumps(payload), encoding="utf-8")
    os.chmod(path, 0o440)
    os.chmod(path.parent, 0o550)
    return payload


def test_snapshot은_전수권한_내용해시_계수와_freshness를_검증한다(tmp_path):
    path = tmp_path / "ledger.json"
    _write(path)
    ledger = ownership_snapshot.load(path, max_age_seconds=3600)
    assert ledger.dataset_files == frozenset({D3})
    assert ledger.upload_files == frozenset({D5})


@pytest.mark.parametrize("change", ["stale", "future", "duplicate", "wrong-scope", "empty", "hash"])
def test_snapshot_불확실성은_0계수로_접지_않는다(tmp_path, change):
    path = tmp_path / "ledger.json"
    if change == "stale":
        _write(path, observed_at=(datetime.now(timezone.utc)-timedelta(hours=2)).isoformat())
    elif change == "future":
        _write(path, observed_at=(datetime.now(timezone.utc)+timedelta(hours=2)).isoformat())
    elif change == "duplicate":
        _write(path, d3=[D3, D3])
    elif change == "wrong-scope":
        _write(path, scope="one-lab")
    elif change == "empty":
        _write(path, d3=[], d5=[])
    else:
        doc = _write(path); doc["d3_file_ids"] = [D5]; os.chmod(path, 0o600); path.write_text(json.dumps(doc)); os.chmod(path, 0o440)
    with pytest.raises(ownership_snapshot.SnapshotNotReady):
        ownership_snapshot.load(path, max_age_seconds=3600)


def test_snapshot은_symlink와_넓은_mode를_거절한다(tmp_path):
    real = tmp_path / "real.json"; _write(real)
    os.chmod(tmp_path, 0o750)
    link = tmp_path / "link.json"; link.symlink_to(real)
    os.chmod(tmp_path, 0o550)
    with pytest.raises(ownership_snapshot.SnapshotNotReady): ownership_snapshot.load(link, max_age_seconds=3600)
    os.chmod(real, 0o644)
    with pytest.raises(ownership_snapshot.SnapshotNotReady): ownership_snapshot.load(real, max_age_seconds=3600)


def test_snapshot은_duplicate_JSON_key와_unhashable_ID도_준비실패로_닫는다(tmp_path):
    path=tmp_path/"ledger.json"; _write(path)
    os.chmod(path,0o640); raw=path.read_text(); os.chmod(path,0o440)
    raw=raw.replace('{', '{"schema":"duplicate",', 1)
    os.chmod(path,0o640); path.write_text(raw); os.chmod(path,0o440)
    with pytest.raises(ownership_snapshot.SnapshotNotReady):
        ownership_snapshot.load(path,max_age_seconds=3600)
    os.chmod(path.parent,0o750); os.chmod(path,0o640); _write(path,d3=[{"bad":"id"}]); os.chmod(path.parent,0o550)
    with pytest.raises(ownership_snapshot.SnapshotNotReady):
        ownership_snapshot.load(path,max_age_seconds=3600)
