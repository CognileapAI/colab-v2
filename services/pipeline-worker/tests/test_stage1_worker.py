"""stage 1 워커 — **감지 다음이 곧 `ready`** (`PLAN-SoT §9-〈73〉` · `S1-PLAN-REFOUND §D.6`).

**왜 파싱·좌표·COG 가 빠지는가 — 「미리보기가 stage 1 로 돌아왔으니 다 켠다」가 아니다.**
`〈74〉`·`〈75〉` 가 되살린 미리보기는 **워커 파이프라인 안이 아니라 화면 요청형**이다
(`§D.6` 흐름도 — `upload.ready` 뒤에 FE 가 `POST /previews` 를 부르고 그리는 것은 **D7**).
그래서 워커의 stage 1 은 `〈73〉` 이 정한 그대로다:

    감지(매직바이트 1.6~23 ms) → file.format-detected → upload.ready     ← 2단계

**한 줄만 늘었다** — `〈79〉-⑷`: `upload.ready` 의 뜻이 「본체 감지가 끝났고, **함께 올라온
격자 파일의 축이 확정되거나 거절됐다**」가 된다. **단계 수는 그대로다.** 늘어난 것은
ready 의 판정 조건이지 단계가 아니다.

그리고 `〈79〉-⑶` — **격자 파일은 감지·미리보기를 태우지 않고 `file.format-detected` 를
발행하지 않는다.** 축 판별 사다리만 돈다.
"""
from __future__ import annotations

import numpy as np
import pytest
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
_G1 = "01JQ00000000000000000000G1"
_G2 = "01JQ00000000000000000000G2"


def _run(tmp_path, files, ledger=None):
    ledger = ledger or MemoryLedger()
    ledger.accept(upload_id=_UPL, lab_id=_LAB, actor_account_id=_ACC)
    svc = IngestionService(ledger)
    res = svc.process_upload(UploadWork(
        upload_id=_UPL, lab_id=_LAB, actor_account_id=_ACC, workdir=tmp_path / "work",
        files=files), stage1=True)
    return ledger, res


def test_stage1_emits_exactly_two_stages(tmp_path):
    """**감지 다음이 곧 ready 다.** 헤더 파싱·좌표 정규화·COG 는 stage 1 밖이다."""
    src = make_readable_geotiff(tmp_path / "kwra_output.tif")
    _ledger, res = _run(tmp_path, [
        UploadFileWork(file_id=_F1, path=src, kind="본체", file_name=src.name)])
    assert [e["type"] for e in res.events] == ["file.format-detected", "upload.ready"]


def test_stage1_flips_ready_so_the_polling_ends(tmp_path):
    """`〈73〉-ⓑ` — **Ted 가 말한 「대기」의 실물이 이것이다.** 배선 전에는 `ready` 가 영원히
    false 라 `UploadModal` 이 1초마다 무한 폴링했다. 가공 코드가 아니라 **가공을 기다리는
    형태**가 원인이었다."""
    src = make_readable_geotiff(tmp_path / "kwra_output.tif")
    ledger, _res = _run(tmp_path, [
        UploadFileWork(file_id=_F1, path=src, kind="본체", file_name=src.name)])
    assert ledger.uploads[_UPL]["ready"] is True


def test_stage1_leaves_renderable_and_metadata_complete_null_in_the_ledger(tmp_path):
    """`S1-PLAN-REFOUND §D.1 #20` — **열은 살리되 값은 NULL 이다.**
    헤더를 안 읽었으므로 「자동 메타 다섯을 다 읽었는가」에 답할 자격이 없다.
    false 로 채우면 **읽어 보고 아니었다**는 뜻이 되어 「모른다」와 갈리지 않는다."""
    src = make_readable_geotiff(tmp_path / "kwra_output.tif")
    ledger, _res = _run(tmp_path, [
        UploadFileWork(file_id=_F1, path=src, kind="본체", file_name=src.name)])
    row = ledger.uploads[_UPL]
    assert row["renderable"] is None and row["metadata_complete"] is None


def test_stage1_ready_payload_is_honest_about_what_it_did_not_read(tmp_path):
    """계약이 두 불리언을 required 로 못 박았으므로 값을 내긴 낸다 —
    `renderable` 은 **감지로 안 사실**이고, `metadataComplete` 는 **안 읽었으니 false** 다."""
    src = make_readable_geotiff(tmp_path / "kwra_output.tif")
    _ledger, res = _run(tmp_path, [
        UploadFileWork(file_id=_F1, path=src, kind="본체", file_name=src.name)])
    ready = next(e for e in res.events if e["type"] == "upload.ready")
    assert ready["payload"]["renderable"] is True     # GeoTIFF 는 그릴 수 있다
    assert ready["payload"]["metadataComplete"] is False


def test_stage1_still_fails_closed_on_an_unknown_format(tmp_path):
    """건너뛴 것은 파싱·좌표·COG 이지 **판정**이 아니다. 매직바이트가 아니면 여전히 실패다."""
    bad = tmp_path / "broken.bin"
    bad.write_bytes(b"\x00" * 2048)
    _ledger, res = _run(tmp_path, [
        UploadFileWork(file_id=_F1, path=bad, kind="본체", file_name=bad.name)])
    types = [e["type"] for e in res.events]
    assert types == ["file.format-detected", "upload.failed"]
    assert "upload.ready" not in types


def test_stage1_still_resolves_grid_axes_before_ready(tmp_path):
    """`〈79〉-⑷` — `ready` 는 「본체 감지가 끝났고 **격자 축이 확정되거나 거절됐다**」는 뜻이다.
    격자 원장 행은 **축이 정해진 뒤에 워커가 만든다**(`〈79〉-㈎ⓒ`)."""
    src = make_readable_geotiff(tmp_path / "kwra_output.tif")
    lat = tmp_path / "lat.npy"
    lon = tmp_path / "lon.npy"
    np.save(lat, np.linspace(33.0, 39.0, 16).reshape(4, 4))
    np.save(lon, np.linspace(124.0, 132.0, 16).reshape(4, 4))
    ledger, res = _run(tmp_path, [
        UploadFileWork(file_id=_F1, path=src, kind="본체", file_name=src.name),
        UploadFileWork(file_id=_G1, path=lat, kind="기준 격자 파일", file_name="lat.npy",
                       storage_key="k/lat"),
        UploadFileWork(file_id=_G2, path=lon, kind="기준 격자 파일", file_name="lon.npy",
                       storage_key="k/lon"),
    ])
    assert ledger.uploads[_UPL]["ready"] is True
    assert set(ledger.axes) == {_G1, _G2}, "축이 확정된 격자 행이 원장에 안 섰다."


def test_stage1_does_not_run_detection_on_grid_files(tmp_path):
    """`〈79〉-⑶` — 격자는 **감지·미리보기를 태우지 않는다.** 감지 이벤트의 per-file 목록에
    격자가 끼면 격자가 「본체 NumPy 업로드」로 취급된 것이다 — 그것이 `〈79〉` 가 막은 자리다."""
    src = make_readable_geotiff(tmp_path / "kwra_output.tif")
    lat = tmp_path / "lat.npy"
    lon = tmp_path / "lon.npy"
    np.save(lat, np.linspace(33.0, 39.0, 16).reshape(4, 4))
    np.save(lon, np.linspace(124.0, 132.0, 16).reshape(4, 4))
    _ledger, res = _run(tmp_path, [
        UploadFileWork(file_id=_F1, path=src, kind="본체", file_name=src.name),
        UploadFileWork(file_id=_G1, path=lat, kind="기준 격자 파일", file_name="lat.npy",
                       storage_key="k/lat"),
        UploadFileWork(file_id=_G2, path=lon, kind="기준 격자 파일", file_name="lon.npy",
                       storage_key="k/lon"),
    ])
    detected = next(e for e in res.events if e["type"] == "file.format-detected")
    assert [p["fileId"] for p in detected["payload"]["perFile"]] == [_F1]


def test_full_pipeline_is_unchanged_when_stage1_is_not_asked_for(tmp_path):
    """**stage 2 를 위해 남겨 둔 것이 실제로 남아 있는가.** 건너뛴 구간은 지운 것이 아니다 —
    `〈73〉` 이 「뜯어내면 비용이 없어지는 것이 아니라 stage2 로 옮겨갈 뿐」이라고 적었다."""
    src = make_readable_geotiff(tmp_path / "kwra_output.tif")
    ledger = MemoryLedger()
    ledger.accept(upload_id=_UPL, lab_id=_LAB, actor_account_id=_ACC)
    res = IngestionService(ledger).process_upload(UploadWork(
        upload_id=_UPL, lab_id=_LAB, actor_account_id=_ACC, workdir=tmp_path / "work",
        files=[UploadFileWork(file_id=_F1, path=src, kind="본체", file_name=src.name)]))
    assert [e["type"] for e in res.events] == [
        "file.format-detected", "file.header-parsed",
        "file.crs-normalized", "preview.cog-built", "upload.ready"]


# ══════════════════ 소비 한 발 — outbox 의 접수분을 실제로 집는가 (`〈73〉` 배선 ②) ══════════════════
class _DriveLedger(MemoryLedger):
    """`pending_uploads` · `accepted_files` 를 더한 대역. 실물은 `SqlLedger` 다."""

    def pending_uploads(self, limit: int = 20):
        return [{"id": u["id"], "lab_id": u["lab_id"],
                 "uploader_account_id": u["uploader_account_id"]}
                for u in self.uploads.values()
                if not u["ready"] and u["failed_at"] is None and u["registered_at"] is None
                ][:limit]

    def accepted_files(self, upload_id: str):
        for e in self.events:
            if e["uploadId"] == upload_id and e["type"] == "upload.accepted":
                return list(e["payload"].get("files") or [])
        return []


def _accept_with_files(ledger, refs):
    ledger.accept(upload_id=_UPL, lab_id=_LAB, actor_account_id=_ACC)
    for e in ledger.events:
        if e["type"] == "upload.accepted":
            e["payload"]["files"] = refs


def test_drive_processes_an_accepted_upload_and_stops_the_polling(tmp_path):
    """`〈73〉` 배선 ② — `run_once` 가 접수분을 집어 stage 1 을 태운다.
    **production 호출자가 0건이던 자리가 여기다** (`S1-upload-path-audit §A-2`)."""
    from colab_pipeline.app.worker import drive_uploads

    root = tmp_path / "store"
    body = root / "uploads" / _UPL / _F1
    body.parent.mkdir(parents=True)
    make_readable_geotiff(body)

    ledger = _DriveLedger()
    _accept_with_files(ledger, [
        {"fileId": _F1, "fileName": "kwra.tif", "kind": "본체", "byteSize": 1}])
    done = drive_uploads(ledger, upload_dir=root, workdir=tmp_path / "work")
    assert done == [_UPL]
    assert ledger.uploads[_UPL]["ready"] is True
    assert [e["type"] for e in ledger.events if e["source"] == "pipeline-worker"] == [
        "file.format-detected", "upload.ready"]


def test_drive_does_not_process_the_same_upload_twice(tmp_path):
    """멱등의 전부는 **`ready` 를 조건에 넣는 것**이다 — 두 번째 바퀴에는 집합에 없다."""
    from colab_pipeline.app.worker import drive_uploads

    root = tmp_path / "store"
    body = root / "uploads" / _UPL / _F1
    body.parent.mkdir(parents=True)
    make_readable_geotiff(body)
    ledger = _DriveLedger()
    _accept_with_files(ledger, [
        {"fileId": _F1, "fileName": "kwra.tif", "kind": "본체", "byteSize": 1}])
    drive_uploads(ledger, upload_dir=root, workdir=tmp_path / "work")
    assert drive_uploads(ledger, upload_dir=root, workdir=tmp_path / "work") == []


def test_drive_finds_grid_files_that_have_no_ledger_row_yet(tmp_path):
    """`〈79〉-㈎ⓑ` — **접수는 격자 행을 만들지 않는다.** 그래서 파일 목록을 `d5_upload_file`
    에서 세면 격자가 통째로 안 보이고 축 판별이 돌 대상이 사라진다. 접수 이벤트의
    `files`(FileRef 전건)가 정본이다."""
    from colab_pipeline.app.worker import drive_uploads

    from colab_pipeline.kernel import storage_layout

    root = tmp_path / "store"
    storage_layout.target_dir(root, _UPL).mkdir(parents=True)
    make_readable_geotiff(storage_layout.target_dir(root, _UPL) / _F1)
    # **격자는 `grid/` 아래에 제 이름으로 놓인다** — 배치가 이름을 보존하기 때문이다
    # (`contracts/storage/layout.json`). 확장자를 벗기던 옛 배치에서는 축 판별 사다리가
    # `.npy` 를 못 알아보고 실패가 **「축 미상」으로 위장**했다.
    storage_layout.grid_dir(root, _UPL).mkdir(parents=True)
    np.save(storage_layout.grid_dir(root, _UPL) / "lat.npy",
            np.linspace(33.0, 39.0, 16).reshape(4, 4))
    np.save(storage_layout.grid_dir(root, _UPL) / "lon.npy",
            np.linspace(124.0, 132.0, 16).reshape(4, 4))

    ledger = _DriveLedger()
    _accept_with_files(ledger, [
        {"fileId": _F1, "fileName": "kwra.tif", "kind": "본체", "byteSize": 1},
        {"fileId": _G1, "fileName": "lat.npy", "kind": "기준 격자 파일", "byteSize": 1},
        {"fileId": _G2, "fileName": "lon.npy", "kind": "기준 격자 파일", "byteSize": 1},
    ])
    drive_uploads(ledger, upload_dir=root, workdir=tmp_path / "work")
    assert set(ledger.axes) == {_G1, _G2}, "격자가 목록에서 빠져 축 판별이 안 돌았다."
