from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
import threading

import pytest
from colab_viz.domains.d7_visualization import jobs
from colab_viz.ports.source import ResolvedTarget, SourcePart


def _spec(tmp_path: Path) -> jobs.RenderSpec:
    part = SourcePart(file_id="file-1", file_name="one.tif",
                      path=tmp_path / "one.tif", size_bytes=1)
    return jobs.RenderSpec(
        target=ResolvedTarget(target_id="target-1", is_upload=False,
                              parts=(part,), grid_dir=None),
        palette="단색-파랑", class_count=5, variable="temperature",
        instant="2026-09-16T00:00:00Z", without_reference_grid=False,
        max_preview_side=32, deadline_seconds=10, preview_dir=tmp_path,
        preview_url_base="/previews",
    )


def _store(tmp_path: Path) -> jobs.JobStore:
    return jobs.JobStore(execution="manual", tile_url_base="/tiles", ttl_seconds=60)


def _capture_timing(monkeypatch):
    events: list[dict] = []
    monkeypatch.setattr(jobs.observability, "structured_event",
                        lambda **fields: events.append(fields))
    return events


def _finish_without_rendering(monkeypatch, store: jobs.JobStore, *, failed: bool = False) -> None:
    def run(job):
        if failed:
            job.status = jobs.STATUS_FAILED
            job.failure = {"code": "RENDER_UNKNOWN_ERROR"}
        else:
            job.render_succeeded = True

    monkeypatch.setattr(jobs, "_run", run)
    monkeypatch.setattr(store, "_plan_for",
                        lambda job, event: SimpleNamespace(regenerate=False))
    monkeypatch.setattr(store, "_supersede_for", lambda job: SimpleNamespace())
    monkeypatch.setattr(jobs.invalidation, "apply", lambda *args, **kwargs: ())


def test_manual_job_emits_independent_queue_and_processing_times(tmp_path, monkeypatch):
    store = _store(tmp_path)
    events = _capture_timing(monkeypatch)
    _finish_without_rendering(monkeypatch, store)
    clock = iter((10.000, 10.020, 10.050))
    monkeypatch.setattr(jobs.time, "monotonic", lambda: next(clock))

    store.submit("render-1", _spec(tmp_path), temporary=False)
    store.run_pending()

    assert events == [{
        "service": "viz-render", "event": "render.timing",
        "render_id": "render-1", "target_id": "target-1",
        "file_ids": ["file-1"], "variable": "temperature",
        "instant": "2026-09-16T00:00:00Z", "queue_ms": 20,
        "processing_ms": 30, "status": "success", "failure_code": None,
        "queue_observation": "measured",
    }]
    store.close()


def test_failed_job_emits_terminal_processing_time_without_cross_job_accumulation(
    tmp_path, monkeypatch,
):
    store = _store(tmp_path)
    events = _capture_timing(monkeypatch)
    _finish_without_rendering(monkeypatch, store, failed=True)
    clock = iter((1.0, 2.0, 2.5, 10.0, 10.1, 10.3))
    monkeypatch.setattr(jobs.time, "monotonic", lambda: next(clock))

    for render_id in ("failed-1", "failed-2"):
        store.submit(render_id, _spec(tmp_path), temporary=False)
        store.run_pending()

    assert [(event["render_id"], event["queue_ms"], event["processing_ms"])
            for event in events] == [("failed-1", 1000, 500), ("failed-2", 100, 200)]
    assert all(event["status"] == "failed" for event in events)
    assert all(event["failure_code"] == "RENDER_UNKNOWN_ERROR" for event in events)
    store.close()


def test_journal_restored_pending_job_marks_queue_time_unknown(tmp_path, monkeypatch):
    journal_dir = tmp_path / "previews"
    first = jobs.JobStore(execution="manual", tile_url_base="/tiles", ttl_seconds=60,
                          journal_dir=journal_dir)
    spec = _spec(tmp_path)
    first.submit("restored-1", spec, temporary=False)
    first.close()

    store = jobs.JobStore(execution="manual", tile_url_base="/tiles", ttl_seconds=60,
                          journal_dir=journal_dir)
    events = _capture_timing(monkeypatch)
    _finish_without_rendering(monkeypatch, store)
    clock = iter((5.0, 5.4))
    monkeypatch.setattr(jobs.time, "monotonic", lambda: next(clock))

    store.restore(lambda record: spec)
    store.run_pending()

    assert events[0]["queue_ms"] is None
    assert events[0]["queue_observation"] == "unknown_restored"
    assert events[0]["processing_ms"] == 400
    store.close()


@pytest.mark.parametrize(("job_status", "timing_status"), [
    (jobs.STATUS_DONE, "success"),
    (jobs.STATUS_FAILED, "failed"),
    (jobs.STATUS_DRAWING, "unknown"),
])
def test_timing_status_follows_job_state_not_failure_code(
    tmp_path, monkeypatch, job_status, timing_status,
):
    events = _capture_timing(monkeypatch)
    job = jobs.RenderJob(render_id="render-without-code", spec=_spec(tmp_path),
                         status=job_status, queued_at=1.0)

    jobs.JobStore._emit_timing(job, worker_started_at=1.1, finished_at=1.2)

    assert events[0]["status"] == timing_status
    assert events[0]["failure_code"] is None


def test_timing_log_failure_does_not_prevent_worker_completion(tmp_path, monkeypatch):
    store = _store(tmp_path)
    _finish_without_rendering(monkeypatch, store)
    monkeypatch.setattr(jobs.time, "monotonic", iter((1.0, 1.1, 1.2)).__next__)
    monkeypatch.setattr(jobs.observability, "structured_event",
                        lambda **fields: (_ for _ in ()).throw(OSError("stdout closed")))

    job = store.submit("render-1", _spec(tmp_path), temporary=False)
    store.run_pending()

    assert job.done.is_set()
    assert job.status == jobs.STATUS_DONE
    store.close()


@pytest.mark.parametrize("execution", ["inline", "thread"])
def test_inline_and_thread_executors_emit_timing(tmp_path, monkeypatch, execution):
    store = jobs.JobStore(execution=execution, tile_url_base="/tiles", ttl_seconds=60)
    events = _capture_timing(monkeypatch)
    _finish_without_rendering(monkeypatch, store)

    job = store.submit(f"{execution}-1", _spec(tmp_path), temporary=False)
    assert job.done.wait(1)

    assert len(events) == 1
    assert events[0]["render_id"] == f"{execution}-1"
    assert events[0]["queue_ms"] >= 0
    assert events[0]["processing_ms"] >= 0
    store.close()


def test_thread_queue_rejection_emits_failure_timing(tmp_path, monkeypatch):
    store = jobs.JobStore(execution="thread", tile_url_base="/tiles", ttl_seconds=60,
                          queue_size=1)
    events = _capture_timing(monkeypatch)
    entered = threading.Event()
    release = threading.Event()

    def blocked_run(job, event):
        entered.set()
        assert release.wait(2)
        job.done.set()

    monkeypatch.setattr(store, "_run_and_plan", blocked_run)
    first = store.submit("first", _spec(tmp_path), temporary=False)
    assert entered.wait(1)
    second = store.submit("second", _spec(tmp_path), temporary=False)

    with pytest.raises(jobs.QueueFull):
        store.submit("rejected", _spec(tmp_path), temporary=False)

    assert events == [{
        "service": "viz-render", "event": "render.timing",
        "render_id": "rejected", "target_id": "target-1",
        "file_ids": ["file-1"], "variable": "temperature",
        "instant": "2026-09-16T00:00:00Z", "queue_ms": None,
        "processing_ms": None, "status": "failed",
        "failure_code": "PREVIEW_QUEUE_FULL", "queue_observation": "measured",
    }]
    release.set()
    assert first.done.wait(1)
    assert second.done.wait(1)
    store.close()
