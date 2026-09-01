"""미리보기 3층의 산출물 — `PREVIEW-IMPLEMENTATION §2·§3.3·§3.4·§9`.

**③은 ②의 대체재가 아니라 추가물이다** — 좌표가 없어도 ①②는 나온다(`§5.5`).

⚠ 이 파일의 위경도는 **시험이 자기 격자를 명시적으로 정의한 것**이지 좌표를 지어내
읽은 척하는 것이 아니다(`conftest.tiny_geotiff` 와 같은 성격). 실데이터 판정은
`test_e2e_real.py` 가 실물 격자로 따로 한다.
"""
from __future__ import annotations

import json

import numpy as np
import pytest

from colab_viz.domains.d7_visualization import colormap, preview, scale

_LUT = colormap.lut256(colormap.VIRIDIS_ANCHORS)
_KEY_PARAMS = dict(source_digest="deadbeef", fills=(-25000.0, -30000.0),
                   palette="단색-파랑", selection="블록1")
#: ⭑ ⟨2026-09-02 · `A-1` 안 ⑷⟩ `source` 는 **`fileId`** 다 — 종전 픽스처는 사람 이름을
#: 넣었고, 그 자리가 무엇인지 못 박은 규약이 없었다. 소유·`fileId` 판정은
#: `test_sidecar_ownership.py` 가 따로 잰다.
_FID = "01ARZ3NDEKTSV4RRFFQ69G5FAW"
_OWNER = preview.BakeOwner(target_id="01ARZ3NDEKTSV4RRFFQ69G5FAW", is_upload=False)
_SRC = dict(source=_FID, sources=(_FID,), owner=_OWNER)


def _range() -> scale.ColorRange:
    return scale.for_dataset("01ARZ3NDEKTSV4RRFFQ69G5FAW", [np.linspace(0, 100, 100,
                                                                        dtype="f4").reshape(-1, 1)])


def _korea_grid(ny: int = 200, nx: int = 160):
    lat = np.repeat(np.linspace(38.0, 33.0, ny)[:, None], nx, axis=1)
    lon = np.repeat(np.linspace(125.0, 130.0, nx)[None, :], ny, axis=0)
    values = np.linspace(0, 100, ny * nx, dtype="f4").reshape(ny, nx)
    return values, lat, lon


# ── ①② 좌표 없이 나온다 ────────────────────────────────────────────────────
def test_썸네일과_비지도형은_좌표_없이_전_포맷에서_나온다(tmp_path):
    values = np.linspace(0, 100, 2881 * 2305, dtype="f4").reshape(2881, 2305)
    thumb, detail, _, _ = preview.build_value_layers(
        values, color_range=_range(), lut=_LUT, out_dir=tmp_path,
        url_base="/previews", key_params=_KEY_PARAMS, **_SRC)

    assert thumb.path.read_bytes()[:4] == b"RIFF"        # WEBP
    assert detail.path.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
    from PIL import Image
    assert max(Image.open(thumb.path).size) <= preview.THUMBNAIL_SIDE
    assert max(Image.open(detail.path).size) <= preview.DETAIL_SIDE
    assert thumb.url.startswith("/previews/") and thumb.cache_key in thumb.url
    assert thumb.cache_key != detail.cache_key          # 긴 변·다운샘플이 키에 들어간다


def test_결측만_있는_층도_실패가_아니라_전부_투명한_그림이다(tmp_path):
    """`§9` 렌더 행 — 「유효 픽셀 0개」는 실패가 아니다."""
    values = np.full((64, 64), np.nan, dtype="f4")
    thumb, detail, _, _ = preview.build_value_layers(
        values, color_range=_range(), lut=_LUT, out_dir=tmp_path,
        url_base="/previews", key_params=_KEY_PARAMS, **_SRC)
    from PIL import Image
    alpha = np.asarray(Image.open(detail.path).convert("RGBA"))[..., 3]
    assert alpha.max() == 0
    assert thumb.size_bytes > 0


# ── ③ 지도형 ────────────────────────────────────────────────────────────────
def test_지도형은_3857_PNG_와_사이드카_와_pgw_세_벌이다(tmp_path):
    values, lat, lon = _korea_grid()
    image, sidecar, world, geom = preview.build_map_layer(
        values, lat, lon, color_range=_range(), lut=_LUT, out_dir=tmp_path,
        url_base="/previews", key_params=_KEY_PARAMS, grid_digest="격자해시", **_SRC)

    assert image.path.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
    doc = json.loads(sidecar.path.read_text(encoding="utf-8"))
    assert set(doc) == {"sidecarVersion", "name", "layer", "source", "sources",
                        "baked_for", "crs", "bbox_3857", "bbox_4326", "width", "height",
                        "pixel_size_m", "created"}
    assert doc["crs"] == "EPSG:3857"
    assert doc["name"] == image.path.name and "/" not in doc["name"]
    assert doc["source"] == _FID          # 파일명이 아니라 `fileId` 다
    assert max(doc["width"], doc["height"]) == preview.DETAIL_SIDE

    # 사이드카 `bbox_4326` 은 계약 `Bounds` 와 **같은 값·같은 순서**다 (`§3.3`)
    b = geom.bounds_dict()
    assert doc["bbox_4326"] == [b["west"], b["south"], b["east"], b["north"]]
    assert 124.9 < b["west"] < 125.1 and 32.9 < b["south"] < 33.1


def test_pgw_는_6줄이고_5_6행은_픽셀_중심이라_반_픽셀_어긋난다(tmp_path):
    values, lat, lon = _korea_grid()
    _, _, world, geom = preview.build_map_layer(
        values, lat, lon, color_range=_range(), lut=_LUT, out_dir=tmp_path,
        url_base="/previews", key_params=_KEY_PARAMS, grid_digest=None, **_SRC)
    lines = [float(v) for v in world.path.read_text().strip().splitlines()]
    assert len(lines) == 6
    assert lines[1] == 0.0 and lines[2] == 0.0        # warp 후라 회전은 항상 0
    assert lines[3] < 0                                # y 픽셀 크기는 음수다
    # **반 픽셀 차이가 정상이다 — 같게 만들려고 고치지 마라** (`§3.4`)
    assert lines[4] == pytest.approx(geom.bbox_3857[0] + abs(lines[0]) / 2, abs=1e-3)
    assert lines[5] == pytest.approx(geom.bbox_3857[3] - abs(lines[3]) / 2, abs=1e-3)


def test_경계_위생_검사가_위도_26도로_밀린_결과를_막는다(tmp_path):
    """`§9` warp 행 — 1차 시도에서 실제로 일어난 일이다. 사람이 보기 전에 막는다."""
    with pytest.raises(preview.BboxSanityError):
        preview.check_bbox_4326((125.0, 24.0, 130.0, 28.0),
                                expect=(125.0, 33.0, 130.0, 38.0))


def test_축이_뒤바뀐_격자는_지도형을_실패시킨다(tmp_path):
    """위도 자리에 경도가 들어가면 **조용히 빈 지도**가 나온다 — 그 전에 걸린다(`§9`)."""
    values, lat, lon = _korea_grid()
    with pytest.raises(preview.BboxSanityError):
        preview.build_map_layer(values, lon, lat, color_range=_range(), lut=_LUT,
                                out_dir=tmp_path, url_base="/previews",
                                key_params=_KEY_PARAMS, grid_digest=None, **_SRC)


def test_사이드카는_위경도_배열도_격자_경로도_싣지_않는다(tmp_path):
    """`§10-3` — 53 MB 와 400 B 의 차이가 여기서 갈린다."""
    values, lat, lon = _korea_grid()
    _, sidecar, _, _ = preview.build_map_layer(
        values, lat, lon, color_range=_range(), lut=_LUT, out_dir=tmp_path,
        url_base="/previews", key_params=_KEY_PARAMS, grid_digest="격자해시", **_SRC)
    text = sidecar.path.read_text(encoding="utf-8")
    assert sidecar.size_bytes < 1024
    for banned in ("lat2d", "lon2d", ".npy", "palette", "vmin"):
        assert banned not in text
