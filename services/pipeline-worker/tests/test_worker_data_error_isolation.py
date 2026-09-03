"""**데이터 오류는 배관 고장이 아니다** — 한 업로드의 실패가 틱을 죽이지 않는다
(코드리뷰 20260903 #4).

`drive_uploads` 의 산문이 이미 계약을 적어 뒀다 — 「`process_upload` 는 실패를 예외가
아니라 `upload.failed` 로 표현하고, 예외가 나는 것은 **배관이 깨진 경우뿐**이다」.
그런데 D5 모듈이 던지는 데이터 오류(축·격자·HSR·파싱·값)에 보호가 없어 그 예외가
`_lab_pass` 의 `except BaseException: session.rollback(); raise` 로 올라갔고, 결과는
셋이었다 —

  ⓐ **같은 틱의 다른 업로드·릴레이·reaper 까지 통째로 롤백**
  ⓑ `serve()` 무보호 → **프로세스 종료**
  ⓒ 롤백으로 `ready=false` 가 남아 `pending_uploads`(ORDER BY created_at)가
     **같은 건을 다시 먼저 집는다** → 재기동마다 같은 자리에서 죽는 크래시 루프

여기서 못 박는 것 — 데이터 오류는 `upload.failed` 로 **원장에 적히고 같은 틱에 발행되며**,
그 업로드는 다시 집히지 않고, 나머지 업로드는 계속 처리된다. **배관 고장은 여전히 던진다.**
"""
from __future__ import annotations

import numpy as np
import pytest
from colab_pipeline.app.worker import drive_uploads
from colab_pipeline.d5.axis import AxisUndeterminedError
from colab_pipeline.d5.grid import GridUnavailableError
from colab_pipeline.domains.d5_ingestion import IngestionService, relay_unpublished
from colab_pipeline.kernel import storage_layout
from fixture_builders import make_readable_geotiff
from memory_ledger import MemoryLedger

_LAB = "01JQ0000000000000000000001"
_ACC = "01JQ0000000000000000000002"
_BAD = "01JQ000000000000000000BAD1"
_OK = "01JQ0000000000000000000OK1"
_F1 = "01JQ00000000000000000000F1"
_F2 = "01JQ00000000000000000000F2"
_G1 = "01JQ00000000000000000000G1"


class _DriveLedger(MemoryLedger):
    """`pending_uploads` · `accepted_files` 를 더한 대역 — 실물은 `SqlLedger` 다.

    **실물보다 헐거우면 시험이 거짓말을 한다** — `failed_at` 조건을 그대로 지킨다.
    """

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


def _accept(ledger, upload_id, refs):
    ledger.accept(upload_id=upload_id, lab_id=_LAB, actor_account_id=_ACC)
    for e in ledger.events:
        if e["type"] == "upload.accepted" and e["uploadId"] == upload_id:
            e["payload"]["files"] = refs


def _body(root, upload_id, file_id):
    storage_layout.target_dir(root, upload_id).mkdir(parents=True, exist_ok=True)
    make_readable_geotiff(storage_layout.target_dir(root, upload_id) / file_id)


class _RaisingService(IngestionService):
    """지정한 업로드에서만 **D5 데이터 오류**를 던진다. 나머지는 실물 그대로 돈다."""

    def __init__(self, ledger, *, blow_up_on: str, exc: BaseException) -> None:
        super().__init__(ledger)
        self._blow_up_on = blow_up_on
        self._exc = exc

    def process_upload(self, work, *, stage1: bool = False):
        if work.upload_id == self._blow_up_on:
            raise self._exc
        return super().process_upload(work, stage1=stage1)


def _two_uploads(tmp_path):
    root = tmp_path / "store"
    ledger = _DriveLedger()
    _accept(ledger, _BAD, [{"fileId": _F1, "fileName": "a.tif", "kind": "본체", "byteSize": 1}])
    _accept(ledger, _OK, [{"fileId": _F2, "fileName": "b.tif", "kind": "본체", "byteSize": 1}])
    _body(root, _BAD, _F1)
    _body(root, _OK, _F2)
    return root, ledger


def test_데이터_오류는_upload_failed_로_적히고_틱은_계속_돈다(tmp_path):
    root, ledger = _two_uploads(tmp_path)
    svc = _RaisingService(ledger, blow_up_on=_BAD,
                          exc=AxisUndeterminedError("2차원이 아니다: shape=(2881,)"))

    done = drive_uploads(ledger, upload_dir=root, workdir=tmp_path / "w", service=svc)

    assert _OK in done, "한 건의 데이터 오류가 같은 틱의 다른 업로드를 멈췄다"
    assert ledger.uploads[_OK]["ready"] is True
    row = ledger.uploads[_BAD]
    assert row["failed_at"] is not None and row["ready"] is False
    assert row["failure_reason"] == "내부 오류" and row["failure_class"] == "영구"
    assert any(e["type"] == "upload.failed" and e["uploadId"] == _BAD
               for e in ledger.events), "`upload.failed` 가 원장에 없다"


def test_실패한_업로드를_다음_바퀴가_다시_집지_않는다(tmp_path):
    """크래시 루프의 정체가 이것이다 — 롤백으로 `ready=false` 가 남아 같은 건이 다시 먼저 온다."""
    root, ledger = _two_uploads(tmp_path)
    svc = _RaisingService(ledger, blow_up_on=_BAD,
                          exc=GridUnavailableError("기준 격자를 못 세운다"))

    drive_uploads(ledger, upload_dir=root, workdir=tmp_path / "w", service=svc)
    again = drive_uploads(ledger, upload_dir=root, workdir=tmp_path / "w", service=svc)

    assert again == [], f"같은 업로드를 다시 집었다: {again}"


def test_실패_이벤트가_같은_바퀴에_발행된다(tmp_path):
    """`_lab_pass` 는 처리 → 릴레이 → reaper 를 **한 트랜잭션**으로 돈다.
    실패를 원장에 적기만 하고 발행하지 않으면 소비자는 그 사실을 영영 못 본다."""
    root, ledger = _two_uploads(tmp_path)
    svc = _RaisingService(ledger, blow_up_on=_BAD, exc=AxisUndeterminedError("깨진 격자"))
    sent: list[dict] = []

    drive_uploads(ledger, upload_dir=root, workdir=tmp_path / "w", service=svc)
    relay_unpublished(ledger, publish=sent.append)

    failed = [e for e in sent if e["type"] == "upload.failed" and e["uploadId"] == _BAD]
    assert len(failed) == 1, f"발행된 실패 봉투가 {len(failed)}건이다"
    assert failed[0]["payload"]["failure"]["willRetry"] is False


def test_배관_고장은_여전히_던진다(tmp_path):
    """DB·IO 는 데이터가 아니다 — 삼켜서 「처리했다」로 세면 유실이 조용해진다."""
    root, ledger = _two_uploads(tmp_path)
    svc = _RaisingService(ledger, blow_up_on=_BAD, exc=OSError("원장에 닿지 못했다"))
    with pytest.raises(OSError):
        drive_uploads(ledger, upload_dir=root, workdir=tmp_path / "w", service=svc)


def test_1차원_격자_업로드가_틱을_죽이지_않는다(tmp_path):
    """리뷰가 든 실물 무늬 — shape `(2881,)` 인 `Lat_*.npy` 가 함께 올라온다.

    ⚠ **결과는 `upload.failed` 가 아니라 「그 격자만 거절」이다**(`〈63〉-ⓒ`) —
    `axis.py` 가 이 형상을 `AxisUndeterminedError` 로 돌려주게 고쳐졌기 때문이다.
    업로드는 `ready` 로 서고 거절 사유가 `gridResolution` 에 실린다. 여기서 지키는 것은
    **예외가 워커까지 올라오지 않는다**는 사실이다.
    """
    root = tmp_path / "store"
    ledger = _DriveLedger()
    _accept(ledger, _OK, [
        {"fileId": _F2, "fileName": "b.tif", "kind": "본체", "byteSize": 1},
        {"fileId": _G1, "fileName": "Lat_1d.npy", "kind": "기준 격자 파일", "byteSize": 1},
    ])
    _body(root, _OK, _F2)
    storage_layout.grid_dir(root, _OK).mkdir(parents=True, exist_ok=True)
    np.save(storage_layout.grid_dir(root, _OK) / "Lat_1d.npy", np.linspace(33.0, 39.0, 2881))

    done = drive_uploads(ledger, upload_dir=root, workdir=tmp_path / "w")

    assert done == [_OK]
    ready = next(e for e in ledger.events if e["type"] == "upload.ready")
    rows = ready["payload"]["gridResolution"]
    # ⭑ **사유는 「축 판별 실패」다** (코드리뷰 20260903-F #2) — 짝이 어긋난 것이 아니라
    #   그 파일 하나로 축을 못 정한 것이다. 형상조차 못 읽어 짝짓기 후보에도 못 든다.
    assert [r.get("rejectionReason") for r in rows] == ["축 판별 실패"], rows
    assert ledger.axes == {}, "축이 빈 격자 행이 섰다"
def test_맨_ValueError_는_데이터가_아니라_배관이라_그대로_올라온다(tmp_path):
    """**형이 없는 예외를 데이터 오류로 세지 않는다** (코드리뷰 20260903-F #1).

    `DATA_ERRORS` 에 맨 `ValueError`·`IndexError` 가 들어 있으면 **프로그래밍·설정 결함**이
    데이터 오류로 위장한다 — 원장 불변식(`축이 빈 기준 격자 파일 행을 만들지 않는다` ·
    `업로드 상태에 없는 열`)과 `storage_layout` 의 설정 오류가 전부 `ValueError` 다.
    그것이 삼켜지면 업로드마다 **영구 실패 `내부 오류`** 가 적히고 사람에게 남는 것은
    `print` 한 줄뿐이라, 고칠 수 있는 결함이 「그 파일이 이상했다」로 굳는다.

    여기서 못 박는 것 — 형이 없는 예외는 **올라간다.** 배관은 배관으로 터진다.
    """
    root, ledger = _two_uploads(tmp_path)
    svc = _RaisingService(ledger, blow_up_on=_BAD,
                          exc=ValueError("축이 빈 기준 격자 파일 행을 만들지 않는다 (〈66〉)"))
    with pytest.raises(ValueError):
        drive_uploads(ledger, upload_dir=root, workdir=tmp_path / "w", service=svc)
    assert ledger.uploads[_BAD]["failed_at"] is None, \
        "배관 결함을 `upload.failed` 로 적어 「그 파일이 이상했다」로 굳혔다"


def test_맨_IndexError_도_그대로_올라온다(tmp_path):
    """같은 갈래 — `IndexError` 는 대개 인덱싱 결함이지 파일 내용이 아니다."""
    root, ledger = _two_uploads(tmp_path)
    svc = _RaisingService(ledger, blow_up_on=_BAD, exc=IndexError("list index out of range"))
    with pytest.raises(IndexError):
        drive_uploads(ledger, upload_dir=root, workdir=tmp_path / "w", service=svc)


def test_numpy_전용_예외는_데이터_오류로_잡힌다(tmp_path):
    """좁히되 **줄이지 않는다** — numpy 가 형상·값에 내는 제 이름의 예외는 여전히 데이터다.

    `np.exceptions.AxisError` 는 `ValueError`·`IndexError` 의 자식이지만 **numpy 전용 형**이라
    프로그래밍 결함과 갈린다. 맨 두 형을 뺀 것이 이 갈래까지 뺀 것이 아님을 여기서 고정한다.
    """
    root, ledger = _two_uploads(tmp_path)
    svc = _RaisingService(ledger, blow_up_on=_BAD,
                          exc=np.exceptions.AxisError("axis 2 is out of bounds"))

    done = drive_uploads(ledger, upload_dir=root, workdir=tmp_path / "w", service=svc)

    assert _OK in done
    assert ledger.uploads[_BAD]["failed_at"] is not None
