# Intent: 되돌리기를 superuser 로 세워 #47 의 잔여 누출을 하네스가 줍게 한다
메타 — 발의자: agent(fable 어드바이저 대조검증) · 방향 결정: Ted · 작성 2026-09-18 · 승인 2026-09-18

## 문제
- 되돌리기 훅 `services/core-api/tests/conftest.py` 의 `_rollback_p2_rows` 가 **앱 롤**로 스냅숏을 뜨고 삭제했다. 경계는 `_cleanup_scope` 가 심는 A 연구실 한 곳이다.
- RLS 가 A 경계에서 다른 연구실 행을 가리므로 `snapshot_test_rows` 의 UNION 에도, `purge_test_rows` 의 `DELETE ... <> ALL(:keys)` 에도 **LAB_B·LAB_C 행이 아예 안 걸린다.** 「안 보인다 = 안 지워진다」가 항등이다.
- 그래서 시험이 커밋한 다른 연구실 행이 회수되지 않고 산다. 확정 생산자는 `services/core-api/tests/test_admin_actor_visibility.py:38`(`@pytest.mark.parametrize("labless", [False, True])` 로 2회) 와 `:62`(1회) — 한 회차에 LAB_B 데이터셋 3벌이고, 파일 어디에도 그것을 지우는 자리가 없다.
- 그 행은 같은 xdist worker 의 다음 시험으로 샌다. 피해는 B 연구실을 **절대 집합**으로 재는 자리다 — `services/core-api/tests/test_pool_no_leak.py:48`·`:99`·`:106` 의 `== {DS_B1}`. `COLAB_SERVICE_TEST_JOBS=12` 에서 배분이 오염원과 피해자를 같은 worker 에 같은 순서로 떨어뜨릴 때만 터져 **간헐 red** 로 보였다.

## 원한 결과 (proposed outcome)
- 시험이 다른 연구실에 커밋한 행을 **하네스가 회수한다.** 시험 파일마다 `try/finally` 회수를 손으로 적지 않는다.
- `test_pool_no_leak.py` 의 절대 집합 오라클이 worker 배분과 무관하게 같은 판정을 낸다.
- `COLAB_SERVICE_TEST_JOBS=12` 로 `gates/run.sh service-tests-core-api` 3회 연속 같은 결과.
- 회수한 행 중 A 연구실 밖의 것은 건수로 드러난다 — `user_properties` 의 `purged_outside_lab_a` 와 출력 한 줄. red 로 만들지 않는다(다른 연구실 쓰기는 관리자 시험의 정상 동작이다).

## 영향 범위
- 시험 하네스: `services/core-api/tests/conftest.py` — `purge_session_factory` 추가, `_rollback_p2_rows`·`purge_test_rows`·`_cleanup_scope`·`snapshot_test_rows` 수정.
- 시험 파일: `services/core-api/tests/test_cleanup_purge.py` — 오라클 2건 추가.
- 서비스 · 스키마 · 계약: 없음. 제품 코드·마이그레이션·계약을 건드리지 않는다.
- 게이트 스크립트: 없음. `-j` 기본값도 그대로다.
- 계약 파괴 여부: 아니오.

## 제약
- `admin_db_url` 의 롤 `colab_account_admin` 은 BYPASSRLS 지만 public 표에 DELETE 권한이 없다(`services/core-api/ops/account-admin-role.sql:49-56`). 그래서 같은 접속처의 **사용자만** `postgres` 로 갈아끼운다. 선례는 `services/core-api/tests/test_admin_role_scope.py:17`·`:29` 와 `services/core-api/tests/test_operator_designation.py` 의 `_remove_created_accounts` 다.
- 계정 3표(`d1_account`·`d2_member_role`·`d2_permission_switch`)는 **A 연구실 안에서만** 지운다. `d8_activity.actor_account_id` 가 `d1_account(id)` 를 ON DELETE 없이 참조하고(`db/platform/versions/0001_p0_platform.py:387`) `d8_activity` 는 append-only 트리거가 DELETE 를 거부한다(`:394-396`) — 한 번이라도 행위한 계정은 영영 못 지운다. `d8_activity.target_id` 에는 FK 가 없으므로 데이터셋 계열은 어느 연구실이든 지울 수 있다.
- `_RESTORE` 문장이 `current_lab_id()`(GUC `app.current_lab`)를 쓰므로 superuser 세션에도 `_cleanup_scope` 를 그대로 건다. `apply_scope`(`services/core-api/src/colab_core/kernel/scope.py`)는 롤을 보지 않아 superuser 접속에서도 선다.
- worker 를 넘지 않는다. `gates/tools/xdist_core_db.py:27`·`:40` 이 앱 URL 과 admin URL 을 **둘 다** worker 별로 다시 써 넣으므로, superuser 접속처도 그 worker 의 일회용 DB 하나다.
- 새 엔진은 커넥션을 **상주시키지 않는다**(`NullPool`). 게이트의 일회용 postgres 는 `max_connections` 기본 100 이고(`gates/tools/_pg.sh:177-180`) 회차 중 실측 최고치가 93 이다. 사유는 설계트리 Q8.
- 흔들림을 눈금으로 덮지 않는다. `gates/run.sh:761` 축자 — 「상한 연장·재시도·병렬도 축소·건너뛰기로 green 을 만들지 않는다.」

## 설계트리 (grill-me 결과)
- Q1 원인이 무엇인가 → A A 경계에서 보이지 않는 행은 스냅숏에도 DELETE 에도 안 걸린다. 생산자는 `test_admin_actor_visibility.py:38`(2회)·`:62`(1회), 피해자는 `test_pool_no_leak.py:48`·`:99`·`:106`.
- Q2 앞선 초안(가드 fixture)을 받는가 → A **받지 않는다.** 초안은 미병합 브랜치 `claude/followup-intents` 의 `dev-package/intent/2026-09-17-tests-writing-outside-rollback-scope.md` 다. 기각 사유 셋:
  - Q2a 가드는 **탐지만 하고 지우지 못한다** → 오염원 시험이 red 로 이름을 남겨도 행은 그대로 남는다. 피해자(`test_pool_no_leak.py`)는 여전히 깨진다. 두 번 red 가 될 뿐이다.
  - Q2b 백오피스 시험 30여 건이 **일부러** LAB_C 에 계정을 남긴다(`services/core-api/tests/test_admin_role_scope.py:13-14` 의 `isolate_created_accounts` 가 teardown 에서 계정을 LAB_C 로 되돌린다). 가드를 전 시험에 걸면 그 전부가 대량 red 가 된다.
  - Q2c 가드는 운영자 읽기 스코프가 `_CLEANUP` 24표 전부에서 타 연구실 행을 보여 준다는 **미확인 전제** 위에 선다. superuser 는 그 전제가 필요 없다.
- Q3 「superuser 로 지우면 경계 증명이 무효가 된다」는 반론은 → A 성립하지 않는다. 경계를 증명하는 것은 시험 **본문의 assert** 이지 뒷정리 경로가 아니다. `services/core-api/tests/test_admin_role_scope.py:29-36` 의 `restore_foreign_lab` 이 이미 `postgres` 로 LAB_B 행을 되돌리고 있고, 그 파일의 경계 증명은 그대로 서 있다. 되돌리기 세션은 시험 본문에 노출되지 않는 별도 fixture 다.
- Q4 계정 계열도 전역으로 지우면 → A 안 된다. Q2b 의 LAB_C 계정 다수가 `d8_activity` 에 행위자로 남아 있고, 그 DELETE 가 FK 로 막히면 되돌리기 **트랜잭션 전체**가 무효가 된다 — 삭제도 `_RESTORE` 도 함께 사라진다(2026-09-13 에 `d4_lineage_edge` 로 겪은 형태). 그래서 `AND lab_id = current_lab_id()` 를 붙여 종전과 같은 A-한정으로 둔다. 소속 없는 계정(`lab_id IS NULL`)도 같은 이유로 남는다.
- Q5 시드 B·C 행이 삭제되지 않는가 → A superuser 스냅숏에는 시드 B·C 행이 **들어온다.** 「시험 전에 있던 키는 남는다」 규율이 그대로 적용되어 삭제 대상에서 빠진다. 오라클은 `services/core-api/tests/test_cleanup_purge.py` 의 `test_purge_removes_a_lab_b_row_a_test_made_and_keeps_the_lab_b_seed`(전 2 · 후 1).
- Q6 회수 사실을 어떻게 남기나 → A `DELETE ... RETURNING lab_id` 로 지우면서 센다. 미리 세고 지우면 사이에 낀 트랜잭션 때문에 셈과 삭제가 갈라진다. A 밖 건수가 있으면 `request.node.user_properties` 에 `("purged_outside_lab_a", "<표>=<n>,…")` 를 얹고 한 줄 출력한다.
- Q7 `test_admin_actor_visibility.py` 를 함께 고치는가 → A 고치지 않는다. 그 누출을 하네스가 줍는 것이 이 결정의 요점이고, 고치면 하네스가 실제로 줍는지 증명할 대상이 사라진다.
- Q8 새 엔진의 커넥션 풀은 → A **풀을 두지 않는다(`NullPool`).** 실측에서 드러난 자리다. `make_engine`(`services/core-api/src/colab_core/kernel/db.py:19-20`)은 20＋20 = 40 이고, 게이트의 일회용 postgres 는 `max_connections` **기본 100** 인 컨테이너 하나를 worker 12 개가 나눠 쓴다(`gates/tools/_pg.sh:177-180`). 회차 중 `pg_stat_activity` 최고치를 2초 간격으로 재니 **93/100** 이었다 — worker 마다 커넥션을 **하나라도 상주**시키면 천장에 닿는다.
  - Q8a 실제로 닿았나 → A 닿았다. `make_engine`(40) 로 3회 — failed 10 · 0 · 2. `pool_size=1, max_overflow=1` 로 3회 — failed 1 · 7 · 7. 실패 시험이 회차마다 바뀌고 사유가 `psycopg.OperationalError: connection failed` 와 그 여파인 `500 Internal Server Error`·`JSONDecodeError` 였다. `NullPool` 로 바꾼 뒤 3회 연속 failed 0.
  - Q8b 그래도 되는가 → A 된다. 되돌리기는 시험 하나당 짧은 트랜잭션 둘을 **차례로** 여는 자리다. 회차 소요는 61~65초(기준선)에서 69~74초로 늘었고, 그 증가분이 커넥션 재수립 비용이다.

## 미해결 질문
- 전수 회차의 나머지 red 9건(`test_cross_tenant` 3 · `test_dashboard` 1 · `test_grid_convenience` 1 · `test_live_endpoints` 2 · `test_operator_designation` 1 · `test_search_execution` 1)이 같은 기전인지. **이 호스트에서는 기준선 2회가 모두 green 이라 그 9건 자체가 재현되지 않았다.** 다른 호스트·다른 부하의 관측이거나 이미 해소된 것이다. 이 회차 범위 밖이며, 재현 로그 없이 원인을 지어내지 않는다.
- 되돌리기가 A 연구실 밖에서 회수한 건수(`purged_outside_lab_a`)의 분포를 아직 모은 적이 없다. 다음 회차의 `-rA`·junit 속성에서 읽을 수 있다.
- 이슈가 보고한 수집계수 불일치(1221 vs 1222)는 재현되지 않았다. 가설 하나만 적어 둔다 — 게이트가 직렬 `--collect-only` 계수와 junit 계수를 대조하므로(`gates/tools/service-tests.sh`) 둘이 다른 회차의 값을 읽었을 가능성. 로그 없이 확정하지 않는다.

## 범위 밖 (명시 제외)
- 게이트 스크립트(`gates/tools/service-tests.sh`·`gates/run.sh`) 변경, `COLAB_SERVICE_TEST_JOBS` 조정, 재시도·플레이크 재실행 도입.
- 가드 fixture(미병합 초안). Q2 에서 기각했다.
- `test_admin_actor_visibility.py` 의 자기 회수 추가.
- 나머지 red 9건. 후속 레인.
- 수집계수 불일치 기전 수정. 미재현.
- 제품 코드·마이그레이션·계약 변경, 커밋·push·PR·이슈 댓글.

## 확인
- Ted 확인 문장(원문 그대로): "좋아 그렇게 하자."
- 재개봉 금지: 아니오.

## 실측 (2026-09-18 · 워크트리 `issue-47-superuser-purge` · 기반 `origin/develop` cb30d344)
- 게이트 `COLAB_SERVICE_TEST_JOBS=12 ./gates/run.sh service-tests-core-api` 3회 — **3회 모두 green**.
  - 회차 1 — `수집 1387 · 실행 1387 · skipped 0 · deselected 6 · failed 0 · errors 0 · 소요 73.7초` (게이트 전체 114초)
  - 회차 2 — `수집 1387 · 실행 1387 · skipped 0 · deselected 6 · failed 0 · errors 0 · 소요 70.3초` (게이트 전체 116초)
  - 회차 3 — `수집 1387 · 실행 1387 · skipped 0 · deselected 6 · failed 0 · errors 0 · 소요 69.2초` (게이트 전체 117초)
- 대조 기준선(이 변경 전 트리) 2회 — `수집 1385 · 실행 1385 · failed 0 · errors 0 · 소요 63.6초 / 64.7초`. **이 호스트에서는 기준선도 green 이었다** — 이슈가 기록한 red 11건은 이 회차에서 재현되지 않았다. 수집 1385 → 1387 의 차이는 이번에 더한 오라클 2건이다.
- 단독 회차 `tests/test_cleanup_purge.py` ＋ `tests/test_pool_no_leak.py`(일회용 DB 1개 · 직렬) — `10 passed in 5.60s`.

## 참조
- 이슈: https://github.com/CognileapAI/colab-v2/issues/47
- 기각한 초안: `dev-package/intent/2026-09-17-tests-writing-outside-rollback-scope.md` (미병합 브랜치 `claude/followup-intents`)
- 선행 intent: `dev-package/intent/2026-09-17-issue-47-service-tests-db-isolation.md`
- 하네스: `services/core-api/tests/conftest.py` — `_CLEANUP`·`_cleanup_scope`·`snapshot_test_rows`·`purge_test_rows`·`_ACCOUNT_TABLES`·`purge_session_factory`·`_rollback_p2_rows`
- 오라클: `services/core-api/tests/test_cleanup_purge.py`
- 누출 생산자: `services/core-api/tests/test_admin_actor_visibility.py:12-21`·`:24`·`:38`·`:62`
- 피해 시험: `services/core-api/tests/test_pool_no_leak.py:48`·`:99`·`:106`
- superuser 선례: `services/core-api/tests/test_admin_role_scope.py:17`·`:29-36`
- 권한 근거: `services/core-api/ops/account-admin-role.sql:49-56`
- FK·트리거 근거: `db/platform/versions/0001_p0_platform.py:387`·`:394-396`
- worker 별 DB: `gates/tools/xdist_core_db.py:27`·`:40`
- 게이트 규율: `gates/run.sh:761`
- 커넥션 천장: `gates/tools/_pg.sh:177-180`, `services/core-api/src/colab_core/kernel/db.py:19-20`
