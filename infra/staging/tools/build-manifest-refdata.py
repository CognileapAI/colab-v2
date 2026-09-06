#!/usr/bin/env python3
"""dev 초기 적재 매니페스트를 원천 폴더에서 다시 짓고 검증한다 (`PLAN-SoT §9 〈356〉`).

⛔ **절대경로를 박지 않는다**(`CLAUDE.md §3-8`) — 원천 뿌리는 env 또는 인자로 받는다.

    COLAB_REFERENCE_DATA=<'03 Reference-Data' 경로> \
      python3 infra/staging/tools/build-manifest-refdata.py [--out DIR] [--check]

`--check` 는 **쓰지 않고 검증만** 한다 — 레포에 든 `infra/staging/manifest-refdata.json` 이
지금 원천과 맞는지 재는 자리다.
"""
import argparse, json, os, collections, sys
from pathlib import Path

_ap = argparse.ArgumentParser()
_ap.add_argument("--source-root", default=os.environ.get("COLAB_REFERENCE_DATA"))
_ap.add_argument("--out", default=None, help="생략하면 infra/staging/")
_ap.add_argument("--check", action="store_true", help="검증만 하고 쓰지 않는다")
_a = _ap.parse_args()
if not _a.source_root:
    print("원천 뿌리가 없다 — COLAB_REFERENCE_DATA 또는 --source-root", file=sys.stderr)
    raise SystemExit(2)

ROOT = Path(_a.source_root)
_REPO = Path(__file__).resolve().parents[3]
OUT  = Path(_a.out) if _a.out else (_REPO / "infra" / "staging")
CHECK_ONLY = _a.check
LD = "01.level-data"; FF = "02.File-format"
PR = f"{LD}/01.precipitation/01.precipitation"
VG = f"{LD}/02.vegetation/02.vegetation"
DR = f"{LD}/03.drought-20260518T233626Z-3-001/03.drought"

ALL = sorted(str(p.relative_to(ROOT)).replace(os.sep,"/")
             for p in list((ROOT/LD).rglob("*"))+list((ROOT/FF).rglob("*"))
             if p.is_file() and p.name != "desktop.ini")
SIZE = {p: (ROOT/p).stat().st_size for p in ALL}

def under(*dirs):
    return [p for p in ALL if any(p.startswith(d.rstrip("/")+"/") for d in dirs)]
def named(d, names):
    return [f"{d}/{n}" for n in names]

GRID = "기준 격자 파일"; BODY = "본체"

#: 폴더가 쓰는 짧은 이름 → **정본 주제값**. 정본은 `db/platform/schema.sql` 의
#: `d3_dataset_description.topic` CHECK 6값이다(`PLAN-SoT §9 〈55〉`·`〈359〉`).
#: ⚠ **여기서 이름을 지어내지 않는다** — CHECK 밖 값을 쓰면 core-api 가 400 을 내고
#:   `load-seed.py` 가 첫 데이터셋에서 `Abort` 한다(그 실측이 `〈357〉`).
TOPIC = {
    "강수":      "강우·강수",
    "식생":      "식생·NDVI",
    "가뭄":      "가뭄",           # ⭑ `〈359〉` 로 새로 생긴 자리
    "파일 포맷": "파일 포맷 예제",  # ⭑ 같은 회차
}


def ds(key, name, topic, summary, rnd, body, grid=(), parents=None):
    files = [{"path": p, "kind": BODY} for p in sorted(body)] + \
            [{"path": p, "kind": GRID} for p in sorted(grid)]
    d = {"key": key, "round": rnd, "name": name, "topic": TOPIC[topic],
         "summary": summary, "files": files}
    if parents: d["lineageParents"] = parents
    return d

# ── 공통 문안 ────────────────────────────────────────────────────────────────
S_PR = ("기상 레이더 합성 반사도(HSR)와 지상 15분 누적 강수(RN15). 반사도는 대기 중 강수 입자가 "
        "레이더 전파를 산란해 되돌린 세기이고, RN15 는 기상청·공공기관 관측자료에 지형효과를 "
        "반영한 3차원 객관분석 산출이다. 출처 = 기상청 API허브. 시·공간해상도 5분 / 0.5 km.")
S_VG = ("GK-2A/AMI 정규식생지수(NDVI). 식 : NDVI = (NIR − Red) / (NIR + Red), 범위 −1~1. "
        "값이 높을수록 식생이 건강하다. 출처 = 국가기상위성센터(NMSC). 원자료 LCC 좌표계 · "
        "1일 / 2 km. 대상 기간 2023-05-01 ~ 2023-05-31 · 대상지 경기 남부~충청권.")
S_DR = ("대한민국 시군구 단위 주간 SPI-4weeks · SPEI-4weeks 가뭄지수. 기상관측소 강우 관측자료로 "
        "지수를 산정하고 관측소 주소지 시군구를 대표값으로 가정해 구축했다. 생산 = 차호영(고려대학교) · "
        "WGS84 · 1 km · 2000-01-01~2025-12-31 · 주 단위.")
FMT = {
 "grib": ("GRIB", "GRIB2 격자 기상자료 판독 실습 묶음"),
 "nc":   ("NetCDF", "NetCDF4 격자 기상자료 판독 실습 묶음"),
 "bin":  ("이진(bin)", "레이더 합성자료 이진 포맷 판독 실습 묶음"),
 "tif":  ("GeoTIFF", "HLS S30 GeoTIFF 판독 실습 묶음"),
 "HDF5": ("HDF5/HDF-EOS", "MODIS HDF-EOS 판독 실습 묶음"),
}
def ff_summary(label, desc):
    return (f"{desc}. 원자료(00.Data) · 판독 코드(01.Code) · 산출(02.Results) · 그림(03.Figure) · "
            f"좌표정보(04.Lat_Lon_info) 다섯 하위 폴더로 구성된다. 파일 종류 어휘가 「{BODY}」·「{GRID}」 "
            f"둘뿐이라 이 구분은 경로로만 남는다({label}).")

# ── Variant A ────────────────────────────────────────────────────────────────
A = []
A.append(ds("LD-PRCP-LV0-HSR", "강수 — HSR 레이더 합성 반사도 (Lv.0)", "강수",
    S_PR + " Lv.0 원자료 = RDR_CMP_HSR_PUB_*.bin.gz (bin, 변량 = 반사도). "
    "＊이 데이터셋에 주제 공통 설명 문서(#readme)를 함께 싣는다.", 1,
    under(f"{PR}/Lv.0/01.HSR") + under(f"{PR}/#readme"),
    named(f"{PR}/#metadata", ["LAT_HSR.npy", "LON_HSR.npy"])))
A.append(ds("LD-PRCP-LV0-RN15", "강수 — RN15 지상 15분 누적 강수 (Lv.0)", "강수",
    S_PR + " Lv.0 원자료 = sfc_grid_rn_15m_*.nc (NetCDF4, 변량 = 15분 누적 강수량).", 1,
    under(f"{PR}/Lv.0/02.rn15"),
    named(f"{PR}/#metadata", ["LAT_RN15.npy", "LON_RN15.npy"])))
A.append(ds("LD-PRCP-LV1", "강수 — WGS84 변환·연구대상지 crop 표본 (Lv.1)", "강수",
    "Lv.0 두 원자료를 기상청 제공 lat·lon 파일에 맞춰 WGS84 로 좌표변환하고 연구대상지 중심으로 "
    "crop 한 표본. 형상 (10, 128, 128).", 2,
    named(f"{PR}/Lv.1", ["hsr_sample.npy", "rn15_sample.npy"]),
    named(f"{PR}/#metadata", ["LAT_crop.npy", "LON_crop.npy"]),
    [{"parentKey": "LD-PRCP-LV0-HSR", "origin": "manual", "parentRole": "주입력",
      "method": "WGS84 좌표변환 ＋ 연구대상지 crop"},
     {"parentKey": "LD-PRCP-LV0-RN15", "origin": "manual", "parentRole": "보조입력",
      "method": "WGS84 좌표변환 ＋ 연구대상지 crop"}]))
A.append(ds("LD-PRCP-LV2", "강수 — U-Net 강우 추정 예측장 (Lv.2)", "강수",
    "Lv.1 표본을 입력·검증자료로 학습한 U-Net 계열 딥러닝 모델의 예측 강우장. "
    "Z–R 관계식의 단일 픽셀 가정을 image-to-image 변환으로 대체한 산출. 형상 (10, 128, 128).", 3,
    named(f"{PR}/Lv.2", ["pred_sample.npy"]), [],
    [{"parentKey": "LD-PRCP-LV1", "origin": "manual", "parentRole": "주입력",
      "method": "U-Net based Model"}]))
A.append(ds("LD-VEG-LV0", "식생 — GK-2A/AMI Lv.2 식생산출물 원자료 (Lv.0)", "식생",
    S_VG + " 자료 구성 = NDVI · EVI · FVC · DQF · gk2a_imager_projection. "
    "＊이 데이터셋에 주제 공통 설명 문서(#readme)를 함께 싣는다.", 1,
    under(f"{VG}/Lv.0") + under(f"{VG}/#readme"),
    named(f"{VG}/#metadata", ["LAT.npy", "LON.npy"])))
A.append(ds("LD-VEG-LV1", "식생 — GK-2A NDVI 100 m 월평균 (Lv.1)", "식생",
    "DQF 로 저품질 픽셀을 NaN 처리하고 유효범위 −1~1 밖을 NaN 으로 바꾼 뒤, LCC→WGS84 변환 · "
    "NDVI 레이어 추출 · 경기 남부~충청권 영역 추출 · Savitzky-Golay 평활화와 선형보간 · "
    "2 km→100 m 균등분할(Uniform Distribution) · 일→월 평균을 거친 자료.", 2,
    named(f"{VG}/Lv.1", ["GK2A_NDVI_mean_202305.tif"]),
    named(f"{VG}/#metadata", ["LAT_crop.npy", "LON_crop.npy"]),
    [{"parentKey": "LD-VEG-LV0", "origin": "manual", "parentRole": "주입력",
      "method": "DQF 품질필터 → LCC→WGS84 → ROI 추출 → SG 평활·선형보간 → 100 m 균등분할 → 월평균"}]))
A.append(ds("LD-VEG-LV1-MODELIN", "식생 — Lv.2 모델 보조입력·검증자료 (Lv.1 형제)", "식생",
    "Lv.2 딥러닝 모델의 보조입력(수치표고모형 DEM 100 m · 경사향 Aspect 100 m · "
    "연 단위 토지피복지도 LULC 100 m)과 검증자료(월 단위 HLS S30 NDVI 100 m). "
    "＊이 묶음은 Lv.1 에서 파생되지 않는다 — 별개 원천에서 온 자료라 Lv.1 의 자식이 아니라 형제이고, "
    "Lv.2 에 대해서만 보조입력 부모가 된다(#readme 「[2] 메인 처리 프로세스 — NDVI · Lv.2 · 학습 시 활용 자료」).", 2,
    under(f"{VG}/Lv.1_(Model_Input_Data)")))
A.append(ds("LD-VEG-LV2", "식생 — U-Net NDVI 예측장 (Lv.2)", "식생",
    "월 단위 GK-2A NDVI(Lv.1)를 주입력으로, DEM·경사향·토지피복을 보조입력으로, "
    "월 단위 HLS NDVI 를 검증자료로 학습한 U-Net 계열 모델의 일별 예측 NDVI(Prediction_yyyymmdd.npy).", 3,
    under(f"{VG}/Lv.2"), [],
    [{"parentKey": "LD-VEG-LV1", "origin": "manual", "parentRole": "주입력",
      "method": "U-Net based Model"},
     {"parentKey": "LD-VEG-LV1-MODELIN", "origin": "manual", "parentRole": "보조입력",
      "method": "U-Net based Model"}]))
A.append(ds("LD-DRGH-LV1", "가뭄 — 시군구 주간 SPI/SPEI-4weeks (Lv.1)", "가뭄",
    S_DR + " Data Level = L1 Calibrated. ＊이 주제에는 Lv.0·Lv.2 폴더가 없다 — 계보 간선 0건. "
    "설명 문서(#readme, 여는 코드 ipynb 포함)를 함께 싣는다.", 2,
    under(f"{DR}/Lv.1") + under(f"{DR}/#readme")))

FF_GRID = {
 "1_grib": ["lat2d.npy", "lon2d.npy"],
 "2_nc":   ["lat2d.npy", "lon2d.npy"],
 "3_bin":  ["Lat_HSR.npy", "Lon_HSR.npy"],
 "4_tif":  ["HLS.S30.T51SYB.2025359T023019.v2.0_lat2d.npy",
            "HLS.S30.T51SYB.2025359T023019.v2.0_lon2d.npy"],
 "5_HDF5": ["lat2d_h27v05.npy", "lon2d_h27v05.npy"],
}
FF_DS = []
for slug, gnames in FF_GRID.items():
    fmt = slug.split("_", 1)[1]
    label, desc = FMT[fmt]
    d = f"{FF}/file_format_{slug}"
    grid = named(f"{d}/04.Lat_Lon_info", gnames)
    body = [p for p in under(d) if p not in set(grid)]
    extra = ""
    if slug in ("4_tif", "5_HDF5"):
        extra = ("  ⚠ 04.Lat_Lon_info 에 위·경도 쌍이 2벌 있으나 데이터셋당 기준 격자 파일 상한이 "
                 "2건(〈58〉)이라 한 벌만 격자로 싣고 나머지는 「본체」로 실었다.")
    FF_DS.append(ds(f"FF-{fmt.upper()}", f"파일 포맷 실습 — {label}", "파일 포맷",
                    ff_summary(label, desc) + extra, 4, body, grid))
A += FF_DS

# ── Variant B ────────────────────────────────────────────────────────────────
B = []
B.append(ds("TP-PRCP", "강수 — 레이더 반사도·지상 강수 전 레벨 (Lv.0~Lv.2)", "강수",
    S_PR + " Lv.0(HSR bin · RN15 nc) · Lv.1(WGS84 변환·crop 표본) · Lv.2(U-Net 예측장) 및 "
    "#metadata·#readme 를 한 데이터셋에 담는다. 레벨 구분은 경로에만 남는다 — 계보 간선 0건.", 1,
    [p for p in under(PR) if not p.endswith(("#metadata/LAT_HSR.npy", "#metadata/LON_HSR.npy"))],
    named(f"{PR}/#metadata", ["LAT_HSR.npy", "LON_HSR.npy"])))
B.append(ds("TP-VEG", "식생 — GK-2A NDVI 전 레벨 (Lv.0~Lv.2)", "식생",
    S_VG + " Lv.0(GK-2A/AMI nc 원자료) · Lv.1(100 m 월평균 tif) · Lv.1_(Model_Input_Data)"
    "(DEM·Aspect·LULC·HLS) · Lv.2(U-Net 예측장) 및 #metadata·#readme 를 한 데이터셋에 담는다. "
    "레벨 구분은 경로에만 남는다 — 계보 간선 0건.", 1,
    [p for p in under(VG) if not p.endswith(("#metadata/LAT.npy", "#metadata/LON.npy"))],
    named(f"{VG}/#metadata", ["LAT.npy", "LON.npy"])))
B.append(ds("TP-DRGH", "가뭄 — 시군구 주간 SPI/SPEI-4weeks", "가뭄",
    S_DR + " Lv.1 자료와 #readme(여는 코드 ipynb 포함)를 한 데이터셋에 담는다. 계보 간선 0건.", 1,
    under(DR)))
for d in FF_DS:
    B.append({k: v for k, v in d.items() if k != "lineageParents"})

# ── 검증 ─────────────────────────────────────────────────────────────────────
def validate(name, datasets):
    seen = collections.Counter()
    for d in datasets:
        for f in d["files"]:
            seen[f["path"]] += 1
            assert (ROOT / f["path"]).is_file(), f"{name}: 실물 없음 {f['path']}"
            assert f["path"].startswith((LD + "/", FF + "/")), f"{name}: 루트 밖 {f['path']}"
    dup = [p for p, c in seen.items() if c > 1]
    missing = [p for p in ALL if p not in seen]
    assert not dup, f"{name}: 중복 {dup[:5]}"
    assert not missing, f"{name}: 누락 {len(missing)} {missing[:5]}"
    for d in datasets:
        g = sum(1 for f in d["files"] if f["kind"] == GRID)
        assert g <= 2, f"{name}/{d['key']}: 격자 {g} > 2"
        assert len(d["files"]) <= 500, f"{name}/{d['key']}: 파일 {len(d['files'])} > 500"
    keys = {d["key"] for d in datasets}
    order = []
    for d in datasets:
        for p in d.get("lineageParents", []):
            assert p["parentKey"] in keys, f"{name}: 미지의 부모 {p['parentKey']}"
            assert p["parentKey"] in order, f"{name}: 부모가 뒤에 있다 {p['parentKey']}"
        order.append(d["key"])
    return sum(seen.values()), sum(SIZE[p] for p in seen)

def write(tag, datasets, note):
    n, b = validate(tag, datasets)
    doc = {
      "_설명": [
        f"CoLAB v2 dev 초기 적재 매니페스트 — 안 {tag}. 소비처 = infra/staging/load-seed.py 의 --manifest.",
        "path 는 --source-root 기준 상대. source-root = '03 Reference-Data'.",
        "적재 범위 = 01.level-data/ ＋ 02.File-format/ 전량. 제외 = 03_KWRA_conference-* 전체 · 전 desktop.ini(50건).",
        "kind 어휘는 contracts/schemas/common.json:78-82 FileKind 의 두 값뿐이다 — '본체'·'기준 격자 파일'.",
        note,
      ],
      "_계수": {"데이터셋": len(datasets), "파일": n, "바이트": b,
                "계보간선": sum(len(d.get("lineageParents", [])) for d in datasets)},
      "datasets": datasets,
    }
    target = OUT / ("manifest-refdata.json" if tag == "A" else f"manifest-refdata-{tag}.json")
    body = json.dumps(doc, ensure_ascii=False, indent=2) + "\n"
    if CHECK_ONLY:
        if tag == "A":
            have = target.read_text(encoding="utf-8") if target.exists() else ""
            print(f"[check] {target.name} — {'일치' if have == body else '⛔ 불일치'}")
        return n, b
    target.write_text(body, encoding="utf-8")
    return n, b

na, ba = write("A", A, "계보 = Lv.0 → Lv.1 → Lv.2. Lv.1_(Model_Input_Data) 는 Lv.1 의 형제이고 Lv.2 의 보조입력 부모다.")
nb, bb = write("B", B, "주제 3 ＋ 포맷 5 = 8 데이터셋. 레벨·하위폴더는 경로로만 표현하고 계보 간선을 싣지 않는다.")

# ── summary md ───────────────────────────────────────────────────────────────
def srcdir(d):
    ps = [f["path"] for f in d["files"]]
    return os.path.commonpath(ps).replace(os.sep, "/") if len(set(os.path.dirname(p) for p in ps)) > 1 \
           else os.path.dirname(ps[0])
def table(tag, datasets):
    L = [f"# 적재 매니페스트 안 {tag} — 요약", "",
         f"- 데이터셋 **{len(datasets)}** · 파일 **{sum(len(d['files']) for d in datasets)}** "
         f"· 바이트 **{sum(SIZE[f['path']] for d in datasets for f in d['files']):,}**",
         f"- 계보 간선 **{sum(len(d.get('lineageParents', [])) for d in datasets)}**", "",
         "| key | 이름 | 원천 폴더 | 파일 | 바이트 | kind | 계보 |",
         "|---|---|---|---|---|---|---|"]
    for d in datasets:
        kc = collections.Counter(f["kind"] for f in d["files"])
        kinds = " · ".join(f"{k} {v}" for k, v in sorted(kc.items()))
        lin = "—" if not d.get("lineageParents") else " ／ ".join(
            f"{p['parentKey']}({p.get('parentRole','')})" for p in d["lineageParents"])
        L.append(f"| `{d['key']}` | {d['name']} | `{srcdir(d)}/` | {len(d['files'])} | "
                 f"{sum(SIZE[f['path']] for f in d['files']):,} | {kinds} | {lin} |")
    return "\n".join(L) + "\n"
if not CHECK_ONLY:
    (OUT / "summary-A.md").write_text(table("A", A), encoding="utf-8")
    (OUT / "summary-B.md").write_text(table("B", B), encoding="utf-8")

print(f"OK  A: {len(A)} 데이터셋 / {na} 파일 / {ba:,} B")
print(f"OK  B: {len(B)} 데이터셋 / {nb} 파일 / {bb:,} B")
print(f"실물 전수: {len(ALL)} 파일 / {sum(SIZE.values()):,} B")
