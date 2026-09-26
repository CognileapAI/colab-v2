"""DEV 28건의 검색 근거(`d3_search_evidence.facts`) payload 를 정본에서 만든다.

**새 표를 만들지 않는다.** 조건 검색(`d3_client_search.candidates`)이 읽는 자리는
`d3_search_evidence.facts` 하나뿐이고, 계약(`SearchEvidenceFacts` 15종)·서버 검증
(`EvidenceFacts`)·편집기(`SearchEvidenceEditor.tsx`)가 이미 서 있다. 비어 있는 것은
데이터뿐이다 — 2026-09-15 보고서 축자 「파일별 검색 근거 d3_search_evidence는 해당
연구실 범위에서 0건이다.」

정본 (이 파일은 값을 지어내지 않는다):
  · `dev-package/tools/dev-seed/canonical-metadata.json`  — 기간과 그 근거(basis)
  · `dev-package/tools/dev-seed/plan-manifest.yaml`       — 프로젝트·포맷·레벨·계보
  · `dev-package/reports/reference-data/datasets-md/**/DATASETS.md` 4건 — 설명 축자

두 등급으로 **갈라 담는다**(2026-09-21 Ted 결정 1 「다 초안으로 넣는다」):
  ㈎ **정본전재 → `facts` · `status: reviewed`** — 정본 문면이 값을 직접 고정한다.
     아래 `READINGS` 의 `quote` 가 그 문면이고, 생성기는 **그 문자열이 실제 정본 설명에
     있는지 확인한 뒤에만** 적는다. 없으면 비영 종료한다 — 옮겨 적기가 어긋난 것을
     조용히 지나치지 않는다. 조건 검색이 읽는 것은 이 등급뿐이다.
  ㈏ **규칙 추론 → `draftFacts` · `status: draft`** — `RULES` 의 규칙이 정본의 레벨·계보·
     기기 이름을 읽어 낸다(계획 §6-2 의 platform·representation·directObservation·
     interpolated ＋ 보조 규칙 `bbox-korea-peninsula`). 1회차는 이것을 `reviewed` 행에
     함께 실어 조건 검색이 규칙값을 사람 확인 없이 근거로 썼다. 2회차는 **싣지 않는다.**

⚠ **왜 draft 행을 따로 쓰지 못하는가** — `d3_search_evidence` 는 `file_id` 가 PRIMARY KEY 이고
`status` 가 **행 단위**다(`db/platform/schema.sql:813`). 한 파일이 reviewed 사실과 draft 사실을
동시에 가질 수 없다. 그래서 규칙 추론값은 payload 의 `draftFacts` 에 `rule:<규칙ID>` locator 와
함께 남고 **DB 에 실리지 않는다**. 승격·폐기 구조(히트 측정 뒤 승격)는 별도 intent 의 몫이며
이 파일은 그 구조가 찾아갈 수 있는 자리와 셈만 만든다 — `ruleSummary` 와 그 옆 JSON 이다.

**정본에 없으면 만들지 않는다**(`PLAN-SoT §9-㊴-②`). 값이 없는 칸은 비운다 —
`EvidenceFacts` 는 성분 하나만 있으면 통과한다.

**지역(2026-09-26 Ted 판정 「자료 지역 확정」)** — 정본 DATASETS.md 기계 블록의 `region` 줄
(「남한 (Ted 확정 …)」)은 괄호 앞 지명을 `facts.region`(reviewed)으로 옮긴다. `bbox` 줄
(표준 격자 계산 w/s/e/n)은 `canonical-metadata.json` 의 `bbox` 와 **같아야** 하고(어긋나면 비영
종료) 보조 규칙 `bbox-korea-peninsula` 의 입력이 된다. 정본 지역이 없는 자료의 지명은 계보로
잇되 **초안**이다 — `region-from-lineage-parent`(가장 가까운 조상의 정본 지역) ·
`region-from-lineage-sibling`(같은 자식의 공동 입력이고 그 자식이 정본 지역을 가진 입력과 같은
기준 격자에 산출될 때). 타일 코드(T51SYB·h27v05 …)는 지명이 아니므로 `region` 에 싣지 않는다 —
위치는 정본 bbox 가 말한다.

쓰는 법
  python3 dev-package/tools/dataset_evidence_backfill.py
  python3 dev-package/tools/dataset_evidence_backfill.py --output <경로>
"""
from __future__ import annotations

import argparse
import calendar
import datetime as dt
import hashlib
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parents[1]
SEED = HERE / "dev-seed"
CANONICAL = SEED / "canonical-metadata.json"
MANIFEST = SEED / "plan-manifest.yaml"
DATASETS_MD_ROOT = REPO / "dev-package" / "reports" / "reference-data" / "datasets-md"
DEFAULT_OUTPUT = HERE / "generated" / "dataset-evidence-payloads.json"

#: `plan-manifest.yaml` 의 format ↔ 계약 `SearchEvidenceFacts.format` enum 5값.
#: 밖에 있는 것(bin(gzip)·GRIB1·GeoPackage·HDF4)은 **적지 않는다** — `measured_format`
#: CHECK 4값도 같은 자리라 결정 3(㈐ 정본 전재)이 자동 측정을 늘리지 않기로 했다.
FORMAT_ENUM = {"npy": "npy", "NetCDF4": "netcdf", "GeoTIFF": "tif"}

#: 프로젝트 4 ↔ `d3_dataset_description.topic` CHECK 6값. DEM·경사향은 지형, 토지피복은 LULC 다.
TOPIC = {
    **{seq: "강우·강수" for seq in range(1, 6)},
    6: "식생·NDVI", 7: "식생·NDVI", 8: "식생·NDVI",
    9: "지형·DEM", 10: "지형·DEM", 11: "토지피복·LULC", 12: "식생·NDVI",
    13: "가뭄", 14: "가뭄",
    **{seq: "파일 포맷 예제" for seq in range(15, 29)},
}

RULES = {
    "platform-from-instrument": "정본이 이름 댄 관측 기기·산출 방식으로 가른다 — 레이더·지상격자·"
                               "기상관측소=ground · GK-2A/HLS/MODIS/Landsat=satellite · "
                               "재분석·U-Net 예측=model.",
    "representation-from-shape": "격자 배열·래스터=spatial_grid · 시군구 벡터 표=table.",
    "direct-observation-from-level": "정본의 Lv 과 계보로 가른다 — 관측계열 원자료와 그 좌표변환·"
                                    "평균 산출물=true · 재분석·예측·지수=false.",
    "interpolated-from-lineage": "정본 설명이 좌표변환·crop·재격자·평균을 말하면 true, "
                                "「재격자 없이 원자료 격자 위에 그대로」면 false.",
    "native-resolution-carried": "좌표변환·crop 만 한 산출물은 부모의 원 관측 해상도를 잇는다"
                                "(재격자화 크기가 아니다 — semantics.json invariants 축자).",
    "region-from-registration-note": "정본 note 가 공간 범위를 말하면 그대로 적는다 — seq 16 축자"
                                    "「전지구 격자라 한반도 경계 밖」.",
    "bbox-korea-peninsula": "보조 규칙(2026-09-21 Ted 결정 2 「가를 넣고, 보조하는 용도로 나를」) — "
                           "정본이 bbox 를 주고 그 상자가 한반도 상자(위도 33~39 · 경도 124~132) "
                           "안에 온전히 들어가면 region 초안 사실 「한반도」를 만든다. 정본 문면이 "
                           "지명을 고정한 reviewed region 은 이 규칙과 무관하게 정본에서만 온다.",
    "region-from-lineage-parent": "정본 지역이 없는 자료는 계보(plan-manifest.yaml parents)를 거슬러 "
                                  "올라가 정본 지역(reviewed)을 가진 **가장 가까운 대**의 조상 지명을 "
                                  "잇는다 — 그 대의 지명이 모두 같을 때만. Ted 판정 2026-09-26 「자료 지역 "
                                  "확정」 2 「연구대상지는 부모 범위(남한)를 초안으로 이음」 · 4 「파생 자료 "
                                  "9건은 계보로 잇되 초안(측정 후 승격)」.",
    "region-from-lineage-sibling": "조상에 정본 지역이 없는 자료가 어떤 자식의 공동 입력이고, 그 자식이 "
                                   "정본 지역을 가진 다른 입력과 **같은 기준 격자 파일**(grid_files)에 "
                                   "산출되면 그 입력의 지명을 잇는다 — 자식이 입력들의 공통 격자 위에 "
                                   "있다는 계보 추론. Ted 판정 2026-09-26 「자료 지역 확정」 4.",
}

#: 보조 검증용 한반도 상자. 정본이 지명을 말하지 않는 자료의 **초안** region 에만 쓴다.
KOREA_PENINSULA = {"latMin": 33.0, "latMax": 39.0, "lonMin": 124.0, "lonMax": 132.0}


def region_from_bbox(bbox: dict | None) -> str | None:
    """bbox 가 한반도 상자 **안에 온전히** 들어가면 「한반도」, 아니면 None.

    이것은 **보조**다(Ted 결정 2 — 「가를 넣고, 보조하는 용도로 나를 해야하지 않을까?」).
    그래서 값이 서도 초안이고 `rule:bbox-korea-peninsula` locator 를 달고 나간다.
    bbox 가 없으면 아무 말도 하지 않는다 — 없는 것을 「미상」이 아니라 사실로 바꾸지 않는다.
    """
    if not isinstance(bbox, dict):
        return None
    try:
        west, south = float(bbox["west"]), float(bbox["south"])
        east, north = float(bbox["east"]), float(bbox["north"])
    except (KeyError, TypeError, ValueError):
        return None
    if not (west < east and south < north):
        return None
    inside = (KOREA_PENINSULA["lonMin"] <= west and east <= KOREA_PENINSULA["lonMax"]
              and KOREA_PENINSULA["latMin"] <= south and north <= KOREA_PENINSULA["latMax"])
    return "한반도" if inside else None

#: 정본 판독표. `quote` 는 그 seq 의 정본 `description` 안에 **그대로 있어야 한다**.
#: `facts` 는 그 문면이 고정하는 값이고, `rules` 는 위 `RULES` 로 읽어 낸 값이다.
READINGS: dict[int, dict] = {
    1: {"quote": "시/공간해상도 5분 / 0.5 km, 변량은 반사도",
        "facts": {"variable": "반사도", "nativeResolutionM": 500.0, "provider": "기상청",
                  "cadence": "5min"},
        "rules": {"platform": "ground", "representation": "spatial_grid",
                  "directObservation": True, "interpolated": False}},
    2: {"quote": "지상 격자 15분 누적강수",
        "facts": {"variable": "강수량", "cadence": "15min", "provider": "기상청"},
        "rules": {"platform": "ground", "representation": "spatial_grid",
                  "directObservation": True, "interpolated": False}},
    3: {"quote": "WGS84 로 좌표계 변환하고, 특정 연구대상지를 중심으로 crop",
        "facts": {"variable": "반사도", "provider": "기상청", "roles": ["model_input"]},
        "rules": {"platform": "ground", "representation": "spatial_grid",
                  "directObservation": True, "interpolated": True,
                  "nativeResolutionM": 500.0}},
    4: {"quote": "WGS84 로 좌표계 변환하고 연구대상지를 중심으로 crop",
        "facts": {"variable": "강수량", "cadence": "15min", "provider": "기상청",
                  "roles": ["validation"]},
        "rules": {"platform": "ground", "representation": "spatial_grid",
                  "directObservation": True, "interpolated": True}},
    5: {"quote": "U-Net 기반 모델의 예측 결과",
        "facts": {"variable": "강수량", "model": "U-Net", "roles": ["prediction"]},
        "rules": {"platform": "model", "representation": "spatial_grid",
                  "directObservation": False, "interpolated": True}},
    6: {"quote": "시/공간해상도는 1일 / 2 km",
        "facts": {"variable": "NDVI", "cadence": "daily", "nativeResolutionM": 2000.0,
                  "provider": "국가기상위성센터"},
        "rules": {"platform": "satellite", "representation": "spatial_grid",
                  "directObservation": True, "interpolated": False}},
    7: {"quote": "2 km 를 100 m 로 균등 분할한 뒤 일 단위를 월 단위 평균으로 변환",
        "facts": {"variable": "NDVI", "cadence": "monthly", "nativeResolutionM": 2000.0,
                  "statistics": ["monthly_mean"], "region": "경기남부충청",
                  "roles": ["model_input"]},
        "rules": {"platform": "satellite", "representation": "spatial_grid",
                  "directObservation": True, "interpolated": True}},
    8: {"quote": "3~7일 간격 자료를 월평균 100 m 로 변환",
        "facts": {"variable": "NDVI", "cadence": "monthly", "statistics": ["monthly_mean"],
                  "roles": ["validation"]},
        "rules": {"platform": "satellite", "representation": "spatial_grid",
                  "directObservation": True, "interpolated": True}},
    9: {"quote": "Copernicus GLO-30 DEM 자료를 100 m 해상도로 변환",
        "facts": {"variable": "표고", "nativeResolutionM": 30.0, "provider": "Copernicus",
                  "roles": ["auxiliary_input"]},
        "rules": {"representation": "spatial_grid", "interpolated": True}},
    10: {"quote": "Copernicus GLO-30 DEM 을 100 m 로 변환한 뒤 GIS 프로그램으로 경사향을 추출",
         "facts": {"variable": "경사향", "nativeResolutionM": 30.0, "provider": "Copernicus",
                   "roles": ["auxiliary_input"]},
         "rules": {"representation": "spatial_grid", "interpolated": True}},
    11: {"quote": "Landsat-8 위성의 밴드를 이용해",
         "quotes": {"cadence": "연 단위 100 m 토지피복지도"},
         "facts": {"variable": "토지피복", "roles": ["model_input"], "cadence": "yearly"},
         "rules": {"platform": "satellite", "representation": "spatial_grid",
                   "directObservation": True, "interpolated": False}},
    12: {"quote": "Lv.0 처럼 일 단위 시간해상도를 갖고",
         "facts": {"variable": "NDVI", "cadence": "daily", "model": "U-Net",
                   "roles": ["prediction"]},
         "rules": {"platform": "model", "representation": "spatial_grid",
                   "directObservation": False, "interpolated": True}},
    13: {"quote": "2000-01-01 ~ 2025-12-31 을 주 단위로 담는다",
         "facts": {"variable": "SPI", "cadence": "weekly", "region": "대한민국시군구",
                   "roles": ["index"]},
         "rules": {"platform": "ground", "representation": "table",
                   "directObservation": False, "interpolated": False}},
    14: {"quote": "2000-01-01 ~ 2025-12-31 을 주 단위로 담는다",
         "facts": {"variable": "SPEI", "cadence": "weekly", "region": "대한민국시군구",
                   "roles": ["index"]},
         "rules": {"platform": "ground", "representation": "table",
                   "directObservation": False, "interpolated": False}},
    15: {"quote": "ERA5 지표 변수를 담은 GRIB1 원자료",
         "facts": {},
         "rules": {"platform": "model", "representation": "spatial_grid",
                   "directObservation": False, "interpolated": False}},
    16: {"quote": "각 24시각이다",
         "facts": {"cadence": "hourly"},
         "rules": {"platform": "model", "representation": "spatial_grid",
                   "directObservation": False, "interpolated": True,
                   "region": "전지구"}},
    17: {"quote": "GK-2A 지표온도(LST)를 10분 간격으로 담은 NetCDF4 원자료",
         "facts": {"variable": "지표온도", "cadence": "10min"},
         "rules": {"platform": "satellite", "representation": "spatial_grid",
                   "directObservation": True, "interpolated": False}},
    18: {"quote": "변수는 지표온도 하나이고",
         "facts": {"variable": "지표온도"},
         "rules": {"platform": "satellite", "representation": "spatial_grid",
                   "directObservation": True, "interpolated": True}},
    19: {"quote": "기상청 HSR 합성 반사도 바이너리 원자료",
         "facts": {"variable": "반사도", "provider": "기상청"},
         "rules": {"platform": "ground", "representation": "spatial_grid",
                   "directObservation": True, "interpolated": False}},
    20: {"quote": "bin 원자료를 시각별 합성 반사도 배열로 바꾼 결과",
         "facts": {"variable": "반사도", "provider": "기상청"},
         "rules": {"platform": "ground", "representation": "spatial_grid",
                   "directObservation": True, "interpolated": True}},
    21: {"quote": "HLS S30 T51SYB 타일의 Blue·Green·Red 3밴드 GeoTIFF 원자료",
         "facts": {},
         "rules": {"platform": "satellite", "representation": "spatial_grid",
                   "directObservation": True, "interpolated": False}},
    22: {"quote": "HLS S30 T52SCE 타일의 Blue·Green·Red 3밴드 GeoTIFF 원자료",
         "facts": {},
         "rules": {"platform": "satellite", "representation": "spatial_grid",
                   "directObservation": True, "interpolated": False}},
    23: {"quote": "재격자 없이 원자료 격자 위에 그대로 있다",
         "facts": {},
         "rules": {"platform": "satellite", "representation": "spatial_grid",
                   "directObservation": True, "interpolated": False}},
    24: {"quote": "형상·구성은 T51SYB 결과와 같다",
         "facts": {},
         "rules": {"platform": "satellite", "representation": "spatial_grid",
                   "directObservation": True, "interpolated": False}},
    25: {"quote": "MODIS MOD15A2H 엽면적지수·광합성유효복사흡수율 산출물의 h27v05 타일",
         "facts": {"variable": "엽면적지수"},
         "rules": {"platform": "satellite", "representation": "spatial_grid",
                   "directObservation": True, "interpolated": False}},
    26: {"quote": "MOD15A2H 의 h28v05 타일 4일치",
         "facts": {"variable": "엽면적지수"},
         "rules": {"platform": "satellite", "representation": "spatial_grid",
                   "directObservation": True, "interpolated": False}},
    27: {"quote": "h27v05 타일의 HDF4 내부 서브데이터셋 6종을 날짜별로 배열로 뽑은 결과",
         "facts": {"variable": "엽면적지수"},
         "rules": {"platform": "satellite", "representation": "spatial_grid",
                   "directObservation": True, "interpolated": False}},
    28: {"quote": "h28v05 타일의 HDF4 서브데이터셋 6종을 날짜별로 배열로 뽑은 결과",
         "facts": {"variable": "엽면적지수"},
         "rules": {"platform": "satellite", "representation": "spatial_grid",
                   "directObservation": True, "interpolated": False}},
}


def sha256_file(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def expand_period(value: str, *, end: bool) -> str:
    """정본의 `YYYY` · `YYYY-MM` · `YYYY-MM-DD` 를 계약의 date 로 편다."""
    parts = value.split("-")
    if len(parts) == 3:
        return value
    if len(parts) == 2:
        year, month = int(parts[0]), int(parts[1])
        day = calendar.monthrange(year, month)[1] if end else 1
        return f"{year:04d}-{month:02d}-{day:02d}"
    year = int(parts[0])
    return f"{year:04d}-12-31" if end else f"{year:04d}-01-01"


def read_datasets_md() -> dict[int, dict]:
    """4건의 DATASETS.md 기계 블록에서 seq → {document, description, name, region?, bbox?} 을 읽는다.

    YAML 파서를 쓰지 않는다 — 이 블록에서 필요한 것은 `seq`·`name`·`description` 세 줄과
    2026-09-26 에 더한 `region`·`bbox` 두 줄(있을 때만)이고, 파서 의존을 늘리지 않는 편이
    게이트 환경에서 안전하다. 형식이 어긋나면 비영 종료한다.
    """
    out: dict[int, dict] = {}
    for path in sorted(DATASETS_MD_ROOT.rglob("DATASETS.md")):
        document = path.relative_to(DATASETS_MD_ROOT).as_posix()
        block = path.read_text(encoding="utf-8").split("## 기계 블록", 1)
        if len(block) != 2:
            raise SystemExit(f"{document}: 기계 블록이 없다. 정본 형식이 바뀌었다.")
        current: dict | None = None
        for line in block[1].splitlines():
            seq = re.match(r"\s*-\s*seq:\s*(\d+)\s*$", line)
            if seq:
                current = {"seq": int(seq[1]), "document": document}
                out[current["seq"]] = current
                continue
            if current is None:
                continue
            for key in ("name", "description", "region", "bbox"):
                found = re.match(rf'\s*{key}:\s*"(.*)"\s*$', line)
                if found:
                    current[key] = found[1]
    missing = [seq for seq in range(1, 29) if seq not in out]
    if missing:
        raise SystemExit(f"DATASETS.md 에서 못 읽은 seq: {missing}")
    return out


def read_manifest() -> dict[int, dict]:
    """plan-manifest.yaml 에서 seq → {project, name, format, level, parents, grid_files} 를 읽는다."""
    out: dict[int, dict] = {}
    current: dict | None = None
    listing: str | None = None
    for line in MANIFEST.read_text(encoding="utf-8").splitlines():
        seq = re.match(r"- seq:\s*(\d+)\s*$", line)
        if seq:
            current = {"seq": int(seq[1]), "parents": [], "grid_files": []}
            out[current["seq"]] = current
            listing = None
            continue
        if current is None:
            continue
        item = re.match(r"  - (.+?)\s*$", line)
        if item and listing:
            current[listing].append(item[1])
            continue
        listing = None
        found = re.match(r"  (project|name|format|level):\s*(.+?)\s*$", line)
        if found:
            current[found[1]] = found[2]
            continue
        opened = re.match(r"  (parents|grid_files):\s*(\[\])?\s*$", line)
        if opened:
            listing = None if opened[2] else opened[1]
    return out


#: 정본 `region` 줄 — 「남한 (Ted 확정 2026-09-26 · 기상청 관측망)」 → 괄호 앞 지명.
REGION_LINE = re.compile(r"^(?P<place>[^()]+?)\s*\((?P<basis>[^()]+)\)$")
#: 정본 `bbox` 줄 — 「w/s/e/n = 125.2458/36.9070/126.5230/37.9256 · …」.
BBOX_LINE = re.compile(r"^w/s/e/n = (-?\d+\.\d+)/(-?\d+\.\d+)/(-?\d+\.\d+)/(-?\d+\.\d+) · ")


def reviewed_regions(md: dict[int, dict]) -> dict[int, dict]:
    """seq → {value, provenance}. 정본 `region` 줄과 판독표(READINGS)의 축자 region 을 모은다.

    둘이 한 seq 에 겹치면 비영 종료한다 — 어느 쪽이 정본인지 조용히 고르지 않는다.
    """
    out: dict[int, dict] = {}
    for seq in range(1, 29):
        source, reading = md[seq], READINGS[seq]
        line = source.get("region")
        if line:
            found = REGION_LINE.match(line)
            if not found:
                raise SystemExit(f"seq {seq}: 정본 region 줄의 형식이 「지명 (근거)」가 아니다 — {line!r}")
            if "region" in reading["facts"]:
                raise SystemExit(f"seq {seq}: 정본 region 줄과 판독표 region 이 겹친다")
            out[seq] = {"value": found["place"].strip(),
                        "provenance": f"정본전재 · {source['document']} seq {seq} 축자 「지역: {line}」"}
        elif "region" in reading["facts"]:
            quote = reading.get("quotes", {}).get("region", reading["quote"])
            out[seq] = {"value": reading["facts"]["region"],
                        "provenance": f"정본전재 · {source['document']} seq {seq} 축자 「{quote}」"}
    return out


def canonical_bbox(seq: int, canon: dict, source: dict) -> dict | None:
    """정본 두 자리(canonical-metadata.json `bbox` · DATASETS.md `bbox` 줄)가 같은 값을 말하는지 본다."""
    line, box = source.get("bbox"), canon.get("bbox")
    if not line and not box:
        return None
    if not (line and box):
        raise SystemExit(f"seq {seq}: bbox 가 정본 한 자리에만 있다(DATASETS.md {bool(line)} · "
                         f"canonical-metadata.json {bool(box)})")
    found = BBOX_LINE.match(line)
    if not found:
        raise SystemExit(f"seq {seq}: DATASETS.md bbox 줄 형식이 「w/s/e/n = …」가 아니다 — {line!r}")
    said = [float(v) for v in found.groups()]
    held = [float(box[k]) for k in ("west", "south", "east", "north")]
    if said != held:
        raise SystemExit(f"seq {seq}: bbox 가 두 정본에서 다르다 — DATASETS.md {said} · "
                         f"canonical-metadata.json {held}")
    return box


def lineage_region(seq: int, parents_of: dict, reviewed: dict) -> dict | None:
    """정본 지역을 가진 **가장 가까운 대**의 조상. 그 대의 지명이 갈리면 None(조용히 고르지 않는다)."""
    frontier, seen = sorted(parents_of[seq]), set()
    while frontier:
        hits = {p: reviewed[p]["value"] for p in frontier if p in reviewed}
        if hits:
            values = set(hits.values())
            if len(values) != 1:
                return {"conflict": hits}
            return {"value": values.pop(), "from": sorted(hits)}
        seen.update(frontier)
        frontier = sorted({g for p in frontier for g in parents_of[p]} - seen)
    return None


def sibling_region(seq: int, parents_of: dict, children_of: dict, grids: dict,
                   reviewed: dict) -> dict | None:
    """같은 자식의 공동 입력 중 정본 지역을 가진 것이 있고, 자식이 그 입력과 **같은 기준 격자
    파일**에 산출되면 그 지명. 격자가 비었거나 다르면 말하지 않는다."""
    for child in sorted(children_of.get(seq, ())):
        grid = grids[child]
        if not grid:
            continue
        anchors = {p: reviewed[p]["value"] for p in parents_of[child]
                   if p != seq and p in reviewed and grids[p] == grid}
        values = set(anchors.values())
        if len(values) == 1:
            return {"value": values.pop(), "child": child, "from": sorted(anchors)}
    return None


def build() -> dict:
    canonical = json.loads(CANONICAL.read_text(encoding="utf-8"))
    md = read_datasets_md()
    manifest = read_manifest()
    canon_by_seq = {row["seq"]: row for row in canonical["datasets"]}
    aux_roles = {row["child"]: row["role"] for row in canonical.get("auxiliaryParents", [])}
    reviewed = reviewed_regions(md)
    seq_of_name = {plan["name"]: seq for seq, plan in manifest.items()}
    parents_of = {seq: [seq_of_name[p] for p in manifest[seq]["parents"]] for seq in range(1, 29)}
    children_of: dict[int, list[int]] = {}
    for child, parents in parents_of.items():
        for parent in parents:
            children_of.setdefault(parent, []).append(child)
    grids = {seq: sorted(manifest[seq]["grid_files"]) for seq in range(1, 29)}
    region_lineage: dict[str, dict] = {}

    datasets = []
    rule_summary: dict[str, int] = {rule: 0 for rule in RULES}
    for seq in range(1, 29):
        canon, source, plan = canon_by_seq[seq], md[seq], manifest[seq]
        reading = READINGS[seq]
        for quote in [reading["quote"], *reading.get("quotes", {}).values()]:
            if quote not in source.get("description", ""):
                raise SystemExit(
                    f"seq {seq}: 판독표의 축자가 정본 설명에 없다 — {quote!r}.\n"
                    f"  정본({source['document']}): {source.get('description', '')!r}")
        if canon["name"] != source.get("name") or canon["name"] != plan.get("name"):
            raise SystemExit(f"seq {seq}: 세 정본의 이름이 어긋난다.")

        facts: dict = {"period": {"start": expand_period(canon["start"], end=False),
                                  "end": expand_period(canon["end"], end=True)}}
        provenance = {"period": f"정본전재 · canonical-metadata.json#/datasets/{seq} · "
                                f"기간 근거 축자 「{canon['basis']}」"}
        enum_format = FORMAT_ENUM.get(plan.get("format", ""))
        if enum_format:
            facts["format"] = enum_format
            provenance["format"] = (f"정본전재 · plan-manifest.yaml seq {seq} format "
                                    f"{plan['format']} → 계약 enum {enum_format}")
        for key, value in reading["facts"].items():
            facts[key] = value
            quote = reading.get("quotes", {}).get(key, reading["quote"])
            provenance[key] = f"정본전재 · {source['document']} seq {seq} 축자 「{quote}」"
        if seq in reviewed:
            facts["region"] = reviewed[seq]["value"]
            provenance["region"] = reviewed[seq]["provenance"]
        bbox = canonical_bbox(seq, canon, source)

        # 규칙 추론값은 **reviewed 사실에 섞지 않는다**(Ted 결정 1). 초안 칸으로 따로 담고
        # locator 에 규칙 ID 를 박아 승격·폐기 구조가 나중에 찾아올 수 있게 둔다.
        draft_facts: dict = {}
        draft_provenance: dict = {}
        rule_of = {"platform": "platform-from-instrument",
                   "representation": "representation-from-shape",
                   "directObservation": "direct-observation-from-level",
                   "interpolated": "interpolated-from-lineage",
                   "nativeResolutionM": "native-resolution-carried",
                   "region": "region-from-registration-note"}
        for key, value in reading["rules"].items():
            draft_facts[key] = value
            rule = rule_of[key]
            rule_summary[rule] += 1
            draft_provenance[key] = (f"규칙 · rule:{rule} · 읽은 정본 = "
                                     f"{source['document']} seq {seq}")
        # 지역 초안(2026-09-26 Ted 판정 「자료 지역 확정」 2·3·4) — 정본 지역이 없을 때만, 이 순서로
        # 하나만 선다: 등록 note(판독표) → 계보 조상 → 계보 공동 입력 → bbox 보조.
        lineage = sibling = None
        if "region" not in facts and "region" not in draft_facts:
            lineage = lineage_region(seq, parents_of, reviewed)
            if lineage and "value" in lineage:
                draft_facts["region"] = lineage["value"]
                rule_summary["region-from-lineage-parent"] += 1
                draft_provenance["region"] = (
                    "규칙 · rule:region-from-lineage-parent · 읽은 정본 = plan-manifest.yaml parents · "
                    "조상 " + " · ".join(f"seq {p}({reviewed[p]['value']})" for p in lineage["from"]))
        if "region" not in facts and "region" not in draft_facts and not lineage:
            sibling = sibling_region(seq, parents_of, children_of, grids, reviewed)
            if sibling:
                draft_facts["region"] = sibling["value"]
                rule_summary["region-from-lineage-sibling"] += 1
                draft_provenance["region"] = (
                    "규칙 · rule:region-from-lineage-sibling · 읽은 정본 = plan-manifest.yaml parents·grid_files · "
                    f"자식 seq {sibling['child']} 의 공동 입력 "
                    + " · ".join(f"seq {p}({reviewed[p]['value']})" for p in sibling["from"])
                    + " 과 같은 기준 격자")
        bbox_region = region_from_bbox(bbox)
        if bbox_region and "region" not in draft_facts and "region" not in facts:
            draft_facts["region"] = bbox_region
            rule_summary["bbox-korea-peninsula"] += 1
            draft_provenance["region"] = (
                "규칙 · rule:bbox-korea-peninsula · 읽은 정본 = "
                f"canonical-metadata.json#/datasets/{seq}/bbox w/s/e/n "
                f"{bbox['west']}/{bbox['south']}/{bbox['east']}/{bbox['north']}")
        region_lineage[str(seq)] = {
            "reviewed": facts.get("region"),
            "draft": draft_facts.get("region"),
            "draftRule": (re.search(r"rule:([a-z-]+)", draft_provenance["region"])[1]
                          if "region" in draft_facts else None),
            "lineageConflict": (lineage or {}).get("conflict"),
            "bbox": ([bbox[k] for k in ("west", "south", "east", "north")] if bbox else None),
            "bboxInsideKoreaBox": (region_from_bbox(bbox) is not None) if bbox else None,
        }

        # 원문 스냅숏에 정본 지역·bbox 줄을 함께 싣는다 — reviewed region 이 그 줄에서 왔다.
        spatial = "".join(f"{label}: {source[key]}\n" for key, label in
                          (("region", "지역"), ("bbox", "공간범위(bbox)")) if source.get(key))
        text = (f"{source['description']}\n{spatial}"
                f"기간 근거: {canon['basis']} ({canon['start']} ~ {canon['end']}, "
                f"{canon['granularity']} 단위)\n"
                f"프로젝트: {plan.get('project')} · 레벨: {plan.get('level')} · "
                f"정본 포맷: {plan.get('format')}")
        datasets.append({
            "seq": seq,
            "name": canon["name"],
            "topic": TOPIC[seq],
            "sourceLabel": reading["facts"].get("provider"),
            "auxiliaryRole": aux_roles.get(canon["name"]),
            "status": "reviewed",
            "facts": facts,
            "provenance": provenance,
            "draftStatus": "draft",
            "draftFacts": draft_facts,
            "draftProvenance": draft_provenance,
            "source": {
                "label": f"{source['document']} · seq {seq} {canon['name']}"[:200],
                "locator": f"DATASETS.md#{source['document']}#seq-{seq}"[:300],
                "text": text,
                "sha256": hashlib.sha256(text.encode()).hexdigest(),
            },
        })

    return {
        "schema": "colab-dataset-evidence/1",
        "generated": {
            "by": "dev-package/tools/dataset_evidence_backfill.py",
            "note": "생성물 — 손으로 고치지 않는다. 값을 바꾸려면 정본을 고치고 다시 돌린다.",
            "at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d"),
        },
        "sourceHashes": {
            "dev-package/tools/dev-seed/canonical-metadata.json": sha256_file(CANONICAL),
            "dev-package/tools/dev-seed/plan-manifest.yaml": sha256_file(MANIFEST),
            **{f"dev-package/reports/reference-data/datasets-md/"
               f"{path.relative_to(DATASETS_MD_ROOT).as_posix()}": sha256_file(path)
               for path in sorted(DATASETS_MD_ROOT.rglob("DATASETS.md"))},
        },
        "rules": RULES,
        "ruleSummary": rule_summary,
        "regionTrace": region_lineage,
        "draftNote": ("규칙 추론값은 초안이다 — 사람 확인 후 승격(2026-09-21 Ted 결정 1). "
                      "d3_search_evidence 는 file_id 가 PK 이고 status 가 행 단위라 한 파일이 "
                      "reviewed 와 draft 를 함께 가질 수 없다. 그래서 draftFacts 는 DB 에 실리지 "
                      "않고 이 payload 에만 남는다. 승격 단계는 rule:<ID> locator 로 찾아온다."),
        "datasets": datasets,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    args = parser.parse_args()
    payloads = build()
    out = pathlib.Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payloads, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    filled = sum(len(row["facts"]) for row in payloads["datasets"])
    drafts = sum(len(row["draftFacts"]) for row in payloads["datasets"])
    topics = sum(1 for row in payloads["datasets"] if row["topic"])
    labels = sum(1 for row in payloads["datasets"] if row["sourceLabel"])
    print(f"{out} — 데이터셋 {len(payloads['datasets'])}건 · reviewed 사실 {filled}칸 · "
          f"draft 사실 {drafts}칸 · topic {topics}건 · source_label {labels}건")

    # 승격·폐기 구조가 찾아올 자리 — 규칙 ID 별 초안 셈. 그 구조 자체는 별도 intent 의 몫이고
    # 이 파일은 셈만 낸다(2026-09-21 Ted 결정 1 「얼마나 히트했냐를 측정하고 승격 또는 폐기」).
    summary_path = out.with_name(out.stem + "-rule-summary.json")
    summary_path.write_text(json.dumps({
        "schema": "colab-dataset-evidence-rule-summary/1",
        "payload": out.name,
        "note": payloads["draftNote"],
        "draftFactsTotal": drafts,
        "reviewedFactsTotal": filled,
        "byRule": payloads["ruleSummary"],
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{summary_path} — 규칙별 초안 셈 " + " · ".join(
        f"{rule} {count}" for rule, count in payloads["ruleSummary"].items()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
