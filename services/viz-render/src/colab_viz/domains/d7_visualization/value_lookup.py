"""값 조회 — **자리에 구워 둔 COG 에서 창 하나를 읽는다** (`V-2` · `PLAN-SoT §9 〈294〉`).

왜 이 파일이 있는가 (`〈254〉` 확정본 · 정본 `Policy_데이터셋_상세 §8 값 조회`)
  값의 출처는 셋 중 **ⓒ 자리의 COG** 다. 기각된 둘 —
  ⓐ 원본 재조회: `readers.py` 5종이 전부 전량을 열고 즉시 데시메이트한다. 한 점 조회의
    하한이 렌더 1회가 된다.
  ⓑ 렌더 부산물(`raster.Rendered.values`): **블록 평균이라 실측값이 아니다.**
    연구 데이터 플랫폼에서 인용되면 틀린 값이 퍼진다.

**자리를 어떻게 찾나 — 키를 다시 짓는다.**
  지도 타일 키는 **내용 주소**라 대상↔키 표도, 사이드카도 원래 필요 없게 설계돼 있다
  (`contracts/storage/layout.json` `contentKeys.지도 타일.why`). 굽는 쪽(D5)이 쓴 재료
  여섯을 **읽는 쪽이 그대로 다시 모아** 같은 키를 얻는다.

  재료 여섯과 그 출처 —
    · `sourceDigest`     — 본체 바이트의 sha256. **D7 이 그 파일을 이미 연다**(`SourcePort`)
    · `sourceByteSize`   — 같은 파일의 크기
    · `gridDigest`       — `storage_layout.map_tile_grid_digest()` (**생성물** — 굽는 쪽과
                           같은 함수다. 규칙을 두 곳에 적으면 갈라지고, 갈라진 실패는
                           에러가 아니라 「값 없음」으로 위장한다)
    · `conversionKind`   — `storage_layout.MAP_TILE_CONVERSION_KIND`   ⎫ **승격분**(`〈294〉`).
    · `overviewResampling` — `storage_layout.MAP_TILE_OVERVIEW_RESAMPLING` ⎬ 종전에는 D5 안에만
    · `compression`      — `storage_layout.MAP_TILE_COMPRESSION`       ⎭ 있어 읽는 쪽이 못 지었다.

⚠ **`used_reference_grid` 만은 D7 이 D5 의 판정을 그대로 볼 수 없다** — 그것은 D5 의
  파서(`d5/parse.py` `crs_embedded`)가 포맷별로 내리는 판정이고 D7 에 그 사다리가 없다.
  **지어내지 않는다.** 대신 규약 규칙이 낳는 **후보 키 전부**(격자 자리가 있으면 둘,
  없으면 하나)를 짓고 **자리에 실재하는 것**을 고른다. 경로를 지어 뒤지는 것이 아니라
  계약이 낳은 이름만 본다 — 후보가 하나도 안 서 있으면 「자리에 산출물이 없다」다.

⚠ **`ownership.scan()`·`grade()` 는 `tile-` 벌을 보지 않는다** — 이 경로가 붙어도 그
  COG 는 소유·회수 규율 밖에 남는다. 별건이고 대장에 세워 둔다(고치는 자리가 아니다).
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path

from ...kernel import storage_layout
# ⭑ **키 계산의 정본은 판독기 쪽 한 자리다** (`TL-1` 완료 정의 ⑵ · `PLAN-SoT §9 〈302〉`).
#   값 조회와 생존 판독이 **같은 이름**을 지어야 하므로 사본을 들지 않는다 — 사본을 들면
#   그것이 세 번째 규칙이 되고, 갈라진 실패는 에러가 아니라 「값 없음」으로 위장한다.
from .tile_liveness import candidate_tile_keys, file_digest  # noqa: F401  (재수출)

#: 「없다」의 사유 — 계약 `ValueLookupResult.unavailableReason` enum 그대로.
NO_TILE = "자리에 산출물이 없다"
NO_VALUE = "값이 없는 칸이다"
OUT_OF_RANGE = "범위 밖이다"

#: `exactness` — 계약 enum 그대로. 값과 **같은 응답**에 실어 ⑷ 를 지킨다.
SAME_CELL = "원본과 같은 칸"
NEAREST_CELL = "가장 가까운 칸"


@dataclass(frozen=True)
class LookupOutcome:
    available: bool
    value: float | None = None
    unit: str | None = None
    variable: str | None = None
    exactness: str = SAME_CELL
    cell: dict | None = None
    unavailable_reason: str | None = None

    def to_result(self) -> dict:
        """`core-viz.yaml#ValueLookupResult` 그대로. **여기서 모양을 늘리지 않는다.**"""
        return {
            "available": self.available,
            "value": self.value,
            "unit": self.unit,
            "variable": self.variable,
            "exactness": self.exactness,
            "cell": self.cell,
            "unavailableReason": self.unavailable_reason,
        }


def find_tile(previews_root, source: Path, *,
              grid_dir: Path | None) -> tuple[Path, bool] | None:
    """자리에 **실재하는** COG 하나 ＋ 그것이 기준 격자를 쓴 벌인가.

    없으면 `None` — 다른 자리를 뒤지지 않는다. **어느 후보가 맞았는지가 곧 `exactness`
    의 근거다**: 기준 격자로 좌표를 입힌 벌은 최근접 재배치를 지났고(`〈254〉` 실측 ②),
    파일 안 좌표를 쓴 벌은 원본과 비트 동일이다(같은 곳 ①). **추측이 아니라 실물이 답한다.**
    """
    for key, used_reference_grid in candidate_tile_keys(source, grid_dir=grid_dir):
        p = storage_layout.preview_path(previews_root, key, ".tif")
        if p.is_file() and p.stat().st_size > 0:
            return p, used_reference_grid
    return None


def _transform_errors() -> tuple[type[BaseException], ...]:
    """좌표를 **못 옮길 때** 나는 예외들 — 「그 점에 값이 없다」이지 서버 고장이 아니다.

    ⚠ `CPLE_*` 는 `rasterio._err` 에만 있고 **공개 이름이 없다**(`rasterio.errors` 에는
    `RasterioError`·`TransformError` 만 노출된다 · 1.5.1 실측). 없는 판에서는 없는 대로
    두고 지어내지 않는다 — 그때는 `RasterioError` 만으로 잡고, 못 잡은 것은 500 으로
    올라가 눈에 띈다. **조용히 넓히지 않는다.**
    """
    from rasterio.errors import RasterioError

    errs: tuple[type[BaseException], ...] = (RasterioError,)
    try:
        from rasterio._err import CPLE_BaseError
    except ImportError:                        # pragma: no cover — rasterio 판 차이
        return errs
    return errs + (CPLE_BaseError,)


def read_point(tile: Path, *, lat: float, lon: float,
               used_reference_grid: bool = False) -> LookupOutcome:
    """COG 한 장에서 **그 칸 하나**를 읽는다. 창은 1×1 이다 — 블록 평균이 아니다."""
    import rasterio
    from rasterio.warp import transform as warp_transform

    with rasterio.open(tile) as ds:
        # ⭑ ⟨2026-09-03 · 코드리뷰 20260903-F #4⟩ **투영 밖 좌표는 500 이 아니다.**
        #   LCC 처럼 평면 전체를 덮지 않는 투영에서는 정의역 밖 좌표에 proj 가
        #   `CPLE_AppDefinedError: Point outside of projection domain` 을 낸다. 그것이
        #   그대로 올라가 표면이 500 을 냈고 — 화면은 「서버 오류」를 띄우고 그 요청은
        #   장애 계수에 섞였다. **계약이 정한 답은 200 ＋ 「범위 밖이다」**이고
        #   (`core-viz.yaml ValueLookupResult.unavailableReason`), 그것이 바로 아래
        #   격자 밖 분기가 이미 내는 답이다. 같은 사실에 두 답을 두지 않는다.
        try:
            xs, ys = warp_transform("EPSG:4326", ds.crs, [lon], [lat])
            row, col = ds.index(xs[0], ys[0])
        except _transform_errors():
            return LookupOutcome(available=False, unavailable_reason=OUT_OF_RANGE,
                                 exactness=_exactness(used_reference_grid))
        if not (0 <= row < ds.height and 0 <= col < ds.width):
            return LookupOutcome(available=False, unavailable_reason=OUT_OF_RANGE,
                                 exactness=_exactness(used_reference_grid))
        window = rasterio.windows.Window(col, row, 1, 1)
        block = ds.read(1, window=window, masked=True)
        cx, cy = ds.xy(row, col)
        clon, clat = warp_transform(ds.crs, "EPSG:4326", [cx], [cy])
        cell = {
            "row": int(row), "col": int(col),
            "center": {"lat": float(clat[0]), "lon": float(clon[0])},
            "sizeDegrees": _size_degrees(ds),
        }
        unit = (ds.units[0] if ds.units and ds.units[0] else None)
        variable = (ds.descriptions[0] if ds.descriptions and ds.descriptions[0] else None)
        exactness = _exactness(used_reference_grid)
        if block.mask.all():
            # **0 으로 바꾸지 않는다** (완료 정의 ⑸). 빈 칸은 빈 칸이다.
            return LookupOutcome(available=False, unavailable_reason=NO_VALUE,
                                 unit=unit, variable=variable, exactness=exactness, cell=cell)
        return LookupOutcome(available=True, value=float(block.filled(0)[0][0]),
                             unit=unit, variable=variable, exactness=exactness, cell=cell)


def _exactness(used_reference_grid: bool) -> str:
    """⑷ 의 고지 — **약속하지 못하는 것을 값으로 말한다.**

    이미 지도 좌표를 가진 격자는 자리의 산출물이 원본과 비트 동일이라 같은 칸이고
    (`〈254〉` 실측 ①), 좌표를 따로 입힌 격자는 최근접 재배치를 지난다(같은 곳 ②).
    """
    return NEAREST_CELL if used_reference_grid else SAME_CELL


def _size_degrees(ds) -> float | None:
    """칸 한 변의 크기(도). 좌표계가 도가 아니면 **지어내지 않고 `None`** 이다."""
    try:
        if ds.crs is not None and ds.crs.to_epsg() == 4326:
            return abs(float(ds.transform.a))
    except Exception:
        return None
    return None


def lookup_timed(previews_root, source: Path, *, grid_dir: Path | None,
                 lat: float, lon: float) -> tuple[LookupOutcome, dict[str, float]]:
    """`lookup` ＋ **구간 시간(밀리초)**. 답은 한 글자도 달라지지 않는다.

    왜 시간을 함께 내는가 (`VL-1` ⑴ · `PLAN-SoT §9 〈311〉`)
      `〈304〉` 는 공개 엣지 앞 벽시계 하나로만 재서 **서버 단독 시간이 `[미확인]`** 이었다.
      「느리다」는 관측이고 「어디가 느리다」가 원인이다 — 가르는 자리는 여기다.

    구간 둘 —
      · `findTile`  = 본체 sha256(`sourceDigest`) ＋ 격자 다이제스트 ＋ 자리 실재 확인
      · `readPoint` = COG 열기 ＋ 1×1 창 읽기. **자리에 없으면 0 이고 그것이 사실이다.**
    """
    t0 = time.perf_counter()
    found = find_tile(previews_root, source, grid_dir=grid_dir)
    t1 = time.perf_counter()
    if found is None:
        # **자리에 없는 것은 실패가 아니라 사실이다** — 500 도, 경로 추측도 아니다.
        return (LookupOutcome(available=False, unavailable_reason=NO_TILE),
                {"findTile": (t1 - t0) * 1000.0, "readPoint": 0.0})
    tile, used_reference_grid = found
    outcome = read_point(tile, lat=lat, lon=lon, used_reference_grid=used_reference_grid)
    t2 = time.perf_counter()
    return outcome, {"findTile": (t1 - t0) * 1000.0, "readPoint": (t2 - t1) * 1000.0}


def lookup(previews_root, source: Path, *, grid_dir: Path | None,
           lat: float, lon: float) -> LookupOutcome:
    """한 조각 · 한 점. **자리에 산출물이 없으면 「없다」이고 500 이 아니다.**

    ⚠ **계측판과 두 벌로 두지 않는다** — 규칙이 두 곳이면 갈린다(`CLAUDE.md §3` 불변규칙 1).
    """
    outcome, _spans = lookup_timed(previews_root, source, grid_dir=grid_dir, lat=lat, lon=lon)
    return outcome
