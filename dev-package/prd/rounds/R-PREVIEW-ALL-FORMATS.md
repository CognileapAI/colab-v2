> spec: dev-package/prd/specs/preview-all-formats.md

# 모든 지원 포맷 미리보기 Implementation Plan

> **For agentic workers:** 위임 원칙(글로벌 `CLAUDE.md`) ＋ `lane-worker` 에이전트로 태스크당 레인 1개(권고), 또는 `executing-plans`(로컬 vendored)로 이 세션에서 직접. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** 기존 다섯 포맷과 GRIB1/2·일반 HDF5를 같은 업로드·선택·렌더 흐름에서 지원한다.

**Architecture:** pipeline-worker가 매직과 try-open으로 일곱 포맷을 감지한다. viz-render가 rasterio/GDAL GRIB 드라이버와 h5py에서 안정적 선택 ID와 2D 값을 만들고 기존 비지도·지도 산출 파이프라인을 재사용한다.

**Tech Stack:** Python 3.12, FastAPI, NumPy, rasterio/GDAL, h5py, pytest, React

**Spec:** `dev-package/prd/specs/preview-all-formats.md`

## Global Constraints

- 좌표를 추정하지 않는다.
- 결측 마스킹 뒤 scale/offset을 적용한다.
- 계약 enum과 일반 지도 기능을 늘리지 않는다.

---

### Task 1: 감지·지원 목록

**Files:** pipeline-worker formats/detect/renderable 및 시험, 계약 설명

- [x] 실패 시험에서 일반 HDF5 감지와 일곱 포맷 renderable을 요구한다.
- [x] RED를 확인한다.
- [x] 매직+try-open 감지와 목록을 구현한다.
- [x] pipeline-worker 단독 시험을 통과시킨다.

### Task 2: GRIB·HDF5 판독

**Files:** viz-render readers, requirements, Dockerfile 및 시험

- [x] 안정적 선택 ID, slice, 결측·scale, 오류 시험을 작성한다.
- [x] RED를 확인한다.
- [x] rasterio/GDAL과 h5py 판독을 구현한다.
- [x] 실제 fixture를 포함한 viz-render 시험을 통과시킨다.

### Task 3: 전 구간 검증과 안내

**Files:** 포맷 커버리지 설정·E2E, frontend 안내 시험/소비 경로, 세션 기록

- [x] 일곱 포맷 커버리지와 신규 두 사용자 여정 시험을 작성하고 RED를 확인한다.
- [x] 기존 서버 제공 목록이 일곱 포맷으로 화면에 표시되게 한다.
- [x] 선언 게이트와 Docker 재현성을 실행한다.
- [x] 실행하지 못한 E2E·arm64 결과를 미완료로 기록한다.
