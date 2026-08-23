# P2 · W0-R1 — 기준 격자 파일이 **코드에서 실제로 어떻게 쓰이는가** (조사 전용)

> **레인** `W0-R1` (조사 전용 · 소스 무수정 · 커밋 없음) · **일자** 2026-08-23
> **발단** `P2-W0-1-measurement.md §4.3 R-1` — 실물 16건 중 2건이 한 파일에 `lat`·`lon` 을 함께 담는다. Ted 가 추상 선택지 3안에서 고르기를 거부하고 **「이 파일들이 코드에서 실제로 어디에 쓰이는지 보고 거기서 다시 보라」**고 지시했다.
> **문서 규약** — `§2` 는 **증거**(연 파일·행 번호)다. `§3` 이후는 **해석**이고 잠정이다(`DATA-REFERENCE §0 M-5`). 열지 않은 것은 인용하지 않았다(`M-4`). 경로는 저장소 상대경로다.

---

## 1. 무엇을 읽었는가

| 대상 | 실제로 연 것 |
|---|---|
| D5 격자 모듈 | `services/pipeline-worker/src/colab_pipeline/d5/grid.py` (전문 75행) |
| D5 파이프라인 입구 | `services/pipeline-worker/src/colab_pipeline/d5/pipeline.py` (전문 181행) |
| D5 시험 | `services/pipeline-worker/tests/test_grid_and_hsr.py` · `tests/test_e2e_real.py` · `tests/test_pipeline.py` · `tests/fixture_builders.py` |
| 계약 | `contracts/seams/fe-core.yaml` (`createUpload`·`addDatasetFile`·`replaceDatasetGridFile`·`deleteDatasetGridFile`·`UploadFileRef`·`DatasetFile`) · `contracts/schemas/common.json` (`FileKind`) · `contracts/events/core-pipeline.json` (`FileRef`) |
| DB | `db/platform/schema.sql` (`d3_file` 및 부분 유니크 인덱스) · `db/platform/versions/0001_p0_platform.py` |
| core-api | `services/core-api/src/colab_core/domains/d3_catalog.py` · `routes/catalog.py` |
| 정본·계획 | `dev-package/DATA-REFERENCE.md` §0·§1 · `PLAN-SoT.md` §9 〈58〉·〈59〉·〈63〉·〈65〉 · `sessions/P2.md` §2 20/21/22 · `sessions/P2-EXEC.md` §4 W1 · `03-HANDOFF.md` 11번·DR-17 |
| PoC 선례 | PoC 저장소의 **두 세대 양쪽** — `backend/app/services/processors/` (binary·hdf·netcdf·grib) · `viz-service/app/decoders/` (binary_hsr·netcdf·hdf5_modis·dispatch) |

---

## 2. 증거 — 코드가 실제로 하는 일

### 2.1 D5 가 기준 격자에 대해 **요구하는 것은 「lat 배열과 lon 배열 한 쌍」이다** — 파일도 축도 아니다

- `grid.py:23-33` — 자료구조 `ReferenceGrid` 의 필드는 `lat`·`lon`(둘 다 `np.ndarray`) + `axes`(튜플) + `lat_path`·`lon_path` 다.
- `grid.py:48-55` `load_reference_grid(*, lat_path, lon_path)` — **두 개의 경로**를 받아 각각 `np.load` 하고, `grid.py:51-53` 에서 **형상 일치**를 검사한 뒤 `axes=("위도","경도")` 를 **하드코딩**해 돌려준다. 즉 `axes` 는 판별 결과가 아니라 **상수**다.
- `grid.py:58-75` `find_reference_grid(grid_dir, *, expect_shape)` — 실제 호출되는 것은 이쪽이고 **디렉터리 하나**를 받는다. `grid.py:66-67` 이 `grid_dir.glob("*.npy")` 결과 중 **파일명이 `lat`/`lon` 으로 시작하는 것**을 골라 `lats[0]`·`lons[0]` 을 짝짓는다.
- `pipeline.py:83` — 파이프라인이 부르는 것은 `find_reference_grid(grid_dir, expect_shape=expect)` **하나뿐**이다. 파이프라인은 **파일 목록도 축 라벨도 넘기지 않는다.**
- 소비 지점 `pipeline.py:100`·`pipeline.py:105-108` — `write_cog_from_grid(data, grid.lat, grid.lon, ...)`. **쓰이는 것은 두 배열뿐**이고 `axes`·`lat_path`·`lon_path` 는 COG 변환에 들어가지 않는다.

> **코드가 「무엇을 달라」고 말하는가의 답: 「형상이 같은 lat 2D 배열 + lon 2D 배열」이다. 파일 단위도 축 라벨도 요구 목록에 없다.**

### 2.2 축이 둘인 파일을 다루는 경로는 **존재한다. 그러나 격자 파일 경로가 아니라 본체 파일 경로에 있다**

- `pipeline.py:143-166` `_embedded_latlon(path, fmt)` — **파일 하나를 열어 `lat`·`lon` 을 둘 다 꺼내는 코드가 실재한다.** `pipeline.py:150-153` 이 변수명을 소문자로 정규화해 `lat`/`latitude`·`lon`/`longitude` 를 찾고, `pipeline.py:161-162` 는 1D 면 `np.meshgrid` 로 2D 화한다.
- **그런데 그 `path` 는 본체 파일이다.** 호출부 `pipeline.py:105-108` 은 `grid` 가 없을 때만 `_embedded_latlon(path, det.format)` 을 부르는데, 이 `path` 는 `run_file` 의 첫 인자, 즉 **처리 대상 본체**다(`pipeline.py:53`). 기준 격자 파일이 이 함수에 들어오는 경로는 없다.
- `pipeline.py:147` — `fmt != "NetCDF"` 이면 즉시 `GridUnavailableError` 다. 그리고 `pipeline.py:79-88` 의 분기 조건이 `meta.crs_embedded` 이므로 **본체가 좌표를 품었다고 판정된 경우에만** 이 경로가 열린다.

### 2.3 그래서 **결합축 `.nc` 격자 파일은 지금 「실패」하지 않는다 — 조용히 무시된다**

- `grid.py:66-67` 의 필터는 `*.npy` 다. `04.Lat_Lon_info` 안의 `.nc` 는 **glob 에 안 걸린다.**
- `file_format_2_nc/04.Lat_Lon_info/` 처럼 `.npy` 쌍과 `.nc` 가 **같이 있는** 폴더에서는 `.npy` 쌍이 잡히고 `.nc` 는 없는 것처럼 지나간다.
- `.nc` **만** 있는 폴더를 주면 `grid.py:68-70` 이 「위도/경도 npy 쌍을 찾지 못했다」로 `GridUnavailableError` 를 던지고 `pipeline.py:85-88` 이 `crs=[미상]` + `FAILURE` 로 닫는다.
- 부재 증명 — `grid.py` 에 NetCDF/HDF5 판독 수단이 없다:
  ```bash
  grep -n "nc\b\|netCDF\|h5py" services/pipeline-worker/src/colab_pipeline/d5/grid.py   # → 0건
  ```

> **「결합축 파일이 이미 동작하는가」의 답은 「아니오」다. 실패 방식도 나쁘다 — 옆에 `.npy` 가 있으면 예외조차 없이 무시된다.**

### 2.4 D5 시험이 격자 경로에 먹이는 것 — **전부 `.npy` 쌍이다. `.nc` 격자 파일을 먹이는 시험은 0건이다**

- `test_grid_and_hsr.py:16-41` — 4건 모두 `load_reference_grid(lat_path=…, lon_path=…)` 를 **두 경로**로 부른다. 픽스처는 `fixture_builders.py:133-140` `make_npy_2d` 로 만든 `.npy` 다.
- `test_grid_and_hsr.py:36-41` `test_good_grid_axis_typed` — 이름에 「axis」가 있지만 검사하는 것은 `g.axes == ("위도","경도")`, 즉 **하드코딩 상수의 확인**이지 축 판별 시험이 아니다.
- 실데이터 E2E `test_e2e_real.py:48`·`:57` — `grid_dir=d / "04.Lat_Lon_info"` 를 **폴더째** 넘긴다. NetCDF 케이스(`:46-51`)가 바로 `.npy` 2 + `.nc` 1 이 든 폴더인데 **`.nc` 의 존재가 시험에 아무 영향을 주지 않는다.**
- `test_e2e_real.py:66-79`(HDF4) — 4파일 동일 형상 문제를 피하려고 `tmp_path` 에 **`lat2d_h27v05.npy`·`lon2d_h27v05.npy` 만 심볼릭 링크한 임시 폴더**를 만들어 넘긴다. **시험이 격자 선택을 손으로 해 주고 있다.**
- `test_e2e_real.py:104-112` — 격자를 안 주면 `FAILURE` + `crs == "[미상]"` 임을 못박는다(DR-9 음성).
- `test_grid_and_hsr.py:44-55` — 소스 어디에도 `linspace` 가 없음을 검사한다(PoC 합성 좌표 재발 방지).
- `fixture_builders.py:144-` `make_netcdf(..., with_latlon=True)` 로 **진짜 NetCDF 컨테이너를 만드는 도구는 있다.** 다만 그것을 **격자 파일로** 쓰는 시험이 없다.

### 2.5 계약과 DB — **어디에도 축이 없다. 알갱이는 「파일」이고 성격은 `kind` 하나뿐이다**

- `fe-core.yaml:1754-1760` `UploadFileRef` = `fileId`·`fileName`·`kind`·`byteSize` **4값**, `additionalProperties: false`.
- `fe-core.yaml:2119-2127` `DatasetFile` = `fileId`·`fileName`·`kind` **3값**, `additionalProperties: false`.
- `fe-core.yaml:534-556` `addDatasetFile` 의 multipart 본문은 `required: [file, kind]` + `additionalProperties: false` — **축을 실을 자리가 구조적으로 막혀 있다.**
- `fe-core.yaml:574-596` `replaceDatasetGridFile` 의 본문은 `required: [file]` 뿐 — **교체 시엔 `kind` 조차 안 받는다.** 대상은 `fileId` 로 지정되고 대상이 `본체` 면 409(`:604-609`).
- `fe-core.yaml:610-624` `deleteDatasetGridFile` — 파일 1건 삭제. **축 단위 삭제라는 개념이 계약에 없다.**
- `contracts/schemas/common.json:79-81` — `FileKind` enum 은 `["본체","기준 격자 파일"]` **2값**뿐이다. 산문에만 「축은 `grid_axis` 가 가른다」가 적혀 있고 **그 필드는 계약 어디에도 정의돼 있지 않다**(= `DR-17` 이 말한 자리).
- DB 현행 `db/platform/schema.sql:275-290` — `d3_file` 열은 `id·lab_id·dataset_id·kind·file_name·size_bytes·storage_key·created_at` 이고 **`grid_axis` 열은 아직 없다.** 유일성은 `:289-290` `CREATE UNIQUE INDEX d3_file_one_reference_grid_per_dataset ON d3_file (dataset_id) WHERE kind = '기준 격자 파일'` — **데이터셋당 격자 1건 강제**다(`0001_p0_platform.py:301-302` 동일).
- **⚠ 2026-08-23 추가 — 이 부분 인덱스가 오늘 당장 무엇을 막고 있는지.** `schema.sql:289-290` 는 `WHERE kind = '기준 격자 파일'` 조건의 부분 유니크 인덱스이고 대상 열이 `dataset_id` 하나뿐이다. 즉 **데이터셋 하나에 「기준 격자 파일」로 표시된 행이 두 번째로 들어오는 순간 유니크 위반으로 거절된다.** `〈58〉` 이 확정한 「위도·경도 `.npy` 한 쌍이 실물이다」는 정의상 **격자 파일 2건**이므로, **오늘 이 인덱스가 걸린 채로는 그 실물 쌍을 둘 다 등록할 수 없다** — 첫 번째 파일은 들어가고 두 번째는 반드시 실패한다. `grid_axis` 열의 유무와 무관하게, **`0004`(또는 그 대안인 두 불리언 안, `§3.4`)가 이 인덱스를 「데이터셋당 1건」에서 「축마다 1건」으로 바꾸지 않는 한 실물 16건 중 `.npy` 쌍을 쓰는 14건이 오늘 이 자리에서 막힌다.** 이것은 축 판별의 정확도 문제가 아니라 **등록 자체가 불가능하다는 긴급성 논거**이고, 위 §2.5 서술에는 빠져 있었다.
- **`d3_file` 행 : 업로드 파일 = 1 : 1 이다** — `storage_key text NOT NULL`(`schema.sql:281`)이 행마다 저장 객체 하나를 가리키고, `UploadFileRef.fileId` 가 등록 전환 후 그대로 D3 파일 레코드 PK 가 된다(`fe-core.yaml:1749-1753`). **행을 축으로 쪼개면 같은 `storage_key` 가 두 행에 들어간다.**
- 부재 증명 — 소스 전체에 `grid_axis` 를 읽거나 쓰는 코드가 없다:
  ```bash
  grep -rn "grid_axis" services --include='*.py' --include='*.sql'
  # → services/pipeline-worker/tests/test_grid_and_hsr.py:36 (함수 이름) 1건뿐
  ```
- **DB 에서 격자 파일을 실제로 조회하는 유일한 자리**는 `services/core-api/src/colab_core/domains/d3_catalog.py:65-71`·`:151-152` `has_reference_grid_file` 이고, 질의는 `WHERE dataset_id = :dataset_id AND kind = '기준 격자 파일'` 의 **존재 여부**다. 응답도 `routes/catalog.py:302` 의 `hasReferenceGridFile` **불리언 하나**다(`fe-core.yaml:2009-2014`).
- 목록 조회 `d3_catalog.py:160-163` `list_files` 가 돌려주는 것도 `fileId·fileName·kind` **3값**이다.

### 2.6 PoC 선례 — **두 세대 양쪽에 「단일 파일에서 lat·lon 둘 다」가 있었다. 그것이 오히려 주류였다**

> ⚠ 지시받은 경로 `20 CoLAB-v1` 은 **빈 디렉터리**였다. 실물 PoC 저장소는 **`00 CoLAB-PoC`** 이고 두 세대가 모두 그 안에 있다. 아래 경로는 그 저장소 기준 상대경로다.

**Gen-1 `backend/app/services/processors/` —**

- `binary/processor.py:43` — HSR 의 기본 격자가 **단일 `.nc` 파일 하나**다(`sample-data/binary/latlon/rdr_500m_latlon.nc`).
- `binary/processor.py:128-135` (그리고 `:140-147`) — `xr.open_dataset(latlon_file)` 뒤 `ds_ll["lon"].values` · `ds_ll["lat"].values`. **한 파일에서 두 축을 다 꺼낸다.**
- `binary/processor.py:153-156` — 그것도 실패하면 `np.linspace` **합성 좌표**로 「성공」을 반환한다(DR-9 가 금지한 바로 그 경로).
- `hdf/processor.py:296-306`·`:316-329` — MODIS 는 **`.npy` pair** 이고, 파일명 tile id 로 디렉터리에서 `lat2d_{tile}.npy`·`lon2d_{tile}.npy` 를 조립한다. `:356-368` 은 단일 `.npy` 가 오면 이름의 `lat`↔`lon` 을 치환해 짝을 찾는다(v2 `grid.py:66-67` 의 조상).
- `hdf/processor.py:376-381` — **여기에도 단일 `.nc` 에서 `lat`/`latitude`·`lon`/`longitude` 를 둘 다 꺼내는 분기가 있다.**
- `netcdf/processor.py:37`·`:47-48` — GK2A 는 **단일 `.nc`**(`*_latlon.nc` 패턴, `requires_latlon_file=True`).
- `base.py:54-55` — 프로세서 계약 필드가 `requires_latlon_file: bool` + `default_latlon_pattern` 이다. **축이 아니라 「짝 파일이 필요한가」가 계약 축이었다.**
- `services/unified.py:131-134` — 공용 진입점이 **`latlon_file`(단일) · `lat_file` · `lon_file`(쌍) 세 인자를 동시에** 노출한다. **PoC 는 두 모양을 나란히 인정했다.**

**Gen-2 `viz-service/app/decoders/` —**

- `netcdf.py:24`·`:41-42` — 번들 격자가 **단일 `.nc`** 이고 `ds["lon"]`·`ds["lat"]` 를 함께 읽는다. `:46-63` 은 본체 자체의 self-meta 를 먼저 시도하고, `:82-99` 는 shape 불일치 시 **조용한 폴백을 금지하고 예외**를 던진다.
- `binary_hsr.py:57-59`·`:107-113` — HSR 은 **`.npy` pair** 로 바뀌었다. 그러나 `:18-27` 주석이 **그 asset 자체가 dummy `linspace` 합성물**임을 명시한다(파일 크기 1D 수준). **참조 구현으로 삼으면 좌표가 틀린다.**
- `binary_hsr.py:116-135` — 사용자 업로드 격자는 **`.npz` 단일 파일에서 `lon`·`lat` 을 둘 다** 꺼낸다. `.npy` 쌍 분기는 **미구현**(`:121` Phase 6 TODO).
- `dispatch.py:43`·`:58-59` — 전달 인터페이스가 **단일 optional `companion_path` 하나로 수렴**했다. 즉 Gen-2 는 「짝 파일 = 파일 한 장」으로 통일해 갔다.
- `hdf5_modis.py:68-84` — MODIS 는 참조 격자 파일을 아예 안 쓰고 affine + `pyproj` 로 좌표를 만든다.

> **선례가 말하는 것: 「기준 격자 = 파일 두 장」은 PoC 어디에서도 불변식이 아니었다. 단일 파일(`.nc`/`.npz`)이 두 축을 함께 나르는 것이 오히려 더 흔했고, Gen-2 는 전달 인터페이스를 「파일 한 장」으로 수렴시켰다.**

---

## 3. 해석 — **잠정**(`M-5`)

### 3.1 코드는 **파일의 축을 한 번도 묻지 않는다**

`§2.1`·`§2.5` 를 겹치면 이렇다. 파이프라인은 `find_reference_grid` 에 **디렉터리**를 넘기고, 그 안에서 **파일명 접두어**로 축을 가르고, 결과로 **배열 두 개**만 쓴다. `core-api` 는 격자에 대해 **있다/없다**만 묻는다. 계약은 **파일 1건 단위**로만 말한다.

**즉 코드의 관심사는 「이 데이터셋에 쓸 수 있는 lat+lon 격자가 있는가」이지 「이 파일이 위도 파일인가」가 아니다.** 축은 **파일의 종류가 아니라 「격자 한 벌」을 구성하는 내부 사정**으로 다뤄지고 있다. `§2.6` 의 선례도 같은 결이다 — PoC 의 계약 축은 `requires_latlon_file` 이라는 **불리언**이었지 축 이름이 아니었다.

### 3.2 `grid_axis` 를 파일 행에 두는 것이 푸는 문제는 정확히 하나 — **「어느 파일을 lat 자리에, 어느 파일을 lon 자리에 넣을지」**

`P2.md §2-22` 가 축 열을 요구한 근거는 「개수만 2로 늘리면 위도 파일이 둘 들어가고 시스템이 둘을 구분하지 못한다」였다. 이 문장이 겨누는 것은 **라벨의 정확성**이 아니라 **소비 시점의 짝짓기 모호성**이다. 지금 그 짝짓기는 **DB 가 아니라 `grid.py:66-67` 의 파일명 접두어**가 하고 있고, `test_e2e_real.py:70-74` 는 그 방식이 실물에서 안 서서 **시험이 손으로 폴더를 만들어 준다.**

**해석 — DB 제약이 실제로 지키려는 것은 「축 라벨의 정합」이 아니라 「데이터셋마다 lat+lon 이 정확히 한 벌이고, 그 한 벌이 유일하게 결정된다」이다.**

### 3.3 그 관점에서 세 선택지를 다시 본다

| 안 | 코드와 대조했을 때 |
|---|---|
| **㈎ 결합축 파일은 `기준 격자 파일` 이 아니다** | **현재 v2 코드의 실제 동작과는 가장 정확히 일치한다**(`§2.3`). 그러나 **구현 결손을 자료모델로 승격**시키는 것이고, `§2.6` 의 선례와 정면으로 어긋난다 — PoC 는 결합축 파일을 **주된 격자 형태로** 다뤘다. 또 `rdr_500m_latlon.nc` 는 바이너리 HSR 본체의 **동봉 격자**라 「본체가 자기 좌표를 갖고 있다」로도 못 넘긴다(`pipeline.py:147` 은 NetCDF 본체에서만 내장 좌표를 인정한다). 실물 12.5% 를 「격자 파일이 아니다」로 부르면 **사용자가 올린 격자를 시스템이 격자라 부르지 않는다.** |
| **㈏ 제3 enum 값 추가** | 값 집합을 **P2 가 지어내는 것**이라 `㊴-②` 저촉 지적(`03-HANDOFF` 11번)이 그대로 산다. 게다가 `'위경도'` 같은 값을 넣어도 `UNIQUE (dataset_id, grid_axis)` 는 **「위도 파일 1 + 위경도 파일 1」을 막지 못한다** — 두 값이 다르므로 통과하고, 소비 코드는 lat 을 두 곳에서 얻는다. **제약이 겨눈 결함을 못 막는다.** |
| **㈑ 「이 파일이 담는 축의 집합」으로 재정의** | 코드의 실제 관심사(`§3.1`)·선례(`§2.6`) 양쪽과 결이 맞고, 유일성을 **「축 원소당 최대 1파일」**로 재구성하면 ㈏ 가 못 막는 겹침도 막는다. 다만 **단일 텍스트 열 + `UNIQUE(dataset_id, grid_axis)` 로는 표현이 안 된다** — 집합을 한 열에 넣으면 겹침 검사가 등호로 안 되기 때문이다. |

### 3.4 코드가 시사하는 **네 번째 모양** — 아무도 안 올린 것

`§3.2` 를 그대로 받으면, 축을 **한 열의 값**이 아니라 **「이 파일이 위도를 담는가 / 경도를 담는가」 두 개의 참·거짓**으로 두는 형태가 나온다. 그러면 유일성이 **부분 유니크 인덱스 둘**로 정확히 표현된다 — 확장 모듈도 배열 연산자도 새 enum 값도 필요 없다.

- `carries_lat boolean` · `carries_lon boolean`
- `CHECK (kind <> '기준 격자 파일' OR (carries_lat OR carries_lon))` — 축 없는 격자 파일을 못 만든다(`P2.md §2-20` 요구 유지)
- `CHECK (kind <> '본체' OR (NOT carries_lat AND NOT carries_lon))` — 축 붙은 본체를 못 만든다(`P2-EXEC §4 W1-⑴-3` 의 「본체 쪽 반쪽」 유지)
- `CREATE UNIQUE INDEX … ON d3_file (dataset_id) WHERE kind='기준 격자 파일' AND carries_lat` — **위도를 담은 파일은 데이터셋당 1건**. 같은 모양으로 `carries_lon` 하나 더
- 결과: `.npy` 쌍 = **2행**(각각 하나만 참) · 결합축 `.nc` = **1행**(둘 다 참) · 위도 파일 2건 = **차단**(`P2.md §2-22` 가 겨눈 결함) · 「위도 1 + 결합 1」 = **차단**(㈏ 가 못 막던 것)

**이것은 ㈑ 와 대립하는 안이 아니라 ㈑ 의 구현 형태다.** ㈑ 의 의미를 유지하면서 Postgres 기본 기능만으로 선다.

### 3.5 더 근본적인 답 — **파일 행에 축이 필요한가?**

`§2.5` 대로 **오늘 이 저장소에서 `grid_axis` 를 읽는 코드는 0건**이고, D5 는 **DB 를 거치지 않고 디렉터리에서 격자를 찾는다**(`pipeline.py:83`). 즉 `0004` 를 어떤 모양으로 걸어도 **당장 그 값을 읽는 소비자가 없다.**

**그러나 「필요 없다」로 닫으면 안 된다.** 이유 둘 — ① `grid.py:66-67` 의 파일명 접두어 짝짓기는 사용자가 올리는 파일(`grid_a.npy`·`좌표1.npy`)에서 무너진다. `〈63〉-㉰` 가 「서버가 파일에서 판별한다」로 닫은 이상 **판별 결과를 어딘가 적어야 하고, 그 자리가 파일 행이다** ② 제약이 지키는 것은 소비자가 아니라 **적재 시점의 불변식**이다(`§3.2`).

**해석 = 파일 행에 필요한 것은 「이 파일이 위도 파일이다」라는 종류 라벨이 아니라 「이 파일이 어느 축(들)을 실제로 담고 있는가」라는 판별 결과다.** 전자는 결합축 파일에서 거짓이 되고 후자는 참이 된다. **`0004` 가 틀렸다면 그것은 제약이 과해서가 아니라 「축 = 파일의 종류」라고 읽은 대목이다.**

---

## 4. 권고와 그 근거

### 4.1 권고 — **㈑ 를 채택하되 `§3.4` 의 두 불리언 형태로 구현한다**

`grid_axis text` 단일 열을 **쓰지 않는다.** 대신 `d3_file` 에 **「담고 있는 축」 두 개를 참·거짓으로** 두고, 유일성을 **축마다 부분 유니크 인덱스 하나씩**으로 건다(구체 형태는 `§3.4`).

**근거 다섯 —**

1. **코드가 파일의 축을 한 번도 묻지 않는다**(`§2.1`·`§2.5` 증거). 파일 행에 「축 이름」을 새기는 것은 **아무도 안 쓰는 라벨**이고, 실제로 필요한 사실은 「이 파일에서 lat 을 얻을 수 있는가 / lon 을 얻을 수 있는가」다. 두 불리언이 **정확히 그 질문**이다.
2. **`P2.md §2-22` 의 원래 목적을 그대로 지킨다** — 「위도 파일 두 개」를 막는 것이 목적이었고 부분 유니크 인덱스 둘이 그것을 막는다. **게다가 ㈏ 가 못 막는 「위도 1 + 결합 1」까지 막는다.**
3. **`d3_file` 행 : 파일 = 1 : 1 을 깨지 않는다**(`§2.5` — `storage_key`·`fileId` 동일성). 결합축 파일을 두 행으로 쪼개는 안은 이 1:1 을 깨고, `replaceDatasetGridFile`·`deleteDatasetGridFile` 이 **한 `fileId` 로 두 행을 건드리게** 만든다 — 계약(`fe-core.yaml:574`·`:610`)이 `fileId` 하나를 대상으로 삼기 때문이다.
4. **계약 무수정으로 선다.** 계약은 파일 단위이고 축을 안 싣는다(`§2.5`). 두 불리언은 **서버가 파일을 열어 채우는 값**이라 `〈63〉-㉰`(서버가 파일에서 판별)·`DR-14`(사람이 타이핑하지 않는다)와 정합한다.
5. **선례가 「파일 두 장」을 불변식으로 쓰지 않았다**(`§2.6`). PoC 양 세대가 단일 파일 결합축을 정상 입력으로 다뤘고, Gen-2 는 전달 인터페이스를 **파일 한 장(`companion_path`)** 으로 수렴시켰다. 「한 쌍이 실물이다」를 DB 불변식으로 굳히면 **선례가 이미 지나온 자리로 되돌아간다.**

### 4.2 함께 권고 — **`grid.py` 의 `.npy` 전용 glob 을 결손으로 등재한다**

`§2.3` 대로 **결합축 `.nc` 는 옆에 `.npy` 가 있으면 조용히 무시되고, 혼자 있으면 「격자 없음」으로 실패한다.** 이것은 `0004` 와 별개의 **W2 `P2-pipeline` 결손**이다. `pipeline.py:143-166` 에 **한 파일에서 lat·lon 을 둘 다 꺼내는 코드가 이미 있으므로**(`§2.2`) 그 로직을 격자 파일 경로에서도 부를 수 있게 하는 것이 사실상 작업 전부다. **`0004` 를 어떤 모양으로 정하든 이 결손을 안 고치면 결합축 파일은 여전히 안 읽힌다.**

### 4.3 판정하지 않는 것

- **HSR 격자가 두 벌인 문제**(`.npy` 쌍과 `rdr_500m_latlon.nc` 가 0.004~0.007° 어긋난다 — 측정 `§2.3`). 어느 쪽이 정본 격자인지는 **자료 출처 문제**라 코드가 답하지 않는다. ⚠ 다만 `§2.6` 이 한 가지를 보탠다 — **PoC Gen-2 의 `Lat_HSR.npy`·`Lon_HSR.npy` 는 dummy `linspace` 합성물이다**(`viz-service/app/decoders/binary_hsr.py:18-27`). 원천 폴더의 `.npy` 가 그 계보라면 **`.nc` 쪽이 정본일 가능성**이 있다. **여기서 닫지 않고 `03-HANDOFF` 11번에 이 단서를 보탠다.**
- `〈58〉` 확정문의 「위도·경도 한 쌍이 실물이다」를 **개정할 것인가**는 정본 전제의 문제라 **Ted 몫**이다. 이 문서는 「코드가 그 전제를 안 쓰고 있다」까지만 말한다.

---

## 5. 반대 근거 · 남는 위험

### 5.1 내 권고에 대한 **가장 강한 반론** — ㈎ 가 현재 코드와 더 정확히 일치한다

**`§2.3` 이 보인 대로 오늘 D5 는 결합축 파일을 격자로 읽지 못한다.** 「코드에서 어떻게 쓰이는가」를 곧이곧대로 물으면 답은 **「안 쓰인다」**다. 그러면 ㈎(결합축 파일은 `기준 격자 파일` 이 아니다)가 **코드의 현실을 그대로 옮긴 자료모델**이고, 내 권고는 **아직 없는 코드를 전제로 스키마를 넓히는 것**이다 — `M-4` 가 경계하는 무늬에 가깝다.

**내가 이 반론을 받지 않는 이유**: 결손(`§4.2`)은 `pipeline.py:143-166` 이 이미 있어 **작고**, 선례(`§2.6`)가 그 결손이 **v2 의 퇴행**임을 보인다. 반대로 `0004` 는 기존 인덱스를 걷는 **되돌리기 어려운 마이그레이션**이다(`P2-EXEC §4 W1`·`:132`). **작은 결손에 맞춰 큰 제약을 굳히는 것이 순서가 뒤집힌 것**이다. — 다만 이 논거는 **비용 판단**이지 코드 증거가 아니다. **Ted 가 뒤집을 수 있는 자리로 명시한다.**

### 5.2 남는 위험

| # | 위험 | 등급 |
|---|---|---|
| **V-1** | **정본 문구를 건드린다** — `〈58〉` 「위도·경도 한 쌍이 실물이다」와 `P2.md §2-20` 「어느 축인지를 함께 받아야 한다」는 **축 = 파일의 종류**로 읽히게 적혀 있다. 두 불리언은 그 읽기를 바꾼다. **관례 판정으로 못 닫고 결정 로그가 필요하다** | 🟧 해석 |
| **V-2** | **`P2-EXEC §4 W1-⑴` 의 작업 문안을 통째로 다시 쓴다** — 적혀 있는 `grid_axis text` + CHECK 2종 + `UNIQUE(dataset_id, grid_axis)` 가 전부 바뀐다. W1 착수 전이면 비용이 작지만 **착수 후면 재작업**이다 | 🟧 해석 |
| **V-3** | **`grid_axis` 라는 이름이 이미 계약 산문에 박혀 있다** — `contracts/schemas/common.json:79` 이 「축은 `grid_axis` 가 가른다」고 적었고 계약은 동결(`P2.md §2-18`)이라 못 고친다. **DB 열 이름이 계약 산문과 달라지면 `DR-16` 과 같은 부류의 산문 드리프트가 하나 더 생긴다** | ✅ 증거(`common.json:79`) |
| **V-4** | ~~**판별 실패 시 무엇을 적는가가 미정이다** — `〈63〉-ⓒ` 는 「판별 실패는 그 파일만 막고 등록은 막지 않는다」인데, `CHECK (격자 파일 → 축 하나 이상)` 가 걸리면 **축을 못 정한 격자 파일은 행 자체를 못 만든다.** 두 불리언 안만의 문제가 아니라 **원안 `0004` 에도 똑같이 있는 미해결점**이고, 이 조사가 새로 드러낸 자리다~~ **⚠ 2026-08-23 정정 — advisor 검토로 이 진단은 절반만 맞았다.** 위 문단은 **「CHECK 가 `〈63〉-ⓒ` 와 충돌한다」로 읽히게 적혀 있었는데, 충돌이 아니다.** `〈63〉-ⓒ` 가 막는 것은 **파일**이다 — 판별에 실패한 그 파일을 **거절**하면 행이 아예 생기지 않고, 행이 없으면 `CHECK` 는 애초에 평가될 대상이 없다. **CHECK 가 걸리는 것은 「거절되지 않고 통과한 격자 파일인데 축이 NULL 인 경우」뿐이고, 그런 경우는 「판별 실패 시 파일을 거절한다」를 지키면 발생하지 않는다.** 그래서 하나의 구현 규칙으로 닫는다 — **판별 실패 = 그 파일을 거절한다(`addDatasetFile` 거절). 축이 NULL 인 행을 삽입하지 않는다.** 이 규칙이 명시적으로 서 있지 않으면 W2 레인이 반대로 「일단 등록시키고 축은 NULL 로 둔다」로 구현할 수 있다 — 그러면 그때는 정말로 `CHECK` 가 걸려 등록 자체가 막히고 `〈63〉-ⓒ` 를 어기게 된다. **즉 원래 결손은 CHECK 조문에 있던 것이 아니라, 「거절」의 의미를 못박아 두지 않은 데 있었다.** | 🟧 해석(정정됨) |
| **V-5** | **결합축 파일의 「형상 검사」가 사라진다** — `grid.py:51-53` 은 lat·lon 두 파일의 형상 일치를 검사하는데, 한 파일 안이면 그 검사가 무의미해지고 대신 **파일 내부 두 변수의 형상 일치**를 봐야 한다. `pipeline.py:143-166` 에는 **그 검사가 없다**(1D→meshgrid 만 있다). W2 가 보태야 한다 | ✅ 증거(`pipeline.py:143-166` 에 형상 대조 없음) |
| **V-6** | **선례 인용의 경계** — `§2.6` 은 PoC 가 **무엇을 했는지**의 증거이지 **무엇이 옳은지**의 증거가 아니다. 같은 PoC 가 `linspace` 합성 좌표(`binary/processor.py:153-156`)로 「성공」을 반환했고 v2 는 그것을 명시적으로 금지했다(DR-9). **선례를 근거로 쓸 때 어디까지 쓰는지 갈라 둔다** — 쓰는 것은 「결합축 파일이 정상 입력이었다」까지다 | 🟧 해석 |
