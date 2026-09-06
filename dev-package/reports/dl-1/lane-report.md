# `DL-1` 레인 보고 — 데이터셋 삭제(묘비)

／ 브랜치 `lane-dl1-dataset-delete` · 기준 `origin/main` = `27733ba`
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
