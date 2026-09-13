# 식생(vegetation) 데이터셋 정본

- 출처 문서: `#readme/#processing_description_NDVI.docx` · 추출일 2026-09-14 · 상태: 초안(Ted 검토 대기)
- 유형 폴더: `01.level-data/02.vegetation/02.vegetation/`(참조자료 뿌리 기준) — 아래 글롭은 전부 이 폴더 기준 상대경로
- 프로젝트: vegetation · 설명: GK-2A 식생자료(Lv.0)에서 월평균 NDVI(Lv.1)를 만들고, 수치표고모형·경사향·토지피복을 추가 입력으로 써 100 m 일 단위 공간상세화 예측(Lv.2)까지 잇는다.
- 계수 기준: 파일 건수·바이트 = `glob` 매칭 후 `desktop.ini` 제외 · 2026-09-14 실측

## 데이터셋 표

| # | 이름 | 레벨 | 부모 | 파일 글롭 | 건수 | 바이트 | 기준 격자(쌍) | 포맷 | 미리보기 기대 | 비고 |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | GK-2A 일 단위 식생자료 | Lv.0 | — | `Lv.0/gk2a_ami_le2_vgt_ko_*.nc` | 31 | 57,900,869 | `#metadata/LAT.npy`·`LON.npy` | NetCDF4 | 미측정(판정 5종 밖) | 등록됨 · 격자 칸 미출현 |
| 2 | GK2A_NDVI_mean_202305 | Lv.1 | GK-2A 일 단위 식생자료 | `Lv.1/GK2A_NDVI_mean_202305.tif` | 1 | 13,047,326 | `#metadata/LAT_crop.npy`·`LON_crop.npy` | GeoTIFF | 미측정 | 등록됨 · 격자 칸 미출현 |
| 3 | HLS_S30_NDVI_mean_202305 | Lv.1(보조 입력) | — | `Lv.1_(Model_Input_Data)/HLS_S30_NDVI_mean_202305.tif` | 1 | 13,172,104 | 없음 | GeoTIFF | 미측정 | 등록됨 |
| 4 | DEM | Lv.1(보조 입력) | — | `Lv.1_(Model_Input_Data)/DEM.tif` | 1 | 12,635,960 | 없음 | GeoTIFF | 미측정 | 등록됨 |
| 5 | Aspect | Lv.1(보조 입력) | DEM | `Lv.1_(Model_Input_Data)/Aspect.tif` | 1 | 12,679,486 | 없음 | GeoTIFF | 미측정 | 등록됨 |
| 6 | LULC_2023 | Lv.1(보조 입력) | — | `Lv.1_(Model_Input_Data)/LULC_2023.tif` | 1 | 7,851,096 | 없음 | GeoTIFF | 미측정 | 등록됨 |
| 7 | Prediction (공간상세화) | Lv.2 | GK2A_NDVI_mean_202305 · HLS_S30_NDVI_mean_202305 · DEM · Aspect · LULC_2023 | `Lv.2/Prediction_2023*.npy` | 31 | 203,165,568 | `#metadata/LAT_crop.npy`·`LON_crop.npy` | npy | 미측정 | 등록됨 |

- 데이터셋 7 · 계보 간선 7 · 자료 바이트 320,452,409
- 기준 격자 파일 바이트 — `LAT.npy`·`LON.npy` 각 8,179,328 · `LAT_crop.npy`·`LON_crop.npy` 각 13,107,328

## 데이터셋 상세

### GK-2A 일 단위 식생자료

- 레벨: Lv.0 — 출처 문장 축자 「Lv.0 자료명 gk2a_ami_le2_vgt_ko_yyyymmddHHMM.nc」
- 부모: 없음 — 출처 문서에 상위 자료 문장 부재(원자료 블록 · 제공처는 국가기상위성센터)
- 파일: `Lv.0/gk2a_ami_le2_vgt_ko_*.nc` · 31건 · 57,900,869 B · 일 단위 `202305010000` ~ `202305310000`(2023-05 전월 31일)
- 격자: 파일 2건 `#metadata/LAT.npy`·`#metadata/LON.npy` · 근거 = 출처 축자 「Lv.0: LAT.npy, LON.npy」
- 설명: 국가기상위성센터가 제공하는 GK-2A le2 식생자료. 좌표계는 Lambert Conformal Conic, 시/공간해상도는 1일 / 2 km 다. 파일 하나에 NDVI·EVI·FVC·DQF·좌표계 정의 5개 자료가 들어 있고 이 흐름은 NDVI 만 사용한다.
- 비고: 오늘 실측 — 등록됨(31건 · 화면 접수 74,259,525 B). 기준 격자 칸이 뜨지 않아 격자 부착을 생략했다(화면이 좌표 보유로 판정 · `DR-3 §5`). 렌더 미측정.

### GK2A_NDVI_mean_202305

- 레벨: Lv.1 — 출처 문장 축자 「Lv.1 자료명 GK2A_NDVI_mean_yyyymm.tif」
- 부모: GK-2A 일 단위 식생자료 — 출처 문장 축자 「복수의 인자가 dictionary 형태로 저장되어 있는 NetCDF4 형식의 파일에서, NDVI 레이어를 추출하여 별개의 TIF 파일로 저장하였음.」
- 파일: `Lv.1/GK2A_NDVI_mean_202305.tif` · 1건 · 13,047,326 B · 2023-05 월평균 1장
- 격자: 파일 2건 `#metadata/LAT_crop.npy`·`#metadata/LON_crop.npy` · 근거 = 출처 축자 「Lv.1, Lv.2: LAT_crop.npy, LON_crop.npy」
- 설명: DQF 로 품질 저하 픽셀을 NaN 으로 바꾸고 유효 범주 -1~1 밖을 NaN 처리한 뒤, 원자료 좌표계 LCC 를 WGS84 로 변환해 NDVI 레이어만 TIF 로 저장한 자료. 경기도 남부~충청권 일대로 영역을 추출하고 2 km 를 100 m 로 균등 분할한 뒤 일 단위를 월 단위 평균으로 변환했다.
- 비고: 오늘 실측 — 등록됨(1건 · 화면 접수 39,261,982 B). 기준 격자 칸이 뜨지 않아 격자 부착을 생략했다. 렌더 미측정.

### HLS_S30_NDVI_mean_202305

- 레벨: Lv.1(보조 입력) — 폴더 이름이 `Lv.1_(Model_Input_Data)` 이고 출처 문장 축자 「(Lv.0 자료, Lv.1 자료 전달)」 · ⚠ 이 축자는 Lv.0 도 전달했다고 적으나 폴더에 Lv.0 실물이 없다(열린 질문 ㈎)
- 부모: 없음 — 출처 문서에 이 자료의 상위 자료로부터의 파생 문장이 없다. 제작 문장은 「HLS S30 자료의 Red, NIR 밴드를 기반으로 NDVI를 계산하고, 3 ~ 7일 공간해상도의 자료를 월 평균으로 변환」이고 그 원본 HLS S30 이 폴더에 없다
- 파일: `Lv.1_(Model_Input_Data)/HLS_S30_NDVI_mean_202305.tif` · 1건 · 13,172,104 B · 2023-05 월평균 1장
- 격자: 0건 · 근거 = 현재 등재표가 격자를 붙이지 않는다. 출처 축자 「Lv.1, Lv.2: LAT_crop.npy, LON_crop.npy」는 보조 4건을 명시하지 않아 부착 여부가 닫히지 않는다(열린 질문 ㈏)
- 설명: Lv.2 공간상세화 모델의 검증자료. HLS S30 자료의 Red·NIR 밴드로 NDVI 를 계산하고 3~7일 간격 자료를 월평균 100 m 로 변환한 것이다.
- 비고: 오늘 실측 — 등록됨(1건 · 화면 접수 13,172,104 B). 렌더 미측정.

### DEM

- 레벨: Lv.1(보조 입력) — 출처 문장 축자 「(Lv.0 자료 보유 X, Lv.1 자료만 전달하였음)」 · 상위 자료 미보유가 문서에 명시됨. 폴더 이름 `Lv.1_(Model_Input_Data)` 에 맞추어 Lv.1 로 제안
- 부모: 없음 — 위 축자가 Lv.0 부재를 명시한다
- 파일: `Lv.1_(Model_Input_Data)/DEM.tif` · 1건 · 12,635,960 B · 시간해상도 없음(출처 축자 「시간해상도 X」)
- 격자: 0건 · 근거 = 현재 등재표가 격자를 붙이지 않는다(열린 질문 ㈏)
- 설명: Lv.2 공간상세화 모델의 입력자료. Copernicus GLO-30 DEM 자료를 100 m 해상도로 변환한 수치표고모형이다. 시간해상도가 없다.
- 비고: 오늘 실측 — 등록됨(1건 · 화면 접수 12,635,960 B). 렌더 미측정.

### Aspect

- 레벨: Lv.1(보조 입력) — 출처 문장 축자 「(Lv.0 자료 보유 X, Lv.1 자료만 전달하였음)」
- 부모: DEM — 출처 문장 축자 「Copernicus GLO-30 DEM 자료를 100 m 해상도로 변환한 뒤, GIS 프로그램을 이용해 경사향 추출」
- 파일: `Lv.1_(Model_Input_Data)/Aspect.tif` · 1건 · 12,679,486 B · 시간해상도 없음(출처 축자 「시간해상도 X」)
- 격자: 0건 · 근거 = 현재 등재표가 격자를 붙이지 않는다(열린 질문 ㈏)
- 설명: Lv.2 공간상세화 모델의 입력자료. Copernicus GLO-30 DEM 을 100 m 로 변환한 뒤 GIS 프로그램으로 경사향을 추출한 자료다.
- 비고: 오늘 실측 — 등록됨(1건 · 화면 접수 12,679,486 B). 렌더 미측정.

### LULC_2023

- 레벨: Lv.1(보조 입력) — 출처 문장 축자 「(Lv.0 자료 보유 X, Lv.1 자료만 전달하였음)」
- 부모: 없음 — 위 축자가 Lv.0 부재를 명시한다. 생산 근거인 Landsat-8 밴드는 폴더에 없다
- 파일: `Lv.1_(Model_Input_Data)/LULC_2023.tif` · 1건 · 7,851,096 B · 연 단위 2023
- 격자: 0건 · 근거 = 현재 등재표가 격자를 붙이지 않는다(열린 질문 ㈏)
- 설명: Lv.2 공간상세화 모델의 입력자료. Landsat-8 위성의 밴드를 이용해 Google Earth Engine 의 smileGradientTreeBoost Module 모델로 군집 분석해 생산한 연 단위 100 m 토지피복지도다.
- 비고: 오늘 실측 — 등록됨(1건 · 화면 접수 7,851,096 B). 렌더 미측정.

### Prediction (공간상세화)

- 레벨: Lv.2 — 출처 문장 축자 「Lv.2 자료명 Prediction_yyyymmdd.npy」
- 부모: GK2A_NDVI_mean_202305 · HLS_S30_NDVI_mean_202305 · DEM · Aspect · LULC_2023 — 출처 문장 축자 「입력자료 월 단위 GK-2A NDVI (2 km) / 수치표고모형 (100 m) / 경사향 (100 m) / 연 단위 토지피복지도 (100 m)」 · 「검증자료 월 단위 HLS NDVI (100 m)」
- 파일: `Lv.2/Prediction_2023*.npy` · 31건 · 203,165,568 B · 일 단위 `Prediction_20230501.npy` ~ `Prediction_20230531.npy`
- 격자: 파일 2건 `#metadata/LAT_crop.npy`·`#metadata/LON_crop.npy` · 근거 = 출처 축자 「Lv.1, Lv.2: LAT_crop.npy, LON_crop.npy」
- 설명: U-Net 기반 공간상세화 모델의 산출물. 월평균 GK-2A NDVI 와 수치표고모형·경사향·토지피복지도를 입력으로, 월평균 HLS NDVI 를 검증자료로 학습했다. Lv.1 과 달리 Lv.0 처럼 일 단위 시간해상도를 갖고 지형 변화에 따른 NDVI 변화가 픽셀별로 다르게 나타난다.
- 비고: 오늘 실측 — 등록됨(31건 · 화면 접수 229,380,224 B). 렌더 미측정.

## 열린 질문 (Ted)

㈎ **HLS 자료의 Lv.0 이 문서에는 「전달」인데 폴더에 없다.** 출처 축자는 HLS 항목에만 「(Lv.0 자료, Lv.1 자료 전달)」로 적고 나머지 셋은 「(Lv.0 자료 보유 X, Lv.1 자료만 전달하였음)」로 적는다. 실물은 `Lv.1_(Model_Input_Data)/HLS_S30_NDVI_mean_202305.tif` 1건뿐이다. ⓐ 문서 표기 오류로 보고 부모 없음을 유지 / ⓑ 생산자에게 HLS Lv.0 전달을 요청하고 받으면 계보 1간선을 더한다.

㈏ **보조 입력 4건에 기준 격자를 붙일지 정해지지 않았다.** 출처 축자 「Lv.1, Lv.2: LAT_crop.npy, LON_crop.npy」는 층만 적고 보조 4건을 명시하지 않는다. 현재 등재표는 4건 모두 격자 0건이다. ⓐ 그대로 둔다(4건 모두 GeoTIFF 라 파일 내부로 격자가 계산된다 · `dev-package/DATA-REFERENCE.md §1.1`) / ⓑ `LAT_crop`·`LON_crop` 을 붙인다(부착 바이트 ＋104,858,624). 판정 입력 = 4건의 ROI 가 crop 격자와 같은지 여부이고 현재 `[미확인]`.

㈐ **보조 입력 4건의 레벨 표기.** 폴더 이름은 `Lv.1_(Model_Input_Data)` 이고 문서는 상위 자료 미보유만 적는다. 현재 초안은 「Lv.1(보조 입력)」으로 적었다. ⓐ 이 표기를 확정 / ⓑ 화면 표기는 `Lv.1` 로만 두고 보조 여부는 설명 칸에 적는다.

㈑ **식생 프로젝트도 미리보기 렌더 판정 대상 5종 밖이다.** NetCDF4·GeoTIFF·npy 세 포맷의 화면 렌더를 측정하지 않았다 `[미확인]`. ⓐ 판정 대상에 넣는다 / ⓑ 포멧테스트의 같은 포맷 결과로 갈음한다.

## 참조

- 출처 문서: `#readme/#processing_description_NDVI.docx`
- 재고 조사: `dev-package/reports/reference-data/2026-09-13-inventory-v2.md` §4-2 · §5-2 · §6 ㈑
- 오늘 등록 실측: `dev-package/sessions/DR-3-run-2026-09-13.md` §1 순번 6~12 · §5
- 기계 등재표: `dev-package/tools/dev-seed/plan-manifest.yaml` seq 6~12
