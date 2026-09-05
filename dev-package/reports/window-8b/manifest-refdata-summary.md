# 적재 매니페스트 안 A — 요약

- 데이터셋 **14** · 파일 **434** · 바이트 **3,780,910,612**
- 계보 간선 **6**

| key | 이름 | 원천 폴더 | 파일 | 바이트 | kind | 계보 |
|---|---|---|---|---|---|---|
| `LD-PRCP-LV0-HSR` | 강수 — HSR 레이더 합성 반사도 (Lv.0) | `01.level-data/01.precipitation/01.precipitation/` | 14 | 70,386,865 | 기준 격자 파일 2 · 본체 12 | — |
| `LD-PRCP-LV0-RN15` | 강수 — RN15 지상 15분 누적 강수 (Lv.0) | `01.level-data/01.precipitation/01.precipitation/` | 12 | 34,835,045 | 기준 격자 파일 2 · 본체 10 | — |
| `LD-PRCP-LV1` | 강수 — WGS84 변환·연구대상지 crop 표본 (Lv.1) | `01.level-data/01.precipitation/01.precipitation/` | 4 | 1,573,376 | 기준 격자 파일 2 · 본체 2 | LD-PRCP-LV0-HSR(주입력) ／ LD-PRCP-LV0-RN15(보조입력) |
| `LD-PRCP-LV2` | 강수 — U-Net 강우 추정 예측장 (Lv.2) | `01.level-data/01.precipitation/01.precipitation/Lv.2/` | 1 | 655,488 | 본체 1 | LD-PRCP-LV1(주입력) |
| `LD-VEG-LV0` | 식생 — GK-2A/AMI Lv.2 식생산출물 원자료 (Lv.0) | `01.level-data/02.vegetation/02.vegetation/` | 34 | 74,272,594 | 기준 격자 파일 2 · 본체 32 | — |
| `LD-VEG-LV1` | 식생 — GK-2A NDVI 100 m 월평균 (Lv.1) | `01.level-data/02.vegetation/02.vegetation/` | 3 | 39,261,982 | 기준 격자 파일 2 · 본체 1 | LD-VEG-LV0(주입력) |
| `LD-VEG-LV1-MODELIN` | 식생 — Lv.2 모델 보조입력·검증자료 (Lv.1 형제) | `01.level-data/02.vegetation/02.vegetation/Lv.1_(Model_Input_Data)/` | 4 | 46,338,646 | 본체 4 | — |
| `LD-VEG-LV2` | 식생 — U-Net NDVI 예측장 (Lv.2) | `01.level-data/02.vegetation/02.vegetation/Lv.2/` | 31 | 203,165,568 | 본체 31 | LD-VEG-LV1(주입력) ／ LD-VEG-LV1-MODELIN(보조입력) |
| `LD-DRGH-LV1` | 가뭄 — 시군구 주간 SPI/SPEI-4weeks (Lv.1) | `01.level-data/03.drought-20260518T233626Z-3-001/03.drought/` | 5 | 50,570,806 | 본체 5 | — |
| `FF-GRIB` | 파일 포맷 실습 — GRIB | `02.File-format/file_format_1_grib/` | 34 | 200,511,675 | 기준 격자 파일 2 · 본체 32 | — |
| `FF-NC` | 파일 포맷 실습 — NetCDF | `02.File-format/file_format_2_nc/` | 152 | 61,284,520 | 기준 격자 파일 2 · 본체 150 | — |
| `FF-BIN` | 파일 포맷 실습 — 이진(bin) | `02.File-format/file_format_3_bin/` | 41 | 721,469,348 | 기준 격자 파일 2 · 본체 39 | — |
| `FF-TIF` | 파일 포맷 실습 — GeoTIFF | `02.File-format/file_format_4_tif/` | 21 | 927,194,170 | 기준 격자 파일 2 · 본체 19 | — |
| `FF-HDF5` | 파일 포맷 실습 — HDF5/HDF-EOS | `02.File-format/file_format_5_HDF5/` | 78 | 1,349,390,529 | 기준 격자 파일 2 · 본체 76 | — |
