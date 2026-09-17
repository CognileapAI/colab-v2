from __future__ import annotations

import threading
import time
import logging
import os
import shutil
import subprocess
import sys
from pathlib import Path

from conftest import AUTH, make_client
from colab_viz.domains.d7_visualization import jobs
from colab_viz.ports.source import WorkspaceExceeded
from colab_viz.kernel import storage_layout


STYLE = {"palette": "단색-파랑"}


def _body(target_id: str) -> dict:
    return {"target": {"datasetId": target_id}, "style": STYLE}


def test_post_returns_before_source_materialization_finishes(
    source_root, put_target, tiny_geotiff,
):
    client = make_client(source_root, "thread")
    target_id = put_target(copy_from=[tiny_geotiff])
    entered = threading.Event()
    release = threading.Event()
    original = client.app.state.source.materialize

    def delayed(target):
        entered.set()
        assert release.wait(2)
        return original(target)

    client.app.state.source.materialize = delayed
    started = time.monotonic()
    response = client.post("/viz/v1/renders", headers=AUTH, json=_body(target_id))
    elapsed = time.monotonic() - started

    assert response.status_code == 202, response.text
    assert entered.wait(1)
    assert elapsed < 0.5, "POST가 worker의 materialize를 기다렸다"
    render_id = response.json()["renderId"]
    assert client.app.state.jobs.get(render_id).status == "그리는 중"
    release.set()
    assert client.app.state.jobs.get(render_id).done.wait(3)


def test_thread_executor_rejects_work_beyond_finite_queue(
    source_root, put_target, tiny_geotiff,
):
    client = make_client(source_root, "thread", render_queue_size=1, journal_enabled=True)
    first = put_target(copy_from=[tiny_geotiff])
    second = put_target(copy_from=[tiny_geotiff])
    third = put_target(copy_from=[tiny_geotiff])
    entered = threading.Event()
    release = threading.Event()
    original = client.app.state.source.materialize

    def delayed(target):
        entered.set()
        assert release.wait(3)
        return original(target)

    client.app.state.source.materialize = delayed
    assert client.post("/viz/v1/renders", headers=AUTH, json=_body(first)).status_code == 202
    assert entered.wait(1)
    assert client.post("/viz/v1/renders", headers=AUTH, json=_body(second)).status_code == 202
    response = client.post("/viz/v1/renders", headers=AUTH, json=_body(third))
    release.set()

    assert response.status_code == 503, response.text
    assert response.json()["code"] == "PREVIEW_QUEUE_FULL"
    assert all(record.get("targetId") != third
               for record in client.app.state.jobs._journal_records.values())


def test_declared_size_rejection_logs_only_correlation_and_counts(
    source_root, put_target, tiny_geotiff, caplog,
):
    client = make_client(source_root, "thread", max_render_bytes=1)
    target_id = put_target(copy_from=[tiny_geotiff])
    with caplog.at_level(logging.WARNING):
        response = client.post("/viz/v1/renders", headers=AUTH, json=_body(target_id))

    assert response.status_code == 413
    line = next(r.message for r in caplog.records if "render_rejected" in r.message)
    assert f"lab={AUTH['X-CoLAB-Lab']}" in line
    assert f"account={AUTH['X-CoLAB-Account']}" in line
    assert f"datasetId={target_id}" in line
    assert "reason=declared_size" in line and "limitBytes=1" in line
    assert str(tiny_geotiff) not in line


def test_async_size_failure_keeps_structured_counts_and_correlation(
    source_root, put_target, tiny_geotiff, caplog,
):
    client = make_client(source_root, "thread")
    target_id = put_target(copy_from=[tiny_geotiff])

    def reject(_target):
        raise WorkspaceExceeded("private/storage/path", limit_bytes=123, target_bytes=456)

    client.app.state.source.materialize = reject
    with caplog.at_level(logging.WARNING):
        response = client.post("/viz/v1/renders", headers=AUTH, json=_body(target_id))
        job = client.app.state.jobs.get(response.json()["renderId"])
        assert job.done.wait(2)

    body = job.to_dict()
    assert body["failure"]["code"] == "RENDER_TOO_LARGE"
    assert body["failure"]["details"]["limitBytes"] == 123
    assert body["failure"]["details"]["targetBytes"] == 456
    line = next(r.message for r in caplog.records if "render_failed" in r.message)
    assert f"renderId={body['renderId']}" in line and f"datasetId={target_id}" in line
    assert "private/storage/path" not in line


def test_restart_restores_final_response_under_same_render_id(
    source_root, put_target, tiny_geotiff,
):
    first = make_client(source_root, "inline", journal_enabled=True)
    target_id = put_target(copy_from=[tiny_geotiff])
    created = first.post("/viz/v1/renders", headers=AUTH, json=_body(target_id)).json()
    render_id = created["renderId"]
    expected = first.app.state.jobs.get(render_id).to_dict()
    first.app.state.jobs.close()
    shutil.rmtree(storage_layout.target_dir(source_root, target_id))

    restarted = make_client(source_root, "thread", journal_enabled=True)
    restored = restarted.get(f"/viz/v1/renders/{render_id}", headers=AUTH)

    assert restored.status_code == 200
    assert restored.json() == expected
    restarted.app.state.jobs.close()


def test_restart_requeues_interrupted_pending_with_same_render_id(
    source_root, put_target, tiny_geotiff,
):
    first = make_client(source_root, "manual", journal_enabled=True)
    target_id = put_target(copy_from=[tiny_geotiff])
    created = first.post("/viz/v1/renders", headers=AUTH, json=_body(target_id)).json()
    render_id = created["renderId"]
    first.app.state.jobs.close()

    restarted = make_client(source_root, "thread", journal_enabled=True)
    job = restarted.app.state.jobs.get(render_id)
    assert job is not None and job.done.wait(3)
    assert job.render_id == render_id and job.status == "완료"
    restarted.app.state.jobs.close()


def test_final_journal_failure_does_not_kill_manual_worker(
    source_root, put_target, tiny_geotiff,
):
    client = make_client(source_root, "manual", journal_enabled=True)
    target_id = put_target(copy_from=[tiny_geotiff])
    render_id = client.post("/viz/v1/renders", headers=AUTH, json=_body(target_id)).json()["renderId"]
    job = client.app.state.jobs.get(render_id)
    original = client.app.state.jobs._write_journal
    client.app.state.jobs._write_journal = lambda: (_ for _ in ()).throw(OSError("disk full"))

    client.app.state.jobs.run_pending()

    assert job.done.is_set() and job.status == "완료"
    client.app.state.jobs._write_journal = original
    client.app.state.jobs.close()


def test_sigkill_restart_requeues_same_render_id(source_root, put_target, tiny_geotiff, tmp_path):
    target_id = put_target(copy_from=[tiny_geotiff])
    id_path = tmp_path / "render-id"
    script = """
import os, signal, sys
from pathlib import Path
from fastapi.testclient import TestClient
from colab_viz.app.main import create_app
from colab_viz.kernel.config import Settings
root, target_id, id_path = Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3])
app = create_app(Settings(source_root=root, service_token='p2viz-test-token',
    tile_signing_secret='p2viz-test-tile-secret', execution='manual',
    preview_dir=root.parent / 'previews', journal_enabled=True))
r = TestClient(app).post('/viz/v1/renders', headers={
    'Authorization': 'Bearer p2viz-test-token',
    'X-CoLAB-Lab': '01JQ00000000000000000LAB01',
    'X-CoLAB-Account': '01JQ00000000000000000ACC01'}, json={
    'target': {'datasetId': target_id}, 'style': {'palette': '단색-파랑'}})
id_path.write_text(r.json()['renderId'])
os.kill(os.getpid(), signal.SIGKILL)
"""
    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path(__file__).resolve().parents[1] / "src")
    killed = subprocess.run([sys.executable, "-c", script, str(source_root),
                             target_id, str(id_path)], check=False, env=env)
    assert killed.returncode == -9
    render_id = id_path.read_text()

    restarted = make_client(source_root, "thread", journal_enabled=True)
    job = restarted.app.state.jobs.get(render_id)
    assert job is not None and job.done.wait(3)
    assert job.render_id == render_id and job.status == "완료"
    restarted.app.state.jobs.close()


def test_restart_preserves_upload_expiry_instead_of_extending_ttl(
    source_root, put_target, tiny_geotiff,
):
    first = make_client(source_root, "inline", journal_enabled=True,
                        result_ttl_seconds=60)
    upload_id = put_target(copy_from=[tiny_geotiff])
    response = first.post("/viz/v1/renders", headers=AUTH, json={
        "target": {"uploadId": upload_id}, "style": STYLE})
    render_id = response.json()["renderId"]
    expires_at = first.app.state.jobs.get(render_id).expires_at
    first.app.state.jobs.close()

    restarted = make_client(source_root, "thread", journal_enabled=True,
                            result_ttl_seconds=3600)
    restored = restarted.app.state.jobs.get(render_id)

    assert restored.expires_at == expires_at
    assert any(item == (expires_at, render_id) for item in restarted.app.state.jobs._expiring)
    restarted.app.state.jobs.close()


def test_restart_restores_tile_and_screenshot_without_source(
    source_root, put_target, tiny_geotiff,
):
    first = make_client(source_root, "inline", journal_enabled=True,
                        tile_branch_enabled=True)
    target_id = put_target(copy_from=[tiny_geotiff])
    body = first.post("/viz/v1/renders", headers=AUTH, json=_body(target_id)).json()
    render_id = body["renderId"]
    tile_url = body["result"]["tileUrlTemplate"].replace("{z}", "0").replace("{x}", "0").replace("{y}", "0")
    before_tile = first.get(tile_url, headers=AUTH)
    shot_body = {"layers": [{"renderId": render_id, "opacity": 1.0}],
                 "viewport": {"width": 16, "height": 16,
                              "bounds": {"west": 126, "south": 36, "east": 128, "north": 38}}}
    before_shot = first.post("/viz/v1/screenshots", headers=AUTH, json=shot_body)
    first.app.state.jobs.close()
    shutil.rmtree(storage_layout.target_dir(source_root, target_id))

    restarted = make_client(source_root, "thread", journal_enabled=True,
                            tile_branch_enabled=True)
    after_tile = restarted.get(tile_url, headers=AUTH)
    after_shot = restarted.post("/viz/v1/screenshots", headers=AUTH, json=shot_body)

    assert before_tile.status_code == after_tile.status_code == 200
    assert after_tile.content == before_tile.content
    assert before_shot.status_code == after_shot.status_code == 200
    assert after_shot.content == before_shot.content
    restarted.app.state.jobs.close()


def test_corrupt_render_snapshot_fails_only_that_job(
    source_root, put_target, tiny_geotiff,
):
    first = make_client(source_root, "inline", journal_enabled=True)
    target_id = put_target(copy_from=[tiny_geotiff])
    render_id = first.post("/viz/v1/renders", headers=AUTH, json=_body(target_id)).json()["renderId"]
    snapshot = source_root.parent / "previews" / ".render-state" / f"{render_id}.npy"
    first.app.state.jobs.close()
    snapshot.write_bytes(b"not numpy")

    restarted = make_client(source_root, "thread", journal_enabled=True)
    restored = restarted.get(f"/viz/v1/renders/{render_id}", headers=AUTH)

    assert restored.status_code == 200
    assert restored.json()["status"] == "실패"
    assert restored.json()["failure"]["code"] == "RENDER_ARTIFACT_MISSING"
    restarted.app.state.jobs.close()


def test_corrupt_journal_does_not_block_startup(source_root):
    preview_dir = source_root.parent / "previews"
    preview_dir.mkdir(parents=True)
    (preview_dir / ".render-journal.json").write_text("{broken", encoding="utf-8")

    client = make_client(source_root, "thread", journal_enabled=True)

    assert client.app.state.jobs._journal_records == {}
    client.app.state.jobs.close()


def test_restart_source_resolution_failure_isolated_to_pending_job(
    source_root, put_target, tiny_geotiff,
):
    first = make_client(source_root, "manual", journal_enabled=True)
    target_id = put_target(copy_from=[tiny_geotiff])
    render_id = first.post("/viz/v1/renders", headers=AUTH, json=_body(target_id)).json()["renderId"]
    first.app.state.jobs.close()
    shutil.rmtree(storage_layout.target_dir(source_root, target_id))

    restarted = make_client(source_root, "thread", journal_enabled=True)
    job = restarted.app.state.jobs.get(render_id)

    assert job is not None and job.status == "실패"
    assert job.failure["code"] == "RENDER_UNKNOWN_ERROR"
    restarted.app.state.jobs.close()


def test_restart_pending_upload_preserves_original_expiry(
    source_root, put_target, tiny_geotiff,
):
    first = make_client(source_root, "manual", journal_enabled=True, result_ttl_seconds=60)
    target_id = put_target(copy_from=[tiny_geotiff])
    render_id = first.post("/viz/v1/renders", headers=AUTH,
                           json={"target": {"uploadId": target_id}, "style": STYLE}).json()["renderId"]
    original = first.app.state.jobs.get(render_id).expires_at
    first.app.state.jobs.close()

    restarted = make_client(source_root, "manual", journal_enabled=True, result_ttl_seconds=3600)
    restored = restarted.app.state.jobs.get(render_id)

    assert restored.expires_at == original
    assert (original, render_id) in restarted.app.state.jobs._expiring
    restarted.app.state.jobs.close()


def test_completed_dataset_journal_count_does_not_become_lifetime_quota(
    source_root, put_target, tiny_geotiff,
):
    client = make_client(source_root, "manual", journal_enabled=True)
    first = put_target(copy_from=[tiny_geotiff])
    second = put_target(copy_from=[tiny_geotiff])
    third = put_target(copy_from=[tiny_geotiff])
    client.app.state.jobs._max_tombstones = 2
    for target in (first, second):
        response = client.post("/viz/v1/renders", headers=AUTH, json=_body(target))
        assert response.status_code == 202
        client.app.state.jobs.run_pending()

    response = client.post("/viz/v1/renders", headers=AUTH, json=_body(third))

    assert response.status_code == 202
    assert len(client.app.state.jobs._journal_records) == 3
    client.app.state.jobs.close()


def test_restart_queue_full_failure_preserves_upload_expiry(
    source_root, put_target, tiny_geotiff, monkeypatch,
):
    first = make_client(source_root, "manual", journal_enabled=True, result_ttl_seconds=60)
    upload_id = put_target(copy_from=[tiny_geotiff])
    render_id = first.post("/viz/v1/renders", headers=AUTH, json={
        "target": {"uploadId": upload_id}, "style": STYLE}).json()["renderId"]
    pending = first.app.state.jobs.get(render_id)
    original_expiry = pending.expires_at
    spec = pending.spec
    first.app.state.jobs.close()
    store = jobs.JobStore(execution="manual", tile_url_base="/tiles", ttl_seconds=3600,
                          journal_dir=source_root.parent / "previews")
    monkeypatch.setattr(store, "submit", lambda *args, **kwargs: (_ for _ in ()).throw(
        jobs.QueueFull()))

    store.restore(lambda _record: spec)
    restored = store.get(render_id)

    assert restored.status == "실패"
    assert restored.expires_at == original_expiry
    assert restored.to_dict()["expiresAt"] == original_expiry.isoformat().replace("+00:00", "Z")
    assert (original_expiry, render_id) in store._expiring
    store.close()


def test_expired_journal_record_removes_its_snapshot(
    source_root, put_target, tiny_geotiff,
):
    client = make_client(source_root, "inline", journal_enabled=True, result_ttl_seconds=-1)
    upload_id = put_target(copy_from=[tiny_geotiff])
    render_id = client.post("/viz/v1/renders", headers=AUTH, json={
        "target": {"uploadId": upload_id}, "style": STYLE}).json()["renderId"]
    snapshot = source_root.parent / "previews" / ".render-state" / f"{render_id}.npy"
    assert snapshot.exists()

    client.app.state.jobs.get(render_id)

    assert render_id not in client.app.state.jobs._journal_records
    assert not snapshot.exists()
    client.app.state.jobs.close()


def test_restart_rebuilds_artifact_index_for_palette_supersession(
    source_root, put_target, tiny_geotiff,
):
    first = make_client(source_root, "inline", journal_enabled=True)
    target_id = put_target(copy_from=[tiny_geotiff])
    render_id = first.post("/viz/v1/renders", headers=AUTH, json=_body(target_id)).json()["renderId"]
    old_paths = {a.path for a in first.app.state.jobs.get(render_id).artifacts.all()}
    first.app.state.jobs.close()

    restarted = make_client(source_root, "inline", journal_enabled=True)
    restored = restarted.app.state.jobs.get(render_id)
    assert restored.artifacts is not None
    assert {candidate.path for candidate in restarted.app.state.jobs._produced_for(target_id)} == old_paths
    body = {"target": {"datasetId": target_id}, "style": {"palette": "다색-무지개"}}
    response = restarted.post("/viz/v1/renders", headers=AUTH, json=body)

    assert response.status_code == 202
    assert any(not path.exists() for path in old_paths)
    restarted.app.state.jobs.close()
