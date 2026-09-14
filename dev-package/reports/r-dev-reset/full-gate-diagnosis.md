# 전수 게이트 비-green 5건 진단 — R-DEV-RESET

- 대상 트리 = `69d86268`(tree `45cf2a40`) · 전수 로그 = 작업 임시 경로(레포 밖 · 미커밋)
- 전수 결과 축자 = `── 계 : green 59 / red(판정) 3 / red(준비) 2`
- 계수 기준 = `gates/run.sh all -j 4` 한 번의 실행 · 내부 worker 12(로그 축자 「# service-tests-core-api 내부 worker 12 · xdist loadfile」)
- ⚠ 재현 시점의 호스트는 유휴가 아니다 — 타 세션 컨테이너 `colab_lane_probe_pg` · `colab_v2_gatepg_*` 가 계속 기동 중(무접촉 유지). 이 부하가 C 의 판독에 섞인다.

## A. `service-tests-core-api` — 환경(실행 구성) red

- 트리 동일성: `69d86268:services/core-api` = **`4d540e91fcab3660c9ce39dffca82f62aba5d581`** · `559b7ef8:services/core-api` = **`4d540e91fcab3660c9ce39dffca82f62aba5d581`** → **완전 동일**. R1a 레인에서 green ×3(1221 passed) 이던 그 트리다. 코드 회귀가 아니다.
- 단독 재실행 1회(기본 worker 4) 요약줄 축자:
  > `service-tests-core-api — 선택자 «not e2e» · 수집 1221 · 실행 1221 · skipped 0 · deselected 6 · failed 0 · errors 0 · 소요 77.0초`
  > `service-tests-core-api green — 실행 1221건 전부 통과`
- worker 수 대조 1회(`COLAB_SERVICE_TEST_JOBS=12` · 전수와 같은 구성) 요약줄 축자:
  > `service-tests-core-api — 선택자 «not e2e» · 수집 1222 · 실행 1222 · skipped 0 · deselected 6 · failed 6 · errors 1 · 소요 53.8초`
  > `::error::service-tests-core-api red — collect-only 선택 1221건과 실행 리포트 수집 1222건이 다르다.`
- 실패 집합이 전수와 **다르다** — 전수 = `test_access_state_three.py` 4건 · worker 12 재현 = `test_dataset_facets.py` 4 · `test_live_endpoints.py` 1 · `test_scope_kernel.py` 1 ＋ errors 1. 동일 시험이 재현되지 않고 수집 건수까지 흔들린다 → **비결정 오염**이다.
- 기전(근거 `gates/tools/service-tests.sh:92-150`): 일회용 postgres 1대를 세우고(`_pg.sh`) **worker 수만큼** DB `colab_platform_gw<N>` 를 만들어 `--dist loadfile` 로 파일 단위 배분한다. DB 는 **worker 당 1개이고 시험 파일마다가 아니다** — 같은 worker 에 배정된 여러 파일이 한 DB 의 시드를 공유한다. worker 수가 바뀌면 배분이 바뀌고, 앞선 파일이 남긴 행이 다음 파일의 계수·상태 단언을 깬다. 전수의 축자 실패 문면(「이미 볼 수 있는 데이터예요」 CONFLICT · 「끊긴 사람 수가 1 이 아니다: [2]」)은 전부 **선행 행 잔존**형이다.
- 판정 = **환경(실행 구성)**. 후속 항목(고치지 않음) — ⑴ worker 당 DB 공유가 파일 간 시드 오염을 허용한다 ⑵ 전수의 내부 worker 12 는 `-j 4` 와 곱해져 호스트 한도를 넘긴다 ⑶ 수집 1221/1222 불일치는 그 자체로 오라클 불안정.

## B. `migration-drift` — main 선재(pre-existing) red(판정) ＋ 0018 은 환경

- ㈑ 실패 원인 = **오라클이 한 칸 뒤에 있다.** `db/platform/tests/` 의 마지막 오라클은 `0030-drift.sh` 이고 **`0031-drift.sh` 는 `origin/main` 에 없다**(`git ls-tree origin/main db/platform/tests/` 0건).
- `0030-drift.sh` 의 대조 방식(축자, `db/platform/tests/0030-drift.sh` ㈑ 절):
  > `apply decl_db "$CHAIN/schema.sql"` … `[0030-drift] ㈑ schema.sql 과 $db 가 갈렸다 ✗`

  — `MERGE_REV="0030_merge_audit_and_backoffice"` 까지만 올린 `order_a`·`order_b` 와 `schema.sql` 을 비교한다. `schema.sql` 은 head(`0031_search_evidence`)까지 재생성돼 있으므로 차이가 남는다.
- `0031_search_evidence.py` 유입 = `77b7c606`(2026-09-13 · 「최신 main의 운영자 기능과 검색 근거를 통합한다」 · `origin/main` 조상 확인). `db/platform/schema.sql` 최근 변경 = `77b7c606` · `dee33683`(둘 다 2026-09-13). **그 커밋들은 `db/platform/tests/` 에 0031 오라클을 추가하지 않았다.**
- 마지막 기록 green = **`71ee15757737`**(2026-09-12 · `PLAN-SoT §9 〈384〉` 축자 「green 64 / red(판정) 0 / red(준비) 0」 · 한 번의 실행). **0031 유입 이전 sha 다** → 이 red 는 `origin/main`(`aa8bee98`)에 **선재**한다. 사이 커밋 `7446eb7d..origin/main` 7건 중 `services/core-api` 를 건드린 것은 **0건**.
- 잡는 자리 = `migration-drift` **하나뿐**이다. 대조 근거 — ⑴ `schema-diff` 는 전수에서 green 이다(축자 「schema-diff green — 두 체인 각각 alembic upgrade head **뒤에** 선언 = 적용」). 즉 `schema.sql` 자체는 head 와 일치하고, 갈린 것은 오라클 쪽이다. ⑵ `deploy_doctor` ⑥⑦ 은 `schema.sql` 을 읽지 않는다 — `services/core-api/ops/deploy_doctor.py` 의 `repo_head()`·`check_head()` 는 `db/<chain>/versions/*.py` 의 revision 그래프와 DB `alembic_version` 만 대조한다(같은 파일 `schema.sql` grep 0건).
- `0018-drift.sh` 단독 재실행(호스트에 타 세션 부하 있는 상태) — **green**. 축자:
  > `0018-drift green — ㈎ 적용 green · ㈏ 0018 없으면 red · ㈐ downgrade 실물 동작 + 0017 복원 · ㈑ 소유자 롤 적용 뒤 두 칸 전 행 NULL(대조군 ㈑-b 백필 red).`

  전제 = `COLAB_ALEMBIC` 선언 필요(미선언 1회차는 축자 「::error::0018-drift red — alembic 을 찾지 못했다(alembic). COLAB_ALEMBIC 로 지정한다.」 · 전수에서는 `gates/run.sh` 가 대신 선언한다). 전수에서의 「postgres 가 60초 안에 뜨지 않았다」 는 **환경**(동시 컨테이너 경합)이다.
- 판정 = ㈑ = **판정-real(단, main 선재 · 이 트리가 만든 것이 아니다)** · 0018 = **환경**. 후속 항목 — `0031-drift.sh` 신설 또는 `0030-drift.sh` ㈑ 의 대조 대상을 head 로 올리는 별건 필요.

## C. `frontend-test` — 환경 red

- 단독 재실행 1회 결과 축자:
  > `Test Files  1 failed | 54 passed (55)` / `Tests  1 failed | 780 passed (781)` / `Errors  53 errors`
  > `::error::frontend-test red — vitest run 이 실패로 종료했다(코드 1).`
- 실패 1건 = `test/lineage-unknown-20260907.test.tsx > PRD-27 종전 문면은 코드에 남지 않는다 > 폐기된 종전 라벨이 `src`·`test` 전체에서 0건이다` · 사유 축자 「`Error: Test timed out in 5000ms.`」 — `src`·`test` 전체를 훑는 파일 스캔 시험이고 이 레포는 NTFS(drvfs) 위다.
- 미처리 오류 53건은 전부 축자 「`Error: [vitest-pool]: Failed to start forks worker for test files …`」 — fork worker 기동 실패. 전수의 1건(`password-rules.test.ts` · 「Timeout waiting for worker」)과 **같은 계열이고 대상 파일만 다르다** → 시험 내용이 아니라 worker 기동이 원인이다.
- 전수 1320 passed → 재실행 781 로 **줄었다**. 파일 자체가 기동하지 못해 판정되지 않은 것이지 통과가 줄어든 것이 아니다.
- 판정 = **환경**(호스트 경합 · 재현 시점 타 세션 게이트 컨테이너 2대 기동 중). 유휴 호스트 재측정은 **[미확인]**.

## D. `frontend-visual` · `harness-eval` — 선언-누락 red(준비)

- 두 게이트 다 **입력의 세 상태** 설계다(`gates/README.md:37`·`:41`). 축자 —
  > `**입력의 세 상태** — COLAB_VISUAL_URLS 로 선언하면 검사한다 · COLAB_VISUAL_EXEMPT=1 로 **명시 면제**하면 건수(페이지 0건)를 드러낸 채 넘어간다 · **아무 말 없으면 red(준비 · 입력미선언 · 78)** 다.`
  > `**입력의 세 상태** — COLAB_HARNESS_EVAL=1 이면 돈다(**실제 모델 호출** · 시간·달러 상한은 COLAB_EVAL_TIMEOUT·COLAB_EVAL_BUDGET 이고 **미선언은 red(준비)**) · COLAB_HARNESS_EVAL_EXEMPT=1 이면 **명시 면제**로 과제 건수를 드러낸 채 넘어간다 · **아무 말 없으면 red(준비 · 입력미선언 · 78)**. 값 대조는 **=1 하나뿐**이다`
- 선언 자리 = **`~/.colab-v2-test.env` 가 아니라 전수 실행 명령의 앞자리**다. `~/.colab-v2-test.env` 의 변수 이름 15개를 실측했고 `COLAB_VISUAL_*`·`COLAB_HARNESS_EVAL*` 는 **0건**이다(이름만 확인 · 값 미열람).
- 회차 관례 축자(`dev-package/sessions/R-D-ROUND-20260908.md:29`):
  > `실행 규약 = COLAB_HARNESS_EVAL_EXEMPT=1 COLAB_GATE_REPORT_DIR=dev-package/reports/R-D/all ./gates/run.sh all -j 1(면제·건수 노출 · 라운드 §3 ㉲)`

  같은 파일 `:27` 이 이번과 같은 사고를 기록한다 — 축자 「red(준비) = `frontend-visual`(`COLAB_VISUAL_URLS` 미선언 · 라운드 지시가 `COLAB_VISUAL_EXEMPT=1` 선언을 빠뜨림 · **선언 후 단독 green(명시 면제 · 페이지 0)**)」. 같은 파일 `:76` 이 다음 전수의 규약으로 두 변수 동시 선언을 적었다.
- 2026-09-05 의 「green 50/50」 은 **이 두 게이트 신설(2026-09-08 · R-D) 이전**이다 — 그 계수에는 두 게이트가 들어 있지 않다. 계수 기준이 다르므로 승자를 고르지 않는다.
- 이번 회차의 유효한 선언(권고) — 전수 명령 앞자리에 `COLAB_HARNESS_EVAL_EXEMPT=1 COLAB_VISUAL_EXEMPT=1` 를 붙여 **면제·건수 노출**로 돈다. 근거 ⑴ `harness-eval` 실행 모드 승격은 「과제 20건이 **3회 연속 2/2 green** 인 뒤의 **별건**」이다(`gates/README.md:41` 축자) ⑵ `frontend-visual` 은 앱이 떠 있어야 하고 이번 회차는 dev·staging 무접촉이다. ⚠ 면제 모드에서도 **과제 0건·페이지 0건 자체가 red(판정)** 이므로 건수 출력을 확인한다.
- 실행 모드로 갈 경우의 자리 = 구독(로그인 CLI)으로 돈다 — API 예산 질의는 하지 않는다(`CLAUDE.md §5-b`). 명령 축자 근거 `dev-package/reports/bugfix-260912/harness-eval-run.md:48`:
  > `cd "<worktree>" && COLAB_HARNESS_EVAL=1 COLAB_EVAL_TIMEOUT=93 COLAB_EVAL_BUDGET=2.01 bash gates/run.sh harness-eval`
- 판정 = **선언-누락** 2건. 이번 회차에 두 게이트를 실행하지 않았으므로 검사 대상은 **미판정**이다.

## 다섯 건 판정 요약

| 게이트 | 판정 | 근거 |
|---|---|---|
| `service-tests-core-api` | 환경 | 트리 동일 ＋ 단독 green 1221/1221 ＋ worker 12 에서 다른 실패 집합 재현 |
| `migration-drift` ㈑ | 판정-real (main 선재) | `0031-drift.sh` 부재 · 마지막 green 은 0031 이전 sha `71ee15757737` |
| `migration-drift` 0018 | 환경 | 단독 green · 전수 실패 사유는 postgres 60초 미기동 |
| `frontend-test` | 환경 | 재실행에서 worker 기동 실패 53건 · 실패 대상이 전수와 다르다 |
| `frontend-visual` · `harness-eval` | 선언-누락 | 세 상태 설계 · 전수 명령이 `_EXEMPT` 를 선언하지 않았다 |

## 이번에 재지 않은 것

- 유휴 호스트에서의 `frontend-test`·`service-tests-core-api` 재측정 — **[미확인]**(재현 내내 타 세션 컨테이너 기동 중).
- `migration-drift` 전체(오라클 전건) 단독 재실행 — 미수행. 확인한 것은 `0018-drift.sh` 1건과 `0030-drift.sh` 의 대조식 정적 판독이다.
- `frontend-visual`·`harness-eval` 실행 — 지시대로 미수행.
- 임시 applied DB 컨테이너(`colab_r_dev_reset_applied2`) 재구성 — **불필요**. 실행한 세 건은 자기 일회용 postgres 를 세운다(`gates/tools/service-tests.sh` · `0018-drift.sh`).
