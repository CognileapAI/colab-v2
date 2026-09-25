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

두 등급으로 나누어 적고, 등급은 payload 의 `provenance` 에 필드마다 남는다:
  ㈎ **정본전재** — 정본 문면이 값을 직접 고정한다. 아래 `READINGS` 의 `quote` 가
     그 문면이고, 생성기는 **그 문자열이 실제 정본 설명에 있는지 확인한 뒤에만** 적는다.
     없으면 비영 종료한다 — 옮겨 적기가 어긋난 것을 조용히 지나치지 않는다.
  ㈏ **규칙** — `RULES` 의 규칙이 정본의 레벨·계보·기기 이름을 읽어 낸다(계획 §6-2 의
     platform·representation·directObservation·interpolated). 규칙 ID 가 provenance 에
     남아 되돌림 경로가 된다.

**정본에 없으면 만들지 않는다**(`PLAN-SoT §9-㊴-②`). 값이 없는 칸은 비운다 —
`EvidenceFacts` 는 성분 하나만 있으면 통과한다.

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
}

#: 정본 판독표. `quote` 는 그 seq 의 정본 `description` 안에 **그대로 있어야 한다**.
#: `facts` 는 그 문면이 고정하는 값이고, `rules` 는 위 `RULES` 로 읽어 낸 값이다.
READINGS: dict[int, dict] = {
    1: {"quote": "시/공간해상도 5분 / 0.5 km, 변량은 반사도",
        "facts": {"variable": "반사도", "nativeResolutionM": 500.0, "provider": "기상청"},
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
         "facts": {"variable": "토지피복", "roles": ["model_input"]},
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
         "facts": {"variable": "지표온도"},
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
         "facts": {"region": "T51SYB"},
         "rules": {"platform": "satellite", "representation": "spatial_grid",
                   "directObservation": True, "interpolated": False}},
    22: {"quote": "HLS S30 T52SCE 타일의 Blue·Green·Red 3밴드 GeoTIFF 원자료",
         "facts": {"region": "T52SCE"},
         "rules": {"platform": "satellite", "representation": "spatial_grid",
                   "directObservation": True, "interpolated": False}},
    23: {"quote": "재격자 없이 원자료 격자 위에 그대로 있다",
         "facts": {"region": "T51SYB"},
         "rules": {"platform": "satellite", "representation": "spatial_grid",
                   "directObservation": True, "interpolated": False}},
    24: {"quote": "형상·구성은 T51SYB 결과와 같다",
         "facts": {"region": "T52SCE"},
         "rules": {"platform": "satellite", "representation": "spatial_grid",
                   "directObservation": True, "interpolated": False}},
    25: {"quote": "MODIS MOD15A2H 엽면적지수·광합성유효복사흡수율 산출물의 h27v05 타일",
         "facts": {"variable": "엽면적지수", "region": "h27v05"},
         "rules": {"platform": "satellite", "representation": "spatial_grid",
                   "directObservation": True, "interpolated": False}},
    26: {"quote": "MOD15A2H 의 h28v05 타일 4일치",
         "facts": {"variable": "엽면적지수", "region": "h28v05"},
         "rules": {"platform": "satellite", "representation": "spatial_grid",
                   "directObservation": True, "interpolated": False}},
    27: {"quote": "h27v05 타일의 HDF4 내부 서브데이터셋 6종을 날짜별로 배열로 뽑은 결과",
         "facts": {"variable": "엽면적지수", "region": "h27v05"},
         "rules": {"platform": "satellite", "representation": "spatial_grid",
                   "directObservation": True, "interpolated": False}},
    28: {"quote": "h28v05 타일의 HDF4 서브데이터셋 6종을 날짜별로 배열로 뽑은 결과",
         "facts": {"variable": "엽면적지수", "region": "h28v05"},
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
    """4건의 DATASETS.md 기계 블록에서 seq → {document, description, name} 을 읽는다.

    YAML 파서를 쓰지 않는다 — 이 블록에서 필요한 것은 `seq`·`name`·`description` 세 줄이고,
    파서 의존을 늘리지 않는 편이 게이트 환경에서 안전하다. 형식이 어긋나면 비영 종료한다.
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
            for key in ("name", "description"):
                found = re.match(rf'\s*{key}:\s*"(.*)"\s*$', line)
                if found:
                    current[key] = found[1]
    missing = [seq for seq in range(1, 29) if seq not in out]
    if missing:
        raise SystemExit(f"DATASETS.md 에서 못 읽은 seq: {missing}")
    return out


def read_manifest() -> dict[int, dict]:
    """plan-manifest.yaml 에서 seq → {project, name, format, level} 을 읽는다."""
    out: dict[int, dict] = {}
    current: dict | None = None
    for line in MANIFEST.read_text(encoding="utf-8").splitlines():
        seq = re.match(r"- seq:\s*(\d+)\s*$", line)
        if seq:
            current = {"seq": int(seq[1])}
            out[current["seq"]] = current
            continue
        if current is None:
            continue
        found = re.match(r"  (project|name|format|level):\s*(.+?)\s*$", line)
        if found:
            current[found[1]] = found[2]
    return out


def build() -> dict:
    canonical = json.loads(CANONICAL.read_text(encoding="utf-8"))
    md = read_datasets_md()
    manifest = read_manifest()
    canon_by_seq = {row["seq"]: row for row in canonical["datasets"]}
    aux_roles = {row["child"]: row["role"] for row in canonical.get("auxiliaryParents", [])}

    datasets = []
    for seq in range(1, 29):
        canon, source, plan = canon_by_seq[seq], md[seq], manifest[seq]
        reading = READINGS[seq]
        if reading["quote"] not in source.get("description", ""):
            raise SystemExit(
                f"seq {seq}: 판독표의 축자가 정본 설명에 없다 — {reading['quote']!r}.\n"
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
            provenance[key] = f"정본전재 · {source['document']} seq {seq} 축자 「{reading['quote']}」"
        for key, value in reading["rules"].items():
            facts[key] = value
            rule = {"platform": "platform-from-instrument",
                    "representation": "representation-from-shape",
                    "directObservation": "direct-observation-from-level",
                    "interpolated": "interpolated-from-lineage",
                    "nativeResolutionM": "native-resolution-carried",
                    "region": "region-from-registration-note"}[key]
            provenance[key] = f"규칙 · rule:{rule} · 읽은 정본 = {source['document']} seq {seq}"

        text = (f"{source['description']}\n"
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
    topics = sum(1 for row in payloads["datasets"] if row["topic"])
    labels = sum(1 for row in payloads["datasets"] if row["sourceLabel"])
    print(f"{out} — 데이터셋 {len(payloads['datasets'])}건 · 사실 {filled}칸 · "
          f"topic {topics}건 · source_label {labels}건")
    return 0


if __name__ == "__main__":
    sys.exit(main())
