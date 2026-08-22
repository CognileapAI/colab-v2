# pipeline-worker

**담는 도메인** — D5 Ingestion & Pipeline

프로파일: 고 CPU·메모리 · bursty · 스팟 가능. **유일하게 워크로드가 다르기 때문에** 별도 배포 단위다.

## 소유하는 것

presigned 업로드 · 파일 헤더 파싱 · 포맷 자동 감지 · 좌표계 변환 · COG 변환 · overview 선생성 · outbox 릴레이 · 처리 원장

## 4포맷 (PoC에서 실증된 도메인 지식)

| 포맷 | 사례 | 변환 함정 |
|---|---|---|
| GRIB | ERA5 | 경도 0–360 → WGS84 |
| NetCDF | GK2A | LCC → WGS84 |
| Binary | HSR | Curvilinear → WGS84 |
| HDF5 | MODIS | Sinusoidal → WGS84 |

절차와 함정 목록은 v1 참조 폴더의 `HARVEST.md`(WU-C3 산출물). **코드가 아니라 알아낸 사실을 가져온다.**

## 규칙

- **전체 파일 메모리 적재 금지.** 50GB급이 들어온다 — 윈도우/스트리밍 처리
- 상태행과 outbox행은 **단일 트랜잭션**. 릴레이는 독립 컴포넌트
- 멱등 키 = 처리 실행 ID + 스테이지. at-least-once 전제
- TTL 초과 처리중 → 실패로 회수하는 reaper 필요
