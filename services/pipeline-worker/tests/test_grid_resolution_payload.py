"""⟨동결 4회 해제 · `PLAN-SoT §9-〈88〉` 묶음 8⟩ — `upload.ready` 가 격자 판정을 싣는다.

**`〈79〉-⑷` 가 `ready` 의 뜻에 「함께 올라온 격자 파일의 축이 확정되거나 거절됐다」를
넣었는데, 페이로드에 그 사실이 없었다.** 소비자(core-api·FE)는 이벤트만 보고는 알 수 없었고,
그래서 화면은 대신 **viz-render 의 렌더 실패 문장**을 근거로 삼았다 — 판정자와 화면이
인용하는 근거가 **다른 기계**였다(스윕 `G`·`B-2`).

⚠ **`〈80〉-㉯ 8` 이 이벤트 계약을 연 유일한 회차였다.** 여기서 안 실으면 다음 해제까지 못 싣는다.
"""
from __future__ import annotations

import numpy as np
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


def _run(tmp_path, files):
    ledger = MemoryLedger()
    ledger.accept(upload_id=_UPL, lab_id=_LAB, actor_account_id=_ACC)
    svc = IngestionService(ledger)
    res = svc.process_upload(UploadWork(
        upload_id=_UPL, lab_id=_LAB, actor_account_id=_ACC, workdir=tmp_path / "work",
        files=files), stage1=True)
    ready = next(e for e in res.events if e["type"] == "upload.ready")
    return ledger, res, ready["payload"]


def _body(tmp_path):
    src = make_readable_geotiff(tmp_path / "kwra_output.tif")
    return UploadFileWork(file_id=_F1, path=src, kind="본체", file_name=src.name)


def test_격자가_없으면_빈_배열이다(tmp_path):
    """`null` 로 「모른다」를 말하지 않는다 — 그 뜻은 `ready: false` 가 이미 말한다."""
    _l, _r, payload = _run(tmp_path, [_body(tmp_path)])
    assert payload["gridResolution"] == []


def test_축이_확정되면_그_배정이_실린다(tmp_path):
    """`gridAxis` 는 등록 뒤의 `DatasetFile.gridAxis` 와 **같은 모양**이다."""
    lat, lon = tmp_path / "lat.npy", tmp_path / "lon.npy"
    np.save(lat, np.linspace(33.0, 39.0, 16).reshape(4, 4))
    np.save(lon, np.linspace(124.0, 132.0, 16).reshape(4, 4))
    _l, _r, payload = _run(tmp_path, [
        _body(tmp_path),
        UploadFileWork(file_id=_G1, path=lat, kind="기준 격자 파일", file_name="lat.npy",
                       storage_key="k/lat"),
        UploadFileWork(file_id=_G2, path=lon, kind="기준 격자 파일", file_name="lon.npy",
                       storage_key="k/lon"),
    ])
    by_id = {r["fileId"]: r for r in payload["gridResolution"]}
    assert set(by_id) == {_G1, _G2}
    assert by_id[_G1]["gridAxis"] == {"carriesLat": True, "carriesLon": False}
    assert by_id[_G2]["gridAxis"] == {"carriesLat": False, "carriesLon": True}
    assert by_id[_G1]["fileName"] == "lat.npy"
    # 확정된 파일에는 거절 사유가 없다 — 파일당 정확히 한쪽이다 (`oneOf`)
    assert "rejectionReason" not in by_id[_G1]


def test_거절되면_사유가_계약의_enum_으로_실린다(tmp_path):
    """**여기가 `B-2` 의 조용한 사라짐이 닫히는 자리다.**

    축을 못 정한 격자는 원장에 행을 만들지 않으므로(`0004` CHECK · `〈63〉-ⓒ`) 접수 201 에
    있던 파일이 조회 200 에서 **사라진다.** 사라진 이유를 말하는 것이 이 배열이다.
    """
    a, b = tmp_path / "lat.npy", tmp_path / "lon.npy"
    # 둘 다 ±90 안이고 통계가 같아 값으로도 안 갈린다 — 지어내지 않고 거절한다
    np.save(a, np.full((4, 4), 30.0))
    np.save(b, np.full((4, 4), 30.0))
    _l, _r, payload = _run(tmp_path, [
        _body(tmp_path),
        UploadFileWork(file_id=_G1, path=a, kind="기준 격자 파일", file_name="lat.npy",
                       storage_key="k/lat"),
        UploadFileWork(file_id=_G2, path=b, kind="기준 격자 파일", file_name="lon.npy",
                       storage_key="k/lon"),
    ])
    by_id = {r["fileId"]: r for r in payload["gridResolution"]}
    assert set(by_id) == {_G1, _G2}
    for row in by_id.values():
        assert row["rejectionReason"] == "축 판별 실패"
        assert "gridAxis" not in row


def test_짝이_없으면_짝_불일치다(tmp_path):
    """격자 한 장만 올라왔고 그것만으로는 축을 못 정한다 — 짝이 없다(`§E.2-⑧`)."""
    a = tmp_path / "grid.npy"
    np.save(a, np.full((4, 4), 30.0))
    _l, _r, payload = _run(tmp_path, [
        _body(tmp_path),
        UploadFileWork(file_id=_G1, path=a, kind="기준 격자 파일", file_name="grid.npy",
                       storage_key="k/g"),
    ])
    rows = payload["gridResolution"]
    assert len(rows) == 1
    assert rows[0]["rejectionReason"] == "짝 불일치"


def test_사유는_계약의_세_값_밖으로_나가지_않는다(tmp_path):
    """워커와 viz-render 가 **같은 값 집합**을 쓴다 — 표면마다 다른 어휘를 만들지 않는다."""
    from colab_pipeline.d5.axis import GRID_REJECTION_REASONS

    assert GRID_REJECTION_REASONS == ("형상 불일치", "짝 불일치", "축 판별 실패")
