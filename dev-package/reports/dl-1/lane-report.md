# `DL-1` 레인 보고 — 데이터셋 삭제(묘비)

／ 브랜치 `lane-dl1-dataset-delete` · 기준 `origin/main` = ~~`27733ba`~~ → **`d969f34`**(리베이스 2026-09-08 · §9 · §1~§4 의 sha 는 옛 것이다)
／ 워크트리 = `.claude/worktrees/agent-a10ad0543e2da26d4`
／ 계획서 = 승인분(사용자 홈 `plans/eventual-forging-piglet.md`) · 회부문 = `dev-package/sessions/DL-1-TED-RULING.md`

⛔ **병합은 Ted 판정 ⓐ(`NOT_IMPLEMENTED_P1` → v2 편입) 회수 뒤다.** 레인은 병행 착수분이다.
⛔ **병합 조건 둘째 — 도커 브리지 경로가 있는 호스트에서 `service-tests-core-api` 1회 green.** 그 자리는
CI(`.github/workflows/ci.yml` `service-tests` 잡 · 바뀐 서비스만 일회용 DB 로 판정)다. 이 기계의
판정은 `red(판정) · exit 1 · 사람이 죽임`(§2·§3)이고 손 실행 843/0 은 **보조 근거**다.
／ ⟨정정 2026-09-07 · 어드바이저 ② 조건부 수용⟩ 머리말·§2·§3·§4·§5·§7·§8 의 게이트 축자·미집행 항목을 고쳤다.

---

## 1. 커밋 4

| 순 | sha | 무엇 |
|---|---|---|
| C0 | `36fc8c2` | 대장 `DL-1`·`DL-2` 등재 ＋ 회부문 ＋ `PERMISSION-PRINCIPLES §2` 삭제 행 |
| C1 | `60b3e00` | 서버 두 op ＋ 도메인 함수 8 ＋ 501 표 4 → 2 ＋ pytest 19 |
| C2 | `a9b571b` | 계보 묘비 노드 결함(`kind="묘비"` ＋ `deletedAt`) ＋ pytest 2 |
| C3 | `a4a48e1` | FE 진입점·모달·소스 ＋ vitest 17 |

---

## 2. 게이트 3계수 — **green 13 / red(판정) 1(service-tests-core-api · 원인 = 호스트 도달성 · 판정 미도달) / red(준비) 1(schema-diff)**

／ 종전 표기 ~~green 13 / red(판정) 0 / red(준비) 2~~ — 게이트 축자와 어긋났다(§3). 3계수는 **게이트가 낸 값**으로 적는다.

⚠ 로그 확장자가 `.log` 라 `.gitignore` 의 `*.log` 에 걸린다 — 파일은 워크트리에 있고 커밋되지
않는다(선례: 다른 레인도 `lane-report.md` 만 추적한다). 요약줄은 아래에 그대로 옮겨 적었다.

| 게이트 | 판정 | 요약줄 | 로그 |
|---|---|---|---|
| `work-item-consistency` | green | 대장과 산문의 불일치 0 (관측 1 · 검사 대상 밖 9 · 항목표 아님 2) | `dev-package/reports/dl-1/gate-work-item-consistency.log` |
| `contract-lint` | green | seam 3건 · 룰 위반 0 | `…/gate-contract-lint.log` |
| `contract-breaking` | green | 기준 `origin/main` 대비 **파괴적 변경 없음** (계약 개정 0) | `…/gate-contract-breaking.log` |
| `generated-up-to-date` | green | 등기부 10건 전부 재생성 일치 · 등기부 밖 자칭 생성물 0 | `…/gate-generated-up-to-date.log` |
| `db-boundary` | green | 단위 7 · 스캔 338 · 위반 0 | `…/gate-db-boundary.log` |
| `import-boundary` | green | 계약 8 kept · 0 broken | `…/gate-import-boundary.log` |
| `banned-import` | green | `.py` 154건 · 금지 import 0 | `…/gate-banned-import.log` |
| `exec-bit` | green | `.sh` 126건 전부 100755 | `…/gate-exec-bit.log` |
| `rls-coverage` | green | allow-list 밖 전부 FORCE RLS ＋ 경계 정책 | `…/gate-rls-coverage.log` |
| `rls-effect` | green | 본체 음성 · 메타 양성 · cross-tenant 셋 다 엔진이 막음 | `…/gate-rls-effect.log` |
| `frontend-typecheck` | green | `tsc --noEmit` 오류 0 | `…/gate-frontend-typecheck.log` |
| `frontend-test` | green | **58 files / 809 tests passed** | `…/gate-frontend-test.log` |
| `frontend-fixture-reach` | green | 도달 152 · 금지 모듈 0 | `…/gate-frontend-fixture-reach.log` |
| `schema-diff` | **red(준비)** | `exit 78 · cause=입력미선언 · missing=COLAB_APPLIED_DB_URL_PLATFORM · COLAB_APPLIED_DB_URL_AI` | `…/gate-schema-diff.log` |
| `service-tests-core-api` | **red(판정) · exit 1 · 사람이 죽임** | 로그 말미·`gate-summary.json` 축자 = `red(판정) service-tests-core-api (exit 1)` · `"status": "red_판정"` · 14분 무진행 뒤 워커가 죽임(`Terminated: 15`) → junit 부재로 게이트가 red(판정)를 냈다. 레인 해석(준비 실패)은 §3 | `…/gate-service-tests-core-api.log` |

**red(준비) 하나의 미선언 내용**
- `schema-diff` — 적용 DB URL 두 개가 이 기계에 선언돼 있지 않다. 이 레인은 **마이그레이션 0 ·
  `db/platform/schema.sql` 무변경**이라 선언돼도 판정이 달라질 자리가 없다.

**red(판정) 하나** — `service-tests-core-api`. 게이트 축자는 red(판정)이고 **판정에는 도달하지 않았다**(pytest 접속 0건). 해석은 §3.

---

## 3. `service-tests-core-api` — 게이트 축자 red(판정) · 레인 해석 = 준비 실패

**게이트 축자(사실)** — `red(판정) service-tests-core-api (exit 1)` · `gate-summary.json` `red_판정 1 / red_준비 0` ·
`started 13:14:09Z → finished 13:31:27Z` · 로그 `Terminated: 15` 뒤 「junit 리포트를 읽지 못했다」. 워커가 14분 뒤 죽였고,
게이트는 준비 실패를 가르지 못한 채 매달려 있다가 종료 신호를 받고서야 red(판정)를 냈다.

**레인 해석(해석 · 게이트가 말한 것이 아니다)** — 실질은 준비 실패다. 호스트에 도커 브리지 경로가 없고 `_pg.sh` 에
도달성 검사·`PGCONNECT_TIMEOUT` 이 없다. 아래 실측이 그 근거다.

**실측**
- 이 게이트는 포트를 하나도 publish 하지 않는 일회용 postgres 를 띄우고
  (`gates/tools/_pg.sh` 축자 「**포트를 하나도 publish 하지 않는다**」),
  `tests/fixtures/setup-db.sh` 가 **컨테이너 IP** 로 된 접속 URL 을 돌려준다
  (`docker inspect -f '{{.IPAddress}}'`).
- 이 호스트에는 **도커 브리지 대역으로 가는 경로가 없다** — `netstat -rn -f inet` 에
  `172.17.0.0/16` 행이 0건이고, `nc -z -w 3 172.17.0.3 5432` = **UNREACHABLE**
  (같은 시각 `nc -z -w 3 127.0.0.1 5432` = 성공).
- 그래서 psycopg 가 connect 에서 막히고, 게이트는 **14분 넘게 진행 없이 대기**했다
  (pytest CPU 시간 7.9초 · 일회용 DB 의 `pg_stat_activity` 에 접속 0건). 사람이 죽였다.

**어느 검사에 걸리는가** — ⛔ **아무 데도 안 걸린다.**
`_pg.sh` 는 컨테이너가 **뜨지 않는** 경우만 red(준비)로 가른다. 「떴는데 호스트에서 못 닿는다」는
갈래가 없고, psycopg 에 connect 타임아웃이 안 걸려 있어 `::gate-readiness-failure::` 도
exit 78 도 나오지 않는다. **판정도 준비 red 도 아닌 채로 매달린다** — 자동 실행에서는
「아직 도는 중」과 구별되지 않는다. **후속 항목으로 올린다**(§7 ⓐ · 대장 WU `gate-pg-reach`).

**보조 근거(같은 시험을 같은 선택자로 손 실행한 값 · 병합 근거가 아니다)**
`cd services/core-api && .venv/bin/python -m pytest -q --strict-markers -p no:cacheprovider -m "not e2e"`
— 로컬 도커 `colab_local_pg` 의 `colab_platform_test`(공개 포트 `127.0.0.1:5432`) 대상,
스키마·롤·시드는 게이트와 **같은 재료**(`tests/fixtures/setup-db.sh`)로 다시 적용했다.
⚠ **새로 찍은 DB 가 아니다** — 기존 로컬 컨테이너의 DB 위에 `setup-db.sh` 로 스키마·롤·시드를 재적용한 것이다
(§7 ⓒ 의 시드 오염 갈래가 그래서 이 경로에 열려 있다). **병합 조건은 CI `service-tests` 1회 green** 이다(머리말).

```
843 passed, 6 deselected in 160.95s
```
`main` 줄기 직전 전수(`b0671f8` 로그)의 같은 게이트 값은 「수집 826 · 실행 826 · deselected 6 ·
failed 0」이었다 — **826 → 843**(신설 21 − 501 표 파라미터화 감소 4).

---

## 4. 시험 red → green (두 실행의 계수)

| 시험 | red (구현 전) | green (구현 뒤) |
|---|---|---|
| `services/core-api/tests/test_dataset_deletion.py` **19** (C1분) | **18 failed / 1 passed** · 축자 `AssertionError: assert 501 == 204` · 로그 `dev-package/reports/dl-1/pytest-red.txt` | 전건 통과 |
| 같은 파일 ＋ **2** (C2분 계보 묘비) | **2 failed** · 축자 `AssertionError: assert '가공 전' == '묘비'` · 로그 `…/pytest-red-c2.txt` | 전건 통과 |
| core-api 전수 (`-m "not e2e"`) | 기준선 = `main` 게이트 826/0 | **843 passed / 0 failed / 6 deselected** · 로그 `…/pytest-green.txt` |
| `frontend/test/dataset-delete.test.tsx` **17** | **1 file failed / 0 tests** · 축자 `Failed to resolve import "../src/components/detail/deletionSource". Does the file exist?` | **17 passed** |
| 프런트 전수 | 기준선 = `main` 게이트 792 | **58 files / 809 tests passed** |

⚠ **정직하게 적는다** — C3(FE)는 **구현 파일을 먼저 쓴 뒤** vitest 를 썼다. red 는 구현 4파일을
치우고 `types.ts`·`DatasetDetailPage.tsx` 를 되돌린 상태에서 실측했고(위 축자), 그 뒤 되돌려
green 을 실측했다. C0~C2 는 시험이 먼저다.
⚠ **C3 의 red 는 `Failed to resolve import` 1 file(모듈 부재 red)이지 단언별 red 가 아니다** — 17건의 단언이
각각 구현 전 red 였음은 실측되지 않았다(TDD 한계 · 어드바이저 ② 지적).

⚠ **1 passed** 로 시작한 시험 하나 = `test_the_seed_datasets_are_never_tombstoned_by_this_file`.
기능 오라클이 아니라 **시드 보호 감시**라 처음부터 green 인 것이 정상이다(`conftest._RESTORE` 가
`deleted_at` 을 되돌리지 않아, 시드를 한 번 지우면 그 뒤 모든 회차가 묘비 위에서 돈다).

---

## 5. 계획과 어긋나 바꾼 것

| # | 계획 | 실제 | 왜 |
|---|---|---|---|
| ⑴ | `ACTION_DATASET_DELETED` 를 `routes/deletion.py` 에 둔다 | `domains/d8_insight.py` 에 뒀다 | 계획이 인용한 **선례 `ACTION_PROJECT_DELETED` 가 그 파일에 있다**(`d8_insight.py:54`). 라우트에 두면 활동 문자열이 두 곳에 살고, 그 표는 「정본이 값 집합을 안 닫아 여기서 하나로 고정한다」는 주석이 붙은 자리다 |
| ⑵ | `_deletable` 이 DELETE 에서 `lock_dataset` 까지 본다 | 관문은 400→404→403 까지만, `lock_dataset` 은 `delete_dataset` 본문 첫 줄 | 파급 조회(GET)가 잠금을 걸면 안 된다. 계획 §5-2 의 「DELETE 만」을 분기 대신 **호출 위치**로 표현했다 — 판정 내용은 같다 |
| ⑶ | `snapshot_access` → `AccessRow` 로 상태만 | `state` ＋ `updated_at` 둘 다 되돌린다 | 상태만 되돌리면 「누가 언제 접근 상태를 바꿨나」가 삭제 때문에 밀리고, 그 밀림은 사람이 바꾼 것과 구별되지 않는다 |
| ⑷ | 모달에 `dl-impact`·`dl-keep` | ＋ `detail-delete-impact-loading`·`-failed`·`-retry` testid | 「파급을 못 읽으면 삭제 비활성 ＋ 다시 불러오기」(계획 §6)를 시험이 잡으려면 그 세 상태에 손잡이가 필요하다 |
| ⑸ | 시험 케이스 15＋8 | pytest **21** · vitest **17** | 계획의 ①~⑮ 를 전부 덮고, 잠금 원복의 반대 경우(행이 **없던** 데이터셋은 삭제 뒤에도 없어야 한다)와 경계 밖 이웃의 `deletedAt: null`, 시드 보호 감시를 더했다 |

**계획에 있었으나 안 한 것 = 2** ／ 종전 ~~0~~(어드바이저 ② 정정) —
- C4 마감(계획 §10) — **이 커밋으로 집행**(대장 evidence · HANDOFF · 세션 기록 · 게이트 결함 WU). `〈N〉` 발급과
  `.claude/rules/deploy.md` 11 산문 갱신은 계획대로 **병합 직전·병합 커밋**이다(이 레인 밖).
- 완료 정의 ⑻(dev 배포 뒤 일회용 데이터셋 실삭제 · `deploy_doctor` 14/14) — **미집행.** dev 배포 회차의 일이다.
  ⟹ **`DL-1` 은 병합 뒤에도 `open` 이다.**

**계획에 없었는데 한 것(초과) = ⑸ 의 추가 시험 3건과 ⑷ 의
testid 3건** — 둘 다 계획의 완료 정의를 잠그기 위한 것이고 제품 표면을 늘리지 않는다.

---

## 6. 계획서 §12 열린 값 중 이 레인이 확인한 것

| 열린 값 | 확인 결과 |
|---|---|
| `body_access` RESTRICTIVE 에 소유자·역할 조항이 **없다** | **확인.** `db/platform/schema.sql` 의 `CREATE POLICY body_access ON d3_file AS RESTRICTIVE FOR ALL` 은 「접근 상태(없으면 연구실 기본값)=`열림`」 또는 「만료 안 된 허용 줄」 둘뿐이다. 시험이 그 함정을 재현한다 — 잠긴 데이터셋의 `d3_file` 은 앱 롤에게 **0행**(`test_a_locked_dataset_loses_its_files_and_bytes_too` 의 전제 단언) |
| `d2_dataset_access_request.state` 가 3값이고 「닫힘」이 없다 | **확인.** ＋ 짝 CHECK 셋(`decided_by`↔`decided_at` · `검토 대기`↔`decided_at IS NULL` · `거절됨`↔`rejection_reason IS NOT NULL`). ⟹ 닫으려면 **사유가 반드시 있어야 한다** |
| 계약에 두 op 이 있다 · `LineageNode.kind` enum 에 `묘비` 가 있다 | **확인.** `fe-core.yaml:980`(`deleteDataset`) · `:1049`(`getDatasetDeletionImpact`) · `:4039`(`DeletionImpact`) · `LineageNode.kind` enum 5값에 `묘비` 포함. 생성물에도 있다(`frontend/src/generated/fe-core.ts:749`·`:2757`) |
| `files_for_download` 가 있다 | **확인.** `d3_catalog.py` — 본체 ＋ 기준 격자 파일, 키를 원장에서 읽는다 |
| ⚠ 계약이 `deleteDataset`·`getDatasetDeletionImpact` 에 **400 을 선언하지 않았다** | **새로 확인.** 형제 op 도 같다(`getDataset` 도 400 없음). 그런데 형제 라우트는 전부 모양 오류를 400 으로 낸다(`access.py::_living_dataset` · `ingestion.py::_file_target` — 근거 `CODE-REVIEW-20260903 #12`). 이 레인은 **선례를 따랐다**(400). `test_route_table.py` 는 응답 코드를 대조하지 않아 게이트에 걸리지 않는다 — **후속 항목**(§7 ⓑ) |
| `ops/purge_datasets.py` 의 RLS 함정 | **`[미확인 · 실행 안 함]` 그대로.** 읽지도 고치지도 않았다(범위 밖). 회부문 ⓗ 에 「어느 검사에도 안 걸린다」로 적었다 |

---

## 7. 후속 항목 (이 레인이 고치지 않은 것)

- **ⓐ `service-tests-core-api` 가 준비 실패를 무한 대기로 낸다.** 컨테이너가 떴는데 호스트에서
  못 닿는 갈래가 `_pg.sh` 에 없고, psycopg 에 connect 타임아웃이 없다. **게이트에도 배포
  스크립트에도 걸리지 않는다** — 자동 실행에서 「도는 중」과 구별되지 않는다.
  고치는 자리 = `gates/tools/_pg.sh`(접속 가능성 확인 한 줄) 또는 `service-tests.sh`
  (`PGCONNECT_TIMEOUT` 선언). 이 레인은 게이트를 고치지 않았다.
- **ⓑ 계약이 두 삭제 op 에 400 을 선언하지 않았다.** 서버는 형제 선례대로 400 을 낸다.
  `test_route_table.py` 는 경로·메서드만 대조하므로 **응답 코드 어긋남을 보는 검사가 0건**이다.
  선택지 = 계약에 400 추가(㉮ 순수 추가) / 라우트가 404 로 접기(형제와 어긋남 · 오타를 못 고침).
- **ⓒ 시드 `DSA1` 의 `topic` 이 시험 사이로 샌다.** `test_input_error_paths.py::
  test_the_two_topics_added_in_354_pass` 가 시드를 `파일 포맷 예제` 로 PATCH 하는데
  `conftest._RESTORE` 에 `topic` 복원이 없다. 한 번의 전수 안에서는 알파벳 순서 덕에 안 터지고
  **다음 전수를 오염시킨다**(같은 DB 를 재사용할 때 `test_dataset_detail`·`test_dataset_facets`·
  `test_dashboard` 4건 red). CI 는 매번 일회용 DB 라 안 보인다 — 실측 재현함.
- **ⓓ 워크트리의 `frontend/node_modules` 에 `@rolldown/binding-darwin-x64` 가 빠져 있었다.**
  `npm ci` 의 optional-deps 사고(npm/cli#4828). 이 레인은 본 체크아웃의 같은 버전 디렉터리를
  워크트리로 복사해 진행했다(추적 대상 아님 · 판정 내용 무변경). `worktree-setup.sh` 가
  설치 뒤 네이티브 바인딩 존재를 확인하지 않는다.
- **ⓔ 묘비의 Verified `검토 대기` 행**(회부문 ⓖ) — 승인함에 ULID 이름으로 남는다.
  고치는 자리 = `list_pending_verification_requests` 질의 조건 한 줄.
- **ⓘ 계약이 `deleteDataset`·`getDatasetDeletionImpact`(및 형제 op)에 400 을 선언하지 않았다**(ⓑ 의 확장 · 회부문 ⓘ).
  서버는 형제 선례대로 400 이고 `test_route_table.py` 는 코드를 안 본다. 선택지 = 계약에 400 을 ㉮ 순수 추가
  (회차 등재 ＋ 생성물 재생성 · **형제 op 까지 한 번에**) / 판정 대기. **권고 = 순수 추가 회차를 별도로** — 이 레인은
  계약 무변경을 유지한다.
- **ⓙ `test_not_implemented.py` 의 「실제로 부른다」 오라클이 문자열 포함 검사다**(`operation_id in path.read_text()` ·
  `tests/test_not_implemented.py:215`). 시험 파일에 op 이름이 글자로만 있어도 통과한다 — 기존 약점 · 전 `*_REAL` 공통 ·
  후속(회부문 ⓙ).
- **ⓚ 게이트 결함 WU `gate-pg-reach`** 를 대장에 등재했다(ⓐ 의 자리 · status `open`). 이 레인은 게이트를 고치지 않았다.

---

## 8. 열린 질문 (Ted 판정 없이는 못 닫는다)

1. **ⓐ** `deleteDataset`·`getDatasetDeletionImpact` 의 P1 → v2 편입 — **병합의 선행조건**.
   `Policy_데이터셋_상세 §6·§8` 축자가 이 기계에 없어 `〈229〉`-㉯ 방식의 정본 인용을 못 했다.
2. **ⓑ** `PERMISSION-PRINCIPLES §2` 에 더한 「데이터셋 삭제」 행의 승인(다른 정본에서 옮겨 적었다).
3. **ⓕ** 대기 접근 요청을 `거절됨` ＋ 고정 사유로 닫는 것 — 요청자에게 「거절」로 보인다.
   고정 사유 문장 `데이터가 지워져서 요청이 닫혔어요.` 는 **`[정본 무근거]`**.
   prod 의 현재 `검토 대기` 건수는 **`[미측정]`**.
4. **ⓒ** prod `admin` 역할 전환 — 병합과 별개의 승인 행동.
5. **ⓓ1~ⓓ3** `DL-2` 게이트(`core-viz.yaml` 동결 해제 · `PreviewSinkPort.remove` · 집합 D 래퍼).
6. `〈N〉` 발급 — **이 레인은 `PLAN-SoT.md` 를 건드리지 않았다.** 번호는 오케스트레이터가
   병합 직전에 발급한다(`rules §4-1`).
7. **ⓘ** 계약 400 순수 추가 회차(형제 op 공통)를 별도로 열 것인가 — 이 레인은 계약 무변경.
8. **ⓙ** `*_REAL` 오라클 강화(문자열 포함 → 실제 호출 검증)의 범위와 시점.
9. **병합 조건 재확인** — Ted ⓐ ＋ CI `service-tests` 1회 green. 이 기계의 `service-tests-core-api` 는 red(판정)이고
   그 원인(호스트 도달성)은 `gate-pg-reach` 가 닫는다. 완료 정의 ⑻ 은 병합 뒤 dev 배포 회차 — `DL-1` 은 그때까지 `open`.

---

## 9. 리베이스 (2026-09-08)

### 9-1. 기준 · 커밋

- 새 기준 = `origin/main` **`d969f34`**(종전 `27733ba` 뒤 **110 커밋** · R-B 라운드 · `〈373〉`·`〈374〉` · 마이그레이션 `0015_rb1_axes_category_type_lv`~`0019_rb7_search_index_m10`).
- 커밋 5 재발급(내용 무변 · C4 만 충돌 해소분 포함) ＋ C5(이 절):

| 순 | 옛 sha | 새 sha | 무엇 |
|---|---|---|---|
| C0 | `36fc8c2` | `b590847` | 대장 등재 ＋ 회부문 ＋ 권한 표 |
| C1 | `60b3e00` | `89d1a57` | 서버 두 op ＋ 도메인 함수 ＋ 501 표 4 → 2 |
| C2 | `a9b571b` | `2f4d103` | 계보 묘비 노드 |
| C3 | `a4a48e1` | `2f48a73` | FE 진입점·모달·소스 |
| C4 | `d811b74` | `3a761f9` | 마감(HANDOFF 충돌 해소 포함 · amend 1회) |
| C5 | — | (이 커밋) | `0017` 정합 코드 ＋ 시험 1 ＋ 보고서·세션·대장 |

- `git diff --name-only origin/main` 25 파일 — `contracts/`·`db/platform/versions`·`routes/catalog.py`·`ports/storage.py`·`d4_lineage.py`·`DetailHeader.tsx` **부재 확인**(계획 §10 터치 0 유지).

### 9-2. 충돌 파일 · 해소

| 파일 | 충돌 자리 | 해소 |
|---|---|---|
| `dev-package/work-items.yaml` | C0 · C4 두 번 | 규칙 §4-2 — 레포 드라이버 `dev-package/tools/merge-work-items.py` 를 `gates/.venv` python 으로 손 실행(git 이 부른 시스템 python3 에 PyYAML 부재 → 드라이버가 손을 뗌). HEAD(main) 전체 ＋ 상대 신규 블록 덧붙임(C0: `DL-1`·`DL-2` 2건 · C4: `gate-pg-reach` 1건 ＋ `DL-1` 한쪽 수정 취함) · `yaml.safe_load` ＋ id 유일성 = 159건 · 중복 0 |
| `dev-package/03-HANDOFF.md` | C4 · 상단 증보 블록 | main 의 R-B 마감 증보(09-08) 블록 보존 ＋ 우리 증보 1행을 그 아래 삽입. §1 `DL-1`·`DL-2` 두 행(T-P 표 4열)과 §4 **71**·**72** 두 행은 자동 병합(main 마지막 번호 70 · 충돌 없음) |
| `frontend/src/routes/DatasetDetailPage.tsx` | C3 · import 1행 | main 의 `{ DatasetEditActions, DatasetEditForm }` 보존 ＋ 우리 import 2행 유지. `deletionSource` prop·훅·`editAction` 슬롯(진입점 둘)은 자동 병합 |
| `d2_access.py` · `d3_catalog.py` · `routes/lineage.py` · `not_implemented.py` · `test_not_implemented.py` | 충돌 없음(자동) | main 판 전체 ＋ 우리 덧붙임 · `def` 중복 0 · 501 표 4 → 2 그대로(main 이 다른 행을 걷지 않았다) · `node()` 묘비 분기 유지 |

### 9-3. `0017_rb4_access_state_3` 정합 (C5)

- 실물 — `d2_dataset_access` 열 4개 무변(`dataset_id`·`lab_id`·`state`·`updated_at`) · CHECK 만 `('열림','잠김','지정 공개')` 3값 · `열림` 어휘 존속(마이그레이션 산문 「열림/잠김 어휘를 지우지 않는다」).
- main(WU-B4)이 그 표의 **제품 쓰기 헬퍼**를 뒀다 — `d2_access.set_access_state(session, *, dataset_id, state)`(upsert ＋ 데이터셋 advisory 잠금 ＋ `잠김` 일 때만 grant 만료). ⟹ 우리 `_OPEN_ACCESS` upsert 를 지우고 `open_access_for_deletion` 이 `set_access_state(state="열림")` 을 부른다(중복 0). `열림` 갈래는 grant 를 건드리지 않고, advisory 잠금은 겹친 승인(`decide_access_request`)과 삭제 트랜잭션을 직렬화한다(잠금 순서 = 삭제가 `d3_dataset FOR UPDATE` → advisory · 승인 경로는 `d3_dataset` 을 잠그지 않아 순환 없음).
- `snapshot_access`·`restore_access` 는 **유지** — main 에 「`updated_at` 까지 되돌리기」·「행 부재를 부재로 되돌리기」 헬퍼가 없다(`set_access_state(None)` 은 `state=NULL` 행을 남긴다).
- 시험 ⑪-b 신설 `test_a_designated_dataset_is_restored_with_its_grant_intact` — `지정 공개` ＋ 유효 grant 1 → DELETE 204 → `state` 그대로 · `updated_at` 그대로 · grant 유효 1 · 파일 0행 · 바이트 부재. **red 먼저**(원복을 `잠김` 으로 고정한 임시 결함 → `AssertionError: 원복이 지정 공개 를 다른 값으로 뭉갰다` · `rebase/pytest-red-c5.txt`) → 되돌린 뒤 green.
- 기존 픽스처(`planted(locked=True)` = `잠김` 직접 INSERT)는 3값 CHECK 와 충돌 없음.

### 9-4. 시험 DB → 0019

- `colab_platform_test` = `tests/fixtures/setup-db.sh`(`CONTAINER=colab_local_pg DB=colab_platform_test`)로 레인 트리 `db/platform/schema.sql` 재적용 — 표 27 → 28 · `d2_dataset_access_state_check` 3값 실측.
- `colab_platform` = 본 체크아웃 venv 의 `alembic upgrade head` → `alembic_version_platform` = `0019_rb7_search_index_m10`(종전 `0014_merge_ra1_and_topic_vocab`). staging·dev·prod 무접촉.

### 9-5. 재검증 3계수 — **green 13 / red(판정) 0 / red(준비) 1**(14 게이트 실행 · `service-tests` 미실행)

| 게이트 | 판정 | 요약줄(축자) | 로그(`dev-package/reports/dl-1/rebase/`) |
|---|---|---|---|
| `work-item-consistency` | green | 대장 159건 · 불일치 0 (C5 대장 갱신 뒤 재실행 §9-6) | `gate-work-item-consistency.log` |
| `frontend-typecheck` | green | `tsc --noEmit` 오류 0 | `gate-frontend-typecheck.log` |
| `frontend-test` | green(2회차) | **73 files / 1013 tests passed**(종전 809 → main 증가분 ＋ 우리 17) | `gate-frontend-test.log` |
| ↳ 1회차 | red(판정 · exit 1) | 「수집된 시험 0건」 · 73 unhandled `ERR_REQUIRE_ESM`(`html-encoding-sniffer` → `@exodus/bytes` ESM require) | `gate-frontend-test-node22.9-noflag.log` |
| `frontend-fixture-reach` | green | 도달 167 · 금지 모듈 0 | `gate-frontend-fixture-reach.log` |
| `contract-lint` | green | seam 3 · 위반 0 | `gate-contract-lint.log` |
| `contract-breaking` | green | 기준 `origin/main` 대비 파괴적 변경 없음 | `gate-contract-breaking.log` |
| `generated-up-to-date` | green | 등기부 10건 재생성 일치 | `gate-generated-up-to-date.log` |
| `db-boundary` | green | 단위 7 · 스캔 346 · 위반 0 | `gate-db-boundary.log` |
| `exec-bit` | green | `.sh` 131건 100755 | `gate-exec-bit.log` |
| `import-boundary` | green | 계약 전부 KEPT | `gate-import-boundary.log` |
| `banned-import` | green | `.py` 154 · 금지 0 | `gate-banned-import.log` |
| `rls-coverage` | green | allow-list 밖 전부 FORCE RLS ＋ 경계 정책 | `gate-rls-coverage.log` |
| `rls-effect` | green | 본체 음성 · 메타 양성 · cross-tenant 셋 다 차단 | `gate-rls-effect.log` |
| `schema-diff` | red(준비 · exit 78) | 적용 DB 미선언(`COLAB_APPLIED_DB_URL_*`) — 종전과 같음 | `gate-schema-diff.log` |
| `service-tests` | **미실행** | 이 맥에서 일회용 postgres 무판정 매달림(§3 · `gate-pg-reach`) — 직접 pytest 로 갈음(아래) | — |

- **`frontend-test` 1회차 red 의 원인 = 호스트 node.** `jsdom 29.1.1` engines `^20.19.0 || ^22.13.0 || >=24`, `@exodus/bytes` `^22.12.0`(require(esm) 지원선) — 이 기계의 node 는 `22.9.0`(지시된 경로)·`21.4.0`(기본) 둘 다 미만. 2회차 = 같은 node 22.9.0 에 `NODE_OPTIONS=--experimental-require-module`(cmux 의 `--require` 옵션을 치우고 이 플래그만) — **검사 대상·설정 무변**, 런타임 플래그만. `package-lock.json` 은 `27733ba`↔`d969f34` diff 0 이라 09-06 green 과 같은 의존 트리다(그때의 node 플래그는 `[미확인]`). CI 는 `setup-node 20`(jsdom 선 `^20.19`).
- **pytest 전수**(`-m "not e2e"` · 로그 `rebase/pytest-full.txt`) = **948 passed / 0 failed / 6 deselected · 175.7s**(기준선 843 → main 증가분 104 ＋ 우리 신설 1 · `test_dataset_deletion.py` 22). 실행 트리 = C5(정합 코드 포함).
- **vitest** = 1013/0(위).

### 9-6. 계획(§11-b)과 달라진 것

| # | 계획 | 실제 | 왜 |
|---|---|---|---|
| ⑴ | 대장 충돌은 규칙 4-2 로 손 해소 | 레포 병합 드라이버를 `gates/.venv` python 으로 손 실행 | 드라이버가 이미 §4-2 를 기계로 옮겼고, git 이 부른 python3 에만 PyYAML 이 없었다. 결과 검증(파싱·id 유일성)은 같은 python 으로 별도 확인 |
| ⑵ | `0017` 정합 = 값·열 확인 | 확인 ＋ **쓰기 문장 재사용**(`set_access_state`) ＋ 시험 1 | 지시 「제품 쓰기 헬퍼가 있으면 재사용하고 우리 것을 지운다」. 코드 변경이 C5 에 들어간 것은 지시 「커밋 1개」 때문 — C1 에 fixup 하면 sha 가 다시 바뀐다 |
| ⑶ | `frontend-test` 1회 | 2회(1회차 red 기록 보존) | 원인이 검사 대상이 아니라 호스트 node 지원선이라 플래그로 재실행. 1회차 로그를 지우지 않았다 |
| ⑷ | C4 그대로 재적용 | C4 amend 1회 | HANDOFF 해소 스크립트가 단언에서 멈춘 채 `git add` 가 먼저 돌아 표식이 커밋됐다 → 표식 0 으로 고쳐 amend. 최종 `git grep` 표식 0건 |

### 9-7. 열린 것

- Ted 판정 ⓐ 회수 · `〈N〉` 발급(병합 직전 · `PLAN-SoT` 무접촉) · CI `service-tests` 1회 green · 병합 · dev 배포(0015~0019 실적용 동반) · 완료 정의 ⑻.
- `frontend-test` 가 이 맥에서 플래그 없이 red 인 것 — 호스트 node 를 `22.13+` 로 올리거나 게이트 진입조건에 적는 것은 별건(`gate-pg-reach` 계열 · 이 레인 범위 밖).

---

## 10. 재리베이스 (2026-09-12)

### 10-1. 기준 · 커밋

- 새 기준 = `origin/main` **`a8a1653`**(종전 `d969f34` 뒤 **192 커밋** · R-C·R-D·로그인/백오피스 회차 ·
  마이그레이션 platform `0020_rc7_project_name_unique`~`0027_operator_audit` · ai `0006` 형제 둘 ＋ `0007` merge).
- 브랜치 이름 `lane/wu-dl-1`(`docs/BRANCHING.md` 규칙 4 · 수명 표 `lane/wu-*` 행) ／ 종전 `lane-dl1-dataset-delete`.
- 워크트리 = 하네스 생성분(`.claude/worktrees/agent-af600bd99d66c0d31`).

| 순 | 2026-09-08 sha | 2026-09-12 sha | 무엇 |
|---|---|---|---|
| C0 | `b590847` | `088c59d` | 대장 `DL-1`·`DL-2` 등재 ＋ 회부문 ＋ 권한 표 |
| C1 | `89d1a57` | `7a7e56e` | 서버 두 op ＋ 도메인 함수 ＋ 501 표 4 → 2 |
| C2 | `2f4d103` | `555bda8` | 계보 묘비 노드 |
| C3 | `2f48a73` | `6d3f297` | FE 진입점·모달·소스 |
| C4 | `3a761f9` | `8bd7023` | 마감(대장 evidence · HANDOFF · `gate-pg-reach`) |
| C5→**C6** | `6448f50` | `17b0b95` | `0017` 3값 정합 ＋ 재리베이스 기록(메시지를 이번 기준으로 고쳐 C6 으로 간주) |
| **C7** | — | `5527408` | 묘비 전환에 운영자 감사 스냅샷(`0027` 규약 정합) |
| **C8** | — | (이 커밋) | 재리베이스 마감 — 보고서 §10 · 세션 · 대장 |

- `git diff --name-only origin/main` **27 파일** — `contracts/`·`db/platform/versions`·`routes/catalog.py`·
  `ports/storage.py`·`d4_lineage.py`·`DetailHeader.tsx` **부재 확인**(계약 개정 0 · 마이그레이션 0 유지).
- `git grep` 충돌 표식 **0건**.

### 10-2. 충돌 파일 5 (사건 7) · 해소

| 파일 | 충돌 자리 | 해소 |
|---|---|---|
| `dev-package/work-items.yaml` | C0 · C4 · C6 | 규칙 §4-2 — 레포 드라이버 `dev-package/tools/merge-work-items.py` 를 `gates/.venv/bin/python` 으로 손 실행. **git 이 부르는 `python3` 에 PyYAML 이 없어** 드라이버가 스스로 손을 뗀다(축자 「work-items 병합 드라이버: 손을 뗀다 — PyYAML 이 없어 결과를 검증할 수 없다」). HEAD 전체 ＋ 상대 신규 블록 덧붙임 — C0 `DL-1`·`DL-2` 2건 · C4 `gate-pg-reach` 1건 · C6 `DL-1` 한쪽 수정 취함. 최종 **항목 185 · id 중복 0** |
| `services/core-api/src/colab_core/app/main.py` | C1 · 라우터 import | **합집합** — main 의 `accounts`·`representative_image` ＋ 레인의 `deletion`. `include_router` 튜플은 자동 병합(`deletion.router` 보존) |
| `services/core-api/tests/test_not_implemented.py` | C1 · `P2_REAL` 합집합 대입 | main 의 `C21_REAL`·`C22_REAL` 보존 ＋ 레인 `DL_REAL` 추가. **501 표는 main 도 4행**(`git show origin/main:…/not_implemented.py` 실측)이라 **4 → 2** 유효 · 단언 `len(OPERATIONS) == 2` 유지 |
| `frontend/src/routes/DatasetDetailPage.tsx` | C3 · 3자리 | 세 자리 전부 **합집합** — import(main `RepresentativeImageSection`·`apiRepresentativeImageSource` ＋ 레인 `DatasetDeleteEntry`·`defaultDeletionSource`) · prop(`representativeImageSource` ＋ `deletionSource`) · `useMemo` 둘. `editAction` 슬롯의 진입점 둘(`DatasetEditEntry` ＋ `DatasetDeleteEntry`)은 자동 병합 · `DetailHeader.tsx` 터치 0 |
| `dev-package/03-HANDOFF.md` | C4 · §4 블로커 표 | main 이 **71번을 이미 썼다**(staging 자동배포 알림 스풀 · 2026-09-12). 레인 두 행을 **72·73 으로 재번호**해 main 의 현재 형식 그대로 삽입. §1 `DL-1`·`DL-2` 행과 상단 증보 1행은 자동 병합 |
| `d2_access.py`·`d3_catalog.py`·`d8_insight.py`·`routes/lineage.py`·`routes/not_implemented.py`·`types.ts` | 충돌 없음(자동) | 도메인 3파일 = **순수 추가 196행 · `def` 중복 0**. `d8_insight.record_activity` 는 main 이 `upload_id=None` 기본 인자를 더했을 뿐이라 레인 호출 무변. `routes/lineage.py::node()` = main 의 `**level_pair(c, …)` 2칸 전개와 레인 묘비 분기(`kind="묘비"`·`deletedAt`·`navigable`·`bodyAccessible`)가 같은 `c is None` 자리에 공존 · main 이 파일 끝에 더한 op 2개 보존 |

- ⚠ **지도(사전 실측)와 다른 곳 2** — ⑴ `routes/lineage.py` 는 **자동 병합됐다**(판단 충돌 예상이었으나 표식 0). 결과물은 지도가 지시한 모양과 같고, `git diff origin/main` 2 hunk 로 확인했다. ⑵ `03-HANDOFF.md` 는 **행 번호 재번호가 추가로 필요했다**(main 이 71 을 선점).

### 10-3. C7 — 운영자 감사 스냅샷 (`0027` 규약 정합)

- 왜 = main 이 `0027_operator_audit` 로 데이터셋 쓰기에 `d3_operator_audit` 스냅샷을 의무화했고
  (`d3_catalog.update_dataset` → `d3_audit.append_snapshot(action="dataset.updated")`), 삭제도 데이터셋 쓰기다.
  활동 한 줄(`d8_activity`)은 **이름·요약을 들지 않아** 「무엇이 지워졌는가」를 대신하지 못한다.
- 자리 = `routes/deletion.py::delete_dataset` 트랜잭션 안 **⑧-b**(활동 한 줄 직후 · 바이트 회수 전).
  `restore_access` **뒤**다 — `d3_operator_audit` 의 RLS 는 `lab_id = current_lab_id()` 하나뿐이라
  「열림」 창과 무관하고, 선례(`routes/project.py::delete_project`)도 활동 다음에 감사를 적는다.
- 인자 축자 = `action="dataset.deleted"` · `before={"name","summary"}` · `after=None`.
  **레포에 이미 있는 값을 재사용**했다 — purge 경로 `d3_audit.append_deletion_snapshots` 가 같은 표에
  같은 이름·같은 모양으로 적는다. 두 삭제 경로가 다른 문자열을 쓰면 감사 질의가 한쪽을 놓친다.
- 실패 시 예외 전파 → 전체 롤백 · 500(§5-4 의미론 그대로). 감사 없이 커밋되는 삭제를 만들지 않는다.
- 시험 1건 신설 `test_deleting_appends_one_operator_audit_snapshot` —
  **red 먼저**(구현 전) 축자 `AssertionError: 삭제가 운영자 감사 스냅샷을 1행 남기지 않았다. assert 0 == 1` ·
  로그 `dev-package/reports/dl-1/rebase2/pytest-red-c7.txt` → 구현 뒤 green.
  `tests/test_dataset_deletion.py` **22 → 23**.

### 10-4. 재검증 3계수 — **green 13 / red(판정) 0 / red(준비) 1**(14 게이트 실행 · `service-tests` 미실행)

／ 실행 둘 — ⑴ 게이트별 단독(`COLAB_GATE_REPORT_DIR=dev-package/reports/dl-1/rebase2/gates/<게이트>
bash gates/run.sh <게이트>` · 요약 JSON 과 `gate.log` 가 그 자리에 선다 · 스키마 `colab-gate-summary/1`) ·
⑵ **작업 증거 1회**(`docs/development/lifecycle-evidence.md` · `begin --role lane-worker` 로 게이트 13을 선언하고
`COLAB_TASK_ID=… bash gates/run.sh task` 로 **한 실행 정체성**에 묶어 돌린 것 · 보고서
`dev-package/reports/dl-1/rebase2/h7/gate-summary.json` · `schema-diff` 는 red(준비)라 선언 집합에서 뺐다).

| 게이트 | 판정 | 요약줄(축자) |
|---|---|---|
| `work-item-consistency` | green | `대장과 산문의 불일치 0` (대장 185건) |
| `contract-lint` | green | `seam 3건, 룰 위반 0` |
| `contract-breaking` | green | `기준 origin/main (3건) 대비 파괴적 변경 없음` |
| `generated-up-to-date` | green | `등기부 13건 전부 재생성 일치, 등기부 밖 자칭 생성물 0건` |
| `db-boundary` | green | `단위 8개 · 스캔 대상 401건 · 위반 0` |
| `import-boundary` | green | `계약 전부 통과` |
| `banned-import` | green | `.py 177건, 금지 import 0` |
| `exec-bit` | green | `.sh 207건 전부 인덱스 모드 100755 (100644 = 0건)` |
| `rls-coverage` | green | `allow-list 밖 테이블 전부 FORCE RLS + 연구실 경계 정책` |
| `rls-effect` | green | `본체 음성 · 메타 양성(P-13) · cross-tenant 셋 다 엔진이 막는다` |
| `frontend-typecheck` | green | `tsc --noEmit … 오류 0건` |
| `frontend-test` | green(2회차) | `vitest run … 통과 1270건 · 실패 0건` (105 files) |
| ↳ 같은 트리 4회 | **red 2 / green 2** | 갈리는 것은 늘 한 건(`test/account-admin.test.tsx` 의 첫 시험) · 축자 `Expected element to have text content: /lab  Received: /account-admin` · 원인·고치는 자리 §10-5 ⓐ. **이 표의 green 은 그 4회 중 green 회차의 값이다** |
| `frontend-fixture-reach` | green | `진입점 src/main.tsx 에서 도달 197개 … 금지 모듈 0건` |
| `schema-diff` | **red(준비 · exit 78)** | `cause=입력미선언|missing=COLAB_APPLIED_DB_URL_PLATFORM · COLAB_APPLIED_DB_URL_AI` — 이 레인은 마이그레이션 0 · `schema.sql` 무변경이라 선언돼도 판정이 달라질 자리가 없다 |
| `service-tests-core-api` | **미실행** | 이 맥에서 일회용 postgres 무판정 매달림(§3 · 대장 `gate-pg-reach`) — 직접 pytest 로 갈음(아래) |

⚠ **게이트 실행 조건 하나를 적어 둔다** — `PATH` 앞에 `gates/.venv/bin` 을 세웠다.
`gates/run.sh` 의 `work-item-consistency` 는 `python3 gates/tools/work_item_consistency.py` 를 그대로 부르는데
**이 맥의 `python3` 셋(3.12 프레임워크 · 3.10 · `/usr/local`) 어디에도 PyYAML 이 없다.** 그 상태의 게이트 축자는
`::error::work-item-consistency — pyyaml 이 없다 (검사 불가는 통과가 아니다)` · **`red(판정) · exit 1`** 이다.
게이트 도구 핀(`gates/requirements.txt`)이 `PyYAML==6.0.2` 를 고정하고 그 해석본이 `gates/.venv` 이므로,
**검사 대상·스크립트를 한 글자도 바꾸지 않고** 그 인터프리터로 돌렸다. 배선 결함은 §10-5 ⓑ.

⚠ **셸도 조건이다** — `bash` 가 macOS 기본 3.2 로 잡히면 `contract-lint` 는 `SPECS[@]: unbound variable`
(`gates/tools/contract-lint.sh:51` 의 `mapfile` 은 bash 4+ 내장), `rls-coverage` 는 `netarg[@]: unbound variable`
(`gates/tools/_pg.sh:181`)로 **선다.** 검사 내용과 무관한 셸 버전 의존이고, 게이트는 그것을 각각
red(판정)·red(준비)로 낸다. 위 표의 값은 **bash 5 가 잡히는 PATH** 에서 잰 것이다. §10-5 ⓓ.

**pytest(직접 실행 · `service-tests` 갈음)** — 로그 `dev-package/reports/dl-1/rebase2/pytest-full.txt`
```
1 failed, 1145 passed, 6 deselected in 356.32s (0:05:56)
```
- 실패 1건 = `tests/test_ownership_snapshot_publisher.py::test_actual_db는_두_lab전수_readonly이고_app_role은_거절한다`.
  축자 `sqlalchemy.exc.OperationalError: (psycopg.OperationalError) connection failed: connection to server at
  "127.0.0.1", port 5432 failed: FATAL:  password authentication failed for user "postgres"`. §10-5 ⓒ.
- `tests/test_dataset_deletion.py` 단독 **23 passed**(C7 신설 1 포함).
- ⑪-b `지정 공개` 원복 시험은 **`0021_rc7_access_state_gap` 이 적용된 시험 DB** 에서 재측정해 green
  (`test_a_designated_dataset_is_restored_with_its_grant_intact` · 로그 `…/rebase2/pytest-11b.txt`).
  `0021` 은 **스키마를 한 글자도 안 바꾸는 데이터 마이그레이션**이라(파일 머리말 축자) 원복 의미론이 달라질 자리가 없고,
  실측도 그대로다.

**vitest** = 105 files / 1270 tests passed(종전 기준 73 files / 1013 → main 증가분 ＋ 레인 17).

### 10-5. 이 회차가 발견한 것 (레인이 고치지 않았다 · 「기존」이라 적지 않는다)

- **ⓐ `frontend-test` 가 같은 트리에서 red 2 · green 2 로 갈린다**(같은 커밋 · 같은 node · 같은 명령 4회).
  갈리는 것은 늘 한 건 — `test/account-admin.test.tsx > 첫 로그인 사용자가 새 비밀번호를 제출하면 새 토큰을
  저장하고 연구실로 이동한다` · 축자 `Expected element to have text content: /lab  Received: /account-admin`.
  단독 실행하면 그 파일 4건 전부 통과한다(실측).
  **원인(코드로 특정)** — 시험이 `await waitFor(()=>expect(fetch).toHaveBeenCalled())` **하나만 기다리고**
  그 다음 줄에서 이동 결과를 잰다(`frontend/test/account-admin.test.tsx:20`·`:24`). 제품 코드는
  `await api.PUT('/me/password')` **응답이 온 뒤에** `setSession` ＋ `navigate('/lab',{replace:true})` 를 한다
  (`frontend/src/auth/PasswordChangePage.tsx:19`·`:25`·`:26`). ⟹ 「fetch 가 불렸다」는 「이동이 끝났다」보다
  **항상 이르다.** 호스트가 한가하면 마이크로태스크가 먼저 비워져 통과하고, 부하가 걸리면 라우터 재렌더가
  단언 뒤로 밀려 red 가 된다. **제품 결함이 아니라 시험의 경주다.**
  **어느 검사에 걸리는가** — `frontend-test` 게이트와 CI `frontend` 잡이 본다. 다만 **판정이 재현되지 않는다** —
  같은 트리에 green 과 red 가 둘 다 서므로 이 파일에 대한 그 게이트의 판정은 근거가 되지 못한다.
  레인 기여분 = 0(`account-admin`·로그인 경로 무접촉 · 변경 27파일에 없다).
  고치는 자리 = 마지막 단언을 `await waitFor(...)` 안으로 옮기는 **한 줄**(`:24`). 이 레인은 고치지 않았다 —
  DL-1 과 무관한 main 쪽 시험 파일이라 범위 확대다(`CLAUDE.md §5`). **후속 항목 · 권고 = 한 줄 회차로 별도.**
- **ⓑ `work-item-consistency` 가 인터프리터에 PyYAML 이 없으면 `red(판정)` 을 낸다.** 이것은 **준비 실패**인데
  판정 red 로 나온다(`exit 78`·`::gate-readiness-failure::` 아님). `gate-pg-reach` 와 같은 계열이다 —
  레인이 「코드 결함」으로 오독하는 자리. **어느 검사에 걸리는가** — 게이트 자신이 red 를 내지만 **종류를 틀리게 낸다.**
  고치는 자리 = `gates/run.sh` 의 그 줄이 `gates/tools/_venv.sh` 의 `GATE_PY` 를 쓰게 하거나, 없을 때 exit 78 로 가르기.
  **후속 항목.**
- **ⓓ 게이트 둘이 bash 4+ 내장을 쓰면서 셸 버전을 검사하지 않는다.** `contract-lint`(`mapfile` ·
  `gates/tools/contract-lint.sh:51`)와 `_pg.sh`(`${netarg[@]}` · `:181`)는 macOS 기본 `bash` 3.2 에서
  `unbound variable` 로 죽는다. `#!/usr/bin/env bash` 라 **PATH 가 무엇을 주느냐에 따라 판정이 갈린다.**
  **어느 검사에 걸리는가** — 게이트 자신이 red 를 내지만 **원인을 셸 버전이라고 말하지 않는다**(ⓑ 와 같은 계열).
  고치는 자리 = 두 스크립트 머리에 `BASH_VERSINFO` 확인 ＋ 미달 시 exit 78, 또는 `mapfile`/배열 기본값
  회피. **후속 항목.**
- **ⓒ `test_ownership_snapshot_publisher.py` 가 `postgres` 슈퍼유저에 `password=None` 으로 접속한다**
  (`:66` 축자 `owner_url=make_url(app_db_url).set(username="postgres",password=None)`). 이 맥의 로컬 컨테이너는
  공개 포트로 들어오는 접속을 `scram-sha-256` 으로 받는다(`pg_hba.conf` 의 `trust` 줄은 컨테이너 내부
  `127.0.0.1/32` 전용이고, 호스트에서 오는 접속은 마지막 `host all all all scram-sha-256` 에 걸린다).
  ⟹ **접속 단계에서 죽는다 — 제품 코드가 한 줄도 돌지 않는다.** 이 시험 파일은 main 쪽 `TL-2`(`d56428d`)가 넣었고
  이 레인은 건드리지 않았다(변경 27파일에 없다). **어느 검사에 걸리는가** — `service-tests-core-api` 게이트와
  CI `service-tests` 잡. 다만 **「`postgres` 가 암호 없이 붙을 수 있어야 한다」는 전제가 어디에도 선언돼 있지 않고**,
  시험에 준비/판정 갈래도 없어 **호스트에 따라 판정 red 로 뜬다.** 고치는 자리 = 그 전제를 시험 환경 선언으로
  올리거나(`~/.colab-v2-test.env` 에 소유자 URL 한 줄) 시험이 준비 실패를 가르게 하기. **후속 항목 · 이 레인 범위 밖**
  (지시문 「시험 DB 권한 오류는 원인 적고 정지」).

### 10-6. 열린 것 (§8·§9-7 에서 달라진 것만)

- Ted 판정 ⓐ 회수 · `〈N〉` 발급(병합 직전 · `PLAN-SoT` 무접촉) · CI `service-tests` 1회 green · 병합 ·
  dev 배포 · 완료 정의 ⑻ — **그대로 열려 있다.**
- 완료 정의 ⑻ 의 `deploy_doctor` 항목 수는 **15** 다(`CLAUDE.md §0` · R-D `WU-D3` 가 ⑮ 를 더했다) ／ 종전 표기 14.
- 감사 스냅샷(C7)이 완료 정의에 한 줄 는다 — dev 실삭제 때 `d3_operator_audit` 에 그 데이터셋 행 1건.
