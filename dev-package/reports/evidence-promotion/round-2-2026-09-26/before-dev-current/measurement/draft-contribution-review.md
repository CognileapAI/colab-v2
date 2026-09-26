# 초안 사실 검토 표 — 2회차 지역 (2026-09-26)

생성: `eval/k4-search/measure_draft_contribution.py` · 정본 intent `dev-package/intent/2026-09-21-evidence-promotion.md` · **기계는 제안만 한다. 판정은 Ted.**

## 입력

- payload `dev-package/reports/evidence-promotion/round-1-2026-09-26/promotion-plan/promoted-payload.json` sha256 `41f488a42ffb07c1c64d4460ea86a6b98c72b63494ec45291f72f5c73561c6fc` · 생성기 재생성 대조: 측정 칸 동일 = False · 그 밖의 칸 차이 27건
- 일회용 DB 시드: 데이터셋 28 · 본체 543 · 계보 18 · 적재 보고 evidence 543 · topic 3 · source_label 9 · draft_withheld 57
- `golden-cases.json` sha256 `ef5227126c801b1a7f527d6292456ffc146c3253c87e3e066845158818497c31`
- `practitioner-conditions.json` sha256 `8ccb477bc9a1d34201cfa0cd0502dc6253bf3b346e0cbab0df2d1dfcc0f14012`
- `heldout-cases.json` sha256 `a4f3f6a1dcc98cbd7783eedbe5db23c97e495420226393d16118ddd11ddcb736`
- `interpret-fixture.json` sha256 `2e4d4a9cfff66ac58f5bca162e16b3a4a0dc345b19db3f7e91f0445f8ad6d89f`
- `dev-data-snapshot-v2.json` sha256 `171ddd497a41a414eb37be31d394f9c97f6c1b0c330de76648a733a4cfafb952`
- DB 지문 전 543행 `b8d4ecc6f6c51edd…` · 후 543행 `b8d4ecc6f6c51edd…` → **남은 변경 0**
- 평가 62회 · 모델 호출 0회 · 경로 2 해석 = `interpret-fixture.json`(규칙 기반 녹화, LLM 아님)

## 기준선 (green 케이스 수)

| 케이스군 | 케이스 | 초안 전부 포함 | 초안 전부 제외 |
|---|---:|---:|---:|
| 경로 1 (결정 근거) | 33 | 28 | 28 |
| 경로 2 (결정 근거) | 10 | 9 | 9 |
| heldout 경로 1 (사후 확인) | 0 | 0 | 0 |
| heldout 경로 2 (사후 확인) | 6 | 4 | 3 |

## 규칙 단위 (결정 5)

형식: green 포함→제외 · 기여 · 역전 · 측정 여부

| 규칙 | 초안 | 경로 1 | 경로 2 | heldout 1/2 뒤집힘(사후 확인) | 제안 |
|---|---:|---|---|---|---|
| `platform-from-instrument` | 0 | 28→28 · 기여 0 · 역전 0 · 미측정(초안 0건) | 9→9 · 기여 0 · 역전 0 · 미측정(초안 0건) | 0/0 기여 · 0/0 역전 | 미측정 — 초안 0건 |
| `representation-from-shape` | 28 | 28→28 · 기여 0 · 역전 0 · 미측정(케이스 0) | 9→9 · 기여 0 · 역전 0 · 미측정(술어 없음) | 0/0 기여 · 0/0 역전 | 미측정 · 보류 |
| `direct-observation-from-level` | 0 | 28→28 · 기여 0 · 역전 0 · 미측정(초안 0건) | 9→9 · 기여 0 · 역전 0 · 미측정(초안 0건) | 0/0 기여 · 0/0 역전 | 미측정 — 초안 0건 |
| `interpolated-from-lineage` | 28 | 28→28 · 기여 0 · 역전 0 · 미측정(술어 없음) | 9→9 · 기여 0 · 역전 0 · 미측정(케이스 0) | 0/1 기여 · 0/0 역전 | 미측정(경로 1)·보류 — 결정 5 고정 |
| `bbox-korea-peninsula` | 0 | 28→28 · 기여 0 · 역전 0 · 미측정(초안 0건) | 9→9 · 기여 0 · 역전 0 · 미측정(초안 0건) | 0/0 기여 · 0/0 역전 | 미측정 — 초안 0건 |
| `native-resolution-carried` | 0 | 28→28 · 기여 0 · 역전 0 · 미측정(초안 0건) | 9→9 · 기여 0 · 역전 0 · 미측정(초안 0건) | 0/0 기여 · 0/0 역전 | 미측정 — 초안 0건 |
| `region-from-registration-note` | 1 | 28→28 · 기여 0 · 역전 0 · 측정(5케이스) | 9→9 · 기여 0 · 역전 0 · 측정(4케이스) | 0/0 기여 · 0/0 역전 | 보류 — 기여 0 |

뒤집힌 케이스:

- `interpolated-from-lineage` — heldout_B 기여 ['N23'] · 역전 []

## 사실 단위 (110칸)

| 사실 | 값 | 규칙 | 경로 1 | 경로 2 | 제안 |
|---|---|---|---|---|---|
| `seq01.representation` HSR 레이더 반사도 원자료 | `"spatial_grid"` | `representation-from-shape` | 28→28 · 기여 0 · 역전 0 · 미측정(케이스 0) | 9→9 · 기여 0 · 역전 0 · 미측정(술어 없음) | 미측정 — 폐기하지 않는다(결정 3: 케이스 0건은 폐기 제안 대상 아님) |
| `seq01.interpolated` HSR 레이더 반사도 원자료 | `false` | `interpolated-from-lineage` | 28→28 · 기여 0 · 역전 0 · 미측정(술어 없음) | 9→9 · 기여 0 · 역전 0 · 미측정(케이스 0) | 미측정 — 폐기하지 않는다(결정 3: 케이스 0건은 폐기 제안 대상 아님) |
| `seq02.representation` rn15 15분 누적강수 | `"spatial_grid"` | `representation-from-shape` | 28→28 · 기여 0 · 역전 0 · 미측정(케이스 0) | 9→9 · 기여 0 · 역전 0 · 미측정(술어 없음) | 미측정 — 폐기하지 않는다(결정 3: 케이스 0건은 폐기 제안 대상 아님) |
| `seq02.interpolated` rn15 15분 누적강수 | `false` | `interpolated-from-lineage` | 28→28 · 기여 0 · 역전 0 · 미측정(술어 없음) | 9→9 · 기여 0 · 역전 0 · 미측정(케이스 0) | 미측정 — 폐기하지 않는다(결정 3: 케이스 0건은 폐기 제안 대상 아님) |
| `seq03.representation` hsr_sample | `"spatial_grid"` | `representation-from-shape` | 28→28 · 기여 0 · 역전 0 · 미측정(케이스 0) | 9→9 · 기여 0 · 역전 0 · 미측정(술어 없음) | 미측정 — 폐기하지 않는다(결정 3: 케이스 0건은 폐기 제안 대상 아님) |
| `seq03.interpolated` hsr_sample | `true` | `interpolated-from-lineage` | 28→28 · 기여 0 · 역전 0 · 미측정(술어 없음) | 9→9 · 기여 0 · 역전 0 · 미측정(케이스 0) | 미측정 — 폐기하지 않는다(결정 3: 케이스 0건은 폐기 제안 대상 아님) |
| `seq04.representation` rn15_sample | `"spatial_grid"` | `representation-from-shape` | 28→28 · 기여 0 · 역전 0 · 미측정(케이스 0) | 9→9 · 기여 0 · 역전 0 · 미측정(술어 없음) | 미측정 — 폐기하지 않는다(결정 3: 케이스 0건은 폐기 제안 대상 아님) |
| `seq04.interpolated` rn15_sample | `true` | `interpolated-from-lineage` | 28→28 · 기여 0 · 역전 0 · 미측정(술어 없음) | 9→9 · 기여 0 · 역전 0 · 미측정(케이스 0) | 미측정 — 폐기하지 않는다(결정 3: 케이스 0건은 폐기 제안 대상 아님) |
| `seq05.representation` pred_sample | `"spatial_grid"` | `representation-from-shape` | 28→28 · 기여 0 · 역전 0 · 미측정(케이스 0) | 9→9 · 기여 0 · 역전 0 · 미측정(술어 없음) | 미측정 — 폐기하지 않는다(결정 3: 케이스 0건은 폐기 제안 대상 아님) |
| `seq05.interpolated` pred_sample | `true` | `interpolated-from-lineage` | 28→28 · 기여 0 · 역전 0 · 미측정(술어 없음) | 9→9 · 기여 0 · 역전 0 · 미측정(케이스 0) | 미측정 — 폐기하지 않는다(결정 3: 케이스 0건은 폐기 제안 대상 아님) |
| `seq06.representation` GK-2A 일 단위 식생자료 | `"spatial_grid"` | `representation-from-shape` | 28→28 · 기여 0 · 역전 0 · 미측정(케이스 0) | 9→9 · 기여 0 · 역전 0 · 미측정(술어 없음) | 미측정 — 폐기하지 않는다(결정 3: 케이스 0건은 폐기 제안 대상 아님) |
| `seq06.interpolated` GK-2A 일 단위 식생자료 | `false` | `interpolated-from-lineage` | 28→28 · 기여 0 · 역전 0 · 미측정(술어 없음) | 9→9 · 기여 0 · 역전 0 · 미측정(케이스 0) | 미측정 — 폐기하지 않는다(결정 3: 케이스 0건은 폐기 제안 대상 아님) |
| `seq07.representation` GK2A_NDVI_mean_202305 | `"spatial_grid"` | `representation-from-shape` | 28→28 · 기여 0 · 역전 0 · 미측정(케이스 0) | 9→9 · 기여 0 · 역전 0 · 미측정(술어 없음) | 미측정 — 폐기하지 않는다(결정 3: 케이스 0건은 폐기 제안 대상 아님) |
| `seq07.interpolated` GK2A_NDVI_mean_202305 | `true` | `interpolated-from-lineage` | 28→28 · 기여 0 · 역전 0 · 미측정(술어 없음) | 9→9 · 기여 0 · 역전 0 · 미측정(케이스 0) | 미측정 — 폐기하지 않는다(결정 3: 케이스 0건은 폐기 제안 대상 아님) |
| `seq08.representation` HLS_S30_NDVI_mean_202305 | `"spatial_grid"` | `representation-from-shape` | 28→28 · 기여 0 · 역전 0 · 미측정(케이스 0) | 9→9 · 기여 0 · 역전 0 · 미측정(술어 없음) | 미측정 — 폐기하지 않는다(결정 3: 케이스 0건은 폐기 제안 대상 아님) |
| `seq08.interpolated` HLS_S30_NDVI_mean_202305 | `true` | `interpolated-from-lineage` | 28→28 · 기여 0 · 역전 0 · 미측정(술어 없음) | 9→9 · 기여 0 · 역전 0 · 미측정(케이스 0) | 미측정 — 폐기하지 않는다(결정 3: 케이스 0건은 폐기 제안 대상 아님) |
| `seq09.representation` DEM | `"spatial_grid"` | `representation-from-shape` | 28→28 · 기여 0 · 역전 0 · 미측정(케이스 0) | 9→9 · 기여 0 · 역전 0 · 미측정(술어 없음) | 미측정 — 폐기하지 않는다(결정 3: 케이스 0건은 폐기 제안 대상 아님) |
| `seq09.interpolated` DEM | `true` | `interpolated-from-lineage` | 28→28 · 기여 0 · 역전 0 · 미측정(술어 없음) | 9→9 · 기여 0 · 역전 0 · 미측정(케이스 0) | 미측정 — 폐기하지 않는다(결정 3: 케이스 0건은 폐기 제안 대상 아님) |
| `seq10.representation` Aspect | `"spatial_grid"` | `representation-from-shape` | 28→28 · 기여 0 · 역전 0 · 미측정(케이스 0) | 9→9 · 기여 0 · 역전 0 · 미측정(술어 없음) | 미측정 — 폐기하지 않는다(결정 3: 케이스 0건은 폐기 제안 대상 아님) |
| `seq10.interpolated` Aspect | `true` | `interpolated-from-lineage` | 28→28 · 기여 0 · 역전 0 · 미측정(술어 없음) | 9→9 · 기여 0 · 역전 0 · 미측정(케이스 0) | 미측정 — 폐기하지 않는다(결정 3: 케이스 0건은 폐기 제안 대상 아님) |
| `seq11.representation` LULC_2023 | `"spatial_grid"` | `representation-from-shape` | 28→28 · 기여 0 · 역전 0 · 미측정(케이스 0) | 9→9 · 기여 0 · 역전 0 · 미측정(술어 없음) | 미측정 — 폐기하지 않는다(결정 3: 케이스 0건은 폐기 제안 대상 아님) |
| `seq11.interpolated` LULC_2023 | `false` | `interpolated-from-lineage` | 28→28 · 기여 0 · 역전 0 · 미측정(술어 없음) | 9→9 · 기여 0 · 역전 0 · 미측정(케이스 0) | 미측정 — 폐기하지 않는다(결정 3: 케이스 0건은 폐기 제안 대상 아님) |
| `seq12.representation` Prediction (공간상세화) | `"spatial_grid"` | `representation-from-shape` | 28→28 · 기여 0 · 역전 0 · 미측정(케이스 0) | 9→9 · 기여 0 · 역전 0 · 미측정(술어 없음) | 미측정 — 폐기하지 않는다(결정 3: 케이스 0건은 폐기 제안 대상 아님) |
| `seq12.interpolated` Prediction (공간상세화) | `true` | `interpolated-from-lineage` | 28→28 · 기여 0 · 역전 0 · 미측정(술어 없음) | 9→9 · 기여 0 · 역전 0 · 미측정(케이스 0) | 미측정 — 폐기하지 않는다(결정 3: 케이스 0건은 폐기 제안 대상 아님) |
| `seq13.representation` SPI-4weeks | `"table"` | `representation-from-shape` | 28→28 · 기여 0 · 역전 0 · 미측정(케이스 0) | 9→9 · 기여 0 · 역전 0 · 미측정(술어 없음) | 미측정 — 폐기하지 않는다(결정 3: 케이스 0건은 폐기 제안 대상 아님) |
| `seq13.interpolated` SPI-4weeks | `false` | `interpolated-from-lineage` | 28→28 · 기여 0 · 역전 0 · 미측정(술어 없음) | 9→9 · 기여 0 · 역전 0 · 미측정(케이스 0) | 미측정 — 폐기하지 않는다(결정 3: 케이스 0건은 폐기 제안 대상 아님) |
| `seq14.representation` SPEI-4weeks | `"table"` | `representation-from-shape` | 28→28 · 기여 0 · 역전 0 · 미측정(케이스 0) | 9→9 · 기여 0 · 역전 0 · 미측정(술어 없음) | 미측정 — 폐기하지 않는다(결정 3: 케이스 0건은 폐기 제안 대상 아님) |
| `seq14.interpolated` SPEI-4weeks | `false` | `interpolated-from-lineage` | 28→28 · 기여 0 · 역전 0 · 미측정(술어 없음) | 9→9 · 기여 0 · 역전 0 · 미측정(케이스 0) | 미측정 — 폐기하지 않는다(결정 3: 케이스 0건은 폐기 제안 대상 아님) |
| `seq15.representation` surface (ERA5 GRIB 원자료) | `"spatial_grid"` | `representation-from-shape` | 28→28 · 기여 0 · 역전 0 · 미측정(케이스 0) | 9→9 · 기여 0 · 역전 0 · 미측정(술어 없음) | 미측정 — 폐기하지 않는다(결정 3: 케이스 0건은 폐기 제안 대상 아님) |
| `seq15.interpolated` surface (ERA5 GRIB 원자료) | `false` | `interpolated-from-lineage` | 28→28 · 기여 0 · 역전 0 · 미측정(술어 없음) | 9→9 · 기여 0 · 역전 0 · 미측정(케이스 0) | 미측정 — 폐기하지 않는다(결정 3: 케이스 0건은 폐기 제안 대상 아님) |
| `seq16.representation` ERA5 변환 결과 | `"spatial_grid"` | `representation-from-shape` | 28→28 · 기여 0 · 역전 0 · 미측정(케이스 0) | 9→9 · 기여 0 · 역전 0 · 미측정(술어 없음) | 미측정 — 폐기하지 않는다(결정 3: 케이스 0건은 폐기 제안 대상 아님) |
| `seq16.interpolated` ERA5 변환 결과 | `true` | `interpolated-from-lineage` | 28→28 · 기여 0 · 역전 0 · 미측정(술어 없음) | 9→9 · 기여 0 · 역전 0 · 미측정(케이스 0) | 미측정 — 폐기하지 않는다(결정 3: 케이스 0건은 폐기 제안 대상 아님) |
| `seq16.region` ERA5 변환 결과 | `"전지구"` | `region-from-registration-note` | 28→28 · 기여 0 · 역전 0 · 측정(5케이스) | 9→9 · 기여 0 · 역전 0 · 측정(4케이스) | 1회차 관측 — 기여 0 · 보류(폐기는 K=3 회차 연속 필요) |
| `seq17.representation` GK-2A LST 원자료 | `"spatial_grid"` | `representation-from-shape` | 28→28 · 기여 0 · 역전 0 · 미측정(케이스 0) | 9→9 · 기여 0 · 역전 0 · 미측정(술어 없음) | 미측정 — 폐기하지 않는다(결정 3: 케이스 0건은 폐기 제안 대상 아님) |
| `seq17.interpolated` GK-2A LST 원자료 | `false` | `interpolated-from-lineage` | 28→28 · 기여 0 · 역전 0 · 미측정(술어 없음) | 9→9 · 기여 0 · 역전 0 · 미측정(케이스 0) | 미측정 — 폐기하지 않는다(결정 3: 케이스 0건은 폐기 제안 대상 아님) |
| `seq18.representation` GK-2A LST 변환 결과 | `"spatial_grid"` | `representation-from-shape` | 28→28 · 기여 0 · 역전 0 · 미측정(케이스 0) | 9→9 · 기여 0 · 역전 0 · 미측정(술어 없음) | 미측정 — 폐기하지 않는다(결정 3: 케이스 0건은 폐기 제안 대상 아님) |
| `seq18.interpolated` GK-2A LST 변환 결과 | `true` | `interpolated-from-lineage` | 28→28 · 기여 0 · 역전 0 · 미측정(술어 없음) | 9→9 · 기여 0 · 역전 0 · 미측정(케이스 0) | 미측정 — 폐기하지 않는다(결정 3: 케이스 0건은 폐기 제안 대상 아님) |
| `seq19.representation` HSR 레이더합성 원자료 | `"spatial_grid"` | `representation-from-shape` | 28→28 · 기여 0 · 역전 0 · 미측정(케이스 0) | 9→9 · 기여 0 · 역전 0 · 미측정(술어 없음) | 미측정 — 폐기하지 않는다(결정 3: 케이스 0건은 폐기 제안 대상 아님) |
| `seq19.interpolated` HSR 레이더합성 원자료 | `false` | `interpolated-from-lineage` | 28→28 · 기여 0 · 역전 0 · 미측정(술어 없음) | 9→9 · 기여 0 · 역전 0 · 미측정(케이스 0) | 미측정 — 폐기하지 않는다(결정 3: 케이스 0건은 폐기 제안 대상 아님) |
| `seq20.representation` HSR 레이더합성 변환 결과 | `"spatial_grid"` | `representation-from-shape` | 28→28 · 기여 0 · 역전 0 · 미측정(케이스 0) | 9→9 · 기여 0 · 역전 0 · 미측정(술어 없음) | 미측정 — 폐기하지 않는다(결정 3: 케이스 0건은 폐기 제안 대상 아님) |
| `seq20.interpolated` HSR 레이더합성 변환 결과 | `true` | `interpolated-from-lineage` | 28→28 · 기여 0 · 역전 0 · 미측정(술어 없음) | 9→9 · 기여 0 · 역전 0 · 미측정(케이스 0) | 미측정 — 폐기하지 않는다(결정 3: 케이스 0건은 폐기 제안 대상 아님) |
| `seq21.representation` HLS S30 T51SYB 원자료 | `"spatial_grid"` | `representation-from-shape` | 28→28 · 기여 0 · 역전 0 · 미측정(케이스 0) | 9→9 · 기여 0 · 역전 0 · 미측정(술어 없음) | 미측정 — 폐기하지 않는다(결정 3: 케이스 0건은 폐기 제안 대상 아님) |
| `seq21.interpolated` HLS S30 T51SYB 원자료 | `false` | `interpolated-from-lineage` | 28→28 · 기여 0 · 역전 0 · 미측정(술어 없음) | 9→9 · 기여 0 · 역전 0 · 미측정(케이스 0) | 미측정 — 폐기하지 않는다(결정 3: 케이스 0건은 폐기 제안 대상 아님) |
| `seq22.representation` HLS S30 T52SCE 원자료 | `"spatial_grid"` | `representation-from-shape` | 28→28 · 기여 0 · 역전 0 · 미측정(케이스 0) | 9→9 · 기여 0 · 역전 0 · 미측정(술어 없음) | 미측정 — 폐기하지 않는다(결정 3: 케이스 0건은 폐기 제안 대상 아님) |
| `seq22.interpolated` HLS S30 T52SCE 원자료 | `false` | `interpolated-from-lineage` | 28→28 · 기여 0 · 역전 0 · 미측정(술어 없음) | 9→9 · 기여 0 · 역전 0 · 미측정(케이스 0) | 미측정 — 폐기하지 않는다(결정 3: 케이스 0건은 폐기 제안 대상 아님) |
| `seq23.representation` HLS S30 T51SYB 변환 결과 | `"spatial_grid"` | `representation-from-shape` | 28→28 · 기여 0 · 역전 0 · 미측정(케이스 0) | 9→9 · 기여 0 · 역전 0 · 미측정(술어 없음) | 미측정 — 폐기하지 않는다(결정 3: 케이스 0건은 폐기 제안 대상 아님) |
| `seq23.interpolated` HLS S30 T51SYB 변환 결과 | `false` | `interpolated-from-lineage` | 28→28 · 기여 0 · 역전 0 · 미측정(술어 없음) | 9→9 · 기여 0 · 역전 0 · 미측정(케이스 0) | 미측정 — 폐기하지 않는다(결정 3: 케이스 0건은 폐기 제안 대상 아님) |
| `seq24.representation` HLS S30 T52SCE 변환 결과 | `"spatial_grid"` | `representation-from-shape` | 28→28 · 기여 0 · 역전 0 · 미측정(케이스 0) | 9→9 · 기여 0 · 역전 0 · 미측정(술어 없음) | 미측정 — 폐기하지 않는다(결정 3: 케이스 0건은 폐기 제안 대상 아님) |
| `seq24.interpolated` HLS S30 T52SCE 변환 결과 | `false` | `interpolated-from-lineage` | 28→28 · 기여 0 · 역전 0 · 미측정(술어 없음) | 9→9 · 기여 0 · 역전 0 · 미측정(케이스 0) | 미측정 — 폐기하지 않는다(결정 3: 케이스 0건은 폐기 제안 대상 아님) |
| `seq25.representation` hdf4 MOD15A2H h27v05 원자료 | `"spatial_grid"` | `representation-from-shape` | 28→28 · 기여 0 · 역전 0 · 미측정(케이스 0) | 9→9 · 기여 0 · 역전 0 · 미측정(술어 없음) | 미측정 — 폐기하지 않는다(결정 3: 케이스 0건은 폐기 제안 대상 아님) |
| `seq25.interpolated` hdf4 MOD15A2H h27v05 원자료 | `false` | `interpolated-from-lineage` | 28→28 · 기여 0 · 역전 0 · 미측정(술어 없음) | 9→9 · 기여 0 · 역전 0 · 미측정(케이스 0) | 미측정 — 폐기하지 않는다(결정 3: 케이스 0건은 폐기 제안 대상 아님) |
| `seq26.representation` hdf4 MOD15A2H h28v05 원자료 | `"spatial_grid"` | `representation-from-shape` | 28→28 · 기여 0 · 역전 0 · 미측정(케이스 0) | 9→9 · 기여 0 · 역전 0 · 미측정(술어 없음) | 미측정 — 폐기하지 않는다(결정 3: 케이스 0건은 폐기 제안 대상 아님) |
| `seq26.interpolated` hdf4 MOD15A2H h28v05 원자료 | `false` | `interpolated-from-lineage` | 28→28 · 기여 0 · 역전 0 · 미측정(술어 없음) | 9→9 · 기여 0 · 역전 0 · 미측정(케이스 0) | 미측정 — 폐기하지 않는다(결정 3: 케이스 0건은 폐기 제안 대상 아님) |
| `seq27.representation` hdf4 MOD15A2H h27v05 변환 결과 | `"spatial_grid"` | `representation-from-shape` | 28→28 · 기여 0 · 역전 0 · 미측정(케이스 0) | 9→9 · 기여 0 · 역전 0 · 미측정(술어 없음) | 미측정 — 폐기하지 않는다(결정 3: 케이스 0건은 폐기 제안 대상 아님) |
| `seq27.interpolated` hdf4 MOD15A2H h27v05 변환 결과 | `false` | `interpolated-from-lineage` | 28→28 · 기여 0 · 역전 0 · 미측정(술어 없음) | 9→9 · 기여 0 · 역전 0 · 미측정(케이스 0) | 미측정 — 폐기하지 않는다(결정 3: 케이스 0건은 폐기 제안 대상 아님) |
| `seq28.representation` hdf4 MOD15A2H h28v05 변환 결과 | `"spatial_grid"` | `representation-from-shape` | 28→28 · 기여 0 · 역전 0 · 미측정(케이스 0) | 9→9 · 기여 0 · 역전 0 · 미측정(술어 없음) | 미측정 — 폐기하지 않는다(결정 3: 케이스 0건은 폐기 제안 대상 아님) |
| `seq28.interpolated` hdf4 MOD15A2H h28v05 변환 결과 | `false` | `interpolated-from-lineage` | 28→28 · 기여 0 · 역전 0 · 미측정(술어 없음) | 9→9 · 기여 0 · 역전 0 · 미측정(케이스 0) | 미측정 — 폐기하지 않는다(결정 3: 케이스 0건은 폐기 제안 대상 아님) |

사실 단위 뒤집힘(경로 1·2 · heldout):

- `seq07.interpolated` — heldout_B 기여 ['N23'] · 역전 []

## 제외한 케이스

- `PC-1-1#p2` (A) — 근거 독립·제외(maxMissingRatePercent → d3_dataset_variable)
- `PC-1-4#p5` (A) — PC-1-4#m1(measure_only)가 대신한다 — 초안 보류 때문에 바뀐 기대다
- `PC-1-5` (A) — probe 0건(mode blocked) — 판정할 것이 없다
- `PC-2-1#p2` (A) — 근거 독립·제외(maxMissingRatePercent → d3_dataset_variable)
- `PC-2-5` (A) — probe 0건(mode blocked) — 판정할 것이 없다
- `PC-2-6` (A) — probe 0건(mode blocked) — 판정할 것이 없다
- `PC-2-7#p3` (A) — 근거 독립·제외(maxMissingRatePercent → d3_dataset_variable)
- `SEARCH-GOLD-001` (A) — plan_query 미인식 — 제품에서 경로 1 로 가지 않는다(경로 2 만 측정)
- `SEARCH-GOLD-002` (A) — plan_query 미인식 — 제품에서 경로 1 로 가지 않는다(경로 2 만 측정)
- `SEARCH-GOLD-003` (A) — plan_query 미인식 — 제품에서 경로 1 로 가지 않는다(경로 2 만 측정)
- `SEARCH-GOLD-004` (A) — plan_query 미인식 — 제품에서 경로 1 로 가지 않는다(경로 2 만 측정)
- `SEARCH-GOLD-005` (A) — plan_query 미인식 — 제품에서 경로 1 로 가지 않는다(경로 2 만 측정)
- `SEARCH-GOLD-006` (A) — plan_query 미인식 — 제품에서 경로 1 로 가지 않는다(경로 2 만 측정)
- `SEARCH-GOLD-007` (A) — plan_query 미인식 — 제품에서 경로 1 로 가지 않는다(경로 2 만 측정)
- `SEARCH-GOLD-008` (A) — plan_query 미인식 — 제품에서 경로 1 로 가지 않는다(경로 2 만 측정)
- `SEARCH-GOLD-009` (A) — plan_query 미인식 — 제품에서 경로 1 로 가지 않는다(경로 2 만 측정)
- `SEARCH-GOLD-010` (A) — plan_query 미인식 — 제품에서 경로 1 로 가지 않는다(경로 2 만 측정)
- `SEARCH-GOLD-011` (A·B) — manual — golden_baseline.assess 가 판정하지 않는다
- `SEARCH-GOLD-012` (A·B) — manual — golden_baseline.assess 가 판정하지 않는다

## 읽는 법·한계

- 기여 = 그 초안을 빼면 green→fail 로 뒤집히는 케이스 수. 역전 = 빼면 fail→green. 순위 변화는 JSON `rank_delta_*` 에만 적는다.
- 「미측정(술어 없음)」 = 그 경로가 이 성분을 읽지 않는다(경로 1 은 interpolated, 경로 2 는 platform·representation). 「미측정(케이스 0)」 = 읽지만 그 술어를 부르는 케이스가 없다 — 폐기 근거가 아니다(결정 3).
- 사실 단위 제안은 1회차라 회차 이력이 없다 — 승격(2회차)·폐기(K=3)는 「1회차 관측」으로만 낸다. 역전만 즉시 폐기 제안이다.
- heldout 은 제안에 쓰지 않는다(과적합 완화 · 사후 확인).
- 경로 1 오라클 = practitioner-conditions.json 의 probes(판정용) + measureOnlyProbes(초안 값 측정 전용 · 정답 주장 아님 · 2026-09-26 Ted 「전부 권고대로」로 되살린 1회차 probe). `#m` 이 measure_only 다.
- 경로 2 는 `routes/catalog.py` 경로 2 블록의 도메인 재현이다. 라우트의 verified·잠김 조립·근거 문장은 green 판정에 들어가지 않는다.
