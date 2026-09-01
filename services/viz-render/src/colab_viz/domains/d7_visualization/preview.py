"""미리보기 3층 — ①썸네일 128 px · ②비지도형 1024 px · ③지도형 1024 px + bbox + `.pgw`.

정본은 `PREVIEW-IMPLEMENTATION.md` 이고 값의 출처는 `DATA-PIPELINE-MEASUREMENT.md` 다.
**③은 ②의 대체재가 아니라 추가물이다** — 격자가 없어 ③을 못 만들어도 ①②는 만든다(`§5.5`).

| 층 | 긴 변 | 다운샘플 | 포맷 | 좌표계 | 동반 파일 |
|---|---:|---|---|---|---|
| ① 썸네일 | 128 | stride | WEBP q80 | 없음(원본 배열 방향 그대로) | 없음 |
| ② 비지도형 | 1024 | 블록평균 | PNG RGBA | 없음 | 없음 |
| ③ 지도형 | 1024 | warp 후 격자 평균 | PNG RGBA | **EPSG:3857** | `.json` 사이드카 + `.pgw` |

**결측은 알파 0.** **좌표를 지어내지 않는다** — 못 읽으면 `[미상]` 이고 지도형은 **보류**다
(`§9`·`DR-9`).

⚠ **위경도 배열은 여기서 소멸한다.** 곡선 격자는 warp 시점에만 쓰이고 밖으로 나가는 것은
**bbox 네 숫자(약 400 B)** 다 — 격자 2장이면 53 MB, **13만 배**다(`§10-3`).
"""
from __future__ import annotations

import io
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from PIL import Image

from ...kernel import storage_layout
from . import cache, colormap, downsample
from .scale import ColorRange

#: 긴 변 (`§2` 결론 표). **썸네일만 stride 다**(`§10-6`).
THUMBNAIL_SIDE = 128
DETAIL_SIDE = 1024

LAYER_THUMBNAIL = "썸네일"
LAYER_DETAIL = "비지도형"
LAYER_MAP = "지도형"

#: 계약 `common.json#/$defs/GridPrecisionBadge` 의 세 값. **여기서 새로 만들지 않는다.**
BADGE_ATTACHED_GRID = "동봉 격자 적용"
BADGE_COMPUTED_GRID = "투영 계산 격자"
BADGE_NO_GRID = "격자 없음 — 지도형 보류"

#: WEBP 품질 (`§3.1` — WEBP q80 이 PNG 의 26~50 %).
WEBP_QUALITY = 80


class BboxSanityError(Exception):
    """warp 결과가 상식 밖이다 — **지도형만 실패하고 비지도형은 유지한다**(`§9` warp 행)."""


@dataclass(frozen=True)
class MapGeometry:
    """③ 한 장의 기하. **`bbox_3857` 은 이미지 바깥 모서리**이고 `.pgw` 5·6행은 픽셀 중심이다."""
    bbox_3857: tuple[float, float, float, float]
    bbox_4326: tuple[float, float, float, float]
    width: int
    height: int
    pixel_size_m: tuple[float, float]

    def bounds_dict(self) -> dict:
        """계약 `Bounds` — 사이드카 `bbox_4326` 과 **같은 값·같은 순서**다(`§3.3`)."""
        w, s, e, n = self.bbox_4326
        return {"west": w, "south": s, "east": e, "north": n}


@dataclass(frozen=True)
class Artifact:
    layer: str
    kind: str                # image | sidecar | worldfile
    path: Path
    url: str
    cache_key: str
    size_bytes: int


# ── 좌표 변환 ────────────────────────────────────────────────────────────────
def _transform(src_crs: str, dst_crs: str, xs, ys):
    """rasterio 의 변환기를 쓴다 — **`pyproj` 를 새로 끌어오지 않는다**(`requirements.in`)."""
    from rasterio.warp import transform as _t
    out_x, out_y = _t(src_crs, dst_crs, list(np.asarray(xs).ravel()),
                      list(np.asarray(ys).ravel()))
    return np.asarray(out_x), np.asarray(out_y)


def check_bbox_4326(bbox: tuple[float, float, float, float],
                    expect: tuple[float, float, float, float] | None = None) -> None:
    """경계 위생 검사 (`§9`). **1차 시도에서 HSR 이 위도 26° 로 밀렸다** — 사람이 보기 전에 막는다."""
    w, s, e, n = bbox
    if not all(np.isfinite([w, s, e, n])):
        raise BboxSanityError("경계에 유한하지 않은 값이 있다")
    if not (-180.0 <= w < e <= 180.0 and -90.0 <= s < n <= 90.0):
        raise BboxSanityError(f"경계가 지구 밖이다: {bbox}")
    if expect is not None:
        ew, es, ee, en = expect
        if w > ee or e < ew or s > en or n < es:
            raise BboxSanityError(
                f"경계가 원본 좌표 범위와 겹치지 않는다: 결과 {bbox} vs 원본 {expect}")


def warp_to_3857(values: np.ndarray, lat: np.ndarray, lon: np.ndarray, *,
                 max_side: int = DETAIL_SIDE) -> tuple[np.ndarray, MapGeometry]:
    """곡선 격자 + 값 → EPSG:3857 규칙 격자. **격자 평균**으로 리샘플한다.

    최근접이 아니라 평균인 이유는 상세에 stride 를 쓰지 않는 이유와 같다 — 한 출력
    픽셀에 여러 입력이 떨어지면 **그 전부를 센다.** 값이 없는 출력 픽셀은 결측이다.
    """
    v = np.asarray(values, dtype="f4")
    la = np.asarray(lat, dtype="f8")
    lo = np.asarray(lon, dtype="f8")
    if v.shape != la.shape or la.shape != lo.shape:
        raise BboxSanityError(f"값과 좌표의 형상이 다르다: {v.shape} / {la.shape} / {lo.shape}")

    ok = np.isfinite(v) & np.isfinite(la) & np.isfinite(lo)
    if not ok.any():
        raise BboxSanityError("좌표와 값이 함께 유효한 자리가 없다")
    # 위생 검사를 **warp 전에도** 한 번 — 축이 뒤바뀐 격자는 여기서 걸린다
    src_bbox = (float(lo[ok].min()), float(la[ok].min()),
                float(lo[ok].max()), float(la[ok].max()))
    check_bbox_4326(src_bbox)

    xs, ys = _transform("EPSG:4326", "EPSG:3857", lo[ok], la[ok])
    good = np.isfinite(xs) & np.isfinite(ys)
    xs, ys, vals = xs[good], ys[good], v[ok][good]
    if xs.size == 0:
        raise BboxSanityError("3857 로 옮길 수 있는 점이 없다")

    minx, maxx = float(xs.min()), float(xs.max())
    miny, maxy = float(ys.min()), float(ys.max())
    span_x, span_y = max(maxx - minx, 1e-9), max(maxy - miny, 1e-9)
    if span_x >= span_y:
        width = int(max_side)
        height = max(1, int(round(max_side * span_y / span_x)))
    else:
        height = int(max_side)
        width = max(1, int(round(max_side * span_x / span_y)))
    px = span_x / width
    py = span_y / height

    cols = np.clip(((xs - minx) / px).astype("i8"), 0, width - 1)
    rows = np.clip(((maxy - ys) / py).astype("i8"), 0, height - 1)
    flat = rows * width + cols
    sums = np.zeros(width * height, dtype="f8")
    counts = np.zeros(width * height, dtype="i8")
    np.add.at(sums, flat, vals.astype("f8"))
    np.add.at(counts, flat, 1)
    out = np.full(width * height, np.nan, dtype="f4")
    hit = counts > 0
    out[hit] = (sums[hit] / counts[hit]).astype("f4")
    out = out.reshape(height, width)

    corner_x = np.array([minx, maxx, minx, maxx])
    corner_y = np.array([miny, miny, maxy, maxy])
    lons4326, lats4326 = _transform("EPSG:3857", "EPSG:4326", corner_x, corner_y)
    bbox_4326 = (round(float(lons4326.min()), 6), round(float(lats4326.min()), 6),
                 round(float(lons4326.max()), 6), round(float(lats4326.max()), 6))
    check_bbox_4326(bbox_4326, expect=src_bbox)

    geom = MapGeometry(bbox_3857=(minx, miny, maxx, maxy), bbox_4326=bbox_4326,
                       width=width, height=height,
                       pixel_size_m=(round(px, 3), round(py, 3)))
    return out, geom


# ── 동반 파일 ────────────────────────────────────────────────────────────────
#: 사이드카 판 번호. **1 = `source` 가 파일명이던 구판**(2026-09-02 이전 · 실배포에서만
#: 우연히 `fileId` 와 같았다), **2 = 이 판** — `source` 가 `fileId` 이고 소유 대상을 싣는다.
#: ⚠ **읽는 쪽은 구판을 거부하지도 옮겨 적지도 않는다** — 판 번호가 없으면 「구판」으로
#: 보고 소유 판정을 **하지 않는다**(`A-1` 안 ⑷). 필드가 있어야 기계가 그것을 가른다.
SIDECAR_VERSION = 2


@dataclass(frozen=True)
class BakeOwner:
    """**구운 시점의** 소유 대상. `job.spec.target` 이 이미 들고 있는 값이다 — Port 불요.

    ⚠ **등록 전환(`createDataset`) 뒤에는 낡는다.** 그래서 필드 이름이 `baked_for` 다 —
    「지금 소유」가 아니라 「구울 때의 대상」이다. 최신 소유는 원장 대조(`fileId` →
    `d3_file.dataset_id`)가 답하고, 그 대조는 이 파일이 하지 않는다.
    """
    target_id: str
    is_upload: bool

    def as_document(self) -> dict:
        return {"target_id": self.target_id, "is_upload": self.is_upload}


def sidecar_document(*, name: str, layer: str, source: str,
                     sources: tuple[str, ...] | list[str], owner: BakeOwner,
                     geom: MapGeometry | None = None,
                     size: tuple[int, int] | None = None,
                     created: datetime | None = None) -> dict:
    """산출물 한 벌의 동반 JSON. **세 층 전부가 이것을 갖는다**(`A-1` 완료 정의 ⑹).

    ⭑ **⟨개정 2026-09-02 · `A-1` 안 ⑷⟩ `source` 는 `fileId` 다.** 종전 문면은 「파일명」
    이었고(실배포에서만 우연히 `fileId` 와 같았다) 시험 픽스처는 사람 이름을 넣었다.
    이제 규약이다 — `sources` 는 그 렌더에 들어간 **모든** 조각의 `fileId` 다.

    **넣지 않는 것** — 위경도 배열 · 격자 파일 경로 · 스케일 범위·컬러맵(범례가 나른다) ·
    원본 CRS 파라미터 · 절대경로(`CLAUDE.md §3-8`). `name` 은 파일명이다.
    **좌표 칸(`crs`·`bbox_*`·`pixel_size_m`)은 지도형에만 선다** — ①②에는 경계가 없고,
    **없는 경계를 지어내지 않는다**(`DR-9`).
    """
    when = created or datetime.now(timezone.utc)
    doc: dict = {
        "sidecarVersion": SIDECAR_VERSION,
        "name": name,
        "layer": layer,
        "source": source,
        "sources": list(sources),
        "baked_for": owner.as_document(),
    }
    if geom is not None:
        doc.update({
            "crs": cache.MAP_CRS,
            "bbox_3857": [round(v, 3) for v in geom.bbox_3857],
            "bbox_4326": list(geom.bbox_4326),
            "width": geom.width,
            "height": geom.height,
            "pixel_size_m": [geom.pixel_size_m[0], geom.pixel_size_m[1]],
        })
    elif size is not None:
        doc["width"], doc["height"] = int(size[0]), int(size[1])
    doc["created"] = when.isoformat(timespec="seconds").replace("+00:00", "Z")
    return doc


def world_file_text(geom: MapGeometry) -> str:
    """`.pgw` 6줄 (`§3.4`). QGIS·ArcGIS 가 PNG 를 바로 연다.

    ⚠ **5·6행은 좌상단 픽셀 *중심*이고 `bbox_3857` 은 이미지 *바깥 모서리*다.**
    반 픽셀 차이가 **정상**이다 — 같게 만들려고 고치지 마라.
    """
    px, py = geom.pixel_size_m
    minx, _, _, maxy = geom.bbox_3857
    lines = [px, 0.0, 0.0, -py, minx + px / 2.0, maxy - py / 2.0]
    return "".join(f"{v:.10f}\n" for v in lines)


# ── 인코딩 ───────────────────────────────────────────────────────────────────
def encode_png(rgba: np.ndarray) -> bytes:
    buf = io.BytesIO()
    Image.fromarray(rgba, mode="RGBA").save(buf, format="PNG")
    return buf.getvalue()


def encode_webp(rgba: np.ndarray) -> bytes:
    buf = io.BytesIO()
    Image.fromarray(rgba, mode="RGBA").save(buf, format="WEBP", quality=WEBP_QUALITY)
    return buf.getvalue()


# ── 층 만들기 ────────────────────────────────────────────────────────────────
def _write(out_dir: Path, url_base: str, layer: str, kind: str, key: str,
           suffix: str, blob: bytes) -> Artifact:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    # 자리는 **규약이 정한다** — `contracts/storage/layout.json` 의 「미리보기 산출물」.
    # 여기서 이름을 다시 조립하면 그것이 세 번째 규칙이 된다(`03-HANDOFF §4 #20` 의 무늬).
    name = storage_layout.preview_key(key, suffix)
    path = out_dir / name
    path.write_bytes(blob)
    return Artifact(layer=layer, kind=kind, path=path,
                    url=f"{url_base.rstrip('/')}/{name}", cache_key=key,
                    size_bytes=len(blob))


def _sidecar_for(out_dir: Path, url_base: str, layer: str, key: str, image: Artifact,
                 *, source: str, sources, owner: BakeOwner,
                 geom: "MapGeometry | None" = None,
                 size: tuple[int, int] | None = None) -> Artifact:
    """산출물 한 벌의 `.json` 을 **같은 키 아래** 놓는다 — `layout.json` `why ④`."""
    doc = sidecar_document(name=image.path.name, layer=layer, source=source,
                           sources=sources, owner=owner, geom=geom, size=size)
    return _write(out_dir, url_base, layer, "sidecar", key, ".json",
                  json.dumps(doc, ensure_ascii=False, indent=2).encode("utf-8"))


def build_value_layers(values: np.ndarray, *, color_range: ColorRange,
                       lut: np.ndarray, out_dir: Path, url_base: str,
                       key_params: dict, source: str,
                       sources: tuple[str, ...] | list[str],
                       owner: BakeOwner
                       ) -> tuple[Artifact, Artifact, Artifact, Artifact]:
    """①썸네일 · ②비지도형 — **좌표를 쓰지 않는다. 전 포맷에서 성립한다**(`〈74〉-㉮`).

    ②는 원본 배열을 블록평균으로 1024 px 까지 줄인 것이고, ①은 그 결과를 stride 로
    한 번 더 줄인 것이다. ⚠ **사양(`§3.1`)은 ①을 원본에서 stride 로 뽑지만, 이미 만든
    ②에서 뽑으면 읽기를 한 번 아끼면서 누락이 더 적다** — 128 px 는 형상 식별용이라
    둘 다 허용 범위이고, **더 잃는 쪽을 고를 이유가 없다.**
    """
    v = np.asarray(values, dtype="f4")
    detail = downsample.block_average(v, downsample.steps_for(v.shape, DETAIL_SIDE))
    thumb = downsample.stride(detail, downsample.steps_for(detail.shape, THUMBNAIL_SIDE))

    detail_key = cache.render_cache_key(long_side=DETAIL_SIDE, downsample="blockavg",
                                        crs=cache.NO_CRS, color_range=color_range,
                                        **key_params)
    thumb_key = cache.render_cache_key(long_side=THUMBNAIL_SIDE, downsample="stride",
                                       crs=cache.NO_CRS, color_range=color_range,
                                       **key_params)
    rgba_detail = colormap.to_rgba(detail, vmin=color_range.vmin,
                                   vmax=color_range.vmax, lut=lut)
    rgba_thumb = colormap.to_rgba(thumb, vmin=color_range.vmin,
                                  vmax=color_range.vmax, lut=lut)
    thumb_art = _write(out_dir, url_base, LAYER_THUMBNAIL, "image", thumb_key, ".webp",
                       encode_webp(rgba_thumb))
    detail_art = _write(out_dir, url_base, LAYER_DETAIL, "image", detail_key, ".png",
                        encode_png(rgba_detail))
    # ⭑ ⟨2026-09-02 · `A-1` 안 ⑷ · 완료 정의 ⑹⟩ **①②도 사이드카를 갖는다.**
    # 층이 셋인데 동반 파일이 지도형에만 있으면 나머지 두 층의 산출물은 **누가 왜 구웠는지
    # 디스크만 보고는 알 수 없다** — 「판정 불가」의 원인이 그것이었다. 좌표는 싣지 않는다.
    thumb_sidecar = _sidecar_for(out_dir, url_base, LAYER_THUMBNAIL, thumb_key, thumb_art,
                                 source=source, sources=sources, owner=owner,
                                 size=(rgba_thumb.shape[1], rgba_thumb.shape[0]))
    detail_sidecar = _sidecar_for(out_dir, url_base, LAYER_DETAIL, detail_key, detail_art,
                                  source=source, sources=sources, owner=owner,
                                  size=(rgba_detail.shape[1], rgba_detail.shape[0]))
    return thumb_art, detail_art, thumb_sidecar, detail_sidecar


def build_map_layer(values: np.ndarray, lat: np.ndarray, lon: np.ndarray, *,
                    color_range: ColorRange, lut: np.ndarray, out_dir: Path,
                    url_base: str, key_params: dict, grid_digest: str | None,
                    source: str, sources: tuple[str, ...] | list[str],
                    owner: BakeOwner) -> tuple[Artifact, Artifact, Artifact, MapGeometry]:
    """③지도형 — PNG + 사이드카 JSON + `.pgw`. **좌표가 없으면 여기 오지 않는다.**"""
    warped, geom = warp_to_3857(values, lat, lon, max_side=DETAIL_SIDE)
    key = cache.render_cache_key(long_side=DETAIL_SIDE, downsample="warp+blockavg",
                                 crs=cache.MAP_CRS, color_range=color_range,
                                 grid_digest=grid_digest, **key_params)
    rgba = colormap.to_rgba(warped, vmin=color_range.vmin, vmax=color_range.vmax, lut=lut)
    image = _write(out_dir, url_base, LAYER_MAP, "image", key, ".png", encode_png(rgba))
    sidecar = _sidecar_for(out_dir, url_base, LAYER_MAP, key, image, source=source,
                           sources=sources, owner=owner, geom=geom)
    world = _write(out_dir, url_base, LAYER_MAP, "worldfile", key, ".pgw",
                   world_file_text(geom).encode("ascii"))
    return image, sidecar, world, geom
