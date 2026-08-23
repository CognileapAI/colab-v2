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
| NetCDF | GK2A | LCC 투영 격자 — 위경도는 파일 내 좌표 변수 또는 기준 격자 |
| Binary | HSR | Curvilinear → WGS84. 블록 수는 헤더 `num_data` 가 말한다 — 가정 금지 |
| HDF4 | MODIS | Sinusoidal → WGS84. `.hdf` 를 HDF5 로 오인하지 않는다 (매직 판정) |
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

## 이벤트 7종 · outbox (`contracts/events/**`)

`upload.accepted` **만 core-api 가 낸다**(봉투가 `source` 를 const 로 못박았고
`d5_pipeline_event` 가 CHECK 로 강제한다). ②~⑦ 이 이 배포 단위 소관이다:
`file.format-detected` → `file.header-parsed` → `file.crs-normalized` →
`preview.cog-built` → `upload.ready`, 그리고 어느 단계에서든 갈라지는 `upload.failed`.

- 저장 자리는 **W1 이 만든 `d5_*` 표**다 — 새 표를 만들지 않는다
- 릴레이(`app/worker.py`)가 미발행분을 내보내고 발행 시각을 찍는다
- reaper 가 **만료된 미등록 업로드**를 지운다(`〈64〉-ⓒ`)

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
