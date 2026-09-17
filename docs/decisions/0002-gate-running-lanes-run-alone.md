# ADR-0002: 게이트를 도는 레인은 한 번에 하나만 실행한다

- 상태: accepted
- 날짜: 2026-09-17
- 대체함: 없음
- 대체됨: 없음

## 배경
이슈 17건을 레인 3개(제품 결함 · 게이트 신뢰성 · 저비용 정비)로 나눠 격리 워크트리에서 동시에 돌리려 했다.
advisor 계획 검토(2026-09-17)가 저장소 실물에서 세 가지를 확인했다.
- `gates/tools/_pg.sh`의 일회용 postgres 슬롯 디렉터리가 `${TMPDIR:-/tmp}/colab-v2-gatepg-slots`로 **호스트 전역**이다. 레포 루트로 키잉되지 않아 워크트리가 갈려도 슬롯 4개(`COLAB_PG_MAX_CONCURRENT`)를 공유한다. 못 얻으면 exit 78 red(준비).
- `gates/run.sh`에 **프로세스 간 뮤텍스가 없다.** `gates/config/parallelism.toml`의 `serial` 선언은 한 `run.sh` 호출 안에서만 지켜진다. 레인 A의 `frontend-test`와 레인 B의 `service-tests-core-api`가 동시에 도는 것을 막는 장치가 없다.
- 워크트리 생성 훅(`scripts/harness/hooks/worktree-setup.sh` · `.claude/hooks/`는 wrapper)이 레인마다 `frontend/node_modules`(`npm ci` · 188행, 실물이 있을 때만 재사용)와 `services/*/.venv`를 새로 짓는다. venv는 절대경로가 박혀 있어 **복사가 아니라 재생성**이다(훅 주석 12-13행). 호스트 12코어 · 가용 메모리 8GB 수준에서 3레인 동시 스폰 자체가 부하다.
이슈 #47(service-tests-core-api 워커 12에서 비결정 실패)·#55(frontend-test 부하 중 간헐 red)가 보고하는 실패 조건이 바로 이 부하다.

## 결정
게이트를 실행하는 레인은 한 번에 하나만 돌린다. 다른 레인은 그 구간에 게이트를 돌리지 않는다.
돌리더라도 좁은 게이트만 쓰고 전수(`gates/run.sh all`)는 쓰지 않는다.
진짜 fan-out이 필요하면 게이트를 돌리지 않는 읽기 전용 작업(조사·문안)끼리만 병렬로 묶는다.
승인 근거: 2026-09-17 대화, Ted "권고대로 ㄱㄱ" (advisor 계획 검토 권고 ①에 대한 승인).

## 검토한 대안
- 레인 3개 동시 실행 유지 — 배제: #47·#55가 보고한 부하 조건을 스스로 만들어 놓고 그 아래에서 같은 문제를 고치게 된다. 측정 오염 비용이 병렬화 이득보다 크다.
- `COLAB_PG_SLOT_DIR`를 워크트리별로 다르게 주기 — 슬롯 경합은 풀리지만 부하와 `run.sh` 뮤텍스 부재는 그대로다. 배제(부분 해법).
- `gates/run.sh`에 호스트 전역 뮤텍스 추가 — 근본 수정이나 이슈 #56(병렬 안전성 미선언 게이트)의 범위다. 이 ADR은 그 수정 전까지의 운영 규칙이다.

## 결과와 감수한 비용
- 얻는 것: 게이트 판정이 다른 레인의 부하에 오염되지 않는다. #47·#55의 재현·수정 측정이 신뢰할 수 있다.
- 부담: 레인이 직렬이 되어 전체 소요가 늘어난다. 병렬은 게이트를 돌리지 않는 작업에만 쓴다.

## 재검토 조건
- `gates/run.sh`에 프로세스 간 뮤텍스가 들어가고 postgres 슬롯이 레포 루트로 키잉될 때(#56·#47 수정 뒤).
- 게이트가 원격 실행기로 옮겨져 호스트 부하와 분리될 때.

## 근거
- `gates/tools/_pg.sh` `PG_SLOT_DIR` · `COLAB_PG_MAX_CONCURRENT` (전역 슬롯 4개).
- `gates/run.sh` `all)` 분기 — `solo_gates`/`pool_gates` 로컬 잡 제어만 있고 호스트 전역 잠금 없음.
- `gates/config/parallelism.toml` `preview-tile-slot-selftest` 항목 — 2026-08-30 한 프로세스 `-j 2`에서 슬롯 고갈 실측.
- 이슈 #47 · #55 본문.
- 관련: [ADR-0001](0001-lane-worktree-base-ref-head.md).
