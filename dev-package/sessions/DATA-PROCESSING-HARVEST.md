# DATA-PROCESSING-HARVEST — 구세대 코드에 있고 기획 정본에 없는 데이터 처리 지식

> **무엇인가** — PoC·그 이전 세대의 **실제로 동작한 데이터 처리 코드**를 읽어, 기획 정본(260818)과 v2 결정 문서가 **덮지 못한 부분**을 file:line 으로 대조한 문서.
> **왜** — 이 지식이 코드에만 있으면 D5(포맷 처리·파이프라인)가 **다시 유도하다 틀리거나 조용히 빠뜨린다.**
> **무엇이 아닌가** — 정본이 아니다. **정본을 고치지 않았다.** ④의 문안은 **초안**이고, 채택은 정본 소유자의 판단이다.
> **읽은 범위** — 아래 ①의 파일 전부를 통독. 측정한 것과 추론한 것을 구분해 적었다.
> *작성 2026-08-23*

---

## ① 무엇을 어디서 찾았는가 — 지도

### 1.1 「v3」의 정체 — 그런 이름의 디렉터리는 없다

**찾은 사실 (측정):**

| 확인한 것 | 결과 |
|---|---|
| 작업공간 전체 `-iname '*v3*'` (maxdepth 4) | **0건** |
| 5개 레포의 브랜치·태그 전수 (`git branch -a` · `git tag`) | `v3` 브랜치·태그 **없음** |
| `20 CoLAB-v1/` | **빈 디렉터리** (파일 0건) — C2(v1 이관)가 아직 안 돌았다 |
| `colab-v2.zip`(작업공간 루트, 200 KB) | v2 문서 묶음 크기이고 데이터 처리 코드가 들어갈 부피가 아니다 |
| v2 문서가 쓰는 「v3」 | **코드가 아니라 비전 문서**를 가리킨다 — `dev-package/PLAN-SoT.md:249` 「hsw Agent-native는 **v3 비전**으로 분리」 · `PLAN-SoT.md:173` 「v3 Agent-native CONCEPT」 · `WORK-UNITS.md:49` 「대화 입구·의도 라우터·협업 프로젝트 — **v3 영역**」. 실물은 `40 COLAB-기획/CoLab_ver2_hsw`(`PLAN-SoT.md:263`) |

**따라서 사용자가 말한 「v3」에 딱 맞는 코드 산출물은 존재하지 않는다.** 대신 실제로 존재하는 **데이터 처리 세대**를 시간순으로 세면 다음과 같고, 그중 **v2 직전의 최신 세대**를 「v3」의 자리에 놓고 harvest 했다.

### 1.2 실제로 존재하는 데이터 처리 세대 — 4세대 (git 날짜 실측)

| 세대 | 실물 | 시점 | 정체 |
|:--:|---|---|---|
| **G0** | `03 Reference-Data/02.File-format/*/01.Code/Lv1_Data Processing.py` (6종) + `3_KWRA_conference/3_해상도변경/code/*.py` (5종) | 데이터 파일 mtime 2025-08 | **연구자 원본 스크립트.** 제품 코드가 아니라 명세의 원천 — `.bin` 포맷 명세가 여기에만 있다 (`SEED-DATA §0-F-4`) |
| **G1** | `00 CoLAB-PoC/backend/app/services/processors/` (base·registry·grib·netcdf·binary·hdf) + `backend/app/core/geo/` | **2026-01-17** 최초 커밋 `ec35300a` 「Hull Clipping fix + Modular processor architecture **v2.5**」, 그 앞에 「GeoGlobe PoC **v2.4.0 / v2.3.0**」 | **COG 변환 파이프라인.** 자체 버전 표기가 **v2.3 → v2.4 → v2.5** 로 올라간다 |
| **G2 (= 「v3」로 본 것)** | `00 CoLAB-PoC/viz-service/` (decoders 5종 + render·png_renderer·cache·upload_buffer) | **2026-05-02** 단일 스쿼시 커밋 `1e8e7c40` 「feat(**E018**): viz-service 가시화 마이크로서비스 — **5포맷** + 시연용 + companion (#89)」 | **G1 다음 세대.** 별도 마이크로서비스로 갈라져 나왔고(`viz-service/README.md:1-20`), **포맷을 5개로 늘렸다**. 자체 버전 번호는 없고 **Epic 태그 `E018`** 로 식별된다 |
| **G3** | `10 CoLAB-Launch/colab-backend-platform/src/colab_backend/bc/pipeline/` | Launch 세대 | ⚠ **스텁이다.** `worker.py` 자체 docstring이 「Real stage execution (rasterio/GDAL format sniffing, COG conversion, …) lives **OUTSIDE** core-api」라 적었고, `execute_stage()` 는 `declared_format` 를 **그대로 되돌려 주는 것**이 전부다(`worker.py:28-41`). geo 라이브러리 import 0건. **harvest 할 처리 지식이 없다** |

> **정직하게 = 「v3」는 못 찾았다.** 그래서 **PoC 를 두 세대(G1·G2)로 갈라** 다뤘고, **v2 직전의 최신 처리 세대는 `viz-service`(E018, 2026-05-02)** 다. G0(연구자 원본)은 명세의 원천이라 함께 넣었다. **Launch(G3)는 스텁이라 뺐다** — 조용히 대체하지 않고 여기 밝힌다.
>
> ⚠ **G1↔G2 는 계승 관계가 아니라 병존이다.** `viz-service/README.md:7-9` 이 「Lives **side-by-side** with the main `backend/` FastAPI app — talks to it only via HTTP, never via shared Python imports」라 못 박았다. **같은 포맷을 두 번 구현했고 규칙이 서로 다르다** — 이 문서의 ⑤가 그 차이를 모은다.

### 1.3 파일 지도 (전부 통독)

**G0 — 연구자 원본** (`03 Reference-Data/`)
- `02.File-format/file_format_1_grib/01.Code/Lv1_Data Processing.py` — cfgrib · 유효 시각 인덱스 5~28
- `02.File-format/file_format_2_nc/01.Code/Lv1_Data Processing.py` — netcdf4 · GK2A LST · 짝 파일 `04.Lat_Lon_info/gk2a_ko020lc_latlon.nc`
- `02.File-format/file_format_3_bin/01.Code/Lv1_Data Processing.py` — **`.bin` 명세의 유일한 원천** (`SEED-DATA §0-F-4`)
- `02.File-format/file_format_4_tif/01.Code/{Lv1_Data Processing.py, …_SY.py, …_SY_ver.2.py}` — HLS S30
- `02.File-format/file_format_5_HDF5/01.Code/Lv1_Data Processing.py` — rasterio subdataset · MODIS · 모자이크
- `3_KWRA_conference-…/3_KWRA_conference/3_해상도변경/code/{01_nearest_neighbor,02_bilinear,03_idw,04_cokriging,05_visualize}.py` — **다운스케일 4종**

**G1 — PoC backend** (`00 CoLAB-PoC/backend/`)
- `app/services/processors/{base,registry,__init__}.py` · `{grib,netcdf,binary,hdf}/processor.py`
- `app/core/geo/{__init__,longitude,fill_values}.py` — 결측·경도 정규화 SSoT
- `app/services/format_detector.py` — 업로드 계층 별도 감지기 (E014)
- `app/api/tiles.py` — 타일 서빙

**G2 — PoC viz-service** (`00 CoLAB-PoC/viz-service/`)
- `app/decoders/{base,dispatch,grib,netcdf,binary_hsr,geotiff,hdf5_modis}.py`
- `app/{render,png_renderer,cmap_registry,upload_buffer,config,cache,formats}.py`
- `tests/test_decoder_*.py` — 기대 상수가 테스트에 박혀 있다

**정본·v2 쪽 (대조 상대)**
- 정본 = `40 COLAB-기획/Co-Lab_ver2_1차마일스톤_목업패키지_260818_이태헌/` (`PLAN-SoT.md:263` 이 지정)
  - `에픽/E-00_공통_기반/documents/DataModel_공통_기반.md`
  - `에픽/E-04_업로드와_계보_확정/documents/{PRD,Policy}_업로드와_계보_확정.md`
  - `에픽/E-03_데이터셋_상세/documents/Policy_데이터셋_상세.md`
- v2 = `30 CoLAB-v2/dev-package/{PLAN-SoT,WORK-UNITS,SEED-DATA,DOMAINS}.md` · `30 CoLAB-v2/contracts/events/core-pipeline.json` · `30 CoLAB-v2/services/pipeline-worker/README.md`

---

## ② 세대별 처리 능력 실측

> 표기 — **[읽음]** = 코드에서 직접 확인 · **[추론]** = 코드에서 도출했으나 실행으로 확인하지 않음.

### 2.1 포맷 감지

| 세대 | 방식 | 실물 |
|---|---|---|
| G1 registry | **확장자 전용.** 매직바이트 안 본다 | `backend/…/processors/registry.py:70-97`. 미지 확장자 → `DataFormat.UNKNOWN`, `get_processor()` 가 **예외가 아니라 `None`** 반환(`registry.py:100-111`) **[읽음]** |
| G1 `.gz` 처리 | 안쪽 확장자를 먼저 본다 — `{inner}.gz` → 맨 `inner` 순 | `registry.py:85-96` · 같은 로직이 `base.py:173-180` 에 **중복** **[읽음]** |
| G1 업로드 계층 | 별개 감지기(E014). 확장자 표 + **보안 강제** | `backend/app/services/format_detector.py:28-75`. `RISKY_RENDER_EXTENSIONS`(`.html .htm .svg .xhtml .xml .xsl .xslt .js .mhtml`)는 선언 MIME 과 무관하게 `ContentType` 를 `application/octet-stream` 으로 **강제**(`:116-157`). MIME 은 아예 참조하지 않는다 — 「MIME type is informational only; this module does not consult it.」(`:10`) **[읽음]** |
| **G2** | **매직바이트 표.** `_sniff_format` | `viz-service/app/render.py:75-79` — 순서대로 `b"GRIB"`→grib · `b"CDF"`→nc · `b"\x89HDF"`→hdf · `b"\x1f\x8b"`→bin(gzip) · `b"II*\x00"`/`b"MM\x00*"`→tif. 미지 → `HTTPException(415, VIZ-4001)`(`:488-496`). **파일명·확장자를 쓰지 않는다** **[읽음]** |
| G1 HDF 내부 | **HDF4/HDF5 를 매직으로 가른다** | `hdf/processor.py:79-87` `b'\x0e\x03\x13\x01'`(주석 `# HDF4 magic number: 0x0e 0x03 0x13 0x01`) · `:89-97` `b'\x89HDF\r\n\x1a\n'`. 둘 다 아니면 **HDF4 먼저 시도 → 실패 시 HDF5** 로 맹목 캐스케이드(`:261-269`, 주석 `# 확장자로 추측`) **[읽음]** |

### 2.2 포맷별 파싱

| 포맷 | G0 | G1 | G2 |
|---|---|---|---|
| GRIB | `xr.open_dataset(engine="cfgrib")` (`file_format_1_grib/…:65,105`) | 같음 (`grib/processor.py:51,114`) | 같음 (`decoders/grib.py:452,460,489`) |
| NetCDF | `engine="netcdf4"` · 변수 `LST` 하드코딩 (`file_format_2_nc/…:54,80`) | `engine="netcdf4"` · `lat/lon/latitude/longitude/gk2a_imager_projection` 을 `data_vars` 에서 제외(`netcdf/processor.py:62-63,112-113`) | `engine="netcdf4"` · **대소문자 관용 변수 해석** — `variable` → `.upper()` → `.lower()` 순 시도(`decoders/netcdf.py:875-878`), 없으면 `KeyError` |
| Binary | 헤더 1024B + **3블록** 읽기 (`file_format_3_bin/…:75-103`) | 헤더 1024B skip · int16 LE · `nx=2305, ny=2881` · **반사도만** (`binary/processor.py:37-39,98-99`) | 동일 구조 상수(`decoders/binary_hsr.py:45-51`) · **반사도만** `np.frombuffer(dtype="<i2", count=NX*NY, offset=1024)`(`:289-291`) |
| GeoTIFF | `rasterio` · HLS S30 (`…_SY.py:33-35`) | **없음** | `rasterio.open` · 밴드 = `band1..bandN`(`decoders/geotiff.py:22-24`) |
| HDF | `rasterio.open(...).subdatasets` (`file_format_5_HDF5/…:70-71`) | HDF4=rasterio subdataset · HDF5=h5py 재귀 탐색(`hdf/processor.py:114-117,139-152`) | rasterio subdataset(`decoders/hdf5_modis.py`) |

### 2.3 좌표계 — 실제로 코드에 박힌 값

| 항목 | 실물 |
|---|---|
| **목표 좌표계** | **`EPSG:4326` 단일 하드코딩.** G1 `base.py:149` `OUTPUT_CRS = CRS.from_epsg(4326)` — 네 프로세서 전부 여기로 수렴. G2 `decoders/geotiff.py:53` · `decoders/hdf5_modis.py:76` 리터럴 `"EPSG:4326"` **[읽음]** |
| **GK2A LCC proj4 (원문)** | `netcdf/processor.py:245-248` — `+proj=lcc +lat_0={lat_0} +lon_0={lon_0} +lat_1={lat_1} +lat_2={lat_2} +x_0={false_easting} +y_0={false_northing} +datum=WGS84 +units=m`. **속성이 없을 때의 기본값** `lat_0=38.0 lon_0=126.0 lat_1=30.0 lat_2=60.0 pixel_size=2000.0` (`:222-228`) **[읽음]** |
| **MODIS Sinusoidal** | `hdf/processor.py:167` · `:64` 리터럴 `"SR-ORG:6974"`. G2 는 하드코딩하지 않고 SDS 메타의 `crs` 를 읽는다 **[읽음]** |
| **HSR 반사도** | G1 `binary/processor.py:72` 는 `crs="EPSG:4326"` 로 **선언만** 하고 bbox 도 근사 고정(`lat_range=(32.0,44.0) lon_range=(120.0,136.0)`, `:69-70`). 실제 좌표는 외부 짝 파일 `rdr_500m_latlon.nc` 에서 온다 **[읽음]** |
| **재투영 방법 — 규칙 격자** | HDF4 만 `rasterio.warp.calculate_default_transform` + `reproject(..., Resampling.nearest)` (`hdf/processor.py:552,555-559,568-579`). 주석: 「rasterio.warp.reproject를 사용하여 GDAL 네이티브 워핑 수행 … **60-80% 성능 향상**」(`:477-479,546-548`) **[읽음]** |
| **재투영 방법 — 곡선 격자** | `base.py::_write_cog_curvilinear` (`:244-400`) — 격자 가장자리로 Delaunay hull → 커버리지 마스크 → `scipy.spatial.cKDTree` **1회 구축** → `query(k=1)`. **즉 최근접 이웃이다.** 주석에 최적화 이력: 「AS-IS: griddata 2회 호출 (KD-tree 매번 재구축) / TO-BE: cKDTree 1회 구축 후 재사용 (**20-30% 성능 향상**)」(`:255-257`) **[읽음]** |
| **재투영 방법 — G2** | `pyproj.Transformer.from_crs(src, "EPSG:4326", always_xy=True)` 를 **픽셀 중심 meshgrid 에 전부 적용**(`geotiff.py:46-57` · `hdf5_modis.py:68-84`). **리샘플이 아니다** — H×W 는 그대로 두고 좌표만 옮기므로 결과가 **불규칙(곡선) 격자**가 된다. 그래서 렌더가 `pcolormesh(..., shading="auto")` 여야 한다(`png_renderer.py:74-82`) **[읽음]** |
| **NetCDF·Binary 재투영** | **G2 는 아예 하지 않는다** — 짝 파일/자체 메타의 lon/lat 을 이미 지리좌표로 믿는다 **[읽음]** |

### 2.4 래스터 산출 — COG

| 항목 | 실물 |
|---|---|
| 라이브러리 | `rio_cogeo.cogeo.cog_translate` + `rio_cogeo.profiles.cog_profiles` (`base.py:21-22`) |
| 프로파일 | **`cog_profiles.get("deflate")` 하나뿐**(`base.py:238,392` · `hdf/processor.py:603`). **blocksize·overview 단계·overview 리샘플을 어디서도 넘기지 않는다** — 전부 `rio_cogeo` 기본값에 맡긴다 **[읽음]** |
| nodata | **항상 `np.nan`**(`base.py:234,385` · `hdf/processor.py:598`). 따라서 출력 dtype 이 float 로 고정된다 **[추론: 코드가 float 를 강제하는 지점을 직접 보진 않음]** |
| 쓰기 절차 | GTiff 임시본(`.temp.tif`) → `cog_translate` → `temp_path.unlink(missing_ok=True)`. **같은 3단계가 3곳에 복제**(`base.py:223-240` · `base.py:373-395` · `hdf/processor.py:586-606`) **[읽음]** |
| 스레드 | `GDAL_NUM_THREADS: "ALL_CPUS"` 를 **곡선격자 경로와 HDF4 경로에만** 넘긴다(`base.py:393-394` · `hdf/processor.py:604-605`). 규칙격자 `write_cog` 는 안 넘긴다 — **비대칭** **[읽음]** |
| **COG 검증기** | **없다.** `backend/app/core/geo/__init__.py:18` 에 「cog_validator: COG 구조 검증 (**현재 inline**)」이라 적혀 있으나 구현체가 없다 **[읽음]** |
| **G2 의 COG** | **없다.** viz-service 는 COG·타일·overview·명시적 다운샘플이 **전무**하고 `matplotlib` PNG 만 낸다(`png_renderer.py:85-92`, `figsize=(8,6) dpi=100` 고정 `:71`) **[읽음]** |

### 2.5 도메인 처리

| 항목 | 실물 |
|---|---|
| **Marshall-Palmer (Z→R)** | 세 세대가 **같은 상수**를 쓴다. G0 `file_format_3_bin/…:116-117` · G1 `binary/processor.py:106-110` · G2 `decoders/binary_hsr.py:183-186` — `ref/100.0` → `Z = 10**(dBZ/10)` → `R = (Z/200)**(1/1.6)`. **200 과 1.6 은 하드코딩, 설정 손잡이가 없다.** G0 에는 대안 경험식이 **주석 처리**돼 남아 있다 — `10**(x/10)`, `**0.60413`, `×0.0683` (`file_format_3_bin/…:111-113`) **[읽음]** |
| | G2 테스트가 값을 못 박는다 — `ref=3500 → 35 dBZ → Z≈3162.28 → R≈5.615 mm/h`(`tests/test_decoder_binary_hsr.py:97-109`) **[읽음]** |
| **결측 — 정확 매칭** | `backend/app/core/geo/fill_values.py::mark_fill_values_as_nan()` — `np.isin()` **정확 매칭**. docstring 이 과거 버그를 기록한다: 「HDF MODIS 의 `fill_mask = data >= 249` 패턴 대체. 기존 코드는 정확한 enum (249-255) 이 아닌 `>= 249` (**256, 1000 등도 포함**)이라 **over-mask 위험**. 본 함수는 정확 매칭만.」(`fill_values.py:49-52`) **[읽음]** |
| **MODIS fill enum** | `list(range(249,256))` = 249~255. 의미까지 적혀 있다 — 249=ocean · 250=inland_water · 251=barren · 252=snow/ice · 253=urban · 254=unclassified · 255=fill (`hdf/processor.py:58,66-74`) **[읽음]** |
| **scale_factor 순서 함정** | HDF4 경로는 공용 유틸을 **일부러 안 쓴다**. 주석: 「scale_factor 적용 **후** 같은 위치를 NaN 으로 표시해야 하므로 `mark_fill_values_as_nan` utility 가 아니라 mask 를 별도 보존.」(`hdf/processor.py:528-529`) — **fill 판정은 스케일 적용 전 raw 값에, NaN 대입은 스케일 적용 후에** (`:526-542`) **[읽음]** |
| **add_offset** | **어느 세대도 읽지 않는다.** `scale_factor`(=`ds.scales[0]`)만 곱한다 — G1 `hdf/processor.py:522,536-538` · G2 `hdf5_modis.py:672` · G0 `file_format_5_HDF5/…:94,156`. MODIS 계열이 offset 을 갖는 경우 **값이 통째로 틀어진다** **[추론 — 대상 파일에 offset 이 실제로 있는지는 확인하지 않음]** |
| **임계 방식 결측 (SSoT 이탈)** | 규칙 문서(`processors.md`)가 「hardcoded magic number (예: `data >= 249`) 금지. `FormatConfig.fill_values` 가 진실의 원천」이라 선언했는데, **Binary·NetCDF 는 지키지 않는다** — Binary `np.where(ref_array > -20000, …, 0)` 후 `> 0` 필터(`binary/processor.py:104-105`, 선언된 `fill_values=[-20000]` 은 `:51` 에만 있고 안 쓰인다) · NetCDF `np.where(data > 0, data, np.nan)`(`netcdf/processor.py:122`). `fill_values.py:7-8` 이 이 미해결을 예고한다: 「Threshold-based fill (Binary 의 `ref < -20000` 같은 경우) 은 의미가 다르므로 별도 함수(`apply_threshold_mask`) 가 필요할 때 추가」 — **그 함수는 아직 없다** **[읽음]** |
| **경도 0-360 → -180-180** | `backend/app/core/geo/longitude.py::normalize_longitude_to_180()`. `lon.max()<=180` 이면 무동작(`:70-71`); 아니면 `np.searchsorted(lon,180)` 으로 자르고 **lon 과 data 를 같이 이어붙여 재정렬**(`:73-79`); 180 을 실제로 넘지 않는 부분영역(예 200~340)이면 **재정렬 없이 `-360` 만**(`:80-83`). 규칙격자 전 포맷에 적용(`base.py:213-215`) **[읽음]** |
| | ⚠ 곡선격자 경로는 **다른 규칙**을 쓴다 — `np.where(lon > 180, lon - 360, lon)` 단순식, 재정렬 없음(`base.py:271`). 최근접 KD-tree 라 순서가 무의미하다는 의도적 비대칭 **[읽음 + 추론(의도 부분)]** |
| **시간축** | **GRIB 만 다중 시각.** `TimeSelection` 이 `index/indices/range/all` 4모드(`base.py:83-132`), 기본은 **첫 스텝만** — 「기본 동작: 첫 번째 시간 스텝(index=0)만 처리합니다.」(`grib/processor.py:135-137`). NetCDF·Binary·HDF 는 `time_steps=[]` 리터럴(`netcdf/processor.py:83` · `binary/processor.py:68` · `hdf/processor.py:163`) — **한 파일 = 한 시각** 전제 **[읽음]** |
| **GRIB 유효 인덱스 5~28** | G0 영어 주석: 「In this dataset, indices 5–28 contain valid data. Other indices are filled with NaNs and are **intentionally ignored**.」(`file_format_1_grib/…:94-101`), 하드코딩 `if 5 <= idx <= 28`(`:121`). **G2 가 이 매직넘버를 그대로 상수로 승격**했다 — `_VALID_TIME_IDX_MIN=5`, `_VALID_TIME_IDX_MAX=28`(`decoders/grib.py:31-32`), 범위 밖은 `IndexError`(`:483-487,500-504`) **[읽음]** |
| **모자이크** | G0 `rasterio.merge.merge` 로 MODIS 두 타일 h27v05+h28v05 결합(`file_format_5_HDF5/…:277`). ⚠ **scale_factor 를 병합 후 마지막 타일 것 하나로만 적용**(`:269-280`) — 타일별 scale 이 다르면 조용히 틀린다 **[추론 — 주석에 경고 없음, 코드 구조에서 도출]**. G2 는 `len>1` 일 때만 merge, 1건이면 `decode()` 로 폴백(`hdf5_modis.py:156-206,165-166`) **[읽음]** |
| **MODIS SDS 허용목록** | G2 `_ALLOWED_SDS_SUFFIXES = ("Fpar_500m","Lai_500m")`(`hdf5_modis.py:47`) — QC·StdDev SDS 를 목록에서 뺀다(`:106-115`). 매칭은 **콜론 뒤 토큰 완전일치**여야 한다 — 부분일치면 `Fpar_500m` 이 `FparExtra_QC` 와 충돌한다(주석 `:59-61`, 코드 `:595`) **[읽음]** |
| | G1 은 대신 우선순위 + **개수 상한** — `PRIORITY_VARIABLES=["Fpar_500m","Lai_500m","sur_refl"]`(`hdf/processor.py:50`), HDF5 `datasets_to_process[:3]  # 최대 3개`(`:437`), HDF4 `priority_sds[:2] + other_sds[:1]  # 최대 3개`(`:510`) **[읽음]** |
| **다운스케일 4종 (G0/KWRA)** | 전부 GK-2A NDVI 2km→1km, 충청권 고정 bbox `126.70~127.96 / 36.08~37.36`, `TARGET_RES=0.01°`, 격자 `126×128`, 목표 `"EPSG:4326"`, 출력 `GTiff/float32/nodata=np.nan/compress="deflate"` **[읽음]** |
| | ① `01_nearest_neighbor.py` `Resampling.nearest`(`:138-150`). 한계를 한국어로 명시 — 「단점 : (1) 계단 모양(blocky) 결과, (2) 공간적 부드러움(smoothness) 완전 부재, (3) **사실상 픽셀 복제 → 정보량 증가는 없음**.」(`:16-27`) |
| | ② `02_bilinear.py` `Resampling.bilinear`(`:317`). **함정 주석** — 「NaN 입력은 그대로 NaN 으로 전파됨(src_nodata=NaN). **결측이 인접해 있을 경우, 가중치 합이 0 이 되어 결과도 NaN.**」(`:112-114`) — 결측 영역이 **번진다** |
| | ③ `03_idw.py` cKDTree KNN-IDW, `k=12 p=2.0`, 도→미터 평면근사 `DEG_TO_M_LAT=111320.0`·경도는 `cos(lat)` 배, 0.3°(~30km) 패딩 후 부분집합에 KDTree(`:102-128,173-179`), 0나눗셈 방지 `eps=1e-6`(`:202`) |
| | ④ `04_cokriging.py` — **이름과 실제가 다르다.** 진짜 co-kriging 이 아니라 **회귀 크리깅**(NDVI~DEM OLS → 잔차를 `pykrige.ok.OrdinaryKriging`, `variogram_model="spherical"`, `coordinates_type="geographic"`). DEM 은 100m→2km `Resampling.average`. 결과를 `[0,1]` 로 클립. **축 방향 함정 주석** — 「pykrige 의 `execute('grid', gridx, gridy)` 는 gridy 가 **오름차순이어야 함** → 뒤집어 전달 … 원래의 위→아래 순서(이미지 좌상단 기준) 로 되돌리기 위해 **flipud**.」(`:281-291`) |

### 2.6 실패 처리

| 항목 | 실물 |
|---|---|
| **G1 — 부분 성공을 허용한다** | HDF4 는 서브데이터셋마다 try/except 후 `continue`(`hdf/processor.py:624-628`) — 일부만 COG 가 나올 수 있다. **전부 실패했을 때만** `raise ValueError("No output files generated…")`(`:271-272`) **[읽음]** |
| **G1 — 조용한 강등** | ① HDF5 실패 시 HDF4 로 재시도(`:245-259`) · 미지 매직은 HDF4→HDF5 맹목 시도(`:261-269`) ② NetCDF 투영 계산 실패는 `(None,None)` 반환 후 삼켜짐(`netcdf/processor.py:255-257`), 최종엔 **근사 규칙격자로 폴백**(`:184-194`) ③ Binary 짝 파일을 못 읽으면 **합성 규칙격자로 폴백**(`binary/processor.py:129-159`) ④ Hull 계산 실패는 `in_hull=all True` 로 계속 — `print("  Warning: Hull computation failed …")`(`base.py:298-314`). **⚠ ②③ 은 좌표가 조용히 틀려도 성공으로 끝난다** **[읽음 + 추론(위험 평가)]** |
| **G1 타일 API** | 예외를 `tile_errors.log` 에 남기고 **투명 빈 타일**을 준다(`tiles.py:71-79,519-522`). COG 누락도 빈 타일(`:390-391,458-460`), 데이터셋 자체가 없을 때만 404(`:387-388`), 미처리면 400(`:357-358,367,377-380`) **[읽음]** |
| **G2 — 오류 분류표가 있다** | `render.py:214-311` — `TimeoutError`→504 `VIZ-5001` · `IndexError`(시각 인덱스)→400 `VIZ-4005` · `KeyError`(변수)→400 `VIZ-4004` · `ValueError "VIZ-4009"`(압축폭탄)→400 · `ValueError "VIZ-4010"`(NC 좌표 근거 없음/shape 불일치)→415 · 컬러맵 오류→400 `VIZ-4007` · `vmin>=vmax`→400 `VIZ-4008`(`:176-185`) · 미지 매직→415 `VIZ-4001`(`:488-496`) · 짝 파일 포맷 불일치→415 `VIZ-4011`(`:505-518`) · 프레임 토큰 만료→410 `VIZ-4006`(`:596-622`) **[읽음]** |
| **G2 — 한도 수치** | 업로드 `max_upload_bytes=524_288_000`(500MB, `config.py:31`), 1MB 청크 누적으로 초과 즉시 중단·파일 삭제·413(`render.py:396-421`) · 본체+짝 파일 합계 `max_companion_combined_bytes=1_073_741_824`(1GB, `config.py:34`)→413 `VIZ-4012` · **gzip 압축폭탄** `bin_decompress_max_bytes=629_145_600`(600MB, `config.py:32`)→`VIZ-4009`(`binary_hsr.py:92-96,179-212`) · 디코드 타임아웃 `decoder_timeout_sec=60`(`config.py:60`) **[읽음]** |
| **G2 — 파일명 불신** | 업로드 파일명을 **버리고** `{uuid4().hex}.{ext}` 로 재명명, 토큰 `secrets.token_urlsafe(16)`(22자), 경로결합 전 `^[A-Za-z0-9_-]{22}$` 정규식 검사 — 주석 태그 「TM-E」(`upload_buffer.py:33-43,52-54`) **[읽음]** |
| **G2 — 최소 크기 검사** | `len(raw) < 1024 + NX*NY*2` 면 `ValueError("BIN HSR header/payload too small…")`(`binary_hsr.py:281-285`) **[읽음]** |

---

## ③ 정본 대비 커버리지 행렬

> **판정 기준** — **기재됨** = 정본이 그 규칙을 말한다 · **부분** = 정본이 현상·화면만 말하고 처리 규칙은 없다 · **없음** = 정본 어디에도 근거가 없다(`[정본 무근거]`).
> **정본 = 260818 패키지**다. `dev-package/*.md` 와 `contracts/**` 는 **정본이 아니라 레포 판단**이라 별도 열로 갈랐다 — 계약 자신이 그렇게 적었다(`contracts/events/core-pipeline.json:135,175`: 「정본 E-04 에 직접 근거가 없다 … `DOMAINS §2 D5` 가 근거다」).

| # | 능력 (출처) | 정본 | 정본 근거 | v2 레포측 근거 |
|:--:|---|:--:|---|---|
| 1 | **매직바이트 감지 표** (`render.py:75-79`) | **없음** | — `Policy_업로드…:116` 은 「grib · nc · bin · tif · HDF5 등 [가정] **형식 제한 없음, 헤더 인식만 형식별**」로 *형식별로 다르다*까지만 | `SEED-DATA:279` `DR-3`(확장자가 거짓말) · `core-pipeline.json:53-56`(포맷값 enum 안 만듦) |
| 2 | **`\x89HDF` 충돌 — NetCDF4 와 HDF5 가 같은 매직** (`render.py:85-86`) | **없음** | — | `SEED-DATA:51` 이 `.nc` 의 실체가 HDF5 컨테이너임은 적었으나 **감지 불능이라는 사실**은 없다 |
| 3 | **HDF4 매직 `0e031301` 분기** (`hdf/processor.py:79-97`) | **없음** | — `DataModel:66` 은 「HDF5」라 적었다 | `SEED-DATA:21` `F-2` **기재됨** |
| 4 | **`.gz` 안쪽 확장자 투시** (`registry.py:85-96`) | **없음** | — | 없음 |
| 5 | **위험 확장자 강제 octet-stream** (`format_detector.py:116-157`) | **없음** | — | 없음 |
| 6 | **목표 좌표계 EPSG:4326** (`base.py:149`) | **없음** | — 정본은 좌표계를 **표시 항목**으로만 다룬다(`Policy_데이터셋_상세:118` 기본정보 9칸 · `PRD_업로드…:73`) | `core-pipeline.json:145-149` — **일부러 상수로 안 박음** |
| 7 | **좌표계 변환 자체** | **없음** | — | `core-pipeline.json:135` 이 **명시적으로 「정본 무근거」라 자백**하고 `DOMAINS.md:68` 을 근거로 든다 |
| 8 | **GK2A LCC proj4 문자열·기본값** (`netcdf/processor.py:222-248`) | **없음** | — | `services/pipeline-worker/README.md:16` 「NetCDF · GK2A · LCC → WGS84」 **한 줄뿐** |
| 9 | **MODIS Sinusoidal `SR-ORG:6974`** (`hdf/processor.py:167`) | **없음** | — | `pipeline-worker/README.md:18` 한 줄뿐 |
| 10 | **곡선격자 리샘플 = cKDTree 최근접** (`base.py:337,359,366`) | **없음** | — | 없음 (`pipeline-worker/README.md:17` 「Binary · HSR · Curvilinear → WGS84」로 사실만) |
| 11 | **HDF4 워핑 = `Resampling.nearest`** (`hdf/processor.py:555-559`) | **없음** | — | 없음 |
| 12 | **COG 프로파일 = `deflate` 기본값, blocksize·overview 미지정** (`base.py:238`) | **없음** | — 정본에 **「COG」라는 말이 없다** | `core-pipeline.json:175` 가 이를 자백 — 「**정본 E-04 에 `COG` 라는 말은 없다**」 |
| 13 | **overview 단계 수** | **없음** | — | `core-pipeline.json:185-189` `overviewLevels` 필드 **있음**(값 규칙은 없음) · `viz-render/README.md:20` 「인제스트 시 overview를 미리 만든다」 |
| 14 | **이미 COG 인 tif 판별 규칙** | **없음** | — | `SEED-DATA:22,278` `DR-2`·`F-3` **기재됨(요구만)** — 「**정본**(②의 판정)」이라 **정본에 공을 넘겨 둔 상태** |
| 15 | **nodata = NaN** (`base.py:234`) | **없음** | — | 없음 |
| 16 | **MODIS fill enum 249~255 정확매칭** (`fill_values.py:49-52`) | **없음** | — | 없음 |
| 17 | **fill 판정↔scale_factor 순서** (`hdf/processor.py:526-542`) | **없음** | — | 없음 |
| 18 | **`add_offset` 미처리** | **없음** | — | 없음 |
| 19 | **Marshall-Palmer Z=200R^1.6** (3세대 공통) | **부분** | `SEED-DATA:179` 가 「*Z-R 관계식(Marshall-Palmer)의 한계를 U-Net 이 보완*」으로 **이름은 안다**. 상수·적용 순서는 없다 | `SEED-DATA:23` `F-4` **기재됨** |
| 20 | **`.bin` 바이트 명세** (`file_format_3_bin/…:75-103`) | **없음** | — | `SEED-DATA:23,281` `F-4` **기재됨(불일치 경고 포함)** |
| 21 | **경도 0-360 정규화 + 180 교차 재정렬** (`longitude.py:70-83`) | **없음** | — | `pipeline-worker/README.md:15` 한 줄 · **`〈51〉` 로 GRIB 범위 밖** |
| 22 | **시간축 — 한 파일 한 시각 vs 다중 시각** | **부분** | `Policy_데이터셋_상세:192` 이 **층마다 시각을 따로 고른다**·「억지로 맞추면 **없는 시각을 있는 것처럼 그린다**」로 *화면 규칙*은 못 박았다. 파서 층 규칙은 없다 | `core-pipeline.json:83` 조각 합치기 = 기간 합집합 |
| 23 | **GRIB 유효 인덱스 5~28** (`decoders/grib.py:31-32`) | **없음** | — | 없음 (`〈51〉` 로 범위 밖이나 **함정의 종류**는 남는다) |
| 24 | **MODIS 모자이크·SDS 허용목록·개수 상한** (`hdf5_modis.py:47` · `hdf/processor.py:437,510`) | **없음** | — | 없음 |
| 25 | **다운스케일 4종 (nearest·bilinear·IDW·회귀크리깅)** | **부분** | `DataModel:89` 「가공 방식 … **관계에 붙는다**」 · `:96` 이 **보조입력 개념의 실례로 다운스케일을 든다**(「성긴 격자를 촘촘하게 만들 때 지형 고도 자료를 같이 넣는 방식」) — **어휘는 있고 방법 목록·한계는 없다** | `WORK-UNITS.md:144` G8 온톨로지 범위에 「가공 방식 어휘」 · `DOMAINS.md:77` D9 「집계·보간·크롭·리샘플」 |
| 26 | **bilinear 의 NaN 번짐** (`02_bilinear.py:112-114`) | **없음** | — | 없음 |
| 27 | **pykrige 축 오름차순 함정** (`04_cokriging.py:281-291`) | **없음** | — | 없음 |
| 28 | **기준 격자(짝) 파일 개념** | **기재됨** | `DataModel:109` 「본체만으로는 그릴 수 없는 포맷에서 위경도를 담은 짝 파일 … 데이터셋당 0건 또는 1건」 · `Policy_업로드…:191-192` · `Policy_데이터셋_상세:200` **`짝 파일 없이 그려 보기`** | `core-pipeline.json:190-193` `referenceGridAvailable` |
| 29 | **짝 파일 해석 우선순위 + shape 검증** (`decoders/netcdf.py:77-100,84-99`) | **없음** | — 정본은 「있다/없다」까지만 | 없음 |
| 30 | **짝 파일 포맷 호환 화이트리스트** (`render.py:87-101`) | **없음** | — | 없음 |
| 31 | **조각 일부 실패 → 읽은 것으로 그린다** | **기재됨** | `Policy_업로드…:9절` 「조각 72개 중 3개를 읽지 못했어요 … **미리보기를 통째로 막지 않는다**」 + 못 읽은 조각의 **시각을 이름으로** · `Policy_데이터셋_상세:241` | `core-pipeline.json:83,181` **정확히 이 규칙으로 설계됨** |
| 32 | **헤더 못 읽음 → 등록은 막지 않는다** | **기재됨** | `Policy_업로드…:3.3` · `:9절` · `PRD:118` | `core-pipeline.json:83` `variables` 의 `null`↔`[]` 구분 규칙까지 |
| 33 | **조각 포맷이 서로 다르면 한 데이터셋이 아니다** | **기재됨** | `DataModel:115-116` 「**모든 조각이 같아야 한다**」 | `core-pipeline.json:61-64` `uniform:false` → `upload.failed` |
| 34 | **그릴 수 없는 형식도 등록·다운로드는 된다** | **기재됨** | `Policy_업로드…:9절` · `Policy_데이터셋_상세:199,215` | `core-pipeline.json:48` |
| 35 | **업로드/디코드 크기·시간 한도 수치** | **부분** | `Policy_업로드…:9절` 「그리다 시간 초과」·「올리다가 끊겼어요」로 **상황만**. **수치가 없다** | 없음 (`PoC config.py:31,32,34,60` 에 실측 기본값이 있다) |
| 36 | **압축폭탄 방어** (`binary_hsr.py:92-96`) | **없음** | — | 없음 |
| 37 | **업로드 파일명 불신·경로탈출 방어** (`upload_buffer.py:52-54`) | **없음** | — | 없음 |
| 38 | **미지 포맷 처리 = 예외가 아니라 `None`** (`registry.py:100-111`) | **부분** | `Policy_업로드…:116` 「인식 불가 형식도 **올릴 수는 있다**」 | `core-pipeline.json:53` `format:null` 허용 |
| 39 | **좌표를 못 구하면 근사 격자로 조용히 폴백** (`netcdf/processor.py:184-194` · `binary/processor.py:129-159`) | **없음** | — 정본은 오히려 **반대 정신** — 「없는 시각을 있는 것처럼 그린다」를 금지(`Policy_데이터셋_상세:192`) | G2 가 이 폴백을 **버그로 판정하고 `VIZ-4010` 예외로 바꿨다**(`decoders/netcdf.py:84-99`) |
| 40 | **미리보기 = 서버 렌더** | **기재됨** | `Policy_데이터셋_상세:207` · `Policy_업로드…:193` (단계 3개 문구까지) | `DOMAINS.md:70` D7 |
| 41 | **D5 자체의 작업지시** | — | — | ⚠ **`WORK-UNITS.md §6` T-D 표에 D5 행이 없다.** 정의된 행은 `D1·D2·D2b·D3·D3b` 뿐인데 `WORK-UNITS.md:164` P2 의 진입조건은 「**D5 D4**」다 |

---

## ④ 갭별 보강 문안 초안

> **성격** — 정본 어투(한국어·개조식)로 쓴 **초안**이다. **채택 여부·귀속 문서는 정본 소유자가 정한다.** 각 항목에 「어디에 붙일 것 같은가」를 제안으로만 달았다.
> **랭킹** = 「안 적어 두면 D5 가 조용히 틀릴 위험」 순.

### G-1 〔최우선〕 D5 작업지시서가 없다 — 문서 구조의 구멍

**갭** — `WORK-UNITS.md:164` 가 P2 의 진입조건을 「D5 D4」로 두었는데, `§6 T-D` 표(`:148-156`)에 **D5·D4·D6·D7 행이 아예 없다.** `DOMAINS.md:68` 이 D5 의 소유물을 열거하고 `services/pipeline-worker/README.md` 가 규칙 4개를 적었을 뿐, **완료 판정이 정의된 작업 단위가 없다.**

**제안 위치** — `WORK-UNITS.md §6` (정본이 아니라 v2 문서)

**문안 초안:**
> | **D5** | **포맷 처리·인제스트 파이프라인** — 지원 포맷 `NetCDF · Binary · HDF4 · GeoTIFF`(`〈51〉`)의 매직바이트 감지 · 헤더 파싱 · 좌표계 정규화 · COG 생성 · overview 선생성 · 실패 분류. 함정 목록의 입력 = `sessions/DATA-PROCESSING-HARVEST.md` | D2 · C3 | ① **4종 각각** 실파일 1건이 감지→파싱→좌표계→COG 까지 완주 ② **음성 시험 3종 green** — (가) 이미 COG 인 tif 가 산출물로 기록되지 않는다(`DR-2`) (나) `.nc` 확장자를 가진 HDF5 컨테이너가 확장자가 아니라 매직으로 판정된다(`DR-3`) (다) 좌표를 못 구한 파일이 **근사 격자로 조용히 폴백하지 않고** 실패로 남는다 |

### G-2 포맷 감지는 매직바이트로 한다 — 표와 충돌 사례까지

**갭** — 정본 `Policy_업로드와_계보_확정.md:116` 은 「헤더 인식만 형식별」까지만 말한다. **무엇을 근거로 형식을 가르는지**가 없다. PoC 는 두 방식이 병존했고(G1 확장자 / G2 매직) **후세대가 매직으로 갈아탔다.**

**제안 위치** — 정본 `Policy_업로드와_계보_확정.md §5 입력값 규칙 — 파일` 아래 (또는 `SEED-DATA §DR-3` 확장)

**문안 초안:**
> **형식은 파일 이름이 아니라 파일 첫 바이트로 가른다.**
> - **근거** — 확장자가 거짓말을 한다. 원천의 `.nc` 는 실제로 HDF5 컨테이너다(`SEED-DATA §0 DR-3`). 확장자를 믿으면 **NetCDF 파서로 HDF5 를 열려다 실패**하고, 그 실패가 「파일이 깨졌다」로 보고된다.
> - **판별 바이트** — `GRIB`→GRIB · `CDF`→NetCDF classic · `\x89HDF`→HDF5 계열 · `\x0e\x03\x13\x01`→**HDF4** · `\x1f\x8b`→gzip(안쪽을 다시 판별한다) · `II*\x00`/`MM\x00*`→TIFF.
> - ⚠ **`\x89HDF` 는 NetCDF4 와 HDF5 를 구분하지 못한다.** 매직만으로 갈리지 않으므로 **컨테이너를 실제로 열어 보고** 어느 쪽 파서가 성공하는지로 확정한다. 열어 보기 전에는 「HDF5 계열」까지만 안다고 적는다.
> - **`.gz` 는 형식이 아니라 포장이다.** 풀고 나서 다시 판별한다.
> - **못 가른 형식도 올라간다** — 형식이 `없음`으로 남고, 등록·다운로드는 그대로 된다(§9 그릴 수 없는 형식).

### G-3 `.hdf` 는 HDF4 다 — 그리고 PoC 는 둘 다 다뤘다

**갭** — 정본 `DataModel_공통_기반.md:66` 과 `Policy_데이터셋_상세.md:199` 이 **「HDF5」**라 적었다. 실물은 HDF4 다(`SEED-DATA §0-F-2`). `F-2` 가 남긴 미결 「PoC 가 말하는 HDF5 도 실은 HDF4 였을 가능성」에 대한 **답은 「둘 다였다」**다.

**제안 위치** — 정본 `DataModel_공통_기반.md §4.1` · `Policy_데이터셋_상세.md §9`

**문안 초안:**
> **`.hdf` 와 `.h5` 는 다른 형식이다.**
> - 원천의 MODIS MOD15A2H 파일은 **HDF4** 다(매직 `\x0e\x03\x13\x01`). HDF5 매직은 `\x89HDF` 로 아예 다르다.
> - **HDF4 는 HDF5 라이브러리로 열리지 않는다.** 읽으려면 `pyhdf` 또는 GDAL 의 HDF4 드라이버가 필요하고, **컨테이너 이미지의 빌드 의존성이 달라진다.**
> - 두 형식을 한 칸에 적지 않는다. 화면의 「그릴 수 있는 형식」 목록도 **HDF4 와 HDF5 를 갈라 적는다.**

### G-4 좌표계를 못 구했으면 **조용히 근사하지 않는다**

**갭** — 이 문서에서 가장 값비싼 교훈이다. G1 은 짝 파일을 못 읽으면 **합성 규칙격자로 폴백**했고(`binary/processor.py:129-159` · `netcdf/processor.py:184-194`) 그대로 **성공으로 끝났다**. G2 가 이것을 버그로 판정해 예외로 바꿨다 — 「self-meta + companion 모두 부재이고 번들 GK2A grid shape 가 data_shape 와 일치하지 않으면 **silent fallback 대신 ValueError('VIZ-4010: …') raise**」(`decoders/netcdf.py:84-99`). 정본은 이 규칙을 **다른 자리에서 이미 말했다** — 「억지로 맞추면 **없는 시각을 있는 것처럼 그린다**」(`Policy_데이터셋_상세.md:192`). **같은 원칙의 공간 판(版)이 비어 있다.**

**제안 위치** — 정본 `Policy_데이터셋_상세.md §5 데이터 규칙` · `Policy_업로드와_계보_확정.md §9`

**문안 초안:**
> **위경도를 못 구했으면 그리지 않는다 — 그럴듯한 격자를 만들어 채우지 않는다.**
> - 위경도의 출처는 셋이고 **순서가 있다** — ① 파일 안에 든 위경도 ② 사람이 같이 올린 **기준 격자 파일** ③ 우리가 가진 격자 견본.
> - ③ 을 쓸 때는 **격자 크기가 데이터와 정확히 같아야 한다.** 다르면 쓰지 않고 「위경도를 못 구했어요」로 끝낸다.
> - **근거** — 견본 격자는 특정 관측(한반도 5km 등)의 것이라, 크기가 다른 자료에 얹으면 **엉뚱한 자리에 값을 그려 놓고도 성공으로 보인다.** 없는 시각을 그리지 않는 것과 같은 이유다(§8 층의 시각).
> - 이때도 **등록은 막지 않는다.** 못 그린다는 사실만 남긴다.

### G-5 이미 COG 인 tif 를 어느 쪽으로 볼 것인가 — `DR-2` 가 정본에 넘긴 판정

**갭** — `SEED-DATA.md:278` 이 이 판정을 **「정본(②의 판정)」**에 명시적으로 넘겼고 아직 비어 있다. 실측: 원천 tif 62건 중 **진짜 COG 6건 · 타일만 있고 오버뷰 없음 16건 · 스트립 40건**(`SEED-DATA.md:22`). **타일링만 보면 16건을 오인한다.** ⚠ **PoC 에서 가져올 것이 없다** — 세 세대 어디에도 COG 판별기가 없다(`backend/app/core/geo/__init__.py:18` 「cog_validator … 현재 inline」은 **미구현 표기**다).

**제안 위치** — 정본 `Policy_업로드와_계보_확정.md §5` (계보 오염 자리이므로 정본이 맞다)

**문안 초안:**
> **사람이 올린 GeoTIFF 를 우리가 만든 산출물로 적지 않는다.**
> - GeoTIFF 는 **올라오는 형식이자 우리가 만드는 형식**이다. 둘을 못 가르면 **계보가 거짓이 된다** — 사람이 만든 자료에 우리가 만들었다는 기록이 붙는다.
> - **판정은 「타일로 나뉘어 있는가」만으로 하지 않는다.** 원천 실측에서 **타일은 있고 축소본(오버뷰)은 없는 파일이 16건**이었다. 타일만 보면 이 16건이 전부 우리 산출물로 기록된다.
> - **우리 산출물로 보는 조건 = 타일 + 축소본 + 우리가 남긴 표시, 셋이 다 있을 때다.** 하나라도 없으면 **사람이 올린 파일로 본다.**
> - **왜 애매하면 사람 쪽인가** — 사람 자료를 우리 것으로 잘못 적으면 출처가 지워지지만, 우리 산출물을 사람 자료로 잘못 적으면 계보가 한 칸 길어질 뿐이다. **되돌릴 수 없는 쪽을 피한다.**
> - 이 규칙에는 **음성 시험**이 붙는다 — 이미 COG 인 tif 를 올렸을 때 산출물로 기록되지 **않아야** 한다.

### G-6 결측값은 **정확히 그 값일 때만** 결측이다

**갭** — 정본 무근거. PoC 에 **실제로 터진 버그의 기록**이 있다: 「기존 코드는 정확한 enum (249-255) 이 아닌 `>= 249` (**256, 1000 등도 포함**)이라 **over-mask 위험**」(`fill_values.py:49-52`).

**제안 위치** — v2 `SEED-DATA.md §DR` 또는 D5 작업지시서 (정본 어휘가 아니라 파서 규칙이라 정본보다 여기가 맞아 보인다)

**문안 초안:**
> **결측 표시값은 목록으로 관리하고, 비교는 「크거나 같다」가 아니라 「그 값과 같다」로 한다.**
> - MODIS 계열의 결측 코드는 249~255 **일곱 개의 열거값**이고 각각 뜻이 다르다(249 바다 · 250 내륙수 · 251 나지 · 252 눈얼음 · 253 도시 · 254 미분류 · 255 결측).
> - **`249 이상`으로 거르면 유효값까지 지운다** — 실제 관측값이 256, 1000 인 자료에서 데이터가 통째로 사라진다.
> - **결측 판정은 배율(scale factor)을 곱하기 *전* 원래 값으로 하고, 결측 표시는 곱한 *뒤*에 한다.** 순서를 바꾸면 결측 코드가 실수로 바뀌어 목록과 안 맞는다.
> - **임계값으로 거르는 방식**(레이더 반사도의 `-20000` 미만 등)은 열거 방식과 **뜻이 다르므로 섞지 않는다.** 자료마다 어느 방식인지 적어 둔다.

### G-7 배율은 읽고 있는데 **더하는 값(offset)은 아무도 안 읽는다**

**갭** — G0·G1·G2 **세 세대 전부** `scale_factor` 만 곱하고 `add_offset` 을 읽지 않는다(`file_format_5_HDF5/…:94` · `hdf/processor.py:522,536-538` · `hdf5_modis.py:672`). **[추론]** — 대상 파일에 offset 이 실제로 들어 있는지는 확인하지 않았다.

**문안 초안:**
> **값을 실제 단위로 되돌릴 때 배율만 곱하고 끝내지 않는다.**
> - 표준 표기는 `실제값 = 저장값 × 배율 + 더하는 값` 이다. **더하는 값을 빠뜨리면 전체가 일정하게 치우친 채로 그려진다** — 그림이 그럴듯해서 눈으로는 안 잡힌다.
> - 파일에 더하는 값이 없으면 0 으로 본다. **없다고 가정하지 말고 읽어서 없음을 확인한다.**

### G-8 크기·시간 한도를 숫자로 적는다 — 압축폭탄 포함

**갭** — 정본 `Policy_업로드와_계보_확정.md §9` 이 「그리다 시간 초과」·「올리다가 끊겼어요」로 **상황만** 말하고 수치가 없다. PoC 에 실측 기본값이 있다(`viz-service/app/config.py:31,32,34,60`).

**문안 초안 (v2 D5 작업지시서용):**
> **한도는 넷이고 각각 다른 사고를 막는다.**
> - **업로드 한 건** 500 MB — 초과 시 **받는 도중에 끊고 지운다**(다 받고 판정하면 그 자체가 디스크 공격이다).
> - **본체 + 기준 격자 파일 합계** 1 GB.
> - **압축 해제 후 크기** 600 MB — `.gz` 는 **작은 파일이 거대하게 풀릴 수 있다.** 풀면서 누적 크기를 세고 넘으면 중단한다. 이 검사가 없으면 1 MB 업로드로 메모리를 채울 수 있다.
> - **한 파일 해석 시간** 60 초 — 넘으면 실패로 끝낸다.
> - 사람에게는 숫자가 아니라 **다음 행동**을 말한다 — 「조각 하나나 좁은 기간으로 다시 해 보세요」(정본 §9 문구 유지).

### G-9 시간축 — 파일 하나가 시각 하나라는 전제를 문서로 못 박는다

**갭** — 정본은 **화면 층위**에서 완결돼 있다(`Policy_데이터셋_상세.md:192`). 파서 층위의 전제가 없다.

**문안 초안:**
> **여러 시각을 한 파일이 담는 형식과, 한 파일이 한 시각인 형식을 갈라 둔다.**
> - NetCDF·Binary·HDF 는 실무에서 **한 파일 = 한 시각**이고, 시계열은 **파일 묶음(조각)**으로 온다. 기간은 조각들의 **합집합**이다(데이터 모델 4.3).
> - **여러 시각을 담은 파일은 기본으로 첫 시각만 그린다.** 전부 그리면 한 번의 미리보기가 수십 장이 된다.
> - ⚠ **파일이 광고하는 시각 개수가 전부 유효하지는 않다** — 앞뒤에 빈(결측만 든) 시각이 붙어 오는 자료가 실재한다. **유효 구간을 코드에 숫자로 박지 말고 값으로 판정한다.**

### G-10 가공 방식 어휘에 다운스케일 4종과 그 한계를 넣는다

**갭** — 정본 `DataModel_공통_기반.md:89,96` 이 「가공 방식」을 **관계에 붙는 한 줄**로 두고 보조입력의 실례로 다운스케일을 들었다. **방법 목록과 각 방법의 한계**가 없다. G0/KWRA 에 4종이 실물로 있고 **각각 한국어로 한계가 적혀 있다.**

**제안 위치** — `WORK-UNITS.md:144` G8(온톨로지 범위) · `DOMAINS.md:77` D9 어휘

**문안 초안:**
> **해상도 높이기(다운스케일)의 방법을 어휘로 둔다 — 넷이고 성격이 다르다.**
> - **최근접** — 계단 모양이 남고 부드럽지 않다. **사실상 픽셀 복제라 정보가 늘지 않는다.** 값을 그대로 보존해야 할 때만 쓴다.
> - **양선형** — 부드럽지만 ⚠ **결측이 번진다.** 이웃이 전부 결측이면 가중치 합이 0 이 되어 결과도 결측이 되므로, **결측 영역이 원본보다 넓어진다.**
> - **역거리가중(IDW)** — 이웃 몇 개를 거리로 가중한다. 위경도를 미터로 바꿔야 거리가 뜻을 갖는다.
> - **회귀 크리깅** — 고도 같은 **고해상도 보조 자료와의 통계적 관계**로 세부를 만든다. ⚠ **이때 보조 자료는 값을 준 것이 아니라 판단에만 쓰였으므로 「보조입력」이다** — 주입력으로 적으면 결과가 두 자료를 합쳐 만든 것처럼 읽힌다(데이터 모델 4.2).
> - **어느 방법을 썼는지는 결과가 아니라 관계에 적는다.**

---

## ⑤ 상충·미해결

> **원칙 — 여기 있는 것을 이 문서가 해결하지 않는다.** 상충은 보고만 한다.

### 5.1 v2 결정과 구세대 코드가 어긋나는 것

| # | 무엇 | 근거 | 성격 |
|:--:|---|---|---|
| **X-1** | **「GeoTIFF 는 PoC 선례 없음」이 사실이 아니다.** `PLAN-SoT.md:151` 「**GeoTIFF — PoC 선례 없음**(`㊿` 로 5번째 입력 포맷 채택) / **없다** / D5 에서 새로 연다. **함정 목록이 비어 있고**」 · `WORK-UNITS.md:223` 「GeoTIFF 만 PoC 선례 없이 v2 에서 새로 여는 경로」 | **실물이 있다** — `viz-service/app/decoders/geotiff.py` 전체. 밴드 선택(`:22-24,37-39`) · nodata 정확일치(`:42-43`) · **`src.crs.to_epsg() != 4326` 일 때 `pyproj` 재투영**(`:51-57`) · 픽셀중심 meshgrid(`:46-49`). 테스트도 있다(`tests/test_decoder_geotiff.py`, 센티넬 `-9999.0` `conftest.py:42`). G0 에도 HLS S30 처리 3종(`file_format_4_tif/01.Code/`)이 있다 | **사실 오류.** 「함정 목록이 비어 있다」는 전제로 **S3 우선순위가 정해졌다**(`WORK-UNITS.md:232` 「GeoTIFF 는 PoC 선례가 없으므로 **가장 먼저 돌린다**」). 우선순위 자체는 여전히 타당할 수 있으나 **근거가 틀렸다** |
| **X-2** | **「PoC 의 4포맷」이 세대에 따라 4도 되고 5도 된다.** `〈51〉`·`WORK-UNITS.md:40,223`·`SEED-DATA.md:7` 이 「PoC 의 4포맷 = GRIB·NetCDF·Binary·HDF5」를 **과거 사실**로 보존하기로 했다 | G1(backend) 기준으로는 **맞다** — 프로세서가 grib·netcdf·binary·hdf 넷이다. 그러나 **G2(viz-service, 더 나중 세대)는 5포맷이다** — `viz-service/README.md:5` 「Decodes **5 raster formats** (GRIB / NetCDF / HSR binary / GeoTIFF / HDF5)」 · 커밋 메시지 `1e8e7c40` 「**5포맷**」 · `app/formats.py` 「5-format manifest」 | **표기 위험.** 「PoC 의 4포맷」은 **PoC 의 어느 세대냐**를 말하지 않으면 참이 아니다. `〈51〉` 이 이미 경고한 「4라는 숫자가 두 가지를 가리킨다」가 **실은 세 가지**다 |
| **X-3** | **`F-2` 의 미결 「PoC 의 HDF5 도 실은 HDF4 였을 가능성」** (`SEED-DATA.md:21`) | **둘 다였다.** G1 `hdf/processor.py` 는 매직으로 HDF4/HDF5 를 갈라 **양쪽 경로를 다 구현했다**(`:79-97`) — HDF4 는 rasterio subdataset + `rasterio.warp`(`:510,552`), HDF5 는 h5py 재귀 탐색(`:139-152,437`). 폴더 이름만 「hdf」다 | **미결 해소(제안).** `pipeline-worker/README.md:18` 의 「HDF5 · MODIS」 한 칸은 **HDF4 로 정정되는 것이 맞아 보인다** — 다만 **그 파일은 D5 레인 소유**라(`㊿`) 여기서 고치지 않았다 |
| **X-4** | **정본이 「HDF5」·「GRIB」을 여전히 목록에 담고 있다** | 정본 `DataModel_공통_기반.md:66` 「포맷(grib·nc·bin·tif·**HDF5** 등)」 · `Policy_데이터셋_상세.md:199` 「지금 그릴 수 있는 형식은 **GRIB** · NetCDF · BIN · GeoTIFF · **HDF5**」 · `Policy_업로드와_계보_확정.md:116` 동일 | **드리프트이지 상충은 아니다** — 정본은 260818 이고 `〈51〉`(GRIB 제외)·`F-2`(HDF4)는 2026-08-23 이다. 다만 **화면 문구가 그대로 나가면 사용자에게 거짓 목록을 보여 준다.** 소유자 = 정본 |
| **X-5** | **계약도 아직 옛 목록을 예시로 든다** | `contracts/events/core-pipeline.json:53-56` 「감지한 포맷(`grib`·`nc`·`bin`·`tif`·`HDF5` 등)」 · `:48` 「정본이 지금 그릴 수 있다고 밝힌 것은 GRIB · NetCDF · BIN · GeoTIFF · HDF5」 | **설계 의도상 무해** — enum 을 일부러 안 박았다고 같은 자리에 적혀 있어 **값이 강제되지는 않는다.** 그러나 **설명문이 낡았다.** 소유자 = 계약 레인(이 세션이 건드리지 않음) |
| **X-6** | **`pipeline-worker/README.md` 의 4포맷 표가 아직 GRIB·HDF5 다**(`:15,18`) | `㊿` 가 이미 **알려진 드리프트 1건**으로 기록하고 소유자를 **D5 착수 레인**으로 지정했다 | **기지(旣知).** 재확인만 — 실물 그대로다 |
| **X-7** | **HSR 좌표계가 두 세대에서 다르고, 최신 세대 쪽이 미완성이다** | G1 은 외부 짝 파일 `rdr_500m_latlon.nc` 를 쓴다(`binary/processor.py:129-159`). **G2 는 합성 더미다** — `decoders/binary_hsr.py:18-26` 자체 주석: 「Phase 6 활성화 마커: **실 KMA HSR 데이터 (1024B header + 진짜 LCC ↔ EPSG:4326 reference) 도착 시** … 전환.」 즉 **현재 georeference 는 한반도 bbox 위 단순 linspace** | **함정.** 「최신 세대가 더 낫다」가 이 항목에는 **성립하지 않는다.** HSR 좌표는 **G1 쪽을 참조해야 한다** |
| **X-8** | **SSoT 를 선언해 놓고 절반만 지켰다** | `processors.md` 규칙 「hardcoded magic number 금지 · `FormatConfig.fill_values` 가 진실의 원천」 ↔ 실제 Binary(`binary/processor.py:104-105`) · NetCDF(`netcdf/processor.py:122`) 는 인라인 임계값. `fill_values.py:7-8` 이 미구현 후속(`apply_threshold_mask`)을 예고 | **v2 로 옮길 교훈** — 「규칙을 문서로 선언하고 관례로 지킨다」가 **또 실패한 사례**다. `WORK-UNITS.md:158`(D3 이 보험인 이유)과 같은 종류 |

### 5.2 `.bin` 3블록 vs 13.28 MB — **해소했다**

**`SEED-DATA.md:23,281` `F-4`** 가 「코드가 가정한 3블록 구성은 압축 해제 시 ~39.8 MB 인데 `gunzip -l` 실측은 13.28 MB … **반사도 블록만 실재할 가능성이 높다** — 파서를 짜기 전에 이 불일치를 먼저 풀어야 한다」로 열어 둔 항목.

**결론 = 파일에는 헤더 + 반사도 블록 하나만 있다. 코드 쪽이 실물과 안 맞는다.**

**① 산술 (독립 검산):**
- `nx × ny = 2305 × 2881 = 6,640,705` 셀
- 한 블록 = `6,640,705 × 2 bytes = 13,281,410`
- **헤더 + 1블록 = `1,024 + 13,281,410` = `13,282,434` B = 13.28 MB**
- 헤더 + 3블록 = `1,024 + 3 × 13,281,410` = `39,845,254` B = 39.85 MB

**② 실측:** `03 Reference-Data/02.File-format/file_format_3_bin/00.Data/*.bin.gz` **12건 전부** 압축 해제 크기가 **정확히 `13,282,434` B**. 오차 0. (원천에 raw `.bin` 은 0건 — 전부 `.bin.gz`.)

**③ 코드 대조:** G0 `file_format_3_bin/01.Code/Lv1_Data Processing.py` 는 세 블록을 읽는다 — `[1024 : 1024+nx·ny·2]` 반사도(`:86-90`) · `[… : 1024+nx·ny·4]` 고도(`:92-96`) · `[… : 1024+nx·ny·6]` 위치(`:98-102`). **실제 파일에는 두 번째 블록의 첫 바이트부터 존재하지 않는다.** 이 스크립트를 실파일에 돌리면 고도 블록을 읽다가 빈 슬라이스에서 `int.from_bytes(b'', …)` → `ValueError` 로 죽는다 **[추론 — 실행하지 않고 코드에서 도출]**.

**④ 결정적 방증 — PoC 두 세대 모두 반사도만 읽는다:**
- G1 `binary/processor.py:98-99` — 헤더 1024 skip 후 `nx·ny` 셀만
- G2 `decoders/binary_hsr.py:289-291` — `np.frombuffer(raw, dtype="<i2", **count=NX*NY**, offset=HEADER_BYTES)`. 3섹션 구조를 **문서화는 하되**(`:5-10,45-51`) 뒤 두 블록에 「unused」라 적고 읽지 않는다
- G2 는 나아가 **최소 크기 검사를 헤더+1블록 기준으로 건다** — `len(raw) < HEADER_BYTES + _GRID_BYTES` 면 실패(`:281-285`). 즉 **PoC 는 이 사실을 이미 알고 우회했다.**

**⑤ 남는 미지:** 「고도·위치 블록이 원래 규격에 있는데 이 공개 배포본(`RDR_CMP_HSR_PUB_*`)만 빠진 것인지, 규격 자체가 1블록인지」는 **모른다** — 판단할 문서가 원천에 없다(`SEED-DATA §0-F-4`: `.ini` 74건 전부 `desktop.ini`). **D5 는 이 파일들에 대해 1블록으로 짜면 되고, 다른 배포본을 받으면 크기로 다시 판정한다.**

**⑥ 제안 문안 (`SEED-DATA §0-F-4` 갱신용 초안):**
> ✅ **해소** — 산술과 실측이 정확히 맞는다. `2305×2881×2 + 1024 = 13,282,434 B` 이고 원천 12건 전부 이 값이다(오차 0). **파일에는 반사도 블록 하나만 있다.** 연구자 원본 코드가 읽는 고도·위치 두 블록은 **이 배포본에 존재하지 않는다.** PoC 의 두 구현 모두 반사도만 읽도록 이미 우회해 두었다(`binary/processor.py:98-99` · `viz-service/app/decoders/binary_hsr.py:289-291`). **D5 는 1블록으로 짜고, 최소 크기 검사를 `1024 + nx·ny·2` 로 건다.**

### 5.3 이 문서가 풀지 않은 것

| 미결 | 상태 |
|---|---|
| **타일만 있고 오버뷰 없는 tif 16건을 어느 쪽으로 볼 것인가** (`DR-2`) | **정본의 판정 대상이다.** ④ G-5 에 초안만 뒀다. **PoC 에 선례가 없다** — 세 세대 어디에도 COG 판별기가 없다 |
| **원천 파일에 `add_offset` 이 실제로 있는가** | **확인 안 했다.** 코드가 안 읽는다는 사실만 확인했다 |
| **`__radar_kma__` 컬러맵** | `cmap_registry.py:7-8,13-21` 이 「discrete legend table, not a matplotlib name」인 센티넬로 선언했는데, `png_renderer.py:67` 은 `plt.get_cmap(cmap)` 를 그냥 호출한다 → **HSR 렌더가 실제로 도는지 의심스럽다** **[추론 — 모든 경로를 다 훑지 않았다]** |
| **`registry.get_processor()` 가 `None` 을 돌려준 뒤 호출부가 무엇을 하는가** | 호출부를 읽지 않았다. `AttributeError` 로 터질 위험 **[추론]** |
| **`viz-service` 가 스쿼시 커밋 1개라 세대 내부 변천을 못 본다** | 코드 안 주석의 「H-6」·「H-8」·「L-14」·「M-Codex」 태그가 **수정 이력의 흔적**이지만 커밋으로는 추적 불가 |

---

## ⑥ 정직한 한계

1. **「v3」를 못 찾았다.** ①에 무엇을 확인했고 무엇을 대신 다뤘는지 전부 적었다. **PoC 를 두 세대로 갈라 G2(viz-service, E018, 2026-05-02)를 「v2 직전 최신 처리 세대」로 놓았다.** 사용자가 다른 것(외부 드라이브·별도 아카이브·다른 사람 레포)을 뜻했다면 **이 문서는 그 세대를 담고 있지 않다.**
2. **읽었을 뿐 실행하지 않았다.** 성능 수치(60-80% 향상 등)·크래시 예측은 **코드와 주석에서 도출한 것**이고, 실파일로 재현하지 않았다. 유일한 실측은 **`.bin` 압축 해제 크기 12건**이다.
3. **정본을 전수 통독하지 않았다.** 8개 에픽 중 데이터 처리와 닿는 **E-00·E-03·E-04** 를 통독했고, 나머지(E-01·E-02·E-05·E-06·E-07·P1)는 처리 관련 어휘 grep 으로만 훑었다. **「없음」 판정이 grep 이 놓친 문장 때문일 가능성이 남는다.**
4. **`contracts/` 는 이벤트 계약(`core-pipeline.json`·`envelope.json`)과 seam 의 처리 관련 필드만 봤다.** 계약 전체를 감사하지 않았다.
5. **③ 행렬의 「정본」 열은 260818 패키지만 본 판정이다.** v2 문서(`SEED-DATA`·`PLAN-SoT`·`DOMAINS`)에 이미 적힌 것은 **별도 열**로 갈랐다 — 이 둘을 합쳐 읽으면 갭이 실제보다 커 보인다.
6. **④의 문안은 초안이고 정본이 아니다.** 정본 어투를 흉내 냈을 뿐 **정본 소유자의 승인을 받지 않았다.** 어느 문서에 붙일지도 제안이다.
7. **아무것도 고치지 않았다.** 이 파일 하나만 썼다. `contracts/**`·`WORK-UNITS.md`·`SEED-DATA.md`·`PLAN-SoT.md`·기존 `sessions/*.md`·정본·구세대 코드 **전부 무변경**이다. ⑤의 상충은 **보고만 하고 해결하지 않았다.**
8. **`20 CoLAB-v1/` 이 비어 있다.** C2(이관)가 아직 안 돌아서 이 문서의 경로는 전부 **원래 자리**(`00 CoLAB-PoC/…`)를 가리킨다. **C2 가 돌면 이 문서의 모든 경로가 깨진다** — 그때 `20 CoLAB-v1/00-poc/…` 로 일괄 치환이 필요하다.

---

## ⑦ `.bin` 스펙 — 정본 문서를 읽어 닫았다 (2026-08-23 추가)

> 출처 = `03 Reference-Data/02.File-format/file_format_3_bin/04.Lat_Lon_info/레이더합성자료포맷정보.pdf` (3쪽).
> **텍스트가 아니라 스캔 이미지**라 표준 추출로는 제목만 나온다. 임베드 이미지를 뽑아 직접 판독했다.
> 이 절의 값은 **전부 그 문서에 적힌 것**이고 추정이 아니다.

### 7-1. 미해결이 닫혔다 — 3블록이 참 스펙이고, 우리 파일은 축소 배포본이다

문서가 자료구조를 **네 덩어리**로 명시한다.

| 구성 | 크기 |
|---|---|
| 헤더 | **1024 bytes** |
| 반사도 | `2 bytes(short int.) × 2305 × 2881` |
| 고도정보 | `2 bytes(short int.) × 2305 × 2881` |
| 지점정보 | `2 bytes(short int.) × 2305 × 2881` |
| **비압축 용량** | **39,845,254 bytes** |

산술이 정확히 맞는다.

- `1024 + 3 × (2305×2881×2) = 1024 + 39,844,230 = 39,845,254` — **문서가 적은 값과 한 바이트도 안 틀린다**
- `1024 + 1 × 13,281,410 = 13,282,434` — **우리 원천 `.bin.gz` 12건이 푸는 크기**

**따라서 연구자 스크립트가 가정한 3블록이 옳았고, 우리가 받은 파일이 반사도 한 블록만 담은 배포본이다.** `[미확인]` 로 남겨 뒀던 항목을 닫는다.

### 7-2. 그런데 블록 수를 **가정하면 안 된다** — 파일이 스스로 말한다

헤더에 `char num_data` 가 있고 설명이 **「(nx*ny*nz)를 1개 자료블록으로 했을 때, 저장된 자료블록수」** 다. 그리고 `char data_code[16]` 가 **저장된 블록별 특성 코드**를 담는다(`1(에코)` · `2(고도)` · `3(지점순서)` · `4(자료수)` · `5(강수량)` · `6(수상체)` · `15(3km 이하 고도 합성 시 일정값 이상 에코 탐지 횟수)`).

**즉 파서는 3 도 1 도 가정하지 않고 `num_data` 를 읽어야 한다.** 우리 배포본이 1이고 정본 스펙이 3인 것은 **같은 포맷의 두 사례**이지 서로 다른 포맷이 아니다. PoC 두 세대가 반사도만 읽은 것은 결과적으로 맞았지만 **이유가 달랐다** — 길이를 `1024 + nx·ny·2` 로 고정했을 뿐 `num_data` 를 보지 않았다. 3블록 파일을 주면 뒤 두 블록을 조용히 버린다.

### 7-3. NULL 이 **세 값**이다 — `>=` 로 자르면 안 되는 이유가 여기 또 있다

| 값 | 뜻 |
|---|---|
| `-20000` | 관측영역내 표시를 위한 **최소값** |
| `-25000` | 관측영역내 **비관측영역** NULL |
| `-30000` | **관측반경 밖** NULL |

**셋이 서로 다른 뜻이고, 그중 하나(`-20000`)는 결측이 아니라 유효한 하한이다.** `값 <= -20000` 같은 범위 비교로 자르면 **표시 최소값을 결측으로 만든다.** 「fill 은 정확일치」(②) 가 이 포맷에서 특히 그렇다.

### 7-4. 나머지 확정 상수

- 시간 해상도 **5분** · 공간 해상도 **500 m** · 격자수 **2305 × 2881**
- 투영 **Lambert conformal conic**, 기준위경도 **N 38.0°, E 126.0°**, 기준격자점 **1121, 1681**, 지도 영역 **HB**
- 영역은 기준점에서 **서 560 km · 남 840 km**
- 값 환산 — **반사도(dBZ) = 값 / 100** · **고도정보(m) = 값** · **지점정보 = 값**
- 헤더 구조 = `RDR_CMP_HEAD(64 bytes)` + `RDR_CMP_STN_LIST(20 bytes) × 48` = **1024 bytes**
- `RDR_CMP_HEAD` 에 `nx`·`ny`·`nz`·`dxy`·`dz`·`z_min`·`ptype`·`map_code` 가 들어 있다 — **격자 크기도 하드코딩할 필요가 없다. 헤더가 준다.**
- `map_code` 1 = LCC / 기준위경도 38N·126E / 기준격자점 좌 1121 · 우 1681 (2 는 좌 801 · 우 1001 인 다른 영역)
- 시각은 `TIME_SS(7 bytes)` = `short YY` + `char MM·DD·HH·MI·SS`

> **이것이 `DR-14`·`DR-9` 와 이어지는 자리다.** PoC 는 변수·좌표를 **하드코딩으로 반환**하고 HSR 위경도를 **합성**했는데, 헤더가 `nx`·`ny`·`dxy`·`map_code` 를 이미 주고 있었고 좌표 배열은 같은 폴더에 있었다. **읽을 것이 있는데 안 읽고 지어낸 것**이다.
