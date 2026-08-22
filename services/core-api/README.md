# core-api

**담는 도메인** — D1 Identity & Lab · D2 Access & Policy · D3 Catalog · D4 Lineage · D6 Project · D8 Insight

프로파일: stateless · IO bound · 지연 민감. 6개 도메인이 같은 프로파일이므로 한 배포 단위(모듈러 모놀리스)다.

## 도메인별 소유

| 도메인 | 소유하는 것 |
|---|---|
| **D1** Identity & Lab | 연구실(테넌트 루트, 정보 7항목, 공개범위 기본값) · 계정. **유일한 shared kernel** |
| **D2** Access & Policy | 역할 2층 · 권한 스위치 4종 · 위임 · 접근 상태(열림/잠김/허용자/만료) · Verified 기록 · 승인 큐 |
| **D3** Catalog | 데이터셋 · 파일(본체 N + 기준 격자 0~1) · 자동 추출 메타 · 사람 기입 메타 · 조회/필터/집계 |
| **D4** Lineage | 계보 관계(다중 부모, 주/보조 입력) · 가공 방식(관계에 부착) · Lv 자동 계산 · 계보 상태 4값(파생) |
| **D6** Project | 과제/논문 1건 · 상태 · 데이터셋 N:N + 활용 의미 문장 |
| **D8** Insight | 데이터 맵 · 요약 지표 · 활동 타임라인 · 할 일 함. **쓰기 없음** |

## 이 서비스의 금지 사항

- **geo 라이브러리 import 금지** — rasterio·GDAL·xarray 등. banned-import 게이트가 막는다.
  래스터를 열어야 하는 일은 전부 `viz-render` 또는 `pipeline-worker`가 한다.
  (v1 PoC에서 타일 API가 core 안에서 rasterio를 직접 열어 프로파일이 오염됐다.)
- **도메인 간 직접 참조 금지** — 자기 테이블 + D1만. cross-domain은 Port 경유.
- **un-scoped 쿼리 금지** — 모든 조회에 연구실 스코프가 자동 주입된다.

## 멀티테넌시 3중 방어

1. 스코프 커널 — 트랜잭션마다 연구실 스코프 주입, 미설정 시 default-deny
2. RLS — ENABLE + FORCE + tenant-isolation 정책
3. cross-tenant 음성 테스트 — 읽기 · 자식 · 미스코프 · 쓰기(WITH CHECK) 4종

---

## 실물 (WU-P0 산출물 #4 — `dev-package/sessions/P0-core-api.md`)

계약 정본은 `contracts/seams/fe-core.yaml` 이고, 이 서비스는 그 **34 오퍼레이션 전부**를 등록한다.
실질의 5 개만 DB 를 읽고 나머지 29 개는 501 + `ErrorEnvelope` 다 — 200 으로 가짜 값을 내리지 않는다.

```
src/colab_core/
  app/        조립 루트 — 여러 도메인을 아는 유일한 자리 (routes/ 포함)
  domains/    d1_identity d2_access d3_catalog d4_lineage d6_project d8_insight
  ports/      cross-domain 인터페이스. 구현은 소유 도메인에 있다
  kernel/     스코프 커널 · 세션 · 설정 · 정규 ID(Ulid)
```

### 띄우기

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
export COLAB_CORE_DATABASE_URL='postgresql+psycopg://colab_app:...@호스트/디비'
export COLAB_CORE_SUBJECTS_FILE=/경로/subjects.json     # 개발자가 심은 계정 (P-17)
.venv/bin/uvicorn --factory colab_core.app:create_app
```

접속 롤은 **NOBYPASSRLS · 비소유자**여야 한다. 만드는 법은 `ops/app-role.sql` (왜 `db/` 가 아닌지도 거기 적었다).

### 테스트

```bash
.venv/bin/pip install -r requirements-dev.txt
COLAB_CORE_TEST_DATABASE_URL=... COLAB_CORE_TEST_SUBJECTS_FILE=... .venv/bin/python -m pytest
```

DB 를 붙이지 않으면 `test_live_endpoints` · `test_scope_kernel` 이 **fail** 한다. skip 이 아니다.

### 의존 핀

`requirements.in`(직접 선언) → `requirements.txt`(전이까지 닫힌 목록, 전부 `==`).
개발 의존은 `requirements-dev.in` / `requirements-dev.txt`. `frontend/package-lock.json` 과 같은 역할이다.
