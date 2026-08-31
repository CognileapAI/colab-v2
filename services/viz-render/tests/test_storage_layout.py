"""**core-api 가 실제로 놓은 자리에서 그린다** — 배치를 단언하는 시험.

`03-HANDOFF §4 #20` 의 실물은 이것이었다: 사람이 올린 격자가 렌더러에 **영영 닿지
않는다.** core-api 는 `uploads/{targetId}/{fileId}` 로 쓰는데 이 단위는 `{root}/{targetId}/`
와 `grid/` 를 봤고, **그 `grid/` 를 만드는 코드가 트리에 하나도 없었다.**
세 규칙 중 어느 것도 틀리지 않았는데 셋이 서로 달랐고, 시험은 전부 green 이었다 —
**저장 배치를 단언하는 시험이 0건이었기 때문이다**(`#26`).

그래서 이 파일은 `conftest.put_target` 같은 자기 편의 픽스처를 쓰지 않고
**생성된 규약 모듈**(`kernel/storage_layout.py`, 정본 `contracts/storage/layout.json`)이
가리키는 자리에 바이트를 놓는다. core-api 도 워커도 같은 함수를 부른다.
"""
from __future__ import annotations

import numpy as np
import pytest
from conftest import AUTH, make_client

from colab_viz.kernel import storage_layout
from colab_viz.kernel.ids import new_ulid

_BODY_NAME = "RDR_CMP_HSR_TEST.bin"


def _hsr_blob(nx: int = 4, ny: int = 3) -> bytes:
    raw = bytearray(1024)
    raw[3:5] = (2025).to_bytes(2, "little", signed=True)
    raw[5], raw[6], raw[7] = 8, 13, 10
    raw[20:22] = nx.to_bytes(2, "little")
    raw[22:24] = ny.to_bytes(2, "little")
    raw[24:26] = (1).to_bytes(2, "little")
    raw[26:28] = (500).to_bytes(2, "little")
    raw[32] = 1
    raw[33] = 1
    return bytes(raw) + (np.arange(nx * ny, dtype="<i2") * 100).tobytes()


def _grid_arrays(nx: int = 4, ny: int = 3):
    lat = np.repeat(np.linspace(38.0, 36.0, ny)[:, None], nx, axis=1).astype("f4")
    lon = np.repeat(np.linspace(126.0, 128.0, nx)[None, :], ny, axis=0).astype("f4")
    return lat, lon


def _as_core_api_would_store(root, *, with_grid: bool) -> tuple[str, str]:
    """core-api 의 `createUpload` 이 **실제로 하는 일**을 규약 함수로 그대로 재현한다."""
    target_id, body_id = new_ulid(), new_ulid()
    body = storage_layout.storage_path(root, target_id, file_id=body_id,
                                       kind=storage_layout.BODY_KIND,
                                       file_name=_BODY_NAME)
    body.parent.mkdir(parents=True, exist_ok=True)
    body.write_bytes(_hsr_blob())
    if with_grid:
        lat, lon = _grid_arrays()
        for name, arr in (("Lat_HSR.npy", lat), ("Lon_HSR.npy", lon)):
            p = storage_layout.storage_path(root, target_id, file_id=new_ulid(),
                                            kind=storage_layout.GRID_KIND, file_name=name)
            p.parent.mkdir(parents=True, exist_ok=True)
            np.save(p, arr)
            # `np.save` 는 확장자가 없으면 붙인다 — 규약이 준 이름이 그대로여야 한다.
            assert p.is_file(), p
    return target_id, body_id


def _render(client, target_id: str) -> dict:
    accepted = client.post("/viz/v1/renders", headers=AUTH, json={
        "target": {"datasetId": target_id}, "style": {"palette": "단색-파랑"}})
    assert accepted.status_code == 202, accepted.text
    return client.get(f"/viz/v1/renders/{accepted.json()['renderId']}",
                      headers=AUTH).json()


def test_core_api_가_놓은_격자로_지도형이_그려진다(source_root):
    """**이 시험 하나가 `#20` 이다.** 격자를 올렸는데 지도형이 안 나오면 red 다."""
    client = make_client(source_root, "inline")
    target_id, _ = _as_core_api_would_store(source_root, with_grid=True)
    job = _render(client, target_id)

    assert job["status"] == "완료", job.get("failure")
    result = job["result"]
    assert result["precisionBadge"] != "격자 없음 — 지도형 보류", \
        "격자를 올렸는데 렌더러가 못 찾았다 — 배치 규약이 갈라졌다"
    assert result["bounds"]["west"] == pytest.approx(126.0, abs=1e-4)
    assert result["bounds"]["north"] == pytest.approx(38.0, abs=1e-4)
    # ⭑ ⟨개정 2026-08-31 · `〈238〉`⟩ 등록된 데이터셋의 주 화면은 타일 갈래다
    assert result["sidecarUrl"] and result["worldFileUrl"] and result["tileUrlTemplate"]


def test_격자를_안_올리면_그대로_보류다(source_root):
    """음성 — 배치를 맞췄다고 「격자 없음」이 사라지면 그건 지어낸 것이다."""
    client = make_client(source_root, "inline")
    target_id, _ = _as_core_api_would_store(source_root, with_grid=False)
    job = _render(client, target_id)

    assert job["status"] == "완료", job.get("failure")
    assert job["result"]["precisionBadge"] == "격자 없음 — 지도형 보류"
    assert "bounds" not in job["result"]


def test_원장이_발급한_fileId_로_조각을_고를_수_있다(source_root):
    """`fileIds` 는 업로드가 발급한 ULID 다 — 배치가 그 id 를 그대로 이름으로 쓴다.

    파일명에서 해시로 만든 id 를 쓰면 이 경로는 **실배포에서만** 404 가 된다.
    """
    client = make_client(source_root, "inline")
    target_id, body_id = _as_core_api_would_store(source_root, with_grid=True)
    accepted = client.post("/viz/v1/renders", headers=AUTH, json={
        "target": {"datasetId": target_id, "fileIds": [body_id]},
        "style": {"palette": "단색-파랑"}})
    assert accepted.status_code == 202, accepted.text


def test_격자가_본체로_오인되지_않는다(source_root):
    """격자는 본체 자리에 서지 않는다 — 종류가 **배치로** 읽혀야 한다."""
    from colab_viz.ports.source import FilesystemSourcePort

    target_id, body_id = _as_core_api_would_store(source_root, with_grid=True)
    resolved = FilesystemSourcePort(source_root).resolve(
        dataset_id=target_id, upload_id=None, file_ids=None)
    # 본체는 **저장 키 그대로**라 디스크상의 이름이 곧 `fileId` 다 — 격자만 이름을 보존한다.
    assert [p.file_id for p in resolved.parts] == [body_id]
    assert resolved.grid_dir is not None and resolved.grid_dir.is_dir()
    assert sorted(p.name for p in resolved.grid_dir.iterdir()) == ["Lat_HSR.npy",
                                                                  "Lon_HSR.npy"]


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
