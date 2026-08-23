"""워커가 이벤트를 **실제로 발행한다** — 행복 경로와 실패 경로 둘 다 (`P2-EXEC §6-7`).

행복 경로만으로는 `upload.failed` 가 안 나온다. **7종을 주장하려면 7종을 봐야 한다.**
`upload.accepted` 는 core-api 소관이라 여기서는 **접수 사실**로 주어지고,
워커는 ②~⑦ 을 낸다(`SOURCE_BY_TYPE` 이 이 경계를 강제한다).
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from colab_pipeline.d5.events import EVENT_TYPES, idempotency_key
from colab_pipeline.domains.d5_ingestion import (
    IngestionService,
    UploadFileWork,
    UploadWork,
)
from fixture_builders import make_readable_geotiff

from memory_ledger import MemoryLedger

_LAB = "01JQ0000000000000000000001"
_ACC = "01JQ0000000000000000000002"
_UPL = "01JQ0000000000000000000003"
_F1 = "01JQ00000000000000000000F1"
_F2 = "01JQ00000000000000000000F2"


def _service(ledger=None):
    return IngestionService(ledger or MemoryLedger())


def test_happy_path_emits_stages_two_to_six(tmp_path):
    src = make_readable_geotiff(tmp_path / "kwra_output.tif")
    ledger = MemoryLedger()
    ledger.accept(upload_id=_UPL, lab_id=_LAB, actor_account_id=_ACC)
    svc = _service(ledger)
    res = svc.process_upload(UploadWork(
        upload_id=_UPL, lab_id=_LAB, actor_account_id=_ACC, workdir=tmp_path / "work",
        files=[UploadFileWork(file_id=_F1, path=src, kind="본체", file_name=src.name)],
    ))
    emitted = res.events
    types = [e["type"] for e in emitted]
    assert types == [
        "file.format-detected", "file.header-parsed",
        "file.crs-normalized", "preview.cog-built", "upload.ready",
    ], types
    assert all(e["source"] == "pipeline-worker" for e in emitted)
    assert [e["idempotencyKey"] for e in emitted] == [idempotency_key(t, _UPL) for t in types]
    assert "upload.failed" not in types      # 행복 경로는 ⑦ 을 못 낸다 — 그래서 실패 경로가 따로 필요하다


def test_failure_path_emits_upload_failed(tmp_path):
    """좌표를 못 구하면 지어내지 않고 실패한다 (`DR-9`). ⑦ 이 여기서 나온다."""
    bad = tmp_path / "broken.bin"
    bad.write_bytes(b"\x00" * 2048)          # 알려진 매직 없음 → 형식 인식 실패
    ledger = MemoryLedger()
    ledger.accept(upload_id=_UPL, lab_id=_LAB, actor_account_id=_ACC)
    res = _service(ledger).process_upload(UploadWork(
        upload_id=_UPL, lab_id=_LAB, actor_account_id=_ACC, workdir=tmp_path / "work",
        files=[UploadFileWork(file_id=_F1, path=bad, kind="본체", file_name=bad.name)],
    ))
    emitted = res.events
    types = [e["type"] for e in emitted]
    assert types[-1] == "upload.failed", types
    failure = emitted[-1]["payload"]["failure"]
    assert failure["reason"] == "형식 인식 실패"
    assert failure["class"] == "영구"
    assert failure["failedAt"] == "file.format-detected"
    assert failure["willRetry"] is False


def test_two_runs_cover_all_seven_event_types(tmp_path):
    """행복 1회 + 실패 1회 + 접수(core-api) = 7종. 계측은 합집합으로 한다."""
    ledger = MemoryLedger()
    ledger.accept(upload_id=_UPL, lab_id=_LAB, actor_account_id=_ACC)
    ok_src = make_readable_geotiff(tmp_path / "ok.tif")
    _service(ledger).process_upload(UploadWork(
        upload_id=_UPL, lab_id=_LAB, actor_account_id=_ACC, workdir=tmp_path / "w1",
        files=[UploadFileWork(file_id=_F1, path=ok_src, kind="본체", file_name=ok_src.name)],
    ))
    upl2 = "01JQ0000000000000000000004"
    ledger.accept(upload_id=upl2, lab_id=_LAB, actor_account_id=_ACC)
    bad = tmp_path / "bad.bin"
    bad.write_bytes(b"\x00" * 2048)
    _service(ledger).process_upload(UploadWork(
        upload_id=upl2, lab_id=_LAB, actor_account_id=_ACC, workdir=tmp_path / "w2",
        files=[UploadFileWork(file_id=_F2, path=bad, kind="본체", file_name=bad.name)],
    ))
    assert {e["type"] for e in ledger.events} == set(EVENT_TYPES)


def test_mixed_formats_fail_permanently(tmp_path):
    """조각의 포맷이 다르면 조각이 아니라 다른 데이터다 (`§2-13`)."""
    a = make_readable_geotiff(tmp_path / "a.tif")
    b = tmp_path / "b.nc"
    import fixture_builders as fb
    fb.make_netcdf(b)
    ledger = MemoryLedger()
    ledger.accept(upload_id=_UPL, lab_id=_LAB, actor_account_id=_ACC)
    res = _service(ledger).process_upload(UploadWork(
        upload_id=_UPL, lab_id=_LAB, actor_account_id=_ACC, workdir=tmp_path / "work",
        files=[UploadFileWork(file_id=_F1, path=a, kind="본체", file_name=a.name),
               UploadFileWork(file_id=_F2, path=b, kind="본체", file_name=b.name)],
    ))
    emitted = res.events
    fmt = emitted[0]
    assert fmt["type"] == "file.format-detected"
    assert fmt["payload"]["uniform"] is False
    assert emitted[-1]["type"] == "upload.failed"
    assert emitted[-1]["payload"]["failure"]["reason"] == "조각이 서로 다름"
    assert emitted[-1]["payload"]["failure"]["class"] == "영구"


def test_replay_is_idempotent(tmp_path):
    """같은 업로드를 두 번 돌려도 원장에 같은 이벤트가 두 벌 생기지 않는다 (S2 완료 판정)."""
    src = make_readable_geotiff(tmp_path / "ok.tif")
    ledger = MemoryLedger()
    ledger.accept(upload_id=_UPL, lab_id=_LAB, actor_account_id=_ACC)
    work = UploadWork(
        upload_id=_UPL, lab_id=_LAB, actor_account_id=_ACC, workdir=tmp_path / "work",
        files=[UploadFileWork(file_id=_F1, path=src, kind="본체", file_name=src.name)],
    )
    svc = _service(ledger)
    svc.process_upload(work)
    first = list(ledger.events)
    svc.process_upload(work)
    assert [e["idempotencyKey"] for e in ledger.events] == [e["idempotencyKey"] for e in first]


def test_emitted_envelopes_validate_against_the_frozen_contract(tmp_path, event_validator):
    src = make_readable_geotiff(tmp_path / "ok.tif")
    ledger = MemoryLedger()
    ledger.accept(upload_id=_UPL, lab_id=_LAB, actor_account_id=_ACC)
    res = _service(ledger).process_upload(UploadWork(
        upload_id=_UPL, lab_id=_LAB, actor_account_id=_ACC, workdir=tmp_path / "work",
        files=[UploadFileWork(file_id=_F1, path=src, kind="본체", file_name=src.name)],
    ))
    for env in res.events:
        assert not event_validator(env), (env["type"], event_validator(env))


def test_grid_file_with_undetermined_axis_is_rejected_but_upload_continues(tmp_path):
    """`〈66〉`·`〈63〉-ⓒ` — 축을 못 정한 격자 파일은 거절되고, 업로드는 계속 간다."""
    src = make_readable_geotiff(tmp_path / "body.tif")
    amb = tmp_path / "mystery.npy"
    np.save(amb, np.repeat(np.linspace(30, 43, 8)[:, None], 8, axis=1))
    ledger = MemoryLedger()
    ledger.accept(upload_id=_UPL, lab_id=_LAB, actor_account_id=_ACC)
    svc = _service(ledger)
    res = svc.process_upload(UploadWork(
        upload_id=_UPL, lab_id=_LAB, actor_account_id=_ACC, workdir=tmp_path / "work",
        files=[UploadFileWork(file_id=_F1, path=src, kind="본체", file_name=src.name),
               UploadFileWork(file_id=_F2, path=amb, kind="기준 격자 파일", file_name=amb.name)],
    ))
    assert [e["type"] for e in res.events][-1] == "upload.ready"   # 등록은 막히지 않는다
    assert _F2 in res.rejected                                     # 그 파일만 막힌다
    assert _F2 not in ledger.axes                                  # 축이 빈 행을 만들지 않는다


def test_resolved_grid_axes_are_written_as_two_booleans(tmp_path):
    src = make_readable_geotiff(tmp_path / "body.tif")
    lon = tmp_path / "grid_x.npy"
    np.save(lon, np.repeat(np.linspace(118.8, 133.5, 8)[None, :], 8, axis=0))
    ledger = MemoryLedger()
    ledger.accept(upload_id=_UPL, lab_id=_LAB, actor_account_id=_ACC)
    _service(ledger).process_upload(UploadWork(
        upload_id=_UPL, lab_id=_LAB, actor_account_id=_ACC, workdir=tmp_path / "work",
        files=[UploadFileWork(file_id=_F1, path=src, kind="본체", file_name=src.name),
               UploadFileWork(file_id=_F2, path=lon, kind="기준 격자 파일", file_name=lon.name)],
    ))
    assert ledger.axes[_F2] == (False, True)
