# 강수(precipitation) 데이터셋 정본

- 출처 문서: `#readme/#processing_description_Precipitation.docx` · `#readme/자료설명.pptx` · 추출일 2026-09-14 · 상태: 확정 — Ted 판정 2026-09-14
- 유형 폴더: `01.level-data/01.precipitation/`(참조자료 뿌리 기준 · 이 문서가 놓이는 자리) — 아래 글롭은 전부 이 문서 폴더 기준 상대경로이고 안쪽 `01.precipitation/` 을 포함한다
- 표기 대응: 폴더 `Lv.N` ↔ 제품 값 `LvN` (제품 값 집합 `Lv0`~`Lv3` · `db/platform/schema.sql` CHECK)
- 프로젝트: precipitation · 설명: HSR 레이더 반사도와 rn15 지상강수를 좌표변환·crop 한 뒤 U-Net 예측까지 잇는 강수 3단 자료. Lv.0 2갈래 → Lv.1 2갈래 → Lv.2 예측 1건.
- 계수 기준: 파일 건수·바이트 = `glob` 매칭 후 `desktop.ini` 제외 · 2026-09-14 실측

## 데이터셋 표

| # | 이름 | 레벨 | 부모 | 파일 글롭 | 건수 | 바이트 | 기준 격자(쌍) | 포맷 | 미리보기 기대 | 비고 |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | HSR 레이더 반사도 원자료 | Lv0 | — | `01.precipitation/Lv.0/01.HSR/RDR_CMP_HSR_PUB_*.bin.gz` | 10 | 16,998,652 | `01.precipitation/#metadata/LAT_HSR.npy`·`LON_HSR.npy` | bin(gzip) | 미측정(판정 5종 밖) | 등록됨 · 프로젝트 미연결 |
| 2 | rn15 15분 누적강수 | Lv0 | — | `01.precipitation/Lv.0/02.rn15/sfc_grid_rn_15m_*.nc` | 10 | 1,247,581 | `01.precipitation/#metadata/LAT_RN15.npy`·`LON_RN15.npy` | NetCDF4 | 미측정 | 등록됨 |
| 3 | hsr_sample | Lv1 | HSR 레이더 반사도 원자료 | `01.precipitation/Lv.1/hsr_sample.npy` | 1 | 655,488 | `01.precipitation/#metadata/LAT_crop.npy`·`LON_crop.npy` | npy | 미측정 | 등록됨 |
| 4 | rn15_sample | Lv1 | rn15 15분 누적강수 | `01.precipitation/Lv.1/rn15_sample.npy` | 1 | 655,488 | `01.precipitation/#metadata/LAT_crop.npy`·`LON_crop.npy` | npy | 미측정 | 등록됨 |
| 5 | pred_sample | Lv2 | hsr_sample · rn15_sample | `01.precipitation/Lv.2/pred_sample.npy` | 1 | 655,488 | `01.precipitation/#metadata/LAT_crop.npy`·`LON_crop.npy` | npy | 미측정 | 등록됨 |

- 데이터셋 5 · 계보 간선 4 · 자료 바이트 20,212,697
- 기준 격자 파일 바이트 — `LAT_HSR`·`LON_HSR` 각 26,562,948 · `LAT_RN15`·`LON_RN15` 각 16,793,732 · `LAT_crop`·`LON_crop` 각 131,200

## 데이터셋 상세

### HSR 레이더 반사도 원자료

- 레벨: Lv0(폴더 `Lv.0`) — 출처 문장 축자 「Lv.0 자료명 RDR_CMP_HSR_PUB_201907281430.bin.gz」
- 부모: 없음 — 출처 문서에 상위 자료 문장 부재(원자료 블록)
- 파일: `01.precipitation/Lv.0/01.HSR/RDR_CMP_HSR_PUB_*.bin.gz` · 10건 · 16,998,652 B · 시각 10점 `201907281430`·`202005151115`·`202007221045`·`202106031430`·`202107031745`·`202207110415`·`202208100500`·`202307140830`·`202405151930`·`202407091315`(연속 계열 아님 · 출처 축자 「자료 전달 기간: test dataset 중 일부 샘플」)
- 격자: 파일 2건 `01.precipitation/#metadata/LAT_HSR.npy`·`01.precipitation/#metadata/LON_HSR.npy` · 근거 = 출처 축자 「기상청에서 제공하는 각각의 lat, lon 파일에 맞추어 WGS84로 좌표계 변환」 ＋ HSR 은 헤더에 투영 파라미터가 없어 격자 파일이 필요(`dev-package/DATA-REFERENCE.md §1.1`)
- 설명: 기상청 API허브가 제공하는 HSR 합성 반사도 원자료. 시/공간해상도 5분 / 0.5 km, 변량은 반사도. 정해진 규칙에 맞추어 원자료를 꺼내오는 이진 파일 형식이다.
- 비고: 오늘 실측 — 등록됨(파일 10건 · 화면 접수 70,124,548 B). **프로젝트에 연결되지 않았다**(`dev-package/sessions/DR-3-run-2026-09-13.md §4`). 미리보기 판정 5종에 들지 않아 렌더 미측정.

### rn15 15분 누적강수

- 레벨: Lv0(폴더 `Lv.0`) — 출처 문장 축자 「Lv.0 자료명 sfc_grid_rn_15m_201907281430.nc」
- 부모: 없음 — 출처 문서에 상위 자료 문장 부재(원자료 블록)
- 파일: `01.precipitation/Lv.0/02.rn15/sfc_grid_rn_15m_*.nc` · 10건 · 1,247,581 B · 시각은 HSR 과 같은 10점
- 격자: 파일 2건 `01.precipitation/#metadata/LAT_RN15.npy`·`01.precipitation/#metadata/LON_RN15.npy` · 근거 = HSR 과 다른 형상의 별도 쌍이 `#metadata` 에 존재(실측 각 16,793,732 B)
- 설명: 기상청 API허브가 제공하는 지상 격자 15분 누적강수. 관측자료에 지형효과를 반영한 3차원 객관분석 기법으로 생산한 분석자료이며, 이 중 15분 누적 강수를 사용한다.
- 비고: 오늘 실측 — 등록됨(10건 · 화면 접수 34,835,045 B). 렌더 미측정.

### hsr_sample

- 레벨: Lv1(폴더 `Lv.1`) — 출처 문장 축자 「Lv.1 자료명 hsr_sample.npy rn15_sample.npy」
- 부모: HSR 레이더 반사도 원자료 — 출처 문장 축자 「입력자료 hsr_sample.npy」(Lv.2 블록에서 hsr 계열임을 지시) · ⚠ 출처 문서는 Lv.1 블록에 두 파일을 함께 적고 각 파일의 Lv.0 대응을 문장으로 쓰지 않는다. `hsr_sample ← HSR` 대응은 `[추론]`(이름 대응)
- 파일: `01.precipitation/Lv.1/hsr_sample.npy` · 1건 · 655,488 B · 형태 (10, 128, 128) = 시각 10 × 격자 128 × 128
- 격자: 파일 2건 `01.precipitation/#metadata/LAT_crop.npy`·`01.precipitation/#metadata/LON_crop.npy` · 근거 = 출처 축자 「lat, lon 정보 첨부해두었음」 ＋ crop 후 형상에 맞는 쌍이 `#metadata` 에 존재(각 131,200 B)
- 설명: HSR 반사도를 기상청 제공 lat·lon 파일에 맞추어 WGS84 로 좌표계 변환하고, 특정 연구대상지를 중심으로 crop 한 전처리 자료. 형태는 (10, 128, 128).
- 비고: 오늘 실측 — 등록됨(1건 · 화면 접수 917,888 B). 렌더 미측정.

### rn15_sample

- 레벨: Lv1(폴더 `Lv.1`) — 출처 문장 축자 「Lv.1 자료명 hsr_sample.npy rn15_sample.npy」
- 부모: rn15 15분 누적강수 — 대응은 `[추론]`(이름 대응 · 위 항목과 같은 사유)
- 파일: `01.precipitation/Lv.1/rn15_sample.npy` · 1건 · 655,488 B · 형태 (10, 128, 128)
- 격자: 파일 2건 `01.precipitation/#metadata/LAT_crop.npy`·`01.precipitation/#metadata/LON_crop.npy` · 근거 = hsr_sample 과 동일 ROI·동일 형상
- 설명: rn15 15분 누적강수를 기상청 제공 lat·lon 파일에 맞추어 WGS84 로 좌표계 변환하고 연구대상지를 중심으로 crop 한 전처리 자료. 형태는 (10, 128, 128).
- 비고: 오늘 실측 — 등록됨(1건 · 화면 접수 917,888 B). 렌더 미측정.

### pred_sample

- 레벨: Lv2(폴더 `Lv.2`) — 출처 문장 축자 「Lv.2 자료명 pred_sample.npy」
- 부모: hsr_sample · rn15_sample — 출처 문장 축자 「입력자료 hsr_sample.npy」 · 「검증자료 rn15_sample.npy」
- 파일: `01.precipitation/Lv.2/pred_sample.npy` · 1건 · 655,488 B · 형태 (10, 128, 128)
- 격자: 파일 2건 `01.precipitation/#metadata/LAT_crop.npy`·`01.precipitation/#metadata/LON_crop.npy` · 근거 = Lv.1 과 같은 crop ROI
- 설명: 레이더 반사도 격자를 입력으로 받아 같은 격자의 강우 분포를 출력하는 U-Net 기반 모델의 예측 결과. 입력은 hsr_sample.npy, 검증은 rn15_sample.npy 다.
- 비고: 오늘 실측 — 등록됨(1건 · 화면 접수 917,888 B). 렌더 미측정.

## 판정 기록 (Ted 확정 2026-09-14)

㈎ **Lv.1 두 건의 부모 대응이 출처 문장으로 닫히지 않는다.** 출처 문서는 Lv.1 블록 하나에 `hsr_sample.npy`·`rn15_sample.npy` 를 함께 적고 각 파일이 어느 Lv.0 에서 나왔는지를 문장으로 쓰지 않는다. 현재 등록은 이름 대응(`hsr_sample ← HSR` · `rn15_sample ← rn15`)으로 간선 2건을 세웠다. ⓐ 이름 대응을 정본으로 확정 / ⓑ 생산자에게 문장 보강을 요청.

→ 확정: ⓐ 이름 대응을 정본으로 채택 — `hsr_sample` ← `HSR 레이더 반사도 원자료` · `rn15_sample` ← `rn15 15분 누적강수`. 간선 2건 유지 · 생산자 문장 보강 요청은 비차단 후속.

㈏ **원자료 2건의 시각 10점이 연속 계열이 아니다.** 출처 축자 「test dataset 중 일부 샘플」이고 2019~2024 에 흩어져 있다. 화면 목록·미리보기에서 시간축을 어떻게 보일지의 기대값이 정해져 있지 않다. ⓐ 그대로 둔다 / ⓑ 설명 칸에 「연속 계열 아님」을 명시한다(현재 초안은 ⓑ).

→ 확정: ⓑ 설명 칸 명시를 유지 — 표·상세의 「연속 계열 아님」 문구를 정본으로 둔다. 시간축 화면 기대값 변경은 없음.

㈐ **강수 프로젝트는 미리보기 렌더 판정 대상 5종에 들지 않는다.** grib·nc·bin·tif·hdf4 만 판정했고 강수 4종(bin(gzip)·NetCDF4·npy)의 화면 렌더는 측정하지 않았다 `[미확인]`. ⓐ 판정 대상에 넣는다 / ⓑ 포멧테스트 프로젝트의 같은 포맷 결과로 갈음한다.

→ 확정: ⓐ 전건을 판정 대상으로 둔다 — `WU-C4` 의 verify 단계가 데이터셋 28건 각각을 판정한다. 포멧테스트 결과로 갈음하지 않는다.

## 참조

- 출처 문서: `#readme/#processing_description_Precipitation.docx` · `#readme/자료설명.pptx`(U-Net 입력·목표·결과 3단 도식)
- 재고 조사: `dev-package/reports/reference-data/2026-09-13-inventory-v2.md` §4-1 · §5-1
- 오늘 등록 실측: `dev-package/sessions/DR-3-run-2026-09-13.md` §1 순번 1~5 · §4
- 기계 등재표: `dev-package/tools/dev-seed/plan-manifest.yaml` seq 1~5

## 기계 블록 (생성기 입력)

```yaml
# colab-datasets v1 — 이 블록이 생성기의 입력이다. 표와 어긋나면 생성기가 비영 종료한다.
# `summary` = 러너가 화면에 그대로 치는 한 줄. `description`·`note` = 문서 요약(생성기 미출력).
project: precipitation
project_name: "precipitation"
project_description: "HSR 레이더 반사도와 rn15 지상강수를 좌표변환·crop 한 뒤 U-Net 예측까지 잇는 강수 3단 자료. Lv.0 2갈래 → Lv.1 2갈래 → Lv.2 예측 1건."
folder: 01.level-data/01.precipitation   # 참조자료 뿌리 기준 · 아래 files/grid_files 는 이 폴더 기준
datasets:
  - seq: 1
    name: "HSR 레이더 반사도 원자료"
    level: Lv0
    parents: []
    summary: "기상청 HSR 합성 반사도 원본"
    files: ["01.precipitation/Lv.0/01.HSR/RDR_CMP_HSR_PUB_*.bin.gz"]
    file_count: 10
    bytes: 16998652
    grid_files: ["01.precipitation/#metadata/LAT_HSR.npy", "01.precipitation/#metadata/LON_HSR.npy"]
    format: "bin(gzip)"
    preview_expected: "미측정(판정 5종 밖)"
    description: "기상청 API허브가 제공하는 HSR 합성 반사도 원자료. 시/공간해상도 5분 / 0.5 km, 변량은 반사도. 정해진 규칙에 맞추어 원자료를 꺼내오는 이진 파일 형식이다."
    note: "오늘 실측 — 등록됨(파일 10건 · 화면 접수 70,124,548 B). **프로젝트에 연결되지 않았다**(`dev-package/sessions/DR-3-run-2026-09-13.md §4`). 미리보기 판정 5종에 들지 않아 렌더 미측정."
  - seq: 2
    name: "rn15 15분 누적강수"
    level: Lv0
    parents: []
    summary: "지상 격자 15분 누적강수 원본"
    files: ["01.precipitation/Lv.0/02.rn15/sfc_grid_rn_15m_*.nc"]
    file_count: 10
    bytes: 1247581
    grid_files: ["01.precipitation/#metadata/LAT_RN15.npy", "01.precipitation/#metadata/LON_RN15.npy"]
    format: "NetCDF4"
    preview_expected: "미측정"
    description: "기상청 API허브가 제공하는 지상 격자 15분 누적강수. 관측자료에 지형효과를 반영한 3차원 객관분석 기법으로 생산한 분석자료이며, 이 중 15분 누적 강수를 사용한다."
    note: "오늘 실측 — 등록됨(10건 · 화면 접수 34,835,045 B). 렌더 미측정."
  - seq: 3
    name: "hsr_sample"
    level: Lv1
    parents: ["HSR 레이더 반사도 원자료"]
    summary: "WGS84 변환·crop 한 HSR 전처리 자료"
    files: ["01.precipitation/Lv.1/hsr_sample.npy"]
    file_count: 1
    bytes: 655488
    grid_files: ["01.precipitation/#metadata/LAT_crop.npy", "01.precipitation/#metadata/LON_crop.npy"]
    format: "npy"
    preview_expected: "미측정"
    description: "HSR 반사도를 기상청 제공 lat·lon 파일에 맞추어 WGS84 로 좌표계 변환하고, 특정 연구대상지를 중심으로 crop 한 전처리 자료. 형태는 (10, 128, 128)."
    note: "오늘 실측 — 등록됨(1건 · 화면 접수 917,888 B). 렌더 미측정."
  - seq: 4
    name: "rn15_sample"
    level: Lv1
    parents: ["rn15 15분 누적강수"]
    summary: "WGS84 변환·crop 한 rn15 전처리 자료"
    files: ["01.precipitation/Lv.1/rn15_sample.npy"]
    file_count: 1
    bytes: 655488
    grid_files: ["01.precipitation/#metadata/LAT_crop.npy", "01.precipitation/#metadata/LON_crop.npy"]
    format: "npy"
    preview_expected: "미측정"
    description: "rn15 15분 누적강수를 기상청 제공 lat·lon 파일에 맞추어 WGS84 로 좌표계 변환하고 연구대상지를 중심으로 crop 한 전처리 자료. 형태는 (10, 128, 128)."
    note: "오늘 실측 — 등록됨(1건 · 화면 접수 917,888 B). 렌더 미측정."
  - seq: 5
    name: "pred_sample"
    level: Lv2
    parents: ["hsr_sample", "rn15_sample"]
    summary: "U-Net 기반 강수 예측 결과"
    files: ["01.precipitation/Lv.2/pred_sample.npy"]
    file_count: 1
    bytes: 655488
    grid_files: ["01.precipitation/#metadata/LAT_crop.npy", "01.precipitation/#metadata/LON_crop.npy"]
    format: "npy"
    preview_expected: "미측정"
    description: "레이더 반사도 격자를 입력으로 받아 같은 격자의 강우 분포를 출력하는 U-Net 기반 모델의 예측 결과. 입력은 hsr_sample.npy, 검증은 rn15_sample.npy 다."
    note: "오늘 실측 — 등록됨(1건 · 화면 접수 917,888 B). 렌더 미측정."
```
