# S1 — 데이터셋 인포 수확 조사 (v1·PoC → v2)

> **조사 전용 세션.** 코드를 고치지 않았고 커밋하지 않았다.
> **결론을 내리지 않는다** — 정본과 어긋나는 지점은 이름만 붙이고 Ted 판단으로 남긴다.

| | |
|---|---|
| 발단 | Ted 가 1차 범위를 재정의 — 데이터 가공·시각화 **제외**, 남는 것은 업로드 · **데이터셋 인포** · AI 검색 · 연구실-프로젝트-데이터셋 · 계보 설정 |
| 지시 | 「데이터셋 인포(설명 항목)를 v1/PoC 에서 가져온다」 — 깊이 3층: **항목 정의 + 실제 설명 문구 + 화면 구성** |
| 상시 규칙과의 충돌 | `CLAUDE.md §0`·`§5` · `PLAN-SoT §6` — **v2 는 PoC·v1 코드를 계승하지 않는다. 도메인 지식·방법론만.** 이 문서는 그 선을 매 절에서 다시 긋는다 |
| 작성 | 2026-08-24 |

**표기** — `EVIDENCE` 는 실제로 열어 본 것만. `INTERPRETATION` 은 **잠정**이며 정본이 아니다 (`M-5`).
측정하지 않은 수는 적지 않는다 — `[미확인]` 이 유효한 답이다 (`M-4`). 줄 번호는 `cat -n`·`awk` 로 확인했다 (`M-7`).
절대경로를 적지 않는다 (`CLAUDE.md §3-8`) — `<작업공간>` 은 이 레포의 부모 폴더다.

---

## 0. 조사 착수에서 먼저 깨진 전제 두 가지

### EVIDENCE

**① `20 CoLAB-v1` 은 빈 폴더다.**

```
$ ls -la "<작업공간>/20 CoLAB-v1"
total 0
drwxrwxrwx 1 ... .
drwxrwxrwx 1 ... ..
```

실물 v1 은 **`<작업공간>/10 CoLAB-Launch`** 에 있다 — `colab-backend-platform` · `colab-contracts` · `colab-frontend` · `colab-infra` · `dev-package`.
v2 자신의 `dev-package/DATAMODEL-BASELINE.md:10` 도 대조 상대를 *「v1 `colab-backend-platform` — `db/schema.sql` + `migrations/0001~0007`」* 로 못 박아 같은 곳을 가리킨다.

**② 「데이터셋 인포」의 실제 소재지는 v1 이 아니라 PoC 다.**
v1 에는 **설명란이 아예 없다**(§A-1). 사람이 적는 칸이 세 개뿐이다.

### INTERPRETATION *(잠정)*

- 지시문의 「v1/PoC 에서 가져온다」는 실질적으로 **「PoC 에서 가져온다」**로 읽어야 한다. v1 에서 가져올 인포 항목은 사실상 없다.
- `M-3`(선례를 한 세대만 보고 「없다」 하기)을 피하려고 PoC 는 두 계보(`backend/app/services/processors/` · `viz-service/app/decoders/`)와 프론트 세대를 모두 훑었다 — 프론트는 `src/components/v2/` **한 세대뿐**이었다(§C-2 EVIDENCE).

---

## A. 항목 정의 — 데이터셋을 설명하는 칸들

### A-1. v1 (`10 CoLAB-Launch`) — 사람이 적는 칸은 **3개**

#### EVIDENCE

`colab-backend-platform/src/colab_backend/bc/catalog/models.py` — `catalog_dataset` 전 컬럼 7개.

| 코드명 | 화면 라벨 | 타입 | 필수 | 값 집합 | 출처 | 저장 | 인용 |
|---|---|---|:--:|---|---|---|---|
| `id` | `ID` | ULID `CHAR(26)` | PK | `^[0-9A-HJKMNP-TV-Z]{26}$` | 시스템 | `catalog_dataset.id` | `models.py:47` |
| `lab_id` | (화면에 없음) | ULID | 필수 | — | 토큰/RLS 파생 | `catalog_dataset.lab_id` | `models.py:48` |
| `title` | `제목` | `String(256)` | 필수 | 자유 문자열 | **사람이 타이핑** | `catalog_dataset.title` | `models.py:49` · 라벨 `features/catalog/DatasetListPage.tsx:50` |
| `format` | `포맷` | `String(16)` | 필수 | `GRIB` `NetCDF` `Binary` `HDF5` | **사람이 선택** | `catalog_dataset.format` | `models.py:50` · enum 정본 `colab-contracts/schemas/format.json:6-11` |
| `source_crs` | `원본 CRS` | `String(64)` | 필수 | 자유 문자열 (`EPSG:4326`·`LCC`·`Sinusoidal`) | **사람이 타이핑** | `catalog_dataset.source_crs` | `models.py:51` · `_contracts/catalog_api.py:78-83` |
| `state` | `상태` | `String(16)` | 필수 · 기본 `UPLOADED` | `UPLOADED→DETECTED→CONVERTING→REGISTERED→READY`, 비종단→`FAILED` | **시스템 파생**(전이 검증기) | `catalog_dataset.state` | `models.py:30-39,52,75-94` · `colab-contracts/schemas/catalog.json:6-11` |
| `created_at` | `생성` | `TIMESTAMP(tz)` | 필수 · `server_default=now()` | — | 시스템 | `catalog_dataset.created_at` | `models.py:53-55` |

파일에서 읽은 곁테이블 — `catalog_variable`(`name` `unit` `default_colormap` `vmin` `vmax` — `models.py:120-129`), `catalog_time`(`index` `timestamp` — `models.py:138-144`), 그리고 화면에 노출되지 않는 `catalog_file`(`object_key` `bytes` `sha256` — `models.py:107-109`) · `catalog_cog`(`models.py:161-166`).

생성 요청 본문 `CreateDatasetRequest` 의 칸은 정확히 **`title` · `format` · `source_crs` 셋** (`_contracts/catalog_api.py:72-83`).
상세 응답 `Dataset` 의 필드 순서 — `id, lab_id, title, format, source_crs, state, created_at` (`_contracts/catalog_api.py:86-100`, TS 미러 `colab-types/src/generated/catalog.d.ts:137-144`).

**「설명란이 없다」의 증거** (`M-2` 회피 — 단정이 아니라 명령과 빈 출력):

```
$ grep -rn "\"description\"\s*:\|description:" .../colab-contracts/seams/catalog.openapi.yaml
  → 엔드포인트 산문만 매치. 스키마 필드 없음
$ grep -rln "tags\|license\|keywords" .../colab-contracts/schemas .../colab-backend-platform/contracts/schemas
  → (빈 출력)
```

#### INTERPRETATION *(잠정)*

- v1 카탈로그는 **연구 협업 카탈로그가 아니라 지오데이터 인제스천 파이프라인**이다 — GRIB/NetCDF/Binary/HDF5 → WGS84 COG. 「데이터셋 인포」라는 개념 자체가 그 모델에 없다.
- 이는 v2 자신의 판정과 일치한다 — `DATAMODEL-BASELINE.md:20-21`: *「v1 스키마에서 물려받을 저장 형태는 없다. v1 의 카탈로그는 파이프라인 처리 모델이고, v1.8 은 연구 협업 모델이다」*.
- **가져올 것이 있다면 「없음」이라는 사실 자체다** — v1 이 설명란 없이도 굴러갔다는 것은, 설명란이 인제스천에 필요 없고 **재사용 판단에 필요하다**는 v2 의 문제 정의를 뒷받침한다.

### A-2. PoC — 데이터셋 설명 항목 **전수**

#### EVIDENCE — 저장 층 (`backend/app/models/dataset.py`)

`Dataset` 테이블(`datasets`) 컬럼을 코드 순서대로 전부 적는다. 「출처」는 H=사람 타이핑 · F=파일에서 추출 · S=시스템 파생.

| 코드명 | 타입 | 필수 | 값 집합 | 출처 | 인용 |
|---|---|:--:|---|:--:|---|
| `id` | `String(20)` | PK | — | S | `models/dataset.py:109` |
| `name` | `String(255)` | **필수** | 자유 | H | `:110` |
| `format` | enum `DataFormat` | 필수 · 기본 `unknown` | 22값 — `grib` `netcdf` `binary` `hdf5` `csv` `zip` `unknown` `pdf` `image` `excel` `doc` `text` `json` `xml` `archive` `other` `mixed` `tiff` `cog` | F | `:111-113` · enum `:49-87` |
| `status` | enum `DatasetStatus` | 필수 · 기본 `uploading` | `uploading` `processing` `ready` `error` `archived` | S | `:114-116` · enum `:38-46` |
| `level` | enum `DatasetLevel` | 필수 · 기본 `L0` | `L0`~`L4` (NASA/CEOS) | H | `:117-119` · enum `:90-96` |
| `category` | `String(50)` | 선택 | 계약층 4값 `precipitation` `vegetation` `drought` `other` | H | `:122` · `constants/vocab.py:50-55` |
| `data_type` | `String(50)` | 선택 | 6값 `observed` `remote_sensing` `simulated` `reanalysis` `composite` `derived` | H | `:123` · `vocab.py:58-65` |
| **`description`** | `Text` | 선택(DB) / **필수(업로드 폼)** | 자유 · **길이 상한 없음** | H | `:124` |
| `uploader_name` | `String(100)` | 선택 | 자유 | S(JWT 강제·생성 후 불변) | `:126-127` |
| `uploader_org` | `String(200)` | 선택 | 자유 | S | `:128` |
| `creator_name` | `String(100)` | 선택 | 자유 | H | `:131` |
| `creator_org` | `String(200)` | 선택 | 자유 | H | `:132` |
| `keywords` | `Text` (JSON 문자열) | 선택 | 자유 목록 | H | `:135` |
| `file_count` | `Integer` | 필수 · 기본 1 | ≥0 | S | `:138` |
| `data_size` | `BigInteger` | 선택 | — | S | `:139` |
| `bounds_west/south/east/north` | `Float` ×4 | 선택 | — | F | `:142-145` |
| `crs` | `String(50)` | 기본 `EPSG:4326` | — | F | `:148` |
| `file_path` | `String(512)` | 선택 | — | S(레거시 단일파일) | `:151` |
| `tile_url_template` | `String(512)` | 선택 | — | S | `:152` |
| `time_start` / `time_end` | `DateTime` ×2 | 선택 | — | **H(사용자 편집 가능)** | `:155-156` |
| `error_message` | `Text` | 선택 | — | S | `:159` |
| `progress` / `progress_stage` / `progress_message` | `Integer`/`String(20)`/`String(255)` | — | — | S | `:162-168` |
| `access_type` | `String(20)` | 기본 `public` | 3값 `public` `request_required` `private` | H | `:173-175` · `vocab.py:68-72` |
| `source_url` | `Text` | 선택 | — | H (**L0 일 때 필수**) | `:176` |
| `preview_image_path` | `String(500)` | 선택 | — | H(업로드) | `:177` |
| `region` | `String(50)` | 선택 | 정규화 id | H → 정규화 | `:178` |
| `region_original` | `String(100)` | 선택 | **사용자가 친 원문 그대로** | H | `:179-181` |
| `spatial_resolution` | `String(50)` | 선택 | 자유 문자열 | H | `:182` |
| `spatial_resolution_meters` | `Float` | 선택 | 파싱 실패 시 NULL | S(파싱) | `:184-185` |
| `measurement_interval` | `String(20)` | 선택 | — | H | `:186` |
| `coordinate_system` | `String(20)` | 선택 | `WGS84` `GRS80` `UTM` `LCC` | H | `:187` · `schemas/v2/dataset.py:125` |
| `bbox_min_lat/max_lat/min_lng/max_lng` | `Float` ×4 | 선택 | — | H(선택 입력) | `:188-191` |
| `related_doi` | `Text` | 선택 | — | H | `:192` |
| `input_dataset_ids` | `Text` (JSON 목록) | 선택 | 부모 데이터셋 id 들 | H(선택) | `:193-195` |
| `download_count` | `Integer` | 필수 · 기본 0 | — | S | `:196` |
| `uploader_id` | `String(20)` FK→`users.id` | 선택 | — | S | `:201-203` |
| `processing_started_at` · `s3_key` · `upload_id` | — | 선택 | — | S | `:204-208` |
| `created_at` / `processed_at` | `DateTime` ×2 | — | — | S | `:211-214` |
| `search_text` / `geom` / `embedding` | `TSVECTOR` / `Geometry(POLYGON,4326)` / `Vector(1536)` | 선택 | — | S(검색 색인) | `:217-219` |

곁테이블 — `dataset_files`(`:300-356`) · `dataset_variables`(`name` `long_name` `units` `min_value` `max_value` `recommended_colormap` — `:372-396`) · `dataset_times`(`:410-431`) · `dataset_cog_files`(`:442-468`) · `dataset_lineage`(`parent_id` `child_id` `relation_type` `description` `link_type` — `:495-532`).

#### EVIDENCE — 화면 라벨 (한국어)

`frontend/src/constants/vocab.ts` 가 라벨 정본이다.

- `CATEGORY_LABELS` (`:36-41`) — `precipitation: 강우` · `vegetation: 식생` · `drought: 가뭄` · `other: 기타`
- `LEVEL_LABELS` (`:88-94`) — `L0 — 원자료` · `L1 — 보정` · `L2 — 파생` · `L3 — 격자` · `L4 — 모델`
- `DATA_TYPE_LABELS` (`:128-135`) — `observed: 관측` · `remote_sensing: 원격탐사` · `simulated: 시뮬레이션` · `reanalysis: 재분석` · `composite: 복합` · `derived: 파생`

별칭 지도 — `CATEGORY_ALIAS_MAP`(`rainfall`·`rain`→`precipitation`) · `DATA_TYPE_ALIAS_MAP`(8건) · `REGION_ALIAS_MAP`(`대한민국`·`한국`→`korea`) — `backend/app/constants/vocab.py:160-185`.
**별칭은 `category`·`data_type` 두 축에만 허용**되고 `access_type`·`level`·`format` 에는 금지다 — 이유가 코드 주석에 있다: *「silent string substitution (e.g. `"open" → "public"`) alter contract semantics, a known privilege-escalation risk」* (`vocab.py:149-158`).

#### EVIDENCE — API 응답 필드 순서

`backend/app/schemas/v2/dataset.py` — `DatasetV2Response`(`:248-293`) 필드 순서:
`id, name, description, level, category, data_type, access_type, format, coordinate_system, source_url, preview_image_url, region, spatial_resolution, period_start, period_end, measurement_interval, bbox, uploader_name, uploader_org, creator_name, creator_org, uploader_verified, data_size, file_count, download_count, created_at, status, related_doi, keywords, input_datasets, error_message, progress, progress_stage, progress_message`.

생성 요청 `DatasetCreateV2`(`:111-139`)에서 **필수(Optional 이 아닌) 칸**: `dataset_id` `name` `uploader_name` `access_type` `level` `category` `data_type` `coordinate_system` `region` `spatial_resolution` `period_start` `period_end` `measurement_interval` **`description`**.

#### INTERPRETATION *(잠정)*

- PoC 의 설명 모델은 **한 테이블에 40여 칸을 평평하게 늘어놓은 형태**다. 사람이 적는 값과 시스템이 파생한 값이 같은 행에 섞여 있고, 무엇을 사람이 채워야 하는지는 **테이블이 아니라 업로드 폼이 안다**.
- **v2 는 이미 그 반대를 택했다** — `d3_dataset`(레코드) / `d3_dataset_description`(사람이 적는 정보) / `d3_dataset_autometa`(자동으로 읽은 정보)로 3분할. `DataModel §4.1` 이 시킨 모양이다.
- 따라서 **PoC 에서 가져올 것은 「칸의 목록」이지 「칸의 배치」가 아니다.** 배치를 그대로 옮기면 v2 가 이미 내린 결정을 되돌리게 된다.
- 지식으로서 값어치가 있는 것은 **어휘 정의와 그 정의의 근거**다 — 특히 ① `data_type` 6값(관측/원격탐사/시뮬레이션/재분석/복합/파생)이라는 **출처 축**이 `category`(주제 축)와 **다른 축**이라는 분리 ② 별칭을 두 축에만 허용한 보안 판단 ③ `region_original`(사용자가 친 원문)과 `region`(정규화 id)을 **둘 다 저장**한 판단 ④ `spatial_resolution`(자유 문자열)과 `spatial_resolution_meters`(파싱값)을 둘 다 둔 판단. 이 넷은 **코드가 아니라 방법**이라 계승 규칙에 걸리지 않는다.

---

## B. 실제 설명 문구 — 데이터로 존재하는가

**한 줄 답 — 존재한다. 다만 코드베이스가 아니라 `03 Reference-Data` 의 원천 동봉 문서 안에 있다.**
v1·PoC 애플리케이션 어디에도 연구자가 쓴 데이터셋 설명이 **적재된 데이터로는 0건**이다.

### B-1. 실물이 있는 곳 — `<작업공간>/03 Reference-Data`

#### EVIDENCE

`.docx`·`.pptx` 는 grep 이 못 읽는다 — `python3 -m zipfile` 로 풀어 본문을 뽑아 직접 읽었다.

**① `Dataset Description:` 이라는 라벨이 붙은 정식 필드 — 2건**

| 파일 | 내용 |
|---|---|
| `01.level-data/03.drought…/03.drought/#readme/[Data Info]SPI-4weeks.docx` | `Dataset Description` + 생산자 `차호영` / `고려대학교` |
| `01.level-data/03.drought…/03.drought/#readme/[Data Info]SPEI-4weeks.docx` | 같은 구조 |

원문 그대로:

> **Dataset Description :** 대한민국 내 기상관측소의 강우 관측자료를 활용하여 SPI-4weeks를 산정하고, 각 관측소의 주소지를 기준으로 해당 관측자료가 소재 시군구를 대표하는 것으로 가정하여 데이터를 구축하였다.

> **Dataset Description:** 대한민국 내 기상관측소의 강우 관측자료를 활용하여 SPEI-4weeks를 산정하고, 각 관측소의 주소지를 기준으로 해당 관측자료가 소재 시군구를 대표하는 것으로 가정하여 데이터를 구축하였다.
> **Data Name:** 대한민국 시군구 주 단위 SPEI-4weeks 데이터 / **생산자 이름:** 차호영 / **생산자 소속:** 고려대학교

**② 라벨은 없지만 연구자가 쓴 설명 산문 — 3건**

`01.level-data/01.precipitation/…/#readme/#processing_description_Precipitation.docx`:

> 레이더는 강우량을 직접 측정하는 장비가 아니라, 대기 중 hydrometeor에 의해 산란되어 돌아오는 전자기파의 세기를 기반으로 레이더 반사도를 관측한다. 실제로 우리가 알고 싶은 값은 강우 강도 이기 때문에, 전통적으로는 반사도와 강우량 사이의 경험적 관계식인 Z–R 관계식을 이용하여 강우량을 추정한다.

> 반사도: 대기 중에 존재하는 강수 입자(예: 빗방울, 눈, 우박 등)가 레이더 전파를 얼마나 강하게 산란(scattering)하여 되돌려 보내는지를 나타내는 물리량

`01.level-data/02.vegetation/…/#readme/#processing_description_NDVI.docx`:

> NDVI는 인공위성으로부터 관측된 근적외선(Near-Infrared, NIR)과 적색(Red) 반사율의 차이를 이용해 식생의 활력 상태를 추정하는 지수이다.

> GK-2A는 대한민국에서 발사한 위성으로 천리안 2A호라고도 불림.

`01.level-data/01.precipitation/…/#readme/자료설명.pptx` (슬라이드 텍스트):

> 레이더 반사도 자료 / 레이더 강우 자료 (Z=200R^1.6 공식으로 환산) / 지상 강우량계 자료 / U-Net 기반 예측 자료

**셈** — 정식 `Dataset Description` 필드 **2건**, 비정형 설명 산문 **3파일**. 스윕에서 이 다섯 파일 외에는 나오지 않았다.
⚠ **총 원천 동봉 문서는 10건이다**(`SEED-DATA.md:56` — `.docx` 5 · `.pptx` 2 · `.pdf` 2 · `.md` 1). 나머지 5건에 설명 문구가 더 있는지는 **`[미확인]`** 이다.

**③ v2 자신이 이미 이 자산을 알고 있다.**
`dev-package/SEED-DATA.md:94` — *「원천 동봉 문서 10건 … 데이터가 아니라 **메타데이터의 출처**. 사람이 읽고 데이터셋 설명란을 채우는 데 쓴다」*
`SEED-DATA.md:214` — *「원천 문서가 Lv.1 과 Lv.2 의 차이를 스스로 대조해 놨다 — 「Lv.1 은 값이 변하지 않는 균등분할, Lv.2 는 U-Net 으로 지형에 따라 값이 실제로 달라진다」. **데이터셋 설명란에 그대로 쓸 문장이다.**」*

### B-2. 없다는 것의 증명 — 명령과 빈 출력 (`M-2`)

| 확인한 곳 | 명령 / 관찰 | 결과 |
|---|---|---|
| v1 시드·스키마 (`00-dev-bootstrap.sql` · `db/schema.sql` · `SEED-DATA.md` · `infra/init-db.sql` · `gates/red-fixtures/schema-drift.sql`) | `grep -nEi "description\|설명\|소개\|abstract\|summary\|keyword"` | **전부 빈 출력** |
| v1 계약 스키마 `*.json` | `grep description` | JSON-Schema 의 `description` 서술자만. 인스턴스 데이터 아님 |
| v1 Pact 파일 | `grep description` | 2건 — 계약 시험 상호작용 이름(`create upload session` 등) |
| PoC `backend/data/datasets` | `find … -maxdepth 2` | **빈 디렉터리** |
| PoC `data/uploads/` · `backend/data/uploads/` | `find` | `.nc`·`.zip` 원파일만. 곁 메타데이터 파일 없음 |
| PoC `demo-scenarios/README.md:245` | `grep -n "description\|설명"` | 1줄 — `**Step 6 — Description**: \`GK-2A 지표온도 시연 데이터셋\``. **QA 시연 대본의 「이 값을 폼에 타이핑하라」**이지 저장된 레코드가 아니다 |
| PoC `backend/tests/` | `grep -rn "테스트\|샘플\|lorem\|placeholder\|dummy"` | 다수 매치 — 이 코드베이스의 설명류 문자열은 **전부 합성·시험용** |

### B-3. PoC 는 설명을 **AI 에게 쓰게 하려 했다**

#### EVIDENCE

`backend/app/services/ai_description.py` — *「OpenAI GPT를 사용하여 데이터셋 메타데이터 기반 설명 자동 생성」*(`:1-5`). 시험은 `backend/tests/test_ai_description.py` 이고 OpenAI 호출은 mock 이다.
프롬프트(`:20-51`)는 포맷·변수·공간범위·시간범위·처리레벨·파일수를 나열하고 이렇게 지시한다:

> 아래 수문/기상 데이터셋의 메타데이터를 보고 한국어로 2-3문장의 설명을 작성해주세요.
> 전문적이지만 간결하게, 이 데이터가 무엇이고 어떻게 활용할 수 있는지 설명해주세요.

키가 없거나 호출이 실패하면 `None` 을 돌린다(`:61-65`).

#### INTERPRETATION *(잠정)*

- **PoC 에 실제 설명 문구가 없는 이유가 여기 있다.** PoC 는 설명을 「사람이 축적하는 자산」이 아니라 **「메타데이터에서 생성 가능한 파생물」**로 다뤘다.
- **이것은 v2 의 AI 정책과 정면으로 어긋난다** — `CLAUDE.md §0`: AI 는 **두 지점**(업로드 시 계보 제안 · 자연어 검색)에만 얹힌다. 설명 자동 생성은 **셋째 지점**이다. `X-12` 로 아래에 세운다.

### B-4. v2 가 오늘 가진 설명 문구

#### EVIDENCE

- `frontend/src/components/detail/fixture.ts` — `summary` 값 **3건 중 2건만 비어 있지 않다**: `null`(`:53`) · `'유역 평균 강수량'`(`:86`) · `'강우와 짝이 되는 유출 결과'`(`:119`).
- 이 둘은 지어낸 값이 아니다 — 정본 목업에서 그대로 왔다. `에픽/E-03_데이터셋_상세/mockups/데이터셋_상세_260817.html:501`(`유역 평균 강수량`) · `:781`(`강우와 짝이 되는 유출 결과`). 픽스처 머리주석이 그 규칙을 적어 뒀다(`fixture.ts:1-8`): *「값은 정본 목업에서 그대로 온다. 새 데이터를 지어내지 않는다」*.
- `frontend/src/components/catalog/fixture.ts` — **`summary`·`description` 칸 자체가 없다.**
- `dev-package/SEED-DATA.md:126-140` — 적재 예정 데이터셋 15건에 **이름·주제는 있으나 `summary` 열이 없다.**

#### INTERPRETATION *(잠정)*

- **v2 의 「설명 문구」 재고는 목업에서 온 2건이 전부다.** 둘 다 6자·15자짜리 UI 견본이고 연구자가 쓴 문장이 아니다.
- **그래서 Ted 가 「v1/PoC 에서 가져오겠다」고 한 것이 정확히 이 결핍을 겨눈다.** 다만 **PoC 에도 없다** — 있는 곳은 `03 Reference-Data` 의 원천 문서이고, 그 사실은 v2 자신의 `SEED-DATA.md` 가 이미 두 번 적어 뒀다(`:94`·`:214`).
- **결핍의 성격이 바뀐다.** 「가져올 문구가 어딘가 있는데 못 찾았다」가 아니라 **「사람이 원천 문서를 읽고 15건분을 써야 한다」**이다. 그 원료는 확보돼 있다.

---

## C. 화면 구성 — v1·PoC 는 인포를 어떻게 놓았나

### C-1. v1 상세 화면 — 설계랄 것이 없다

#### EVIDENCE

유일한 상세 화면은 `colab-frontend/.claude/worktrees/catalog-ingestion-ui/src/features/catalog/DatasetDetailPage.tsx` 다.
⚠ **커밋되지 않은 워크트리 안에만 있다** — `colab-frontend/src` 본류에는 `*catalog*` 파일이 없다(`find src -iname "*catalog*"` → 빈 출력).

순서: ① `← 목록` 되돌아가기(`:27`) → ② `<h2>{title}</h2>` — 유일한 큰 글자(`:28`) → ③ `<dl>` 네 줄: `상태`·`포맷`·`원본 CRS`·`ID`(`:29-40`) → ④ `<h3>변수</h3>`(`:42-53`) → ⑤ `<h3>시간축</h3>`(`:55-66`).

빈 상태 문구(원문 그대로): `"변수 없음 (meta.extract 이전)."`(`:52`) · `"시간축 없음."`(`:65`) · `"불러오는 중…"`(`:21`) · `"데이터셋 조회 실패"`(`:22`).

칩·배지·히어로·탭·접기·「더보기」·편집 모드 **전부 없다**. 업로드도 마법사가 아니라 한 줄 폼이다 — 파일 선택 · `데이터셋 제목` · 포맷 `<select>` · `원본 CRS`(기본 `EPSG:4326`), 제출 버튼 `업로드` (`features/ingestion/UploadPanel.tsx:79-109`). 사용자가 보는 진행은 문장 한 줄뿐: `① 업로드 세션 생성…` → `② 파트 업로드…` → `③ 카탈로그 승격…` → `완료 — dataset {id} …`(`:51,59,62,67`).

#### INTERPRETATION *(잠정)*

**설계 의도를 읽을 것이 없다.** 이것은 계약을 눈으로 확인하려고 세운 개발 도구다. **v1 화면에서 v2 가 배울 것은 없다** — 이 절은 「v1 화면을 참조하라」는 요구가 들어왔을 때 그 요구를 닫기 위한 증거다.

### C-2. PoC 상세 화면 — 모달 2열

#### EVIDENCE — 세대 확인 (`M-3` 회피)

```
$ find .../frontend/src -path "*/v1/*"        → 빈 출력
$ find .../frontend/src/pages                 → 빈 출력
$ ls .../frontend/src/components              → error  icons  ui  v2
```
데이터셋 상세는 **`src/components/v2/` 한 세대뿐**이다. 백엔드 쪽 두 계보(`backend/app/services/processors/` · `viz-service/app/decoders/`)는 **파서 계보**이고 인포 화면과 무관하다.

#### EVIDENCE — 배치

`src/components/v2/detail/DatasetDetailModal.tsx` (1048줄). **페이지가 아니라 모달**이다.

1. **헤더**(`:758-772`) — `dataset.name` 을 `text-xl font-bold` 로. 이 화면에서 유일하게 큰 글자다. 우측에 닫기(X).
2. **본문 — CSS Grid 2열 `3fr 2fr`**(`:774-784`)
   - **좌열(넓은 쪽)**
     - ⓐ 라벨 없는 속성 `<dl>`(`:788-901`) — 측정 기간 · 측정 간격 · 공간 해상도 · 공간 범위 · 좌표계 · 바운딩박스(조건부) · 유형 · 포맷 · 업로드일 · 데이터 수 · **`Classification`**(Level·Category·DataType 배지 **세 개를 한 줄에 묶음**, `:828-832`) · 키워드(칩, 조건부) · 데이터 생산자 / 업로더(**둘이 다르면 두 줄로 쪼개고 같으면 한 줄로 합침**, `:849-896`) · 용량
     - ⓑ **`Information`** 섹션(`:903-946`) — 설명 본문(`whitespace-pre-wrap` `break-words`) + `Related Paper` DOI/URL 링크
     - ⓒ **`Input Datasets`** 섹션(`:405-493`, `948-952`) — **0건이어도 항상 그린다**. 부모마다 카드 + LevelBadge. 잠긴 부모(`name === 'private'`)는 🔒 + 비활성
   - **우열(좁은 쪽)**
     - ⓓ **`Geographic Coverage`** — Leaflet/OSM 미니맵 + bbox 사각형(`:957-961`)
     - ⓔ **`File List (N)`** — `maxHeight:300` 스크롤 상자, 지연 로딩, 로딩 중 스켈레톤, `file_count>0` 인데 0건이 오면 경고 배너(`:354-400`)
3. **푸터**(`:972-1029`) — 닫기(좌) / 우측 그룹: 관리자 전용 `Delete dataset`(위험 스타일) · `가공 이력` · `가공하기` · `Add to Bundle`. 뒤 셋은 전부 `alert('${feature} 기능은 준비 중입니다')` 스텁이다.

**지연·접힘** — 파일 목록은 모달이 열린 뒤 `v2Api.getFiles` 로 따로 부른다. 상세 자체도 목록 페이지가 준 축약 객체로 먼저 그리고, `v2Api.getDataset(id)` 결과가 오면 갈아끼운다(`:603-636`) — 그래서 `Input Datasets` 가 첫 페인트 뒤 늦게 차오른다. **설명 본문은 접지 않는다** — 「더보기」 없이 전문을 편다.

**빈 상태** — 스칼라 칸은 전부 리터럴 `'-'`(`:61-72, 791-822`). 설명·Related Paper·키워드는 **값이 없으면 섹션째 사라진다**(조건부 `&&` — `:907, 930, 834`). 파일 목록은 영어(`"Failed to load files"` · `"No files available"` · `File list unavailable (count: {n})` — `:368-390`).
**한국어 빈 상태는 딱 한 곳** — `Input Datasets` 가 0건일 때: 라벨 `"원천 자료"`, 본문 `"다른 데이터셋으로부터 파생되지 않은 독립 자료입니다."`(`:438-441`).

**편집 모드 없음.** `edit`·`편집` grep 무매치. 유일한 쓰기 동작은 관리자 하드 삭제(2단 확인) — `"데이터셋 삭제 (복구 불가)"` / `"{name} 데이터셋과 연결된 모든 파일 · COG 산출물 · 썸네일이 영구 삭제됩니다. 이 동작은 되돌릴 수 없습니다."`(`:548-553`).

#### EVIDENCE — 업로드 폼(7단계 마법사)

`src/components/v2/upload/UploadPage.tsx` + `uploadStore.ts::canProceedForStep`(`:156-190`).

| 단계 | 이름 | 다음으로 가는 조건 | 건너뜀 |
|:--:|---|---|---|
| 1 | File Upload | ok/renamed 파일 ≥1, 에러 행 0 | — |
| 2 | Basic Info | `name` · `accessType` · `uploaderName` | 생산자 이름/기관 선택 — `"본인이면 비워두세요"` · `"소속 기관 (선택)"` |
| 3 | Classification | `category` · `dataType` · `coordinateSystem`; **`sourceUrl` 은 `level === 'L0'` 일 때만 필수** | L1·L2 는 sourceUrl 선택 |
| 4 | Spatial & Temporal | `region` · `spatialResolution` · `periodStart` · `periodEnd` · `measurementInterval` | 바운딩박스 `(optional)` |
| 5 | Processing (부모 고르기) | 조건 없음 | **`level === 'L0'` 이면 통째로 건너뛴다** — `opacity-30` 으로 흐려짐 |
| 6 | Description | **`description` 비어 있으면 못 넘어간다** | DOI/논문 URL · 미리보기 이미지 선택 |
| 7 | Review & Submit | — | — |

업로더 칸은 읽기 전용 자동 채움 — `"업로더"` · `"업로더는 로그인 계정으로 자동 설정됩니다."` · `"(자동 설정됨)"`(`Step2BasicInfo.tsx:110-124`).
**단계 6 은 Lv 에 따라 다른 안내를 준다** (`Step6Description.tsx:5-9`):
```
L0: 'Describe the source URL and data collection method.'
L1: 'Describe interpolation methods, coordinate transformations, and quality control processes.'
L2: 'Describe the production method, algorithms used, and reference papers.'
```

#### INTERPRETATION *(잠정)*

배울 만한 **판단** 네 가지 — 전부 코드가 아니라 결정이다.

1. **「분류 배지 세 개를 한 줄로 묶는다」** — Level·Category·DataType 을 흩지 않고 `Classification` 한 행에 모았다. 배지가 화면 곳곳에 흩어지면 무엇이 판단 축인지 안 읽힌다는 판단이다.
2. **「생산자와 업로더가 같으면 한 줄, 다르면 두 줄」** — 같은 값을 두 번 말하지 않으면서, 다를 때는 그 다름이 눈에 띈다.
3. **「부모 데이터셋 섹션은 0건이어도 항상 그린다」** — 코드 주석이 이유를 남겼다: v1.3.0 이전에 0건일 때 섹션을 숨겼더니 **사용자가 혼란스러워했다**. 「없음」과 「그런 개념이 없음」이 구분되지 않았던 것.
4. **「단계 6 의 안내를 Lv 별로 바꾼다」** — 설명란을 「자유 서술」로 두지 않고 **Lv 에 따라 무엇을 적어야 하는지 다르게 알려 준다.** L0=출처·수집방법 / L1=보간·좌표변환·품질관리 / L2=산출방법·알고리즘·참고논문.

⚠ **가져오면 안 되는 판단도 뚜렷하다.**
- **모달** — v2 정본은 상세를 **전체 페이지**로 정하고, 모달 안 파일 목록에 자체 스크롤을 둔 것을 **명시적으로 반례로 든다**(`Policy_데이터셋_상세 §5`·개정 1.9).
- **정보 구조가 영어** — 섹션명·라벨이 영어이고 한국어는 몇몇 마이크로카피뿐. v2 는 화면 언어가 한국어다.
- **빈 값을 `'-'` 로 채우는 방식** — v2 는 `—` 를 쓰고 「없는 값을 지어내지 않는다」를 규칙으로 삼는다(`frontend/src/components/detail/fixture.ts:6-7`).
- **설명·키워드 섹션을 값이 없으면 통째로 없앰** — 3번 판단(부모 섹션은 항상 그린다)과 **PoC 내부에서도 서로 어긋난다.** 같은 화면이 한 섹션은 「0건도 그린다」, 다른 섹션은 「없으면 지운다」로 갈렸다.

---

## D. v2 현행·정본과의 대조

### D-1. v2 가 오늘 가진 것

#### EVIDENCE — 저장

`db/platform/schema.sql`

- `d3_dataset`(`:214-232`) — `id` `lab_id` `owner_account_id` `uploader_account_id` `source_label` `uploaded_at` `last_modified_at` `lineage_confirmed_at` `deleted_at` `deleted_by_account_id` `file_count`. 주석이 못 박는다: *「가공 단계 Lv 컬럼도 계보 상태 컬럼도 여기 없다 — 둘 다 파생값이다」*(`:212`).
- **`d3_dataset_description`**(`:241-251`) — 칸이 **셋뿐**이다: `name`(NOT NULL, 공백 불가) · `topic`(nullable, CHECK 4값 `강우·강수` `식생·NDVI` `지형·DEM` `토지피복·LULC`) · `summary`(nullable, **길이 상한 없음**) + `updated_at`.
- `d3_dataset_autometa`(`:257-270`) — `format` `variables[]` `period_start` `period_end` `crs` `grid` `total_size_bytes` `bundle_file_name`.
- `d3_file`(`:283-300`) — `kind`(CHECK `본체`|`기준 격자 파일`) `file_name` `size_bytes` `storage_key` `carries_lat` `carries_lon`.

#### EVIDENCE — 계약과 화면

- `contracts/seams/fe-core.yaml`
  - `DatasetUpdate`(`:1888-1899`) — **`name` · `topic` · `summary` 셋만.** 주석: *「자동으로 읽은 정보는 이 스키마에 자리가 없다」*
  - `DatasetBasicInfo`(`:1986-2027`) — required `[variables, crs, period, grid, format, files, sourceLabel, owner, uploader]` = **아홉**
  - `DatasetDetail`(`:2046-2075`) — `name` `fileName` `summary` `topic` `processingLevel` `lineageState` `verification` `accessState` `bodyAccessible` `accessRequestPending` `uploadedAt` `lastModifiedAt` `lineageConfirmedAt` `basicInfo` `projects` `actions`
- `frontend/src/components/detail/BasicInfoGrid.tsx:9-19` — 아홉 칸이 **이미 구현돼 있다**: `구성` `좌표계` `기간` `격자` `포맷` `파일` `원천 표기` `소유자` `올린 사람`

#### EVIDENCE — 정본

- `Policy_데이터셋_상세.md:118` — *「**기본 정보는 아홉 칸이다** — 구성 · 좌표계 · 기간 · 격자 · 포맷 · **파일** · 원천 표기 · 소유자 · 올린 사람. 공간 범위는 이름과 지도가 이미 말하므로 칸을 따로 두지 않는다.」*
- `Policy_데이터셋_상세.md:159` (상세 헤더) — *「줄마다 한 가지만 말한다 — ① 제목 = 사람이 붙인 이름 ② 그 아래 파일명(작게·고정폭) ③ 한 줄 요약 ④ 칩은 판단에 쓰는 것만(주제 · 가공 단계 · Verified). **소유자·올린 사람·포맷은 헤더에 두지 않고 기본 정보가 라벨:값으로 맡는다**」*
- `Policy_데이터셋_상세.md:102` (판단 순서) — *「뭔가 → 믿을 수 있나 → 어떻게 생겼나 → 어떻게 쓰였나」*. 섹션 순서 = **기본 정보 → 계보 → 미리보기 → 활용**. 2026-08-17 에 계보를 미리보기보다 앞으로 옮겼다.
- `DataModel_공통_기반.md:65-68` — `자동으로 읽은 정보`(파일에서 자동) / `파일` / **`사람이 적는 정보 = 이름 · 주제 · 설명`**
- `Policy_업로드와_계보_확정.md:114-124` (입력값 규칙) — 이름 **1~80자 필수**(기본값=파일명에서 생성) · 주제 **고정 4값 필수** · **설명 0~300자 선택** · 소속 프로젝트 0개 이상 · 가공 방식 문장 1~120자 · 부모 역할 2값 · 원천 표기 0~60자

### D-2. 항목 대조 — PoC 대 v2

「이미 있다 / 이름이 다르다 / 없다」로만 가른다. **없다고 해서 넣어야 한다는 뜻이 아니다** — 정본이 뺀 것도 여기 들어 있다.

| PoC 항목 | v2 상태 | v2 자리 |
|---|---|---|
| `name` | **있다** | `d3_dataset_description.name` |
| `description` | **이름이 다르다** → `summary`(한 줄 요약) | `d3_dataset_description.summary` |
| `category`(4값) | **이름이 다르다** → `topic`(4값, 값 자체도 다름) | `d3_dataset_description.topic` |
| `format` | **있다** (자동) | `d3_dataset_autometa.format` |
| `crs` / `coordinate_system` | **있다** (자동) | `d3_dataset_autometa.crs` |
| `time_start`/`time_end` | **있다** (자동, 이름 `period_*`) | `d3_dataset_autometa.period_start/end` |
| 변수 목록 (`dataset_variables`) | **있다** (자동, `구성` 칸) | `d3_dataset_autometa.variables[]` |
| `data_size` | **있다** (자동) | `d3_dataset_autometa.total_size_bytes` |
| `file_count` | **있다** | `d3_dataset.file_count` |
| 격자 | **있다** (자동) | `d3_dataset_autometa.grid` |
| `uploader_name` | **있다** (계정 참조) | `d3_dataset.uploader_account_id` |
| 소유자 | **있다** — **PoC 에는 없던 개념** | `d3_dataset.owner_account_id` |
| `source_url` | **이름이 다르다** → `source_label`(URL 이 아니라 **표기 문자열**) | `d3_dataset.source_label` |
| `input_dataset_ids` | **이름이 다르다** → 별도 관계 테이블 | `d4_lineage_edge` |
| `level` (L0~L4) | **이름·성격이 다르다** → `processingLevel`, **저장 안 하고 계보에서 파생** | 파생 |
| `access_type`(3값) | **이름·값이 다르다** → 접근 상태 2값(`열림`/`잠김`) | `d2_dataset_access` |
| `data_type` (6값 · 출처 축) | **없다** | — |
| `keywords` | **없다** | — |
| `related_doi` | **없다** | — |
| `creator_name` / `creator_org` | **없다** | — |
| `uploader_org` | **없다** | — |
| `region` / `region_original` | **없다** | — |
| `spatial_resolution` / `_meters` | **없다** | — |
| `measurement_interval` | **없다** | — |
| `bbox_*` (4칸) | **없다** — 정본이 *「공간 범위는 이름과 지도가 이미 말한다」*로 뺐다 | — |
| `preview_image_path` | **없다** (미리보기는 D7 렌더 경로) | — |
| `download_count` | **없다** (다운로드는 `d8_download` 이력으로 쌓기만) | `d8_download` |
| `status`(5값) / `progress_*` | **없다** — 업로드 세계(`d5_upload`)로 분리 | `d5_upload` |
| `search_text` / `embedding` | **없다** (D9·D10 체인 분리 — `CLAUDE.md §3-3`) | `db/ai` |

**셈** — PoC 의 데이터셋 설명 항목(bbox 4칸·progress 3칸을 각 1항목으로 묶어 센 항목 기준) **34항목** 중,
v2 에 **이미 있다 12** · **이름이 다르다 6** · **v2 에 없다 16**.
v2 에만 있고 PoC 에 없는 것 — **소유자**(승계 개념) · **레코드 시점 3종** · **계보 상태** · **묘비** · **Verified** · **주제 4값 CHECK** · **기준 격자 파일**.

### D-3. 정본과의 충돌 — **해소하지 않는다**

| # | 충돌 | v1/PoC | v2 정본 | 성격 |
|:--:|---|---|---|---|
| **X-1** | **설명의 길이** | `description` = `Text`, 상한 없음. 화면도 접지 않고 전문을 편다 | `설명 0자 이상 **300자 이하**`(`Policy_업로드 §5`), 화면 명칭은 **`한 줄 요약`**(`Policy_상세 §8`) — 그런데 **DB `d3_dataset_description.summary` 에는 CHECK 가 없다** | 정본이 이긴다. 다만 「300자」와 「한 줄」이 **정본 안에서도 서로 다른 크기**를 말한다 |
| **X-2** | **설명의 필수 여부** | 업로드 마법사 6단계에서 **비면 못 넘어간다** (`canProceedForStep`) | **선택**(`Policy_업로드 §5`) | 정본이 이긴다. PoC 는 「설명 없는 데이터셋을 만들지 않겠다」를 강제로 택했고 v2 는 안 택했다 |
| **X-3** | **주제/분류 축의 개수** | **두 축** — `category`(주제 4값) + `data_type`(출처 6값). 게다가 `level` 이 사람 입력 | **한 축** — `topic` 4값뿐. `data_type` 에 대응하는 자리가 v2 에 **없다**. Lv 는 계보에서 **파생** | 정본이 이긴다. 「출처가 관측인가 위성인가 모델인가」를 v2 는 못 적는다 |
| **X-4** | **주제 값 집합이 실데이터를 못 담는다** | PoC 는 `other` 를 뒀다 | v2 4값에 `기타` 가 없다. `SEED-DATA.md:138-139` 의 `D-11`(가뭄지수)·`D-12`(LST)가 `[주제 무근거]` 로 남는다 | **이미 열린 미결이다** — `SEED-DATA.md:266`: *「이건 시드 문제가 아니라 정본 문제이고 Ted 판단이 필요하다」* |
| **X-5** | **화면 그릇** | 모달 | 전체 페이지. 정본이 모달+내부 스크롤을 **반례로 명시**(`Policy_상세` 개정 1.9) | 정본이 이긴다 |
| **X-6** | **원천의 성격** | `source_url` — **URL** | `source_label` — **표기 문자열**(계보 그래프의 점선 노드), 0~60자 | 정본이 이긴다. PoC 의 URL 을 담을 자리가 v2 에 없다 |
| **X-7** | **관련 논문·DOI** | `related_doi` 를 상세 `Information` 섹션에 링크로 노출 | 데이터셋에 **없다.** 논문은 **프로젝트**(`d6_project`, 유형 `논문`)로 표현되고 `연결 주소`는 프로젝트 1:1 | 정본이 이긴다 — 다만 **모델이 다른 것**이지 「빠뜨린 것」이 아니다 |
| **X-8** | **빈 상태 처리** | 값 없는 섹션을 **통째로 없앤다**(설명·키워드) / `-` 로 채운다(스칼라) | `—` 를 적고 **자리는 남긴다**. 「없으면 없다고 적는다」가 기준 파일 칸에 명시(`Policy_상세 §5`) | 정본이 이긴다 |
| **X-9** | **`Classification` 배지 묶음** | Level·Category·DataType 세 배지를 기본 정보 안 한 행에 | 칩은 **헤더**에 있고(주제·가공 단계·Verified), **기본 정보에는 라벨:값만** — 정본이 *「같은 값을 두 곳에서 말하지 않는다」*로 못 박음 | 정본이 이긴다 |
| **X-10** | **미리보기 이미지** | 업로드 6단계에서 **사람이 올린다**(`preview_image_path`) | 미리보기는 **D7 렌더 산출**이고 v2 는 *「바꾼 설정은 저장하지 않는다」* | 정본이 이긴다 |
| **X-11** | **v1 세대 문제** | v1 의 상세·업로드 화면이 **커밋되지 않은 워크트리 안에만 있다** | — | 「v1 화면」을 인용할 근거가 실은 **본류에 없다**. 참조하려면 Ted 가 그 워크트리를 정본으로 인정해야 한다 |
| **X-12** | **설명을 누가 쓰는가** | PoC 는 **AI 가 쓴다** — `ai_description.py` 가 메타데이터로 2-3문장을 생성 | v2 의 AI 는 **두 지점뿐**(계보 제안 · 자연어 검색 — `CLAUDE.md §0`). 설명은 *「업로드할 때 사람이 적는다」*(`DataModel §4.1`) | 정본이 이긴다. **하지만 이것이 「PoC 에 실제 설명 문구가 0건인 이유」이므로 Ted 가 알아야 한다** — 「가져오겠다」의 대상이 애초에 축적되지 않았다 |

---

## 「v2 가 가져올 것 / 가져오면 안 되는 것」

### 가져올 것 — 전부 **지식·방법**이고, v2 가 새로 만든다

1. **업로드 설명란의 Lv 별 안내 문구 전략.** 설명란을 빈 상자로 두지 않고 「이 Lv 에서는 무엇을 적어야 하는가」를 다르게 안내한다. PoC 의 셋(L0=출처·수집방법 / L1=보간·좌표변환·품질관리 / L2=산출방법·알고리즘·참고논문)은 **문구가 아니라 축**으로 가져온다 — v2 의 Lv 는 사람이 고르는 값이 아니라 계보 파생값이므로 안내가 붙는 시점도 다르다.
2. **「0건도 그리는 섹션」이라는 판단과 그 근거.** PoC 코드 주석이 남긴 사실 — 부모 데이터셋 섹션을 0건일 때 숨겼더니 사용자가 혼란스러워했고 v1.3.0 에서 되돌렸다. v2 의 *「없으면 없다고 적는다」*(기준 격자 파일)와 **같은 판단이다.** 정본이 이미 이긴 자리라 새로 도입할 것은 없고, **다른 섹션에도 같은 규칙을 밀 근거**로 쓴다.
3. **분류 축을 둘로 나눈 발상 — 주제(무엇에 관한 데이터인가) 대 출처(어떻게 만들어진 데이터인가).** PoC 의 `data_type` 6값(관측·원격탐사·시뮬레이션·재분석·복합·파생)이 그것이다. v2 에 자리가 없으므로 **지금 넣자는 뜻이 아니라, `X-3`·`X-4` 를 Ted 에게 올릴 때 「무엇이 빠졌는가」를 정확히 부르는 어휘**로 쓴다.
4. **원문과 정규화값을 둘 다 저장한 판단.** `region_original`(사람이 친 그대로) + `region`(필터용 정규화 id), `spatial_resolution`(자유 문자열) + `spatial_resolution_meters`(파싱 실패 시 NULL). 「검색을 위해 정규화하되 사람이 쓴 말을 지우지 않는다」는 방법이다.
5. **어휘 별칭을 두 축에만 허용한 보안 판단.** `category`·`data_type` 에만 별칭을 두고 `access_type`·`level`·`format` 에는 금지했다 — 이유가 *권한 상승 벡터*(`"open"→"public"` 같은 조용한 치환)라고 코드에 남아 있다. v2 의 AI 검색이 동의어 사전(`d9_topic_synonym`)을 쓰므로 **그 사전이 절대 건드리면 안 되는 축**을 정할 때 그대로 유효하다.
6. **「소유자와 올린 사람이 같으면 한 줄, 다르면 두 줄」.** v2 는 정본이 *「소유자와 올린 사람을 둘 다 표시한다」*(`Policy_상세 §5`)로만 정해 뒀고, **같을 때의 처리는 정하지 않았다.** 정본 목업이 실제로 *「같은 사람이라 두 칸이 됐다」*(`데이터셋_상세_260817.html:519`)고 적어 둔 자리다 — 여기서 PoC 의 판단이 참고가 된다.
7. **v1 의 「설명란이 없다」는 사실 자체.** 인제스천 파이프라인에는 설명란이 필요 없었고, 재사용 판단에는 필요하다. **1차 범위 재정의의 근거**로 쓸 수 있는 관찰이다.
8. **`03 Reference-Data` 의 원천 동봉 문서 — 설명 문구의 유일한 실물 원료.** 특히 `[Data Info]SPI/SPEI-4weeks.docx` 두 건은 **`Dataset Description` · `Data Name` · `생산자 이름` · `생산자 소속`** 이라는 **연구자 스스로가 쓴 메타데이터 서식**을 보여 준다 — 어떤 칸을 두어야 연구자가 실제로 채우는지의 실증이다. 문서를 **읽고 사람이 v2 의 `summary` 를 쓴다.** 파일을 옮기거나 파싱해 자동 채우지 않는다.
9. **PoC 의 AI 설명 생성이 남긴 반증.** 설명을 AI 파생물로 다루면 **사람이 쓴 설명이 한 건도 쌓이지 않는다** — PoC 가 그 결과다(§B-2). v2 가 설명을 「사람이 적는 정보」로 못 박은 판단을 뒷받침하는 실측이다.

### 가져오면 안 되는 것

1. **어떤 코드도.** 모델 클래스·Pydantic 스키마·React 컴포넌트·CSS — `CLAUDE.md §0`·`§5` · `PLAN-SoT §6`. 이 문서 어디에도 「복사」를 권하는 문장이 없다.
2. **PoC 의 저장 형태 — 40여 칸 단일 테이블.** v2 는 `d3_dataset` / `d3_dataset_description` / `d3_dataset_autometa` 3분할을 **이미 골랐고** 그것이 `DataModel §4.1` 이다. 옮기면 v2 가 내린 결정을 되돌린다.
3. **모달 상세 화면.** 정본이 명시적 반례로 든다.
4. **설명 필수화.** 정본은 선택이다(`X-2`).
5. **상한 없는 설명 본문.** 정본은 300자이고 화면 명칭이 `한 줄 요약`이다(`X-1`).
6. **`level` 을 사람이 고르게 하는 것.** v2 의 Lv 는 계보 파생값이고, 정본이 *「직접 고치는 칸은 두지 않는다」*로 못 박았다.
7. **`access_type` 3값.** v2 는 2값(`열림`/`잠김`) + 허용 목록 + 6개월 만료라는 다른 모델이다.
8. **`preview_image` 를 사람이 올리게 하는 것**(`X-10`), **`source_url` 을 URL 로 받는 것**(`X-6`), **`related_doi` 를 데이터셋에 붙이는 것**(`X-7`).
9. **빈 값 섹션을 통째로 없애는 처리.** 정본은 자리를 남기고 `—` 를 적는다(`X-8`).
10. **v1 의 화면.** 계약 확인용 개발 도구이고, 그마저 **커밋되지 않은 워크트리 안에만 있다**(`X-11`).
11. **PoC 의 어휘 값 자체.** `precipitation/vegetation/drought/other` 는 v2 의 `강우·강수 / 식생·NDVI / 지형·DEM / 토지피복·LULC` 와 **값이 다르다.** 축의 발상은 가져오되 값은 정본이 정한다.
12. **AI 로 설명을 생성하는 것**(`X-12`). `CLAUDE.md §0` 이 AI 를 두 지점으로 못 박았고, 설명은 그 둘이 아니다.
13. **PoC·v1 의 설명 문구를 「가져오는」 것 — 가져올 것이 없다.** 실물은 `03 Reference-Data` 문서에 있고, 코드베이스에는 시연 대본 1줄과 mock 뿐이다(§B-2). **「PoC 에서 문구를 옮긴다」는 계획은 성립하지 않는다.**

---

## 측정하지 못한 것

- **PoC 백엔드 두 파서 계보**(`backend/app/services/processors/` · `viz-service/app/decoders/`)의 메타데이터 추출 항목을 **전수로 열지 않았다.** 이 조사는 *사람이 적는 설명 항목*이 대상이라 자동 추출 항목은 `dataset_variables` 테이블 층에서 끊었다. 「자동으로 읽은 정보」를 v2 가 어디까지 읽을 수 있는가는 **별도 조사**다(`DATA-PROCESSING-HARVEST.md` 소관).
- **v1 `colab-frontend` 본류에 데이터셋 화면이 있었던 이력**은 확인하지 않았다(git 히스토리 미조회). 지금 시점에 없다는 것만 확인했다.
- PoC 상세 화면의 **CSS 수준 레이아웃 의도**(간격·타이포 스케일)는 읽지 않았다. 섹션 구성·순서·강조·접힘까지만 봤다.
- **원천 동봉 문서 10건 중 5건만 열었다**(§B-1). `.pdf` 2 · `.md` 1 · 나머지 `.docx`/`.pptx` 2 에 설명 문구가 더 있는지는 **`[미확인]`**. 설명란 채우기를 실제로 착수할 때 전수로 열어야 한다.
- PoC 의 **운영 DB 덤프**는 존재하지 않아 확인할 수 없었다 — 「실제 사용자가 채운 설명이 몇 건인가」는 코드베이스만으로는 **원리적으로 `[미확인]`** 이다. 확인하려면 PoC 가 돌던 DB 가 필요하다.
- v2 정본 목업 `데이터셋_상세_260817.html` 을 전수로 읽지 않았다 — `dh-sum`(한 줄 요약) 자리만 grep 해 2건을 확인했다.
