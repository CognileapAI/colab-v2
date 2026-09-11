> spec: dev-package/prd/specs/s1-gate-perf.md

# G10 Implementation Plan

## Task 1: 기준선과 실패 시험

- [x] 기존 기준선 확보: core-api 1040 실행/6 deselect/157.4초, pipeline 268/48/7.6초. viz와 ai는 같은 tree에서 추가 측정한다.
- [x] jobs 값 오류, xdist 부재, core worker DB 부재가 green이 아닌지 selftest로 고정한다.
- [x] jobs=1/4가 같은 테스트 집합과 판정 계수를 내는지 실패 시험을 먼저 작성한다.

## Task 2: 서비스 pytest 병렬화

- [x] pytest-xdist를 네 서비스 시험 의존에 고정한다.
- [x] `service-tests.sh`에 1~32 jobs 검증과 xdist 준비 경계를 추가한다.
- [x] core-api에 worker별 격리 DB와 pytest worker 환경 plugin을 연결한다.
- [x] 선택자·strict marker·junit 판정부는 변경하지 않는다.

## Task 3: 나머지 단독 게이트 대조

- [x] frontend-test의 기존 vitest worker 병렬 실행을 실측한다.
- [x] db-selftest의 migration/db 독립 절만 병렬화하고 두 출력·종료 상태를 합친다.
- [x] render-latency의 읽기 전용 원천 시험을 내부 병렬화하고 p95 판정이 유지되는지 확인한다.
- [x] preview-tile-slot-selftest는 fixture 격리 여부를 확인해 독립 케이스만 병렬화한다.

## Task 4: 검증·인계

- [x] 네 서비스 jobs=1/4 계수 동일, selftest green, 준비 실패 0.
- [ ] `all -j 4` 전후 선언·green·판정 red·준비 red 계수 동일 및 시간 기록.
- [ ] G10 완료 정의 전건이 아니면 상태를 partial로만 갱신한다.
