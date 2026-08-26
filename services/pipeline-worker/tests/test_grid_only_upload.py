"""격자 전용 업로드는 **감지 실패가 아니다** — Ted 판정 2026-08-26 (해소안 ⓐ).

「워커에서 격자전용은 제외하라」 — 감지 루프는 본체만 순회하므로(`d5_ingestion.py`
`bodies` 필터) 격자 전용 업로드는 감지 대상이 **공집합**이다. 공집합을
「전건이 알려진 매직바이트가 아니다」로 읽으면 원장은 성공, 파이프라인은 실패로 갈린다.

가르는 세 경우 —
  ⑴ 본체 0 · 격자 1 이상 → 실패 없음. 축 판별 뒤 `upload.ready`
  ⑵ 본체 1 이상 · 감지 실패 → **그대로 실패**(뭉개지 않는다)
  ⑶ 본체 0 · 격자 0 → 실패. 격자 전용과 다른 경우다
"""
from __future__ import annotations

from pathlib import Path

import numpy as np

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


def _lon(tmp_path: Path) -> Path:
    p = tmp_path / "grid_x.npy"
    np.save(p, np.repeat(np.linspace(118.8, 133.5, 8)[None, :], 8, axis=0))
    return p


def _grid_only_work(tmp_path: Path) -> UploadWork:
    lon = _lon(tmp_path)
    return UploadWork(
        upload_id=_UPL, lab_id=_LAB, actor_account_id=_ACC, workdir=tmp_path / "work",
        files=[UploadFileWork(file_id=_F2, path=lon, kind="기준 격자 파일",
                              file_name=lon.name, storage_key="s3://grid_x.npy")])


def test_grid_only_upload_emits_no_failure(tmp_path: Path):
    ledger = MemoryLedger()
    ledger.accept(upload_id=_UPL, lab_id=_LAB, actor_account_id=_ACC)
    res = _service(ledger).process_upload(_grid_only_work(tmp_path))
    types = [e["type"] for e in res.events]
    assert "upload.failed" not in types
    assert types[-1] == "upload.ready"
    row = ledger.uploads[_UPL]
    assert row["ready"] is True
    assert row["failed_at"] is None and row["failure_reason"] is None


def test_grid_only_upload_still_stands_the_grid_row_and_says_the_axis(tmp_path: Path):
    ledger = MemoryLedger()
    ledger.accept(upload_id=_UPL, lab_id=_LAB, actor_account_id=_ACC)
    res = _service(ledger).process_upload(_grid_only_work(tmp_path))
    assert ledger.file_rows[_F2]["carries_lon"] is True
    ready = res.events[-1]["payload"]
    assert ready["renderable"] is False and ready["metadataComplete"] is False
    assert [r["fileId"] for r in ready["gridResolution"]] == [_F2]


def test_grid_only_upload_is_the_same_in_stage1(tmp_path: Path):
    ledger = MemoryLedger()
    ledger.accept(upload_id=_UPL, lab_id=_LAB, actor_account_id=_ACC)
    res = _service(ledger).process_upload(_grid_only_work(tmp_path), stage1=True)
    assert "upload.failed" not in [e["type"] for e in res.events]


def test_a_body_that_cannot_be_detected_still_fails(tmp_path: Path):
    """음성 — 두 경우를 뭉개지 않는다."""
    junk = tmp_path / "body.bin"
    junk.write_bytes(b"\x00\x01\x02\x03" * 8)
    lon = _lon(tmp_path)
    ledger = MemoryLedger()
    ledger.accept(upload_id=_UPL, lab_id=_LAB, actor_account_id=_ACC)
    res = _service(ledger).process_upload(UploadWork(
        upload_id=_UPL, lab_id=_LAB, actor_account_id=_ACC, workdir=tmp_path / "work",
        files=[UploadFileWork(file_id=_F1, path=junk, kind="본체", file_name=junk.name),
               UploadFileWork(file_id=_F2, path=lon, kind="기준 격자 파일",
                              file_name=lon.name, storage_key="s3://grid_x.npy")]))
    failed = [e for e in res.events if e["type"] == "upload.failed"]
    assert len(failed) == 1
    assert failed[0]["payload"]["failure"]["reason"] == "형식 인식 실패"
    assert ledger.uploads[_UPL]["ready"] is False


def test_an_empty_upload_fails_with_its_own_detail(tmp_path: Path):
    """⑶ — 파일이 0건인 업로드는 격자 전용과 다른 경우다."""
    ledger = MemoryLedger()
    ledger.accept(upload_id=_UPL, lab_id=_LAB, actor_account_id=_ACC)
    res = _service(ledger).process_upload(UploadWork(
        upload_id=_UPL, lab_id=_LAB, actor_account_id=_ACC,
        workdir=tmp_path / "work", files=[]))
    failed = [e for e in res.events if e["type"] == "upload.failed"]
    assert len(failed) == 1
    assert failed[0]["payload"]["failure"]["detail"] == "업로드에 파일이 없다"
    assert failed[0]["payload"]["failure"]["class"] == "영구"


def test_a_readable_body_is_untouched(tmp_path: Path):
    src = make_readable_geotiff(tmp_path / "body.tif")
    ledger = MemoryLedger()
    ledger.accept(upload_id=_UPL, lab_id=_LAB, actor_account_id=_ACC)
    res = _service(ledger).process_upload(UploadWork(
        upload_id=_UPL, lab_id=_LAB, actor_account_id=_ACC, workdir=tmp_path / "work",
        files=[UploadFileWork(file_id=_F1, path=src, kind="본체", file_name=src.name)]))
    types = [e["type"] for e in res.events]
    assert "file.format-detected" in types and types[-1] == "upload.ready"
