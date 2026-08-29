"""워커가 **접수한 바이트를 실제로 여는가** — 배치를 단언하는 시험.

`drive_uploads` 는 운영에서 저장 경로를 만드는 유일한 함수인데, 이 함수를 보던 시험들은
**배치를 자기 손으로 다시 타이핑했다**(`test_stage1_worker.py` 의 `root/"uploads"/…`).
같은 규칙을 시험이 한 번 더 적으면 그 시험은 배치를 검증하는 것이 아니라 **자기가 적은
배치를 확인**할 뿐이다 — `03-HANDOFF §4 #26` 이 적은 그 무늬다. 그래서 코드가 배치를
바꾸면 시험도 같이 바뀌어 red 가 나지 않는다. 여기서는 배치를 **규약 함수에게만** 묻는다.
워커가 파일을 못 여는 실패는 에러가 아니라 **「형식 인식 실패」·「축 미상」으로 위장**한다.

바이트는 `kernel/storage_layout.py`(정본 `contracts/storage/layout.json`)가 가리키는
자리에만 놓는다 — core-api 가 쓰는 것과 **같은 함수**다.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from colab_pipeline.app.worker import drive_uploads
from colab_pipeline.kernel import storage_layout
from fixture_builders import make_readable_geotiff
from memory_ledger import MemoryLedger

_LAB = "01JQ0000000000000000000001"
_ACC = "01JQ0000000000000000000002"
_UPL = "01JQ0000000000000000000003"
_BODY = "01JQ00000000000000000000B1"
_GRID = "01JQ00000000000000000000G1"


class _Ledger(MemoryLedger):
    """`drive_uploads` 가 부르는 두 조회를 더한다 — 실물은 `SqlLedger` 다.

    ⚠ `accepted_files` 는 **접수 이벤트**에서 읽는다(`d5_upload_file` 이 아니다) —
    접수는 격자 행을 안 만들기 때문이다(`〈79〉-㈎ⓑ`). 대역도 같은 자리에서 읽는다.
    """

    def pending_uploads(self, limit: int = 20) -> list[dict]:
        return [row for row in self.uploads.values() if not row["ready"]][:limit]

    def accepted_files(self, upload_id: str) -> list[dict]:
        for e in self.events:
            if e["type"] == "upload.accepted" and e["uploadId"] == upload_id:
                return list(e["payload"]["files"])
        return []


def _accepted(tmp_path: Path, *, grid_name: str | None) -> tuple[_Ledger, Path]:
    root = tmp_path / "storage"
    ledger = _Ledger()
    ledger.accept(upload_id=_UPL, lab_id=_LAB, actor_account_id=_ACC)

    files = []
    body_src = make_readable_geotiff(tmp_path / "kwra_output.tif")
    body = storage_layout.storage_path(root, _UPL, file_id=_BODY,
                                       kind=storage_layout.BODY_KIND,
                                       file_name=body_src.name)
    body.parent.mkdir(parents=True, exist_ok=True)
    body.write_bytes(body_src.read_bytes())
    files.append({"fileId": _BODY, "fileName": body_src.name, "kind": "본체"})

    if grid_name is not None:
        grid = storage_layout.storage_path(root, _UPL, file_id=_GRID,
                                           kind=storage_layout.GRID_KIND,
                                           file_name=grid_name)
        grid.parent.mkdir(parents=True, exist_ok=True)
        np.save(grid, np.repeat(np.linspace(118.8, 133.5, 8)[None, :], 8, axis=0))
        files.append({"fileId": _GRID, "fileName": grid_name, "kind": "기준 격자 파일"})

    ledger.events[-1]["payload"]["files"] = files
    return ledger, root


def test_워커가_본체를_배치대로_찾아_감지한다(tmp_path: Path) -> None:
    ledger, root = _accepted(tmp_path, grid_name=None)
    assert drive_uploads(ledger, upload_dir=root, workdir=tmp_path / "work") == [_UPL]
    assert ledger.uploads[_UPL]["ready"] is True
    assert ledger.formats[_BODY] == "GeoTIFF"


def test_워커가_격자를_원래_이름으로_열어_축을_확정한다(tmp_path: Path) -> None:
    """**이 시험이 실패하면 격자는 어디에도 도달하지 않는다.**

    축 판별은 `.npy` 를 확장자로 가르고 짝짓기는 파일명을 읽는다 — 배치가 이름을
    잃으면 실패는 에러가 아니라 **「축 미상」** 으로 조용히 나온다.
    """
    ledger, root = _accepted(tmp_path, grid_name="Lon_HSR.npy")
    assert drive_uploads(ledger, upload_dir=root, workdir=tmp_path / "work") == [_UPL]

    row = ledger.file_rows[_GRID]
    assert row["kind"] == "기준 격자 파일"
    assert (row["carries_lat"], row["carries_lon"]) == (False, True)
    # 원장이 적는 저장 키도 **같은 규약**이다 — 사람이 다시 계산하지 않는다.
    assert row["storage_key"] == storage_layout.storage_key(
        _UPL, file_id=_GRID, kind=storage_layout.GRID_KIND, file_name="Lon_HSR.npy")


def test_바이트가_없으면_조용히_넘어가지_않는다(tmp_path: Path) -> None:
    """음성 — 파일이 사라진 업로드를 `ready` 로 넘기면 그 실패는 영영 안 보인다."""
    ledger, root = _accepted(tmp_path, grid_name=None)
    storage_layout.storage_path(root, _UPL, file_id=_BODY,
                                kind=storage_layout.BODY_KIND).unlink()
    drive_uploads(ledger, upload_dir=root, workdir=tmp_path / "work")
    assert ledger.uploads[_UPL]["ready"] is not True


# ── 미리보기 산출물의 자리 ──────────────────────────────────────────────────
# **세 단위가 같은 답을 내야 한다** — 아래 기대값은 세 시험 파일에 **같은 문자열**로
# 박혀 있고(core-api·pipeline-worker·viz-render), 하나라도 갈리면 그 단위가 틀린 것이다.
# 자리가 없으면 이미 구운 그림을 못 찾아 매번 다시 굽는다 — 그래서 자리를 규약에 둔다.

_PREVIEW_CONTENT_KEY = "0123456789abcdef" * 4      # sha256 자리끼움 (64자)
_PREVIEW_EXPECTED = _PREVIEW_CONTENT_KEY + ".png"  # 세 단위 공통 오라클


def test_preview_key_is_content_addressed_and_stable():
    """ⓐ **같은 입력이면 같은 키** — 재사용이 성립하는 근거다."""
    first = storage_layout.preview_key(_PREVIEW_CONTENT_KEY, ".png")
    second = storage_layout.preview_key(_PREVIEW_CONTENT_KEY, ".png")
    assert first == second == _PREVIEW_EXPECTED
    assert storage_layout.preview_key(_PREVIEW_CONTENT_KEY, ".webp").endswith(".webp")
    assert storage_layout.KEY_TEMPLATES[storage_layout.PREVIEW_KIND] == "{contentKey}{extension}"


def test_preview_root_is_not_the_uploads_root():
    """ⓑⓒ **원본과 갈린다** — 루트가 다르고, 그 루트가 실물 볼륨 둘과 어긋나지 않는다."""
    assert storage_layout.ROOTS[storage_layout.PREVIEW_KIND] == storage_layout.PREVIEW_ROOT
    assert storage_layout.ROOTS[storage_layout.BODY_KIND] == storage_layout.UPLOAD_ROOT
    assert storage_layout.ROOTS[storage_layout.GRID_KIND] == storage_layout.UPLOAD_ROOT
    assert storage_layout.PREVIEW_ROOT != storage_layout.UPLOAD_ROOT
    # 접수분 루트 아래로 새어 들어가지 않는다 — 백업·복원·삭제가 둘을 갈라야 한다.
    assert storage_layout.UPLOADS_PREFIX not in _PREVIEW_EXPECTED


def test_storage_key_refuses_preview_kind(tmp_path):
    """산출물을 접수분 배치 함수로 부르면 **거절**한다 — 조용히 섞이지 않는다."""
    import pytest as _pytest

    with _pytest.raises(ValueError):
        storage_layout.storage_key("T1", file_id="F1",
                                   kind=storage_layout.PREVIEW_KIND)
    body = storage_layout.storage_key("T1", file_id="F1",
                                      kind=storage_layout.BODY_KIND)
    assert body != _PREVIEW_EXPECTED
    got = storage_layout.preview_path(tmp_path, _PREVIEW_CONTENT_KEY, ".png")
    assert got == tmp_path / _PREVIEW_EXPECTED
