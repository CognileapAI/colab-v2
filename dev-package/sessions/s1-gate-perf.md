# G10 게이트 내부 병렬화 — 로컬 부분 검증

날짜: 2026-09-11. 같은 dirty tree의 로컬 실행이며 판정 범위, 선택자, 게이트 사이 `serial` 선언은 줄이지 않았다.

## 서비스 시험

| 서비스 | jobs=1 | jobs=4 | 시간 |
|---|---:|---:|---:|
| core-api | 1040 passed / 6 deselected | 1040 / 6 | 157.44 → 49.74초 |
| pipeline-worker | 268 / 48 | 268 / 48 | 7.60 → 6.74초 |
| ai-service | 137 / 26 | 137 / 26 | 2.23 → 4.27초 |
| viz-render | 387 / 42 | 387 / 42 | 27.99 → 14.03초 |

core-api는 xdist worker별 일회용 DB를 별도로 만들고 URL/비밀번호를 출력하지 않는다. 실행 전에 직렬 collect-only로 선택 집합을 고정해 xdist 출력에서 사라지는 deselected 수를 보존한다. xdist 또는 worker DB 준비 실패는 78, jobs 범위 오류는 1이다. `service-tests-selftest`의 수집0·실행0·실패·venv·xdist 부재 픽스처가 기대 상태를 유지했다.

## 나머지 단독 게이트

- frontend-test: 기존 Vitest 내부 worker가 실제로 동작했고 88 files / 1186 tests / failed 0, 626.92초. 별도 중첩 worker는 추가하지 않았다.
- render-latency: 동일 25표본/5포맷. jobs=1은 39.74초, p95 2.490초; jobs=4는 23.98초, p95 3.193초. 양쪽 모두 p95 10초·상한60초 기준을 통과했다.
- db-selftest: migration 절과 db 절만 격리 출력으로 병렬화했고 독립 2절 green.
- preview-tile-slot-selftest: read-only 입력 경계 5케이스만 병렬화했고 전체 20 기대 판정 green.
- generated-up-to-date: 등기 10건 재생성 일치, 밖 자칭 생성물 0.

## 판정

구성요소 병렬화와 fail-closed 의미는 green이다. `G10`은 아직 `partial`이다. 모든 Stage 1·2 코드가 고정된 동일 트리에서 `all -j4`의 전후 선언/green/판정 red/준비 red 계수와 총 시간을 각각 한 번 측정해야 완료 정의 ⑷이 선다.
