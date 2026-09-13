# `03 Reference-Data` 재조사 (v2 · 읽기 전용)

- 조사일 = 2026-09-13 · 루트 = 외부 드라이브 `03 Reference-Data` 폴더(레포 밖 · 무수정 · 읽기 전용)
- 본 문서 경로는 전부 위 루트 기준 상대경로.
- 대조 대상 = `reference-data-inventory.md`(같은 날 13:58 작성분, 이하 「v1」).
- 계수 기준 = `find <루트> -type f`(`desktop.ini` 74건 포함), 용량은 `du -sh`(NTFS/drvfs 블록) 또는 `du -sb`·`find -printf '%s'`(정확 바이트 · 표에 B 로 표기).
- 무변경 확인 = 조사 중 생성·수정·삭제 0건(`find`·`du`·`ls`·`head`·`grep`·`awk`·`sed` 만 사용).
- npy 형상·dtype = 파일 선두 128 B 헤더 직접 판독(`head -c 128`). numpy 실행 불가(시스템 `python3` 에 numpy 부재 · 서비스 venv 는 세션 워크트리 가드로 실행 거부) — mmap 적재 대신 헤더 판독으로 측정.
- 산출 위치 = 오케스트레이터 지정 경로 `~/.claude/jobs/ff466cc1/tmp/reference-data-inventory-v2.md` 는 H6 가드가 차단(`lifecycle evidence blocked: path outside task checkout`). 본 파일이 대체 산출물.

---

## 1. 총계 대조

| 항목 | v1 (13:58) | v2 (현재) | 증감 | 계수 기준 |
|---|---|---|---|---|
| 총 파일 수 | 2,123 | **2,470** | **＋347** | `find -type f` |
| 총 용량 | 3.7 G | **4.4 G** | ＋0.7 G | `du -sh` 루트 |
| `01.level-data/` | 498 M | **498 M** | 0 | `du -sh` |
| `02.File-format/` | 3.1 G | **3.8 G** | ＋0.7 G | `du -sh` |
| `03_KWRA_conference-.../` | 116 M | **116 M** | 0 | `du -sh` |
| 최상위 폴더 수 | 3 | **3** | 0 | `find -maxdepth 1 -type d` |

### 1-1. 확장자 증감 (전건)

| 확장자 | v1 | v2 | 증감 |
|---|---|---|---|
| `npy` | 1,622 | **1,831** | ＋209 |
| `png` | 115 | **251** | ＋136 |
| `nc` | 184 | **186** | ＋2 |
| `ini`·`tif`·`gz`·`py`·`hdf`·`jpg`·`docx`·`pptx`·`pdf`·`gpkg`·`md`·`jpeg`·`ipynb`·`grib`·`avif` | 74·62·22·13·8·7·5·2·2·2·1·1·1·1·1 | 동일 | 0 |

- ＋347 = npy ＋209 ＋ png ＋136 ＋ nc ＋2.

### 1-2. mtime 판독 주의

- `find . -newermt "2026-09-13 00:00" -type f` = **0건**. `-newermt "2026-09-01"` 도 0건.
- 파일 mtime 은 전부 원본 보존값(최신 파일 = 2026-05-19 08:37). 파일 mtime 으로는 오늘 변경을 식별할 수 없다.
- 오늘 변경 식별은 **디렉터리 mtime** 으로 수행 — `find . -newermt "2026-09-13 00:00"` 디렉터리 9건:

| mtime | 디렉터리 |
|---|---|
| 2026-09-13 15:13 | `02.File-format/file_format_1_grib/02.Results` · `.../02.Results/slhf` · `.../02.Results/ssr` · `.../02.Results/str` |
| 2026-09-13 15:13 | `02.File-format/file_format_2_nc` · `.../00.Data` · `.../02.Results` · `.../03.Figure` |
| 2026-09-13 15:00 | `01.level-data/03.drought-20260518T233626Z-3-001/03.drought/#readme` |

---

## 2. 신규 · 변경 · 삭제 목록

### 2-1. 신규 폴더 (2건)

| 경로 | 내용 | 건수 | 바이트 |
|---|---|---|---|
| `02.File-format/file_format_1_grib/02.Results/slhf/` | `ERA5_slhf_202509010000.npy` ~ `...202509012300.npy` | 24 npy | 99,674,112 |
| `02.File-format/file_format_1_grib/02.Results/ssr/` | `ERA5_ssr_202509010000.npy` ~ `...202509012300.npy` | 24 npy | 99,674,112 |

### 2-2. 파일 증가 (5건)

| 경로 | v1 | v2 | 증감 | v2 바이트(`desktop.ini` 제외) |
|---|---|---|---|---|
| `file_format_1_grib/02.Results/str/` | 6 npy | **24 npy** | ＋18 | 99,674,112 |
| `file_format_1_grib/03.Figure/` | 6 png `[추론]` | **24 png** | ＋18 | 9,461,176 |
| `file_format_2_nc/02.Results/` | **0**(폴더 미기재) | **143 npy** | ＋143 | 463,338,304 |
| `file_format_2_nc/03.Figure/` | 25 png `[추론]` | **143 png** | ＋118 | 51,109,479 |
| `file_format_2_nc/00.Data/` | 142 nc | **143 nc** | ＋1 | 50,707,958 |

- `[추론]` 근거 = v1 이 `03.Figure` 를 폴더별로 계수하지 않고 전체 png 115 만 기재. v2 실측에서 변화 없는 png 소재(bin 12 · tif 2 · hdf 17 · KWRA 53 = 84)를 빼면 v1 의 grib＋nc `03.Figure` 합 = 31 이고, v1 이 grib `02.Results/str` 을 6 으로 적었으므로 grib 6 · nc 25 로 갈린다. 폴더별 v1 원값 기록은 부재 `[미확인]`.

### 2-3. 삭제 = 0건

- v1 기재 경로 전건이 v2 에 존재. 동일 이름 파일의 바이트 전건 일치.

### 2-4. 변경 사유 미상 1건

- `01.level-data/03.drought-.../03.drought/#readme/` 디렉터리 mtime = 2026-09-13 15:00.
- 내부 파일 3건(`01.가뭄 데이터 여는 코드.ipynb` 383,565 B · `[Data Info]SPEI-4weeks.docx` 284,678 B · `[Data Info]SPI-4weeks.docx` 308,195 B)은 v1 과 이름·크기·mtime 전건 동일.
- 디렉터리 mtime 만 변하고 내용물 변화 0건 — 사유 `[미확인]`.

### 2-5. 신규 설명 문서 = 0건

- 설명 문서 후보 전수 검색(`*.md`·`*.txt`·`*.docx`·`*.pptx`·`*.pdf`·`*.csv`·`*.xlsx`·`*.json`·`*.yaml`·`README*`·`*설명*`·`*구성*`·`*계보*`·`*목록*`) = 10건, 전부 v1 기재분이며 mtime 최신값 2026-05-19.
- 최상위·프로젝트별 신규 README·매니페스트(xlsx·csv) = 부재. 지시 4항의 재현 대상 없음.
- `.txt`·`.csv`·`.xlsx`·`.json`·`.yaml` = 각 0건(실측).

---

## 3. 포맷 5종 구조 실측

### 3-1. 공통 구조

- 5종 모두 `00.Data/`(원자료) · `01.Code/`(변환 코드) · `02.Results/`(npy) · `03.Figure/`(png) · `04.Lat_Lon_info/`(격자) 로 동일.
- `02.Results` 하위폴더 보유 = `file_format_1_grib` 1건뿐(`slhf`·`ssr`·`str`). 나머지 4종은 평면.
- `03.Figure` 하위폴더 보유 = `file_format_5_HDF5/03.Figure/{01.shot(16 png), 02.merge(1 png)}` 1건뿐.
- **신규 하위폴더 = grib `slhf`·`ssr` 2건. 그 밖의 신규 하위폴더 없음.**
- 각 폴더 최상위에 `desktop.ini` 1건씩 상주(적재 대상 아님).

### 3-2. 폴더별 실측표

| 포맷 | `00.Data` | `02.Results` | `04.Lat_Lon_info` | `01.Code` | `03.Figure` |
|---|---|---|---|---|---|
| grib | 1 `.grib` · 149,514,336 B | 3 하위폴더 × 24 npy = 72 · 299,022,336 B | `lat2d.npy`·`lon2d.npy` 2 · 16,612,096 B | `Lv1_Data Processing.py` 1 | 24 png(`ERA5_ssr_*` 만) |
| nc | 143 `.nc` · 50,707,958 B | 143 npy · 463,338,304 B | `lat2d.npy`·`lon2d.npy` 2 · 6,480,256 B ＋ `gk2a_ko020lc_latlon.nc` 2,111,516 B | 1 | 143 png |
| bin | 12 `.bin.gz` · 15,341,732 B | 12 npy · 637,509,216 B | `Lat_HSR.npy`·`Lon_HSR.npy` 2 · 53,125,896 B ＋ `rdr_500m_latlon.nc` 11,471,526 B ＋ `레이더합성자료포맷정보.pdf` | 1 | 12 png |
| tif | 6 `.tif` · 153,372,376 B | 6 npy · 321,495,168 B | 타일별 `_lat2d.npy`·`_lon2d.npy` 4 · 428,659,712 B | 3 | 2 png |
| hdf | 8 `.hdf` · 55,249,549 B | 48 npy · 1,105,926,144 B | `lat2d_h2{7,8}v05.npy`·`lon2d_h2{7,8}v05.npy` 4 · 184,320,512 B | 1 | 17 png |

### 3-3. `02.Results` dtype · 형상 · 격자 일치 (헤더 실측)

| 포맷 | 표본 파일 | 결과 dtype·형상 | 격자 파일 dtype·형상 | 격자 일치 | 분할 기준 |
|---|---|---|---|---|---|
| grib | `02.Results/slhf/ERA5_slhf_202509010000.npy` | `<f4 (721,1440)` | `04.Lat_Lon_info/lat2d.npy` `<f8 (721,1440)` | 일치 | **변수별**(slhf·ssr·str) × 시각 24 |
| grib | `02.Results/ssr/ERA5_ssr_202509010000.npy` | `<f4 (721,1440)` | 동일 | 일치 | 동일 |
| grib | `02.Results/str/ERA5_str_202509010000.npy` | `<f4 (721,1440)` | 동일 | 일치 | 동일 |
| nc | `02.Results/gk2a_ami_le2_lst_ko_202005010000.npy` | `<f4 (900,900)` | `04.Lat_Lon_info/lat2d.npy` `<f4 (900,900)` | 일치 | **시각별** 143(단일 변수 LST) |
| bin | `02.Results/RDR_CMP_HSR_PUB_202508131000.npy` | `<f8 (2881,2305)` | `Lat_HSR.npy` `<f4 (2881,2305)` | 형상 일치 · dtype 상이 | **시각별** 12 |
| tif | `02.Results/HLS.S30.T51SYB.…B02.npy` | `<f4 (3660,3660)` | `HLS.S30.T51SYB.…_lat2d.npy` `<f8 (3660,3660)` | 일치 | **타일별**(T51SYB·T52SCE) × 밴드 3 |
| hdf | `02.Results/MOD15A2H.A2019273.h27v05.…_Fpar_500m.npy` | `<f4 (2400,2400)` | `lat2d_h27v05.npy` `<f8 (2400,2400)` | 일치 | **타일별**(h27v05·h28v05) × 변수 6 × 날짜 4 |

- 결과 전건이 원자료 격자와 동일 격자 위에 있다. 격자 파일 형상과 결과 형상이 전건 일치 — 재격자 흔적 없음.
- dtype = 결과 `<f4`(bin 결과만 `<f8`), 격자 `<f8`(nc·bin 격자만 `<f4`).

### 3-4. grib 결과가 변수별인 근거

요지 = 변환 코드가 GRIB 안의 변수를 순회하며 변수명 폴더를 만들고 `ERA5_<변수>_<시각>.npy` 로 저장한다.

근거 = `02.File-format/file_format_1_grib/01.Code/Lv1_Data Processing.py:125-126` 축자 —
> `file_name = f"ERA5_{var}_{time_strings[idx]}.npy"`
> `np.save(os.path.join(save_var_dir, file_name), data)`

같은 파일 `:140-141` 축자 —
> `# Load converted NumPy files for visualization (Variable Setting = SSR)`
> `npy_files = glob("./02.Results/ssr/*.npy")`

[추론] `03.Figure` 가 `ERA5_ssr_*` 24건뿐인 것은 시각화 절이 `ssr` 하나를 예시로 고정하기 때문이다.

### 3-5. hdf 결과 분해 (48 npy)

| 타일 | 날짜 | 변수 | 소계 |
|---|---|---|---|
| `h27v05` | `A2019273`·`A2019281`·`A2019289`·`A2019297` | `Fpar_500m`·`Lai_500m`·`FparStdDev_500m`·`LaiStdDev_500m`·`FparLai_QC`·`FparExtra_QC` | 24 |
| `h28v05` | 동일 4 | 동일 6 | 24 |

- `00.Data` 8 `.hdf` = 타일 2 × 날짜 4. 변수 6은 `.hdf` 내부 서브데이터셋 → 결과에서 파일로 분리.

### 3-6. tif 결과 분해 (6 npy)

- 타일 2(`T51SYB`·`T52SCE`) × 밴드 3(`B02`·`B03`·`B04`). 파일당 53,582,528 B 동일.
- 원자료도 같은 2×3 구성. 타일별 격자 파일 2건씩(총 4건).

---

## 4. level data 재확인

- **세 프로젝트 전부 v1 대비 변화 0건** — 파일 수·바이트·이름 전건 일치. 신규 결과 데이터 없음. 신규 설명 텍스트 없음. 디렉터리 트리 21개 전건 동일.

### 4-1. precipitation

요지 = Lv.0 두 갈래(HSR 반사도 · rn15 지상강우) → Lv.1 두 갈래(좌표변환·crop `.npy`) → Lv.2 U-Net 예측.

근거 = `01.level-data/01.precipitation/01.precipitation/#readme/#processing_description_Precipitation.docx` 축자 —
> Lv.2 / 자료명 pred_sample.npy / 처리 방법 딥러닝 모델 (U-Net based Model) / 학습 시활용 자료 / 입력자료 hsr_sample.npy / 검증자료 rn15_sample.npy

> Lv.1 / 자료명 hsr_sample.npy rn15_sample.npy / 처리 과정 (처리 순서대로 나열) 기상청에서 제공하는 각각의 lat, lon 파일에 맞추어 WGS84로 좌표계 변환 / 특정 연구대상지를 중심으로 crop 을 진행함 / lat, lon 정보 첨부해두었음 / 형태 (10, 128, 128)

- 본 회차 docx 재추출 미실시(파일 바이트·mtime 동일 확인으로 갈음) — 축자는 v1 추출분 `[미확인]`.

### 4-2. vegetation

요지 = Lv.0 GK-2A 식생(nc) → Lv.1 월평균 NDVI(tif) → Lv.2 일 단위 100 m 예측(npy). Lv.2 는 `Lv.1_(Model_Input_Data)` 4종을 추가 입력·검증으로 사용.

근거 = `01.level-data/02.vegetation/02.vegetation/#readme/#processing_description_NDVI.docx` 축자 —
> Lv.2 / 자료명 Prediction_yyyymmdd.npy / 처리 방법 딥러닝 모델 (U-Net based Model) / 입력자료 월 단위 GK-2A NDVI (2 km) / 수치표고모형 (100 m) / 경사향 (100 m) / 연 단위 토지피복지도 (100 m) / 검증자료 월 단위 HLS NDVI (100 m)

> Lv.0에서 Lv.1-B로 자료가 변환되는 과정에서 대상 지역(ROI)가 변경되므로, 이에 따른 좌표 파일을 각각 #metadata 폴더 내에 포함하였음. / Lv.0: LAT.npy, LON.npy / Lv.1, Lv.2: LAT_crop.npy, LON_crop.npy

- 동일하게 v1 추출분 · 본 회차 재추출 미실시 `[미확인]`.

### 4-3. drought

- Ted 규칙 = SPI 와 SPEI 는 독립 데이터셋 2건, 계보 없음.
- 폴더 실물이 이를 지지 — `Lv.1/` 만 존재(`Lv.0`·`Lv.2` 부재), 설명 문서가 `[Data Info]SPI-4weeks.docx`·`[Data Info]SPEI-4weeks.docx` 두 건으로 분리.
- v1 열린 질문 ㈏(SPI·SPEI 묶음 여부) = Ted 규칙으로 종결(2건 독립).

---

## 5. 최종 등록안 (제안 · 미승인)

적용한 Ted 규칙 —
1. 데이터셋 = 한 산출물 · 한 격자 · 함께 처리된 파일 묶음. 격자·타일이 다르면 별개 데이터셋. 같은 산출물의 시간 단계는 한 데이터셋의 여러 파일.
2. 포맷 폴더 `00.Data/` → `02.Results/` 는 계보(원자료 데이터셋 → 결과 데이터셋). `01.Code/`·`03.Figure/` 는 적재하지 않는다.
3. drought SPI·SPEI = 독립 2건, 계보 없음.
4. `desktop.ini` 74건 적재 제외.
5. 격자 파일 부착 상한 = 데이터셋당 2건.

### 5-1. precipitation (`01.level-data/01.precipitation/01.precipitation/`)

| # | 데이터셋명(설명서 표기) | level | 파일 glob | 건수 | 바이트 | 부모 | 부착 격자 | 포맷 |
|---|---|---|---|---|---|---|---|---|
| P1 | HSR 레이더 반사도 원자료 | Lv.0 | `Lv.0/01.HSR/RDR_CMP_HSR_PUB_*.bin.gz` | 10 | 16,998,652 | — | `#metadata/LAT_HSR.npy`·`LON_HSR.npy` | bin(gzip) |
| P2 | rn15 15분 누적강수 | Lv.0 | `Lv.0/02.rn15/sfc_grid_rn_15m_*.nc` | 10 | 1,247,581 | — | `#metadata/LAT_RN15.npy`·`LON_RN15.npy` | NetCDF4 |
| P3 | hsr_sample (전처리) | Lv.1 | `Lv.1/hsr_sample.npy` | 1 | 655,488 | P1 | `#metadata/LAT_crop.npy`·`LON_crop.npy` | npy |
| P4 | rn15_sample (전처리) | Lv.1 | `Lv.1/rn15_sample.npy` | 1 | 655,488 | P2 | 동일 | npy |
| P5 | pred_sample (U-Net 예측) | Lv.2 | `Lv.2/pred_sample.npy` | 1 | 655,488 | P3 ＋ P4 | 동일 | npy |

- 데이터셋 5 · 계보 간선 4(P1→P3 · P2→P4 · P3→P5 · P4→P5).
- 데이터 바이트 20,212,697 · 격자 고유 86,975,760(3쌍) · 격자 부착 실적재 87,500,560.

### 5-2. vegetation (`01.level-data/02.vegetation/02.vegetation/`)

| # | 데이터셋명 | level | 파일 glob | 건수 | 바이트 | 부모 | 부착 격자 | 포맷 |
|---|---|---|---|---|---|---|---|---|
| V1 | GK-2A 일 단위 식생자료 | Lv.0 | `Lv.0/gk2a_ami_le2_vgt_ko_*.nc` | 31 | 57,900,869 | — | `#metadata/LAT.npy`·`LON.npy` | NetCDF4 |
| V2 | GK2A_NDVI_mean_202305 | Lv.1 | `Lv.1/GK2A_NDVI_mean_202305.tif` | 1 | 13,047,326 | V1 | `#metadata/LAT_crop.npy`·`LON_crop.npy` | GeoTIFF |
| V3 | HLS_S30_NDVI_mean_202305 | Lv.1 보조 | `Lv.1_(Model_Input_Data)/HLS_S30_NDVI_mean_202305.tif` | 1 | 13,172,104 | — (Lv.0 미전달) | `LAT_crop`·`LON_crop` `[미확인]` | GeoTIFF |
| V4 | DEM | Lv.1 보조 | `Lv.1_(Model_Input_Data)/DEM.tif` | 1 | 12,635,960 | — (Lv.0 보유 X) | 동일 `[미확인]` | GeoTIFF |
| V5 | Aspect | Lv.1 보조 | `Lv.1_(Model_Input_Data)/Aspect.tif` | 1 | 12,679,486 | V4 | 동일 `[미확인]` | GeoTIFF |
| V6 | LULC_2023 | Lv.1 보조 | `Lv.1_(Model_Input_Data)/LULC_2023.tif` | 1 | 7,851,096 | — (Lv.0 보유 X) | 동일 `[미확인]` | GeoTIFF |
| V7 | Prediction (공간상세화) | Lv.2 | `Lv.2/Prediction_2023*.npy` | 31 | 203,165,568 | V2 ＋ V4 ＋ V5 ＋ V6 ＋ V3 | `#metadata/LAT_crop.npy`·`LON_crop.npy` | npy |

- 데이터셋 7 · 계보 간선 7(V1→V2 · V4→V5 · V2→V7 · V4→V7 · V5→V7 · V6→V7 · V3→V7).
- 데이터 바이트 320,452,409 · 격자 고유 42,573,312(2쌍).
- 격자 부착 실적재 68,787,968(V1 에 `LAT/LON` 1회 ＋ V2·V7 에 `LAT_crop/LON_crop` 2회). V3~V6 에도 crop 격자를 붙이면 ＋104,858,624 → 173,646,592 `[미확인]`(§6 ㈑).

### 5-3. drought (`01.level-data/03.drought-20260518T233626Z-3-001/03.drought/`)

| # | 데이터셋명 | level | 파일 | 건수 | 바이트 | 부모 | 부착 격자 | 포맷 |
|---|---|---|---|---|---|---|---|---|
| D1 | SPI-4weeks | Lv.1 (L1 Calibrated) | `Lv.1/SPI_4weeks_sig_wide.gpkg` | 1 | 24,797,184 | — | 없음(벡터) | GeoPackage |
| D2 | SPEI-4weeks | Lv.1 (L1 Calibrated) | `Lv.1/SPEI_4weeks_sig_wide.gpkg` | 1 | 24,797,184 | — | 없음(벡터) | GeoPackage |

- 데이터셋 2 · 계보 간선 0 · 데이터 바이트 49,594,368 · 격자 0.

### 5-4. 포멧테스트 (`02.File-format/`)

| # | 데이터셋명 | 단계 | 파일 glob | 건수 | 바이트 | 부모 | 부착 격자 | 포맷 |
|---|---|---|---|---|---|---|---|---|
| F1 | surface (ERA5 GRIB 원자료) | 원자료 | `file_format_1_grib/00.Data/surface.grib` | 1 | 149,514,336 | — | `…/04.Lat_Lon_info/lat2d.npy`·`lon2d.npy` | GRIB1 |
| F2 | ERA5 slhf | 결과 | `file_format_1_grib/02.Results/slhf/ERA5_slhf_*.npy` | 24 | 99,674,112 | F1 | 동일 | npy |
| F3 | ERA5 ssr | 결과 | `…/02.Results/ssr/ERA5_ssr_*.npy` | 24 | 99,674,112 | F1 | 동일 | npy |
| F4 | ERA5 str | 결과 | `…/02.Results/str/ERA5_str_*.npy` | 24 | 99,674,112 | F1 | 동일 | npy |
| F5 | GK-2A LST 원자료 | 원자료 | `file_format_2_nc/00.Data/gk2a_ami_le2_lst_ko_*.nc` | 143 | 50,707,958 | — | `…/04.Lat_Lon_info/lat2d.npy`·`lon2d.npy` | NetCDF4 |
| F6 | GK-2A LST 결과 | 결과 | `file_format_2_nc/02.Results/gk2a_ami_le2_lst_ko_*.npy` | 143 | 463,338,304 | F5 | 동일 | npy |
| F7 | HSR 레이더합성 원자료 | 원자료 | `file_format_3_bin/00.Data/RDR_CMP_HSR_PUB_*.bin.gz` | 12 | 15,341,732 | — | `…/04.Lat_Lon_info/Lat_HSR.npy`·`Lon_HSR.npy` | bin(gzip) |
| F8 | HSR 레이더합성 결과 | 결과 | `file_format_3_bin/02.Results/RDR_CMP_HSR_PUB_*.npy` | 12 | 637,509,216 | F7 | 동일 | npy |
| F9 | HLS S30 T51SYB 원자료 | 원자료 | `file_format_4_tif/00.Data/HLS.S30.T51SYB.*.tif` | 3 | 74,288,594 | — | `…T51SYB…_lat2d.npy`·`_lon2d.npy` | GeoTIFF |
| F10 | HLS S30 T52SCE 원자료 | 원자료 | `file_format_4_tif/00.Data/HLS.S30.T52SCE.*.tif` | 3 | 79,083,782 | — | `…T52SCE…_lat2d.npy`·`_lon2d.npy` | GeoTIFF |
| F11 | HLS S30 T51SYB 결과 | 결과 | `file_format_4_tif/02.Results/HLS.S30.T51SYB.*.npy` | 3 | 160,747,584 | F9 | T51SYB 쌍 | npy |
| F12 | HLS S30 T52SCE 결과 | 결과 | `file_format_4_tif/02.Results/HLS.S30.T52SCE.*.npy` | 3 | 160,747,584 | F10 | T52SCE 쌍 | npy |
| F13 | MOD15A2H h27v05 원자료 | 원자료 | `file_format_5_HDF5/00.Data/MOD15A2H.*.h27v05.*.hdf` | 4 | 37,562,489 | — | `lat2d_h27v05.npy`·`lon2d_h27v05.npy` | HDF4(폴더명 HDF5) |
| F14 | MOD15A2H h28v05 원자료 | 원자료 | `…/00.Data/MOD15A2H.*.h28v05.*.hdf` | 4 | 17,687,060 | — | `lat2d_h28v05.npy`·`lon2d_h28v05.npy` | HDF4 |
| F15~F20 | h27v05 결과 6종 — `Fpar_500m`·`Lai_500m`·`FparStdDev_500m`·`LaiStdDev_500m`·`FparLai_QC`·`FparExtra_QC` | 결과 | `…/02.Results/MOD15A2H.*.h27v05.*_<변수>.npy` | 각 4 | 각 92,160,512 | F13 | h27v05 쌍 | npy |
| F21~F26 | h28v05 결과 6종(동일 변수) | 결과 | `…/02.Results/MOD15A2H.*.h28v05.*_<변수>.npy` | 각 4 | 각 92,160,512 | F14 | h28v05 쌍 | npy |

- 데이터셋 26 · 계보 간선 19(grib 3 · nc 1 · bin 1 · tif 2 · hdf 12).
- 데이터 바이트 3,251,477,119.
- 격자 고유 689,198,472(grib 16,612,096 ＋ nc 6,480,256 ＋ bin 53,125,896 ＋ tif 428,659,712 ＋ hdf 184,320,512).
- 격자 부착 실적재 2,333,223,696(grib 쌍×4 ＝66,448,384 · nc 쌍×2 ＝12,960,512 · bin 쌍×2 ＝106,251,792 · tif 타일쌍 각×2 ＝857,319,424 · hdf 타일쌍 각×7 ＝1,290,243,584).

### 5-5. 총계

| 프로젝트 | 데이터셋 | 계보 간선 | 데이터 바이트 | 격자 고유 B | 격자 부착 실적재 B | 적재 합(데이터＋부착) |
|---|---|---|---|---|---|---|
| precipitation | 5 | 4 | 20,212,697 | 86,975,760 | 87,500,560 | 107,713,257 |
| vegetation | 7 | 7 | 320,452,409 | 42,573,312 | 68,787,968 | 389,240,377 |
| drought | 2 | 0 | 49,594,368 | 0 | 0 | 49,594,368 |
| 포멧테스트 | 26 | 19 | 3,251,477,119 | 689,198,472 | 2,333,223,696 | 5,584,700,815 |
| **합계** | **40** | **30** | **3,641,736,593** | **818,747,544** | **2,489,512,224** | **6,131,248,817** |

- 계수 기준 = 데이터 바이트는 `00.Data`·`02.Results`·level 폴더의 실데이터만(`desktop.ini`·`01.Code`·`03.Figure`·`*.pdf` 제외).
- 「격자 고유 B」와 「격자 부착 실적재 B」를 갈라 적는다 — 같은 격자 파일을 여러 데이터셋에 부착하면 데이터셋마다 파일 레코드가 생기므로 실적재 바이트가 고유 바이트를 초과한다. 어느 쪽이 전송·과금 기준인지는 적재 구현에 달림 `[미확인]`.
- 적재 제외 = `desktop.ini` 74 · `01.Code` `*.py` 13 · `03.Figure` png 251·jpg 7 · `03_KWRA_conference-…` 전체(§6 ㈎).

---

### 5-6. 판정 반영 (2026-09-13)

Ted 판정 — 원문 그대로 "너 생각은 어때? 종료가 다르다고 봐야하는거? 데이터셋을 묶는건 하나의 목적인건데".

- 데이터셋 = 한 목적 단위. 결과 데이터셋을 물리량(변수)별로 쪼개지 않는다. §5-4 표의 F2~F4(grib 변수 3종) 는 결과 1건 · F15~F26(hdf 변수 6종 × 타일 2) 는 타일별 결과 1건씩 2건으로 묶는다.
- 타일별 분리(tif 2 · hdf 2)는 목적 구분이 아니라 데이터셋당 기준 격자 파일 2건 상한이라는 시스템 제약에 따른 분리다(`services/core-api/src/colab_core/app/routes/upload_transfers.py:40`).
- 등록 계수는 아래가 정본이며 §5-4·§5-5 의 26/19 · 40/30 을 대체한다.

| 프로젝트 | 데이터셋 | 계보 간선 |
|---|---|---|
| precipitation | 5 | 4 |
| vegetation | 7 | 7 |
| drought | 2 | 0 |
| 포멧테스트 | 14 | 7 |
| **합계** | **28** | **18** |

- 포멧테스트 14 내역 = grib 원본 1→결과 1 · nc 1→1 · bin 1→1 · tif 타일별 2→2 · hdf 타일별 2→2.
- 바이트 계수(§5-4·§5-5)는 파일 집합이 그대로이므로 데이터셋 경계 변경으로 바뀌지 않는다. 격자 부착 실적재 바이트는 데이터셋 수가 줄어 감소하며 재계산 미수행 `[미확인]`.
- §6 ㈏·㈐(tif·hdf 결과 경계)는 본 판정으로 종결 — 둘 다 타일별 1건.
- 반영처 = `dev-package/intent/2026-09-13-dev-reset-reference-scenario.md`.

---

## 6. 열린 질문 (폴더가 답하지 않는 것만)

㈎ **`03_KWRA_conference-20260517T141236Z-3-001/` 116 M · 1,536건의 귀속처 미정.** v1 ㈎ 그대로 미해소. 오늘 변화 0건. 선택지 = ⓐ 적재 제외 ⓑ vegetation 에 편입 ⓒ 5번째 프로젝트 신설.

㈏ **tif 결과의 데이터셋 경계 — 타일별 2건인가 타일×밴드별 6건인가.** 밴드 `B02`·`B03`·`B04` 는 같은 격자·같은 촬영. 「밴드 = 다른 산출물」인지 판정 필요. 본 표는 타일별 2건으로 작성. ⓑ 밴드별이면 원자료 2→6, 결과 2→6, 간선 2→6.

㈐ **hdf 결과의 데이터셋 경계 — 타일×변수 12건인가 타일별 2건인가.** 6 변수의 물리량이 서로 달라 본 표는 12건으로 작성. ⓑ 타일별 2건이면 포멧테스트 데이터셋 26→16, 간선 19→9.

㈑ **vegetation `Lv.1_(Model_Input_Data)` 4건의 격자 부착 여부.** 설명서는 「Lv.1, Lv.2: LAT_crop.npy, LON_crop.npy」로만 적고 보조 4종을 명시하지 않음. 4건 전부 100 m GeoTIFF 이나 crop 격자와 동일 ROI 인지 미확인(GeoTIFF 헤더 판독 도구 부재).

㈒ **HSR 격자 정본 2중.** `file_format_3_bin/04.Lat_Lon_info/Lat_HSR.npy`·`Lon_HSR.npy` 와 `rdr_500m_latlon.nc` 가 형상 동일·값 상이. v1 ㈑ 그대로. 레포 `dev-package/DATA-REFERENCE.md:55` 와 `:80` 의 진술이 갈림.

㈓ **`file_format_5_HDF5` 명칭 ↔ 실물 HDF4.** 등록 포맷명을 ⓐ `hdf5`(폴더명·지시 축자) ⓑ `hdf4`(실물 매직 `0e 03 13 01`) 중 무엇으로 할지 미정. v1 ㈒ 그대로.

㈔ **drought `#readme` 디렉터리 mtime 변경(15:00)의 사유.** 내부 파일 변화 0건.

㈕ **nc `00.Data` 143건 중 신규 1건의 식별 불가.** 파일 mtime 이 전부 원본 보존값이라 어느 `.nc` 가 추가됐는지 판별 불가. 시각 계열 `202005010000`~`202005012350` 10분 간격 = 하루 144 시각 중 143건이므로 1 시각 결번 — 결번 시각 미측정 `[미확인]`.

㈖ **격자 파일 중복 부착의 전송·과금 기준.** §5-5 참조.

---

## 7. Ted 규칙·v1 과의 불일치

1. **v1 §5 「nc 후보 142건」 ↔ v2 실측 143건.** v1 총계 184 nc 와 v1 세부(142＋1＋1＋10＋31＝185)가 이미 서로 갈림 — v1 계수 오류인지 오늘 ＋1 인지 판별 불가 `[미확인]`. v2 실측 143 을 채택.
2. **v1 §4-2 npy 형상표는 v2 에서 무효.** `<f4 (721,1440)` 6→72 · `<f4 (900,900)` 2→145. v1 표를 인용하지 않는다.
3. **v1 등록안 §8 은 포멧테스트를 `00.Data` 만으로 5건 구성.** Ted 규칙 2(원자료→결과 계보)에 따라 v2 는 결과까지 26건으로 확장 — 불일치가 아니라 규칙 추가에 따른 개정.
4. **v1 열린 질문 ㈐(포맷당 파일 구성)·㈕(Code·Figure 적재 여부)·㈏(SPI·SPEI 묶음)은 Ted 규칙으로 종결.** ㈓(precipitation Lv.0 2분할)도 규칙 1로 종결 = 2건 유지.
5. **Ted 진술 「결과데이터 하고 다 만들어뒀다」 ↔ 실물.** 오늘 결과 데이터가 채워진 것은 grib(slhf·ssr·str 3변수 × 24시각)·nc(143시각) 2종. bin·tif·hdf 의 `02.Results` 는 v1 시점에 이미 존재했고 오늘 변화 0건. **level data 3개 프로젝트에는 오늘 추가된 결과 데이터가 없다.**

---

## 8. 후속 항목 (레포 수정 대상 · 본 조사 미수정)

1. `dev-package/DATA-REFERENCE.md:55` 와 `:80` 의 HSR 격자 정본 진술 상충 — 한 자리로 정리.
2. `dev-package/DATA-REFERENCE.md` 에 `01.level-data/` 3개 프로젝트·GeoPackage 포맷 기재 부재.
3. 같은 문서의 npy 형상 계수는 v1 표 기준일 경우 v2 실측값으로 갱신 필요.
