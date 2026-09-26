"""타일 4종(MGRS 2 · MODIS sinusoidal 2)의 bbox 를 **표준 격자**에서 계산한다 — 2회차 지역(2026-09-26).

Ted 판정 2026-09-26 「자료 지역 확정」 3 축자 — 「㈎ 타일 8건(seq 21~28)은 표준표로 bbox 계산해
정본에 적고 지명은 bbox 규칙 초안」. 이 파일은 그 「표준표로 bbox 계산」의 재현 가능한 기록이다.
제품 코드가 아니다. 결과는 정본(`canonical-metadata.json` 의 `bbox` · DATASETS.md 의 「공간범위」 줄)에
손으로 옮겨 적었고, 이 스크립트는 그 값이 어디서 왔는지를 되짚는 근거다.

방법 (셋 — 첫째가 정본 값이고 나머지 둘은 대조다)
  ① MGRS 손 유도 + pyproj — 100 km 격자 글자에서 UTM 원점(E0, N0)을 규칙으로 유도한다.
     · 열 글자: 구역번호 mod 3 = 1 → A–H · 2 → J–R · 0 → S–Z, E0 = (글자 순번 + 1) × 100 km
     · 행 글자: A–V(I·O 제외 20자), 홀수 구역은 A 가 0 m · 짝수 구역은 F 가 0 m(5칸 밀림),
       N0 = (순번 − 밀림) mod 20 × 100 km + k × 2,000 km — k 는 위도대(S = 32–40°N) 안에 들도록 고른다
     · Sentinel-2/HLS 타일 = 그 칸의 북서 모서리(E0, N0 + 100 km)에서 동·남으로 109.8 km
       (3660 px × 30 m · 동·남 9.8 km 가 이웃 칸과 겹친다)
     · 가장자리를 1 km 간격으로 표본해 UTM(EPSG:326zz) → WGS84 로 옮기고 위경도 최소·최대를 낸다
       (UTM 칸의 가장자리는 위경도에서 곡선이라 네 모서리만으로는 외접 상자가 모자랄 수 있다)
  ② `mgrs` 패키지 — 칸 원점 글자열(예: 51SYB0000000000)을 위경도로 바꿔 ① 의 E0·N0 이 같은 점인지 본다
  ③ 참조자료 격자 파일 실측 — `04.Lat_Lon_info/*lat2d.npy`·`*lon2d.npy` 의 최소·최대(있을 때만)
  MODIS: 정현(sinusoidal) 구 R = 6371007.181 m, 타일 한 변 T = 1111950.5197665233 m,
     x ∈ [−20015109.354 + h·T, +T], y ∈ [10007554.677 − (v+1)·T, +T].
     위도 = y / R, 경도 = x / (R cos 위도) 로 네 변을 표본해 위경도 외접 상자를 낸다.

쓰는 법(저장소 밖 임시 venv — pyproj·mgrs 는 서비스 의존성이 아니다):
  uv venv /tmp/geo-venv --python 3.12 && uv pip install --python /tmp/geo-venv/bin/python pyproj mgrs packaging numpy
  /tmp/geo-venv/bin/python compute_tile_bbox.py [--ref-root <참조자료 뿌리>] > tile-bbox.json
"""
from __future__ import annotations

import argparse
import json
import math
import pathlib

import mgrs
from pyproj import Transformer

ROWS = "ABCDEFGHJKLMNPQRSTUV"          # I·O 제외 20자
COLS = {1: "ABCDEFGH", 2: "JKLMNPQR", 0: "STUVWXYZ"}
BANDS = {"S": (32.0, 40.0)}
S2_TILE_M = 109_800.0
MODIS_R = 6_371_007.181
MODIS_T = 1_111_950.5197665233
MODIS_X0 = -20_015_109.354
MODIS_Y0 = 10_007_554.677
KOREA = {"latMin": 33.0, "latMax": 39.0, "lonMin": 124.0, "lonMax": 132.0}


def mgrs_origin(tile: str) -> dict:
    """`T51SYB` → 구역 51 · 위도대 S · E0 = 700 km · N0 = 4100 km (손 유도)."""
    tile = tile.removeprefix("T")
    zone, band, col, row = int(tile[:2]), tile[2], tile[3], tile[4]
    cols = COLS[zone % 3]
    easting = (cols.index(col) + 1) * 100_000
    shift = 0 if zone % 2 else 5
    base = ((ROWS.index(row) - shift) % 20) * 100_000
    lat_lo, lat_hi = BANDS[band]
    to_utm = Transformer.from_crs("EPSG:4326", f"EPSG:326{zone:02d}", always_xy=True)
    n_lo = to_utm.transform(zone * 6 - 183, lat_lo)[1]
    n_hi = to_utm.transform(zone * 6 - 183, lat_hi)[1]
    candidates = [base + k * 2_000_000 for k in range(5)]
    northing = next(n for n in candidates if n_lo - 100_000 <= n <= n_hi)
    return {"zone": zone, "band": band, "E0": easting, "N0": northing}


def utm_envelope(zone: int, x0: float, y0: float, x1: float, y1: float, step: float = 1000.0) -> dict:
    to_ll = Transformer.from_crs(f"EPSG:326{zone:02d}", "EPSG:4326", always_xy=True)
    pts = []
    n = int(round((x1 - x0) / step))
    m = int(round((y1 - y0) / step))
    for i in range(n + 1):
        x = x0 + (x1 - x0) * i / n
        pts += [to_ll.transform(x, y0), to_ll.transform(x, y1)]
    for j in range(m + 1):
        y = y0 + (y1 - y0) * j / m
        pts += [to_ll.transform(x0, y), to_ll.transform(x1, y)]
    corners = {name: to_ll.transform(x, y) for name, (x, y) in
               {"SW": (x0, y0), "SE": (x1, y0), "NE": (x1, y1), "NW": (x0, y1)}.items()}
    return _box(pts, corners)


def modis_envelope(h: int, v: int, samples: int = 2400) -> dict:
    x0 = MODIS_X0 + h * MODIS_T
    y1 = MODIS_Y0 - v * MODIS_T
    x1, y0 = x0 + MODIS_T, y1 - MODIS_T

    def ll(x, y):
        lat = y / MODIS_R
        return (math.degrees(x / (MODIS_R * math.cos(lat))), math.degrees(lat))

    pts = []
    for i in range(samples + 1):
        t = i / samples
        pts += [ll(x0 + (x1 - x0) * t, y0), ll(x0 + (x1 - x0) * t, y1),
                ll(x0, y0 + (y1 - y0) * t), ll(x1, y0 + (y1 - y0) * t)]
    corners = {"SW": ll(x0, y0), "SE": ll(x1, y0), "NE": ll(x1, y1), "NW": ll(x0, y1)}
    box = _box(pts, corners)
    box["sinusoidal_m"] = {"x0": x0, "x1": x1, "y0": y0, "y1": y1}
    return box


def _box(pts, corners) -> dict:
    lons = [p[0] for p in pts]
    lats = [p[1] for p in pts]
    return {"west": round(min(lons), 4), "south": round(min(lats), 4),
            "east": round(max(lons), 4), "north": round(max(lats), 4),
            "corners": {k: [round(c[0], 4), round(c[1], 4)] for k, c in corners.items()}}


def inside_korea(box: dict) -> bool:
    return (KOREA["lonMin"] <= box["west"] and box["east"] <= KOREA["lonMax"]
            and KOREA["latMin"] <= box["south"] and box["north"] <= KOREA["latMax"])


def grid_file_box(lat_path: pathlib.Path, lon_path: pathlib.Path) -> dict | None:
    if not (lat_path.is_file() and lon_path.is_file()):
        return None
    import numpy as np  # noqa: PLC0415
    lat, lon = np.load(lat_path), np.load(lon_path)
    ok = np.isfinite(lat) & np.isfinite(lon)
    return {"west": round(float(lon[ok].min()), 4), "south": round(float(lat[ok].min()), 4),
            "east": round(float(lon[ok].max()), 4), "north": round(float(lat[ok].max()), 4),
            "shape": list(lat.shape)}


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--ref-root", type=pathlib.Path, default=None,
                   help="참조자료 뿌리(02.File-format 의 부모). 없으면 ③ 을 건너뛴다")
    args = p.parse_args()
    ref = args.ref_root / "02.File-format" if args.ref_root else None
    m = mgrs.MGRS()
    out = {"schema": "colab-tile-bbox/1", "koreaBox": KOREA, "tiles": []}
    grids = {"T51SYB": "HLS.S30.T51SYB.2025359T023019.v2.0", "T52SCE": "HLS.S30.T52SCE.2025361T022121.v2.0"}
    for tile, stem in grids.items():
        o = mgrs_origin(tile)
        square = utm_envelope(o["zone"], o["E0"], o["N0"], o["E0"] + 100_000, o["N0"] + 100_000)
        s2 = utm_envelope(o["zone"], o["E0"], o["N0"] + 100_000 - S2_TILE_M,
                          o["E0"] + S2_TILE_M, o["N0"] + 100_000)
        lat, lon = m.toLatLon(f"{tile.removeprefix('T')}0000000000")
        hand = Transformer.from_crs(f"EPSG:326{o['zone']:02d}", "EPSG:4326",
                                    always_xy=True).transform(o["E0"], o["N0"])
        measured = (grid_file_box(ref / "file_format_4_tif/04.Lat_Lon_info" / f"{stem}_lat2d.npy",
                                  ref / "file_format_4_tif/04.Lat_Lon_info" / f"{stem}_lon2d.npy")
                    if ref else None)
        out["tiles"].append({
            "tile": tile, "kind": "MGRS/Sentinel-2(HLS)", "utm": o,
            "method": "MGRS 손 유도(E0·N0) → S2 타일 109.8 km(북서 모서리 원점) → pyproj EPSG:326zz→4326 · 가장자리 1 km 표본",
            "bbox": {k: s2[k] for k in ("west", "south", "east", "north")},
            "corners": s2["corners"],
            "mgrsSquare100km": {k: square[k] for k in ("west", "south", "east", "north")},
            "crossCheckMgrsPackage": {"swOrigin_mgrs": [round(lon, 6), round(lat, 6)],
                                      "swOrigin_hand": [round(hand[0], 6), round(hand[1], 6)],
                                      "deltaDeg": round(max(abs(lon - hand[0]), abs(lat - hand[1])), 7)},
            "crossCheckGridFile": measured,
            "insideKoreaBox": inside_korea(s2),
            "square100kmInsideKoreaBox": inside_korea(square),
        })
    for tile, (h, v) in {"h27v05": (27, 5), "h28v05": (28, 5)}.items():
        box = modis_envelope(h, v)
        measured = (grid_file_box(ref / "file_format_5_HDF5/04.Lat_Lon_info" / f"lat2d_{tile}.npy",
                                  ref / "file_format_5_HDF5/04.Lat_Lon_info" / f"lon2d_{tile}.npy")
                    if ref else None)
        # 손 대조 — 위도는 y/R 로 곧바로 선다: v05 → [30°, 40°] 가 정확해야 한다.
        hand_lat = (round(math.degrees(box["sinusoidal_m"]["y0"] / MODIS_R), 4),
                    round(math.degrees(box["sinusoidal_m"]["y1"] / MODIS_R), 4))
        out["tiles"].append({
            "tile": tile, "kind": "MODIS sinusoidal",
            "method": f"R={MODIS_R} · T={MODIS_T} · 네 변 각 2400 표본 · 위도=y/R · 경도=x/(R·cos 위도)",
            "bbox": {k: box[k] for k in ("west", "south", "east", "north")},
            "corners": box["corners"], "sinusoidal_m": box["sinusoidal_m"],
            "crossCheckHandLatitude": {"south": hand_lat[0], "north": hand_lat[1]},
            "crossCheckGridFile": measured,
            "insideKoreaBox": inside_korea(box),
        })
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
