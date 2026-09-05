# 레인 보고 — 게이트 준비 대기 정밀화 (`gates/tools/_pg.sh`)

- 브랜치: `gate/pg-ready-wait` (기점 `origin/integration/bf-11-8` · `09d4af5`)
- 범위: `gates/tools/_pg.sh` · `rls-effect.sh` · `db-selftest.sh` · `rls-effect-selftest.sh` · `gates/README.md` 한 줄 · `gates/fixtures/pg-ready/` 신설
- 접촉하지 않은 것: staging 컨테이너 0 · 병합 0 · `work-items.yaml`·`PLAN-SoT.md`·`03-HANDOFF.md` 0줄

---

## §1 결함 — 무엇이 틀렸나

- 증상: `./gates/run.sh rls-effect-selftest` 단독 실행이 유휴 호스트에서 **3연속 red(준비)**, 매번 **다른 케이스**.
- 표식: `::gate-readiness-failure::gate=rls-effect|waited_for=postgres 접속 준비(pg_isready …)|limit=60초|elapsed=1초|… 마지막 로그: PostgreSQL init process complete; ready for start up.`
- 모순: 상한 60초인데 **실경과 1초**. 즉 「기다리다 못 떴다」가 아니라 **기다리지 않고 떨어졌다**.
- 원인: `postgres:16-alpine` 엔트리포인트는 initdb 동안 **임시 서버**를 띄운다. 그것도 `database system is ready to accept connections` 를 찍고 `pg_isready` 에 응답한다. 옛 대기 루프는 거기서 `break` 했고, 뒤이은 **확인용 `pg_isready`** 가 임시 서버 종료와 실서버 기동 사이 공백에 떨어졌다.
- 부하 의존: 셀프테스트는 컨테이너를 **동시 4개** 띄운다 → 공백이 벌어진다. 전체 스위트에서 `rls-effect` 본체가 green 이었던 것과 모순되지 않는다.

## §2 프로브 증거

`gates/fixtures/pg-ready/temp-server-probe.sh` (신설 · 판정하지 않고 관측만 한다) 실측:

```
② 옛 대기 정지 지점 로그: 2026-09-05T10:03:59.292879573Z … [1] LOG:  database system is ready to accept connections
② 정지 직후 확인 pg_isready: 성공   ← '실패' 가 곧 red(준비) 오탐이다
③ pg_wait_ready: 성공 · 직후 확인 pg_isready: 성공
① 로그 시각선:
   2026-09-05T10:03:59.077755896Z … [61] LOG:  database system is ready to accept connections   ← 임시 서버
   2026-09-05T10:03:59.176412456Z … [62] LOG:  shutting down                                     ← 임시 서버 종료
   2026-09-05T10:03:59.274000282Z PostgreSQL init process complete; ready for start up.
   2026-09-05T10:03:59.292879573Z … [1]  LOG:  database system is ready to accept connections    ← 실서버
```

- 읽는 법: `.077`(임시 ready) ~ `.292`(실서버 ready) 사이 **≈215ms** 가 오탐 창이다. 이 유휴 실행은 폴링이 창을 지나쳐 「성공」이 찍혔고, 그것이 결함의 **간헐성**이다 — 창이 없어진 것이 아니라 이번엔 안 맞았을 뿐이다.
- 옛 표식이 남긴 「마지막 로그 = init process complete」는 창의 **정확히 그 자리**를 가리킨다.

## §3 고친 것 — diff 요약

| 파일 | 변경 |
|---|---|
| `gates/tools/_pg.sh` | `PG_INIT_DONE_MARK`·`PG_ACCEPT_MARK` 선언. `pg_real_server_started`(로그에 초기화 완료 표식이 있는가 / 초기화 흔적 없이 접속 준비만 있으면 = 이미 초기화된 PGDATA 로 보고 준비) · `pg_wait_ready <컨테이너> <상한>`(표식 ＋ 그 뒤 `pg_isready` 성공을 **함께** 볼 때만 0) · `pg_ready_detail`(상한 초과 사유 — 임시 서버 단계에서 멈춤 / 표식은 있으나 무응답을 갈라 적는다) 신설. `pg_start` 의 대기 루프를 `pg_wait_ready` 로 교체 |
| `gates/tools/rls-effect.sh` | 자기 벌 대기 루프(＋확인 `pg_isready`) 삭제 → `pg_wait_ready` ＋ `pg_ready_detail` 사용. `ready_red` 표식 모양 그대로 |
| `gates/tools/db-selftest.sh` | `_pg.sh` 를 source. 적용 DB 컨테이너(`APPC`) 대기도 같은 `pg_wait_ready` 로 |
| `gates/tools/rls-effect-selftest.sh` | fail-closed 케이스 **1건 신설**(18 → 19). 기존 픽스처 감소 0 |
| `gates/README.md` | 「준비됐다」 정본이 `pg_wait_ready` 하나임을 밝히는 한 줄 |
| `gates/fixtures/pg-ready/temp-server-probe.sh` | 신설 프로브 |

- **정밀화이지 범위 축소가 아니다**: 예산 60초 그대로 · 게이트 재시도 없음 · 병렬도 그대로 · 케이스·판정 기준 감소 0 · `COLAB_PG_FORCE_UNAVAILABLE` 주입 경로 그대로 · 표식 필드(`waited_for`/`limit`/`elapsed`/`detail`) 그대로. 상한을 넘기면 여전히 **red(준비)**.

## §4 red 픽스처 — 정밀화가 관대해지지 않았음의 증명

- 방식: `postgres` 이미지의 **엔트리포인트만 `sleep` 으로 바꾼 파생 이미지**를 셀프테스트가 즉석 build(base 는 이미 로컬 · 레지스트리 접촉 0). 서버가 영영 안 뜨니 초기화 완료 표식도 `pg_isready` 응답도 없다.
- 케이스: `expect ready "rls-effect: 실서버가 끝내 안 뜨면 상한에서 red(준비) …" env COLAB_PG_IMAGE=… COLAB_PG_READY_TIMEOUT=5 "$GATE"`
- 실측 출력(축자):
  ```
  ::gate-readiness-failure::gate=rls-effect|waited_for=postgres 접속 준비(실서버 · pg_isready · 컨테이너 b3_rlseffect_2344593_28960)|limit=5초|elapsed=6초|detail=컨테이너 상태=running · 초기화 완료 표식 없음(임시 서버 단계에서 멈춤) · 호스트 load average: 2.24, 1.73, 2.37 · 마지막 로그:
  [selftest] rls-effect: 실서버가 끝내 안 뜨면 상한에서 red(준비) (임시 서버 오인 방지의 fail-closed) → red(준비) OK (이 케이스가 재는 것이 준비 실패다)
  ```
- 이미지 build 가 실패하면 그 회차는 `FAILURES` 로 red — **증명하지 못한 것을 통과로 세지 않는다**.

## §5 실행 결과 (축자)

### 고치기 전 · 1회

```
[selftest] 케이스 18 건 (동시 4)
rls-effect-selftest green — 보호 장치를 하나씩 떼면 실제로 red 가 난다. 틀린 롤도 red 다.
EXIT=0
```

- ⚠ 이번 baseline 은 **green 이 나왔다**. 결함은 타이밍 의존이라 1회 실행으로 재현되지 않는다 — green 을 「결함 없음」의 근거로 쓰지 않는다. 재현 근거는 오케스트레이터의 3연속 red(준비)와 §2 의 시각선이다.

### 고친 뒤 · `rls-effect-selftest` 3연속

```
[1회] [selftest] 케이스 19 건 (동시 4)
      rls-effect-selftest green — 보호 장치를 하나씩 떼면 실제로 red 가 난다. 틀린 롤도 red 다.
      EXIT=0
[2회] [selftest] 케이스 19 건 (동시 4)
      rls-effect-selftest green — 보호 장치를 하나씩 떼면 실제로 red 가 난다. 틀린 롤도 red 다.
      EXIT=0
[3회] [selftest] 케이스 19 건 (동시 4)
      rls-effect-selftest green — 보호 장치를 하나씩 떼면 실제로 red 가 난다. 틀린 롤도 red 다.
      EXIT=0
```

### `db-selftest` · 1회

```
db-selftest green — DB 게이트 3종 모두 틀린 것을 틀렸다고 말한다 (fail-closed 증명).
EXIT=0
```

### `rls-effect` · 1회

```
rls-effect green — 본체 음성 · 메타 양성(P-13) · cross-tenant 셋 다 엔진이 막는다. 판정 롤은 우회 불가.
EXIT=0
```

### `selftest` (집합) · 1회

```
── selftest 요약 ───────────────────────────────────────────
  선언 20 · 실행 18 · 면제 2
  green 16 / red(판정) 0 / red(준비) 2
::gate-readiness-failure::gate=selftest|waited_for=셀프테스트 2건의 실행 환경|limit=케이스별 상한|elapsed=-|detail=frontend-typecheck-selftest frontend-test-selftest
::error::selftest red(준비) — 아래 증명을 **돌리지 못했다.** 통과로 세지 않는다: frontend-typecheck-selftest frontend-test-selftest
EXIT=78
```

- 읽는 법: **red(판정) 0**. red(준비) 2 건은 이 워크트리에 `frontend/node_modules` 가 없어서다(`ls frontend/node_modules` → 없음). 이 레인의 변경과 접점이 없다(둘 다 DB 를 쓰지 않는다). ⛔ 이 두 건을 「green 이다」로 접지 않는다 — **판정되지 않았다**가 사실이다.

## §6 §9 초안 (번호 미부여)

> | 〈N〉 | **게이트 준비 대기가 initdb 의 임시 서버를 「준비됐다」로 세어 60초 예산 중 1초 만에 red(준비) 오탐을 냈다** | **집행 (2026-09-05 · 발견 = `rls-effect-selftest` 단독 3연속 red(준비) · 근거 `dev-package/reports/gate-pg-ready/lane-report.md` · 게이트 도구 5파일 · 계약 0 · 마이그레이션 0 · staging 접촉 0 · 배포 0).** **㉮ 실물** — `postgres:16-alpine` 엔트리포인트는 initdb 동안 **임시 서버**를 띄웠다 내린 뒤 실서버를 띄운다. 실측 시각선 = 임시 ready `.077` → shutting down `.176` → `PostgreSQL init process complete` `.274` → 실서버 ready `.292` (`gates/fixtures/pg-ready/temp-server-probe.sh`). 종전 대기 루프는 **첫 `pg_isready` 성공**(= 임시 서버)에서 break 했고, 뒤이은 확인 `pg_isready` 가 그 **≈215ms 공백**에 떨어졌다. **㉯ 그래서 무엇이 틀렸나 — 상한이 아니라 뜻이다.** 표식은 `limit=60초|elapsed=1초` 를 함께 찍었다 — 기다리다 못 뜬 것이 아니라 **기다리지 않고 떨어진 것**이다. 셀프테스트는 컨테이너를 동시 4개 띄우므로 공백이 벌어져 단독 실행이 매번 다른 케이스에서 red(준비) 를 냈다. ⛔ 이것은 **검사기의 결함이지 검사 대상의 결함이 아니다** — 같은 회차에 `rls-effect` 본체는 green 이었다. **㉰ 집행 — 준비의 뜻을 실서버로 좁혔다.** `_pg.sh` 에 `pg_wait_ready` 를 세워 **초기화 완료 표식 ＋ 그 뒤 `pg_isready` 성공**을 함께 볼 때만 준비로 센다(이미 초기화된 PGDATA 는 initdb 단계가 없으므로 접속 준비 로그만으로 준비). 세 곳에 흩어져 있던 대기 루프(`pg_start` · `rls-effect.sh` · `db-selftest.sh`)를 그 하나로 모았다 — 두 벌로 두면 한쪽이 언젠가 다른 말을 한다. **㉱ ⚠ 대기 정밀화이지 범위 축소가 아니다** — 예산 60초 그대로 · 게이트 재시도 없음 · 병렬도 축소 없음 · 판정 기준·케이스 감소 0 · `COLAB_PG_FORCE_UNAVAILABLE` 주입 경로 그대로 · 표식 필드 모양 그대로. **상한을 넘기면 여전히 red(준비) 다.** **㉲ fail-closed 증명 1건 신설**(`rls-effect-selftest` 18 → 19건) — 엔트리포인트를 `sleep` 으로 바꾼 파생 이미지로 실서버를 영영 안 띄우고 상한 5초를 선언 → `limit=5초|elapsed=6초|detail=… 초기화 완료 표식 없음(임시 서버 단계에서 멈춤)` 로 red(준비). 기존 픽스처 감소 0. **㉳ 실측** — `rls-effect-selftest` 3연속 green(19건) · `db-selftest` green · `rls-effect` green · 집합 `selftest` = green 16 / **red(판정) 0** / red(준비) 2. red(준비) 2 = `frontend-typecheck-selftest`·`frontend-test-selftest`(이 체크아웃에 `frontend/node_modules` 부재 · 이 회차의 변경과 접점 없음) — ⛔ green 으로 접지 않는다. **㉴ ⚠ `[미확인]`** — 고치기 전 baseline 1회는 **green 이 나왔다**(타이밍 의존). 고친 뒤 3연속 green 이 오탐 **소멸**을 증명하는지는 시행 3회로 확정되지 않는다 — 확정 근거는 실행 횟수가 아니라 **§2 의 시각선과 ㉲ 의 fail-closed 케이스**다. |

## §7 `[미확인]`

- ⚠ 고치기 전 baseline 은 **1회 green** — 결함의 재현을 이 레인이 직접 잡지는 못했다. 근거는 오케스트레이터의 3연속 관측 ＋ §2 시각선.
- ⚠ 고친 뒤 3연속 green 이 오탐 **소멸**의 통계적 증명은 아니다. 남은 위험이 0 인지는 `[미확인]`.
- ⚠ `pg_wait_ready` 의 폴링 간격은 1초 그대로다 — 표식 확인이 `docker logs` 전문을 매 초 읽으므로 **로그가 매우 커지는 컨테이너**에서의 비용은 재지 않았다(이 게이트들의 컨테이너는 수십 줄 규모).
- ⚠ 「이미 초기화된 PGDATA」 갈래(초기화 흔적 없이 접속 준비 로그만)는 **이 레포에서 발생하지 않는다**(PGDATA 가 tmpfs). 실행으로 밟아 보지 않았다 — 코드로만 처리했다.
- ⚠ `service-tests-core-api` · `schema-diff` · `rls-coverage` · `autometa-loss-selftest` 등 `pg_start` 를 쓰는 다른 게이트는 이 회차에 **돌리지 않았다**. 대기 경로가 하나로 모였으므로 회귀 위험은 같은 자리지만, 실측은 하지 않았다.
- ⚠ `frontend-typecheck-selftest` · `frontend-test-selftest` 는 **판정되지 않았다**(node_modules 부재). 이 레인이 그것을 green 으로 세지 않았다.
- ⚠ fail-closed 픽스처는 `docker build` 를 쓴다 — build 를 못 하는 CI 러너에서는 그 케이스가 `FAILURES` 로 red 가 된다(설계 그대로). CI 에서 실제로 도는지는 `[미확인]`.
