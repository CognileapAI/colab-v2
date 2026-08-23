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

## 규칙

- **전체 파일 메모리 적재 금지.** 50GB급이 들어온다 — 윈도우/스트리밍 처리
- 상태행과 outbox행은 **단일 트랜잭션**. 릴레이는 독립 컴포넌트
- 멱등 키 = 처리 실행 ID + 스테이지. at-least-once 전제
- TTL 초과 처리중 → 실패로 회수하는 reaper 필요
