"""`〈69〉-⑴` — 기준 격자 파일 행은 **워커가 만든다**. 접수는 만들지 않는다.

접수(`createUpload`)는 업로드와 본체 파일 행까지만 세운다. 격자 파일 행은
워커가 축을 판별한 **뒤에** `carries_lat`/`carries_lon` 을 채워 세운다.
판별에 실패하면 **그 행은 아예 생기지 않고**, 등록은 그대로 진행한다(`〈63〉-ⓒ`).

`0004` 는 무수정이다 — CHECK 를 상태로 조건화하면 「축이 빈 격자 행」이 합법이 된다.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from colab_pipeline.domains.d5_ingestion import IngestionService, UploadFileWork, UploadWork
from fixture_builders import make_readable_geotiff
from memory_ledger import MemoryLedger

_LAB = "0000000000000000000000000A"
_ACC = "000000000000000000000000A1"
_UPL = "01JQ00000000000000000UPL01"
_F1 = "01JQ0000000000000000000F01"
_F2 = "01JQ0000000000000000000F02"


def _service(ledger) -> IngestionService:
    seq = iter(f"01JQ{i:022d}" for i in range(1, 99))
    return IngestionService(ledger, id_factory=lambda: next(seq))


def _accepted(ledger: MemoryLedger) -> None:
    ledger.accept(upload_id=_UPL, lab_id=_LAB, actor_account_id=_ACC)


def test_the_grid_row_does_not_exist_before_the_worker_runs():
    """접수 직후에는 격자 파일 행이 원장에 없다 — 그것이 `〈69〉-⑴` 이 치른 대가다."""
    ledger = MemoryLedger()
    _accepted(ledger)
    assert ledger.file_rows == {}


def test_worker_creates_the_grid_file_row_with_the_two_booleans(tmp_path: Path):
    src = make_readable_geotiff(tmp_path / "body.tif")
    lon = tmp_path / "grid_x.npy"
    np.save(lon, np.repeat(np.linspace(118.8, 133.5, 8)[None, :], 8, axis=0))
    ledger = MemoryLedger()
    _accepted(ledger)
    res = _service(ledger).process_upload(UploadWork(
        upload_id=_UPL, lab_id=_LAB, actor_account_id=_ACC, workdir=tmp_path / "work",
        files=[UploadFileWork(file_id=_F1, path=src, kind="본체", file_name=src.name),
               UploadFileWork(file_id=_F2, path=lon, kind="기준 격자 파일",
                              file_name=lon.name, storage_key="s3://grid_x.npy")],
    ))
    assert [e["type"] for e in res.events][-1] == "upload.ready"
    # **갱신이 아니라 생성이다** — 접수가 안 만든 행이 여기서 처음 생긴다.
    row = ledger.file_rows[_F2]
    assert row["kind"] == "기준 격자 파일"
    assert (row["carries_lat"], row["carries_lon"]) == (False, True)
    assert row["upload_id"] == _UPL and row["lab_id"] == _LAB
    assert row["storage_key"] == "s3://grid_x.npy"


def test_detection_failure_creates_no_row_and_the_upload_still_completes(tmp_path: Path):
    """`〈63〉-ⓒ` — 그 파일만 거절하고 등록은 진행한다. 축이 빈 행을 만들지 않는다."""
    src = make_readable_geotiff(tmp_path / "body.tif")
    amb = tmp_path / "mystery.npy"
    np.save(amb, np.repeat(np.linspace(30, 43, 8)[:, None], 8, axis=1))
    ledger = MemoryLedger()
    _accepted(ledger)
    res = _service(ledger).process_upload(UploadWork(
        upload_id=_UPL, lab_id=_LAB, actor_account_id=_ACC, workdir=tmp_path / "work",
        files=[UploadFileWork(file_id=_F1, path=src, kind="본체", file_name=src.name),
               UploadFileWork(file_id=_F2, path=amb, kind="기준 격자 파일",
                              file_name=amb.name)],
    ))
    assert [e["type"] for e in res.events][-1] == "upload.ready"
    assert _F2 in res.rejected
    assert _F2 not in ledger.file_rows            # 행이 **생기지 않는다**
    assert ledger.file_rows == {}


def test_an_empty_axis_row_is_refused_by_the_ledger():
    ledger = MemoryLedger()
    _accepted(ledger)
    with pytest.raises(ValueError):
        ledger.record_file_axes_row(
            file_id=_F2, lab_id=_LAB, upload_id=_UPL, file_name="e.npy",
            storage_key="s3://e", carries_lat=False, carries_lon=False)
