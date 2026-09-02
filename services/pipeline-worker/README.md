# pipeline-worker

**담는 도메인** — D5 Ingestion & Pipeline

프로파일: 고 CPU·메모리 · bursty · 스팟 가능. **유일하게 워크로드가 다르기 때문에** 별도 배포 단위다.

## 소유하는 것

presigned 업로드 · 파일 헤더 파싱 · 포맷 자동 감지 · 좌표계 변환 · COG 변환 · overview 선생성 · outbox 릴레이 · 처리 원장

## 지원 포맷 — `NetCDF` · `Binary` · `HDF4` · `GeoTIFF` (`〈51〉`)

숫자가 아니라 목록이다. PoC 의 4포맷(GRIB·NetCDF·Binary·HDF5)과 **수만 같고 구성이 다르다** —
GRIB 이 빠지고 GeoTIFF 가 들어오며, MODIS 실물은 매직바이트상 **HDF4**(`0e 03 13 01`)다(`SEED-DATA F-2`).

| 포맷 | 사례 | 변환 함정 |
|---|---|---|
| NetCDF | GK2A | LCC 투영 격자 — 위경도는 **파일 내 좌표 변수로 계산된다**(동봉 격자 대비 오차 1.3e-5°). 기준 격자는 편의 |
| Binary | HSR | Curvilinear → WGS84. **기준 격자 파일 필수** — 헤더에 투영 파라미터가 없다(36~63 B 가 0). 블록 수는 `num_data` 를 읽되 **파일 길이와 교차검증**한다 — 원천은 3 을 선언하고 1블록만 담는다 |
| HDF4 | MODIS | Sinusoidal → WGS84. **꼬리 `StructMetadata` 로 격자 계산 가능**(오차 7e-14°). `.hdf` 를 HDF5 로 오인하지 않는다 (매직 `0e031301`) — 폴더명 `file_format_5_HDF5` 는 오기다 |
| GeoTIFF | HLS S30 · KWRA | **입력 tif ↔ 산출 COG 를 층에서 가른다** — 이미-COG · 타일만 · 스트립 3부류(`DATA-REFERENCE §4`) |

감지는 **매직바이트**가 정본이고 확장자는 힌트다(`DR-3`). 좌표를 못 읽으면 `[미상]` + 실패 —
지어내지 않는다(`DR-9`). 절차와 함정 목록은 `dev-package/DATA-REFERENCE.md` 와
`dev-package/sessions/DATA-PROCESSING-HARVEST.md`(C3). **코드가 아니라 알아낸 사실을 가져온다.**

## 기준 격자 축 판별 (`〈63〉-㉰`·`〈65〉`·`〈66〉`)

**서버가 파일에서 읽는다 — 사람에게 묻지 않는다.** 계약에 `gridAxis` 가 없다.
출력은 **`carries_lat`·`carries_lon` 두 불리언**이다(`〈66〉`) — 한 파일이 둘 다 담을 수 있다
(실물 16건 중 2건. `rdr_500m_latlon.nc`).

| 순서 | 신호 | 단독 판정 |
|---|---|---|
| ① | 컨테이너 내부 변수명(`lat`·`lon`) | **가능** — 값 범위로 교차검증 |
| ② | 값 범위 `max > 90` / `min < -90` → 경도 | **가능**(`〈65〉` 유권해석. 물리적 불가에 의한 배제) |
| ③ | 쌍 정합 — 같은 형상 격자 **정확히 2건** | 1차 신호. 2건이 아니면 미정의 → 거절 |
| ④ | 이방성(축별 변화량) | **불가** — 단독 14/16, 경도 2건을 조용히 뒤집는다 |
| ⑤ | 파일명 | **불가** — 대조 전용. 값과 어긋나면 값을 따르고 기록 |

**판별 실패는 그 파일을 거절한다** — 축이 빈 행을 만들지 않는다(`〈66〉`). **등록은 막지 않는다**
(`〈63〉-ⓒ`). 그릴 수 없는 것과 등록할 수 없는 것은 다르다.

**기준 격자 파일 행은 워커가 만든다**(`〈69〉-⑴`). 접수(`createUpload`)는 업로드와 본체 파일
행까지만 세운다 — `d5_upload_file` 의 CHECK 가 축을 요구하는데 축은 파일을 열어야 나온다.
`0004` 는 고치지 않는다(CHECK 를 상태로 조건화하면 「축이 빈 격자 행」이 합법이 된다).
**대가 — 판별 전까지 격자 파일이 원장에 안 보인다.**

**같은 폴더에 `.npy` 쌍과 결합축 `.nc` 가 함께 있으면 `.nc` 가 정본이다**(`〈66〉`·`〈69〉-⑵`).
HSR 두 격자는 **행·열 각 1셀(500 m) off-by-one** 만큼 어긋난다 — 남단 위도가 `.nc` 30.107119,
`.npy` 30.102751 이다. **그림으로는 구분되지 않는다.** 격자가 아닌 컨테이너는 사유를
`ReferenceGrid.container_rejections` 에 남긴 채 `.npy` 로 내려간다 — 조용히 무시하지 않는다.

## 이벤트 7종 · outbox (`contracts/events/**`)

`upload.accepted` **만 core-api 가 낸다**(봉투가 `source` 를 const 로 못박았고
`d5_pipeline_event` 가 CHECK 로 강제한다). ②~⑦ 이 이 배포 단위 소관이다:
`file.format-detected` → `file.header-parsed` → `file.crs-normalized` →
`preview.cog-built` → `upload.ready`, 그리고 어느 단계에서든 갈라지는 `upload.failed`.

- 저장 자리는 **W1 이 만든 `d5_*` 표**다 — 새 표를 만들지 않는다
- 릴레이(`app/worker.py`)가 미발행분을 내보내고 발행 시각을 찍는다
- reaper 가 **만료된 미등록 업로드**를 지운다(`〈64〉-ⓒ`). **처리 중인 것은 건너뛴다**
  (`〈67〉` 이행 제약 ㉠ — 「시계가 처리를 앞지르지 않는다」). 「처리 중」의 정의는
  `core-api` 와 **같은 문장**이다 — 갈라지면 두 스윕이 다른 행을 지운다

`renderable` 목록은 **여기**(`d5/renderable.py`)에 있고 **계약에 박지 않는다**(`NB-3`).

## 규칙

- **전체 파일 메모리 적재 금지.** 50GB급이 들어온다 — 윈도우/스트리밍 처리
- 상태행과 outbox행은 **단일 트랜잭션**. 릴레이는 독립 컴포넌트
- **멱등 키 = `<이벤트 타입>:<uploadId>`** — 결정론적이다. ⚠ 이 줄은 예전에
  「처리 실행 ID + 스테이지」였는데 **동결 계약과 어긋난다**: `envelope.json#IdempotencyKey`
  가 「발행자가 난수를 쓰지 않으므로 outbox 행이 다시 만들어져도 같은 키가 나온다」로
  못박았고, 실행 ID 를 섞으면 재적재 때 키가 달라져 **중복 제거가 뚫린다.** 계약을 따랐다
- at-least-once 전제 — 소비자가 멱등 키로 거른다
- TTL 초과 처리중 → 실패로 회수하는 reaper 필요

## 저장 모드 — 바이트를 어디서 읽나 (`ports/blobs.py` · `kernel/blob_backends.py` · `PLAN-SoT §9 〈178〉-㉴`)

감지·파싱은 로컬 경로만 본다. 그 경로에 바이트를 놓는 것이 `UploadBlobPort` 다 — s3 모드는 키를
**통째로 내려받는다**(부분·스트림 아님 — netCDF4·h5py·pyhdf 와 매직 try-open 이 파일 전체를 요구한다).

| env | 모드 | 뜻 |
|---|---|---|
| `COLAB_WORKER_STORAGE_MODE` | — | `local`(기본) \| `s3`. **모르는 값은 기동 거부**(local 로 접지 않는다) |
| `COLAB_WORKER_UPLOAD_DIR` | local **필수** | core-api `COLAB_CORE_UPLOAD_DIR` 과 같은 자리. s3 모드에선 불요 |
| `COLAB_WORKER_WORKDIR` | local 선택 · s3 **필수** | 이름 붙은 뷰·산출물·(s3) 내려받은 바이트. local 기본 = `<UPLOAD_DIR>/_work` |
| `COLAB_WORKER_S3_BUCKET` · `COLAB_WORKER_S3_REGION` | s3 **필수** | core-api 와 같은 버킷·리전. 자격증명은 `kernel/aws_credentials.py` 사슬(env→ECS→IMDSv2) — **액세스 키를 env 에 두지 않는다**(EC2 는 역할) |

- s3 모드의 작업 디렉터리는 **캐시이지 상태가 아니다** — 처리(성공·실패 모두) 뒤 그 업로드 디렉터리를 지운다.
  상한은 두지 않는다(동시 처리 1 → 업로드 한 건 크기). EBS 사이징은 Ted 판정 항목.
- 헬스 본문 `storageMode` 는 env 에 **선언된** 값(정적 — 버킷·자격증명을 안 본다). `deploy_doctor` 가 읽는다.
- `kernel/{sigv4,aws_credentials,s3}.py` 는 core-api 원본의 byte-identical 복제본(`contracts/codegen/manifest.toml` 등기) —
  **여기서 고치지 않는다.** core 에서 고치고 재생성한다.
