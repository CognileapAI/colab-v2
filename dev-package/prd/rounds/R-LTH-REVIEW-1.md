# R-LTH-REVIEW-1 — 이태헌 1차 검증 반영 실행 계획

> spec: [2026-09-13-lth-review-1.md](../specs/2026-09-13-lth-review-1.md)

- 실행자 = 스킬 `executing-plans`. 이 파일이 실행 계획의 정본이고 레인은 이 파일 ＋ spec 해당 절만 읽는다.
- 쓰기 주체 = **한 사본당 하나**. 레인은 자기 워크트리만 편집한다.
- 통합 브랜치 = `integration/r-lth-review-260913`(기점 = `main` tip) · 레인 브랜치 = `lane/lth-*`.
- 판정 정본 = `dev-package/reports/issues/2026-09-13-ted-decisions.md` 10건(Ted · 2026-09-13 · 확인 문장 「전부 권고대로 하자. 이걸로 스펙이랑 계획잡아보자」).
- 입력 intent 6건(승인 2026-09-13) = `dev-package/intent/2026-09-13-lth-{shell-header,account-members,a11y-empty-states,search-scope,verified-chip,processing-level-mismatch}.md`.
- 조사 정본 = `dev-package/reports/issues/2026-09-13-lth-review-1-SUMMARY.md` §3(즉시 착수 11) · §4(판정 카드 10) · §5(기획자 회신 2).
- 레인은 `03-HANDOFF.md`·`PLAN-SoT.md`·`work-items.yaml` 을 열지 않는다.

## Goal

- 기획자 이태헌 1차 검증 16항목(`D-1`~`D-7` · `I-1`~`I-9`)을 기존 화면·기존 흐름 위에서 닫는다.
- 사용자 기준 결과 7 = ⑴ 상단에서 누를 수 있는 것은 전부 동작이 있다 ⑵ 계정 관리와 구성원 표가 같은 사람을 같게 말한다 ⑶ 키보드만으로 프로젝트 카드가 열린다 ⑷ 빈 표가 다음 행동을 말한다 ⑸ 승인 칸 글자가 한 표기다 ⑹ 가공 단계가 계산값을 기본으로 서고 갈리면 근거를 말한다 ⑺ 검색 범위 줄이 실제 조회 범위를 말한다.
- 범위 밖(명시) = 연구실 고르개 · 계정 드롭다운 메뉴 · 가공 단계 사유 입력 절차 ＋ 저장 칸 · 행 전체 클릭 패턴 표 3자리 · 승인 상태 3값 · 접근성 게이트 신설 · 검색 범위 고르개 · 「할 일 함」 표기 변경 · 대표 제목 규약의 나머지 화면 집행.

## Architecture

- 변경 레이어 = D1(계정 상태 투영) · D3(검색 분모 스코프 · 목록 표식) · frontend 셸·화면.
- 계약 = **additive 1건**(`contracts/seams/fe-core.yaml` 앵커 `LabMember:` 에 선택 열쇠 `accountStatus`) ＋ 생성물 재생성. 계약 파괴 0 · `required` 무변.
- 마이그레이션 = **0건**. 계정 상태는 조회 시점 D1 투영이고 `d1_account` 에 상태 열을 신설하지 않는다.
- 경계 = Port 신설 0~1(상태 투영) · `core-api` 에 geo 라이브러리 0 · D10 → D4 쓰기 0 · 연구실 경계 주입 규칙 무변.
- ⚠ `[미확인]` = 상태 투영에 롤 권한 한 칸이 필요한지. 해소 = `kernel/db_credentials.py` 현 조회가 쓰는 롤과 `GET /lab/members` 의 `scoped_db` 롤 대조 ＋ `ops/account-admin-role.sql` 적용 상태 확인(선례 실패 `PLAN-SoT` 앵커 `〈384〉` ⑨ⓐ). Task 7 은 이 대조를 먼저 하고 결과를 보고에 적는다.

## Tech Stack

- frontend = React ＋ TypeScript · 시험 Vitest(jsdom · `frontend/test`) · 타입 검사 게이트 `frontend-typecheck`.
- core-api = FastAPI ＋ SQLAlchemy · 시험 pytest(`services/core-api/tests` · 일회용 Postgres ＋ RLS).
- 계약·생성물 = `contracts/seams/fe-core.yaml` → `frontend/src/api/generated/*`(재생성물 · 손수정 금지).
- 계측 = jsdom 은 레이아웃을 계산하지 않는다. 크기·초점 링 주장은 **CSS 원문 계측**(주석 제거 후 · 존재 단언)으로 가른다(`CLAUDE.md §5-b` 오탐 3건).

## Spec

- 해법 개요 = spec §2 · 코드 실측 앵커 = §4 · 구현 결정 ㉮~㉶ = §6 · 레인 분할 = §7 · 시험 결정 = §8 · 완료 정의 = §9.
- 우선순위 = **이 라운드 파일 > 판정 정본 > spec.** spec 과 이 파일이 갈리면 이 파일을 따르고 갈린 자리를 최종 메시지에 열거한다.

## 상태

- **미착수 · 2026-09-13 계획 확정.** 착수 = 통합 브랜치 생성 뒤 Task 1.

## 공통 제약

- 스폰 = `Agent(isolation: "worktree")` · 에이전트 `lane-worker`. 손으로 만든 형제 워크트리를 쓰지 않는다(`colab-rules §2-3`).
- 첫 줄 = `git checkout -B lane/lth-<이름> origin/integration/r-lth-review-260913`. 이어서 `git rev-parse --short HEAD` 로 스폰 지시문의 기대 HEAD 를 대조하고, 어긋나면 구현하지 말고 정지·보고한다.
- 복귀 = 레인 브랜치를 통합 브랜치 위로 **rebase ＋ ff** 한 줄. 통합 → `main` 도 ff-only 한 줄(`docs/BRANCHING.md` 규칙 3·4). 병합은 오케스트레이터만 한다.
- **한 레인 = 작업 하나.** 리베이스 ＋ 조건 수정 ＋ 구현 ＋ 전수를 한 지시문에 싣지 않는다(`CLAUDE.md §5-b` — 200턴 한도 2회 초과 사례).
- 순서 = 항목마다 ① red 시험 먼저(실패 로그 한 줄 인용) → ② 최소 구현 → ③ 단독 게이트. green 으로 시작한 시험은 오라클이 아니다.
- 반복 검증은 **단독 게이트**로 좁힌다. 전수(`bash gates/run.sh all`)는 **병합 직전 1회** · 레인은 돌리지 않는다(`colab-rules §3-1`).
- 전수 실행 전 `set -a; . ~/.colab-v2-test.env; set +a` · 병렬도는 실행 레인 0건일 때 `-j 4`, 레인이 돌고 있으면 `-j 2`(`colab-rules §3-4`·§9 · 호스트 메모리 12GB).
- 워크트리 게이트 환경 = `frontend` 는 `npm ci`, `core-api` 는 `uv venv .venv` ＋ `uv pip install -r requirements.txt -r requirements-dev.txt` ＋ `uv pip install -e .`(`colab-rules §2-4`).
- 게이트 실행 = `COLAB_GATE_REPORT_DIR=dev-package/reports/lth-review-260913/<레인> bash gates/run.sh <게이트>`. 배출처를 빠뜨리면 `gate-summary.json` 이 서지 않는다.
- red 판독 = 판정 red / 준비 red(exit 78 · `::gate-readiness-failure::`)를 갈라 적는다. 갈라 적지 않은 계수는 보고에 쓰지 않는다.
- **「main 과 동일」을 수용 근거로 쓰지 않는다.** 기존 결함을 발견하면 그 결함이 어느 검사(게이트 · Dockerfile · 배포 스크립트 · 없음)에 걸리는지 적고 후속 항목으로 올린다(`colab-rules §3-3`).
- 게이트 우회·비활성화 금지 · green 을 만들려고 검사 대상 축소 금지 · 준비 red 를 green 으로 계수 금지.
- 계약 변경은 `contracts/` 를 고치고 생성물을 **재생성**한다. 생성물 손수정 0(`CLAUDE.md §3` 규칙 7).
- 새 `.sh` 를 만들면 `git update-index --chmod=+x <파일>` 후 커밋한다(`colab-rules §4-3`).
- 문서·보고에 절대경로를 적지 않는다. 행 번호 대신 앵커 문자열(함수명 · 상수명 · `data-testid`)을 쓴다.
- 원장·대장·HANDOFF 편집 0 · `〈N〉` 하드코딩 0 · `main` push 0 · 전수 실행 0 — 전부 Task 8 몫이다.

### Ted 확정 대기 문면 2건

- 승인 칸 한국어 값 = **제안값 「승인 전」**(선례 1자리 = `frontend/src/components/catalog/columns.ts` 앵커 `if (column === 'Verified')`).
- 가공 단계 불일치 사유 한 줄 = **spec §6 ㉲ 제안 축자**(두 값 ＋ 각 값의 근거).
- 취급 = 레인은 **제안값으로 구현**하고 문면 상수 바로 위에 `// Ted 문면 확정 대기 · R-LTH-REVIEW-1` 주석을 붙인다. Ted 가 바꾸면 **문면만 교체**하고 구조·시험 구성은 유지한다. 레인이 PRD 문면표를 고치지 않는다.

## 실행 순서

| 단계 | 작업 | 주체 | 의존 | 완료 근거 |
|---|---|---|---|---|
| 0 | 통합 브랜치 생성 · 레인 절단 고정 | 오케스트레이터 | intent 6건 승인 | 이 파일 |
| 1 | Task 1~7 착수(직렬 기본) | `lane-worker` | 0 | 각 레인 최종 메시지 |
| 2 | 단독 게이트 green 회수 | 레인 7 | 1 | `gate-summary.json` 3계수 |
| 3 | 병합 rebase ＋ ff (Task 1→2→3→4→5→6→7 순) | 오케스트레이터 | 2 | 통합 브랜치 로그 |
| 4 | 전수 게이트 1회 `-j 4` | 오케스트레이터 또는 `gate-runner` | 3 ＋ 실행 레인 0건 | 전수 요약줄 |
| 5 | 원장·대장·HANDOFF 기재 | 오케스트레이터 | 4 | 커밋 |
| 6 | `main` ff → dev 배포 ＋ `deploy_doctor` 15/15 한 번의 실행 ＋ 기획자 회신 2건 | 오케스트레이터 | 5 | 배포 로그 |

- **실행은 직렬 기본**(`colab-rules §3-1` 「한 시점에 하나」). 병렬은 **파일 교집합 0** 인 쌍에만 허용하고 그때 게이트는 `-j 2`.
- **Task 4 → Task 5 는 직렬 고정**(`ProjectDatasetTable.tsx`·`project.css` 공유). 그 밖 쌍은 교집합 0이다.

## 작업 표

| 작업 | 산출물 | 선행 | 접촉 파일 | 단독 게이트 | 판정 카드/intent |
|---|---|---|---|---|---|
| **Task 1 · L2 계정 관리** | 본문 영역 1개 · 표 좌우 이동 안내 ＋ 키보드 초점 · 초기 비밀번호 자동완성 · 자기 줄 비활성화 가드 | 없음 | `frontend/src/routes/AccountAdminPage.tsx` · `frontend/src/auth/login.css` · `frontend/test/account-admin.test.tsx` | `frontend-test` 2회 ＋ `frontend-typecheck` 1회 | SUMMARY §3 3건(`D-3`·`I-4`·`I-8`) ＋ 카드 ⑤ ⓐ(`I-5`) · `…-lth-account-members.md` |
| **Task 2 · L7 검색 범위** | 분모를 결과와 같은 스코프에서 계산 · 범위 줄이 유효 연구실 집합을 말함 | 없음 | `services/core-api/src/colab_core/app/routes/catalog.py` · `frontend/src/routes/SearchResultsPage.tsx` · `services/core-api/tests/test_search_scope.py`(신설) · `frontend/test/search-scope-line-20260913.test.tsx`(신설) | `service-tests-core-api` ＋ `frontend-test` | 카드 ⑧ ⓐ(`I-2`) · `…-lth-search-scope.md` |
| **Task 3 · L6 가공 단계** | 기본값 = 계산값 추종 · 사유 한 줄 공용 함수 · 상세 편집 칸 | 없음 | `upload/RegisterArea.tsx` · `upload/UploadModal.tsx` · `lineage/LineageStep.tsx` · `detail/DetailHeader.tsx` · `common/processingLevel.ts`(신설) · `detail/editFields.ts` · `detail/DatasetEditForm.tsx` · `useDatasetEdit.ts` · `routes/DatasetDetailPage.tsx` | `frontend-test` 2회 ＋ `frontend-typecheck` 1회 | 카드 ⑩ ⓐ(`I-1`) · `…-lth-processing-level-mismatch.md` |
| **Task 4 · L4 카드 ＋ 빈 표** | 프로젝트 카드 링크화 ＋ 초점 표시 · 0행 문면 ＋ 0행 안내 숨김 | 없음 | `project/ProjectCards.tsx` · `project/project.css` · `project/ProjectDatasetTable.tsx`(0행 분기만) | `frontend-test` 2회 ＋ `frontend-typecheck` 1회 | 카드 ⑥ ⓐ(`D-2`) ＋ SUMMARY §3(`I-6`) · `…-lth-a11y-empty-states.md` |
| **Task 5 · L5 승인 칸 ＋ 목록 표식** | 승인 칸 한국어 표기 2자리 · 목록 가공 단계 불일치 표식 · 시험 4건 정정 | **Task 4** | `catalog/CatalogTable.tsx` · `catalog/catalog.css` · `project/ProjectDatasetTable.tsx`(승인 칸) · `project/project.css` | `frontend-test` 2회 ＋ `frontend-typecheck` 1회 | 카드 ⑨ ⓐ(`I-3`) ＋ 카드 ⑩ 목록 표식 · `…-lth-verified-chip.md` · `…-lth-processing-level-mismatch.md` |
| **Task 6 · L1 상단 셸** | 연구실 표기 칩화 · 사용자 이름 `▾` 제거 · 휴대전화 상단 「더보기」 목록 | 없음 | `shell/Gnb.tsx` · `shell/shell.css` · `shell/design-system.css` · `upload/UploadEntry.tsx` | `frontend-test` 2회 ＋ `frontend-typecheck` 1회 | 카드 ① ⓐ · ② ⓐ · ③ ⓒ(`D-1`·`D-5`·`I-9`) · `…-lth-shell-header.md` |
| **Task 7 · L3 연구실 설정 ＋ 구성원** | h1·h2 단계 · 비활성 상태 칩 ＋ 행 잠금 · 계약 열쇠 1개 ＋ 생성물 · 서버 투영 ＋ 저장 검사 · 규약 한 줄 | 없음(가장 큼 · 마지막) | `routes/LabSettingsPage.tsx` · `lab/LabInfoPanel.tsx` · `members/MemberPermissionGrid.tsx` · `members/permissions.ts` · `members/port.ts` · `contracts/seams/fe-core.yaml` · `frontend/src/api/generated/*`(재생성) · `routes/members.py` · `domains/d1_identity.py` · `frontend/README.md` | `frontend-test` · `frontend-typecheck` · `contract-lint` · `contract-breaking` · `generated-up-to-date` · `seam-consistency` · `service-tests-core-api` | 카드 ④ ⓐ-1 · 카드 ⑦(ⓑ 규약 ＋ ⓐ 집행) · `…-lth-account-members.md` · `…-lth-a11y-empty-states.md` |
| **Task 8 · 통합 · 전수 · dev 배포** | 통합 ff · 전수 1회 · 원장·대장·HANDOFF · dev 배포 ＋ `deploy_doctor` 15/15 · 기획자 회신 2건 | Task 1~7 | `dev-package/**` 문서 · `CLAUDE.md`(필요 시) | `all` 1회 ＋ `work-item-consistency` | 판정 10건 전부 ＋ 개정 표시 2건 |

- 파일 소유 고정 = `shell/design-system.css` 는 Task 6 만 · `catalog/CatalogTable.tsx` 는 Task 5 만 · `routes/catalog.py` 는 Task 2 만 건드린다.

---

### Task 1: 계정 관리 화면 4건 (`lane/lth-account-admin`)

- 목적(사용자가 보는 것) = 계정 관리 화면에서 ⑴ 본문 영역이 셸 것 하나다 ⑵ 1100px 이하에서 표 위에 좌우 이동 안내가 보이고 표 래퍼가 키보드 초점을 받는다 ⑶ 초기 비밀번호 칸을 비밀번호 관리 도구가 새 비밀번호로 인식한다 ⑷ 자기 줄의 「비활성화」가 처음부터 눌리지 않고 그 이유가 화면에 적혀 있다.
- 실패 시험(spec §8-2 5~8 · `frontend/test/account-admin.test.tsx` **확장**) — ⑸ 화면 서브트리에 `main` 0건(현행 1~2건) ⑹ 표 래퍼에 `role="region"` ＋ `tabIndex=0` ＋ 안내 `<p>` 존재(현행 0건) ⑺ `name="initialPassword"` 의 `autocomplete` = `new-password`(현행 속성 없음) ⑻ 자기 줄 비활성화 버튼 `disabled` = true ＋ 이유 문면 조회(현행 `disabled={rowBusy}`). 네 건이 red 임을 먼저 보이고 실패 로그 한 줄을 인용한다.
- 최소 구현 = `AccountAdminPage.tsx` 앵커 `<main className="login">` ＋ 조기 반환 앵커 `if (!operator) return <main><h1>계정 관리</h1>` 를 비`main` 요소로 · 앵커 `<div className="account-table-scroll">` 를 공용 패턴(`CatalogTable.tsx` 앵커 `<p className="table-scroll-hint">` ＋ 앵커 `<div className="tblwrap" data-scroll="both" role="region" … tabIndex={0}>`)으로 교체 · 앵커 `name="initialPassword"` 에 `autoComplete="new-password"` 1개 · 비활성화 버튼 앵커 `disabled={rowBusy}` 를 같은 파일 선례 앵커 `disabled={rowBusy || row.accountId === account?.accountId}` 와 같은 꼴로 ＋ 이유 문면.
- green-by-skip 방지 = 자기 줄 단언에 **대조군**(남의 줄은 눌린다)을 함께 둔다 · `frontend-test` 요약줄 수집 건수를 착수 전후로 기록하고 줄어들면 red(§8-6 ⑶⑸).
- 단독 게이트 = `bash gates/run.sh frontend-test`(연속 2회 green) · `bash gates/run.sh frontend-typecheck`(1회).
- 종료 보고 = `WORKTREE=` · `BRANCH=` · 게이트별 3계수(green / red(판정) / red(준비)) ＋ 요약줄 축자 · 접촉 파일 목록 · red 선실측 인용 · 범위 밖 접촉 0 확인.

### Task 2: 검색 범위 정합 (`lane/lth-search-scope`)

- 목적 = 검색 결과 머리줄이 **실제로 뒤진 범위**를 말한다. 관리자는 「전체 연구실 (읽기 전용)」 ＋ 전 연구실 건수, 일반 구성원은 소속 연구실 이름 ＋ 소속 연구실 건수. 0건에도 범위 줄이 먼저 선다.
- 실패 시험(spec §8-2 23~25) — `services/core-api/tests/test_search_scope.py` **신설**: 연구실 2개 ＋ 각 데이터셋 1건 이상에서 운영자 `searchedCount` = 전 연구실 건수이고 결과와 같은 스코프 · 일반 구성원은 소속 연구실 건수 · 운영자 `labName` = 「전체 연구실 (읽기 전용)」 · `labId` 는 `Ulid` 로 존재. `frontend/test/search-scope-line-20260913.test.tsx` **신설**: 범위 줄이 응답 `labName`·`searchedCount` 를 그대로 말한다.
- 최소 구현 = `routes/catalog.py` 앵커 `searched_count = d3_catalog.count_datasets(db)` 계산을 앵커 `with read_only_scope(` 블록 **안(또는 뒤)** 으로 옮긴다(spec §6 ㉰ 갈래 ㈎) · `isDataQuery` 가 거짓인 갈래에서도 값이 채워지도록 순서를 정리 · 앵커 `"scope": {"labId"` 의 `labName` 조립을 유효 연구실 집합 표기로. `labId` 는 필수 `Ulid` 로 남기고 `scopeKind` 류 열쇠를 신설하지 않는다(계약 무변).
- green-by-skip 방지 = **연구실 2개 ＋ 양쪽에 데이터셋**을 심어 두 스코프가 우연히 같아지는 통과를 막는다(§8-6 ⑵). 한 연구실만 심은 시험은 오라클이 아니다.
- 단독 게이트 = `bash gates/run.sh service-tests-core-api` · `bash gates/run.sh frontend-test`.
- 종료 보고 = Task 1 과 같은 항목 ＋ 「`labId` 의미 불일치를 스펙 명시로 남겼다」 1줄.

### Task 3: 가공 단계 기본값 ＋ 사유 ＋ 편집 칸 (`lane/lth-processing-level`)

- 목적 = 등록 흐름에서 ⑴ 부모를 연결하면 가공 단계 기본값이 **계산값**으로 서고 ⑵ 계산값과 다른 값을 고르면 두 값 ＋ **각 값의 근거** 한 줄이 뜨며 저장은 계속 성공하고 ⑶ 데이터셋 상세 편집에서 가공 단계를 고쳐 저장하면 표시값이 바뀐다.
- 실패 시험(spec §8-2 19~22) — `frontend/test/processing-level-default-20260913.test.tsx` **신설**(부모 1건 Lv1 → 기본값이 계산값으로 선다 · 부모 0건 → `Lv2` 유지 ＋ Lv0 경고 0건 · 불일치 상태 제출 성공 회귀) · `frontend/test/lv-mismatch-reason-20260913.test.tsx` **신설**(상세·등록 두 자리 문장이 동일하고 근거 구절을 포함) · `frontend/test/detail-edit.test.tsx` **확장**(편집 칸에 가공 단계 ＋ 저장 본문에 `processingLevelUserSet`).
- 최소 구현 = `RegisterArea.tsx` 앵커 `data-testid="reg-level"` 의 기본값을 `LineageStep.tsx` 앵커 `const derivedPreview =` 규칙으로 추종(부모 Lv 를 하나라도 모르면 `Lv2` 유지 · 사람이 한 번 고른 뒤에는 추종 중단) · 사유 문장 생성 함수 1개를 `components/common/processingLevel.ts` 에 두고 앵커 `data-testid="dh-lv-mismatch"`·`data-testid="lin-lv-mismatch"` 두 자리가 같은 함수를 부른다 · `detail/editFields.ts` 에 가공 단계 칸 1개(값 집합 `Lv0`~`Lv3`) ＋ 폼·훅이 기존 계약 열쇠 `DatasetUpdate.processingLevelUserSet` 로 전송.
- 차단 0건 · 사유 입력 요구 0건 · 「경고만」 유지(판정 축자). 파생값·사유를 테이블에 저장하지 않는다.
- green-by-skip 방지 = 불일치 `false` **대조군**과 부모 0건 대조군을 함께 둔다 · 불일치 상태 제출 성공 회귀 단언을 같은 파일에 둔다(§8-6 ⑶).
- 단독 게이트 = `bash gates/run.sh frontend-test`(연속 2회) · `bash gates/run.sh frontend-typecheck`(1회).
- 종료 보고 = Task 1 과 같은 항목 ＋ 문면 확정 대기 주석 자리 1줄.

### Task 4: 프로젝트 카드 ＋ 빈 표 (`lane/lth-cards-empty`)

- 목적 = ⑴ 프로젝트 카드가 Tab 초점을 받고 Enter 로 상세가 열리며 초점 표시가 보인다 ⑵ 데이터셋 0건 프로젝트에서 표 대신 「연결된 데이터셋이 없어요. 데이터셋 상세에서 이 프로젝트를 고르면 여기에 보여요.」 가 보이고 0행에 좌우 이동 안내가 없다.
- 실패 시험(spec §8-2 13~15) — `frontend/test/project-cards-a11y-20260913.test.tsx` **신설**(카드가 링크 역할 ＋ 키보드 활성으로 `onOpen` 1회 · `project.css` 원문에 `.pcard:focus-visible` 규칙 존재) · `frontend/test/project-detail-empty-20260913.test.tsx` **신설**(`datasets=[]` 에서 문면 조회 ＋ `table-scroll-hint` 0건 · `datasets=[1건]` 대조군에서 안내 출력).
- 최소 구현 = `ProjectCards.tsx` 앵커 `<article` 를 링크 역할로(카드 안에 두 번째 클릭 대상을 만들지 않는다 — 같은 파일 앵커 `data-testid="card-cta"` 주석 규칙 유지) · `project.css` 의 `.pcard` 에 `:focus-visible` 규칙 1건 · `ProjectDatasetTable.tsx` `<tbody>` 에 0행 `colSpan` 분기(선례 `CatalogTable.tsx` 앵커 `<td colSpan={9} className="empty">`) ＋ 0행에서 안내·래퍼 감춤.
- 연결 방법 문장의 실제 경로 축자는 `[미확인]` — 레인이 화면에서 확인하고 문면을 그에 맞춘다.
- green-by-skip 방지 = 접근성 단언이 **현행 `<article onClick>` 픽스처에 대해 red** 임을 먼저 보인다(§8-6 ⑴) · 빈 상태에 1건 대조군을 둔다 · CSS 단언은 주석 제거 후 존재 단언.
- 표 3자리(`ProjectTable`·`CatalogTable`·`ProjectDatasetTable` 행 클릭)는 **범위 밖** — 손대지 않는다.
- 단독 게이트 = `bash gates/run.sh frontend-test`(연속 2회) · `bash gates/run.sh frontend-typecheck`(1회).
- 종료 보고 = Task 1 과 같은 항목 ＋ 「`ProjectDatasetTable.tsx` 접촉은 0행 분기뿐(승인 칸 미접촉)」 1줄.

### Task 5: 승인 칸 문면 ＋ 목록 불일치 표식 (`lane/lth-verified-chip`)

- 목적 = ⑴ 데이터셋 목록·프로젝트 상세 표의 승인 대기 칸 글자가 한 표기(제안값 「승인 전」)로 모이고 취소선·회색·꺼진 모양과 열 제목 `Verified` 는 그대로다 ⑵ 목록 가공 단계 칸이 불일치 행에 표식 ＋ 보조기기용 이름을 그린다.
- 선행 = **Task 4 병합 뒤 착수**(`ProjectDatasetTable.tsx`·`project.css` 공유).
- 실패 시험(spec §8-2 16~18) — `frontend/test/catalog.test.tsx` **정정**(승인 대기 칸 텍스트 = 제안값 ＋ 클래스 `verified--pending` 유지) · `frontend/test/qa-20260903.test.tsx` · `frontend/test/search-verified-20260903.test.tsx` **정정**(같은 칩 규칙 · 검색 카드에는 칩 부재 유지 회귀) · `frontend/test/catalog-level-mismatch-20260913.test.tsx` **신설**(`processingLevelMismatch=true` 행에 표식 ＋ 보조기기 이름 · `false` 행에 0건 대조군).
- 최소 구현 = `CatalogTable.tsx` 앵커 `className="verified verified--pending"` 의 글자만 교체(`data-testid`·`aria-disabled`·`title` 유지) · `ProjectDatasetTable.tsx` 앵커 `data-testid="dataset-verified"` 같은 교체 · `CatalogTable.tsx` 가공 단계 칸이 `row.processingLevelMismatch` 를 읽어 표식. **서버 무변**(열쇠가 이미 응답에 실린다).
- 손대지 않는 것 = `approval/VerifiedBadge.tsx` · `search/SearchHitCard.tsx`(두 파일의 반대 규칙은 의도된 것) · 열 제목 `Verified` · 프로젝트 상세 표·계보 노드의 `level_pair`.
- green-by-skip 방지 = 불일치 `false` 대조군 ＋ 검색 카드 칩 부재 회귀를 함께 둔다 · 수집 건수 전후 기록.
- 단독 게이트 = `bash gates/run.sh frontend-test`(연속 2회) · `bash gates/run.sh frontend-typecheck`(1회).
- 종료 보고 = Task 1 과 같은 항목 ＋ 「정정한 기존 시험 4건과 그 파일」 열거.

### Task 6: 상단 셸 3건 (`lane/lth-shell-header`)

- 목적 = ⑴ 「전체 연구실 (읽기 전용)」이 누를 수 없는 상태 표시로만 보이고 키보드 초점을 받지 않는다 ⑵ 사용자 이름 자리에 `▾` 가 없다 ⑶ 390px 에서 업로드·계정 관리·연구실 설정의 **이름이 글자로** 확인된다(「더보기」 목록).
- 실패 시험(spec §8-2 1~4) — `frontend/test/shell-lth-20260913.test.tsx` **신설**(`lab-switcher` 의 `tagName` ≠ `BUTTON` ＋ 비초점 · `gnb-avatar` 하위 `.cv` 텍스트 `▾` 0건 · 좁은 폭에서 더보기 목록에 세 이름이 글자로 조회) · `frontend/test/shell.test.tsx`·`recs-20260903.test.tsx`·`auth.test.tsx` **정정**(`lab-switcher`·`gnb-avatar` 참조가 새 요소로 성립).
- 최소 구현 = `Gnb.tsx` 앵커 `data-testid="lab-switcher"` 를 비대화형 칩으로(`aria-label` 문면은 유지) · 앵커 `<span className="cv" aria-hidden="true">▾</span>` 제거 · 더보기 목록 부품 1개 신설 ＋ `UploadEntry.tsx` 가 그 목록에 업로드 항목을 수용 · `shell.css`·`design-system.css` 의 `.labswitch`·`.avatar .cv`·반응형 규칙 정리.
- 유지 = 권한 없는 항목은 목록에 서지 않는다(기존 권한 분기 승계) · `shell.css` 앵커 `@media (max-width: 560px)` 의 「주 내비 라벨은 여기서도 지킨다」 규칙 · 휴대전화에서 아바타를 다시 보이게 하지 않는다.
- green-by-skip 방지 = 폭 조건 단언은 CSS 원문 계측(주석 제거 후 존재 단언)으로 세우고 DOM 단언과 분리한다 · 기존 3파일 정정 뒤 수집 건수가 줄지 않음을 확인.
- 단독 게이트 = `bash gates/run.sh frontend-test`(연속 2회) · `bash gates/run.sh frontend-typecheck`(1회).
- 종료 보고 = Task 1 과 같은 항목 ＋ 「실제 초점 링 확인은 사람 몫 · `[미확인]` 유지」 1줄.

### Task 7: 연구실 설정 제목 ＋ 비활성 구성원 (`lane/lth-lab-settings-members`)

- 목적 = ⑴ `/lab-settings` 의 대표 제목이 1단계에서 시작하고 탭 본체 제목이 2단계다(글자 크기 무변) ⑵ 계정 관리에서 「비활성」인 사람이 구성원 권한 표에서도 「비활성」으로 보이고 그 줄 권한 편집이 막히며 저장 요청도 거절된다.
- 선행 대조(구현 전) = 상태 투영 롤 `[미확인]` 해소 — `kernel/db_credentials.py` 현 조회 롤과 `GET /lab/members` 의 `scoped_db` 롤 대조 ＋ `ops/account-admin-role.sql` 적용 상태. 롤 권한 신설이 필요하다고 판정되면 **구현을 멈추고 보고**한다(경계 판정은 오케스트레이터 몫 · `CLAUDE.md §4`).
- 실패 시험(spec §8-2 9~12) — `frontend/test/lab-settings-headings-20260913.test.tsx` **신설**(화면에 `h1` 1개 「연구실 설정」 · 패널 제목 `h2` 2개 · 단계 누락 0 · CSS 원문에 패널 제목 크기 고정 선언 존재) · `frontend/test/members-inactive-20260913.test.tsx` **신설**(`accountStatus='inactive'` 행에 「비활성」 칩 ＋ 그 행 스위치 전부 `disabled` · 활성 행 대조군은 편집 가능) · `services/core-api/tests/test_lab_members.py` **확장**(비활성 계정 행의 `accountStatus='inactive'` ＋ `editablePermissions == []` · 그 계정 권한 저장 요청 400).
- 최소 구현 = `LabSettingsPage.tsx` 에 `h1` 1개 · `LabInfoPanel.tsx`·`MemberPermissionGrid.tsx` 의 `<h3>` → `<h2>` ＋ CSS 로 크기 고정 · `contracts/seams/fe-core.yaml` 앵커 `LabMember:` 에 선택 열쇠 `accountStatus: active|inactive`(`required` 미포함) ＋ 생성물 재생성 · `domains/d1_identity.py` 앵커 `_MEMBERS = text(` 경로에 상태 투영 · `routes/members.py` 앵커 `def _grid(`·`def _editable_permissions(` 가 비활성 행의 `editablePermissions` 를 빈 배열로 내리고 앵커 `def save_lab_member_permissions(` 에 상태 검사 1건 · 화면은 `permissions.ts` 앵커 `export function isEditable(` 의 「서버가 실어 준 배열만 읽는다」 규칙을 유지한 채 칩만 그린다 · `frontend/README.md` `## 규칙` 절에 대표 제목 규약 한 줄(화면당 `h1` 1개 · 탭 본체 `h2` · 그 아래 `h3` · 대화상자는 별도 계수).
- 마이그레이션 0건 · `d1_account` 에 상태 열 신설 0 · 집행 화면은 `/lab-settings` **한 화면**(`/lab` 등은 후속).
- green-by-skip 방지 = 활성 행 **대조군**을 둔다 · **서버 저장 검사**(저장 요청 400)를 함께 둔다 — 화면 `disabled` 만으로 통과시키지 않는다(§8-6 ⑹) · 생성물은 재생성으로만 바꾸고 `generated-up-to-date` 로 판정.
- 단독 게이트 = `bash gates/run.sh frontend-test` · `bash gates/run.sh frontend-typecheck` · `bash gates/run.sh contract-lint` · `bash gates/run.sh contract-breaking` · `bash gates/run.sh generated-up-to-date` · `bash gates/run.sh seam-consistency` · `bash gates/run.sh service-tests-core-api`.
- 종료 보고 = Task 1 과 같은 항목 ＋ 롤 `[미확인]` 해소 결과 ＋ 계약 변경 1건이 additive 임을 `contract-breaking` 계수로 제시.

### Task 8: 통합 · 전수 · dev 배포 (오케스트레이터)

- 통합 = 각 레인 브랜치를 `integration/r-lth-review-260913` 위로 rebase 한 뒤 **ff** 한 줄. 순서 = Task 1 → 2 → 3 → 4 → 5 → 6 → 7.
- 전수 = 통합 트리에서 **1회** `bash gates/run.sh all -j 4`(실행 레인 0건 확인 후 · 환경 source 선행). 3계수를 갈라 기록한다. 트리 해시가 같으면 `main` 에서 재실행하지 않는다(`colab-rules §3-2`).
- 원장 `dev-package/PLAN-SoT.md §9` 기재 — **`〈N〉` 은 병합 직전 재실측**(`dev-package/prd/tools/max-decision.sh` · 예약 금지 · `colab-rules §4-1`). 기재 대상 = ⑴ Ted 판정 10건 기록(등재문 = `dev-package/reports/issues/2026-09-13-ted-decisions.md`) ⑵ **개정 표시 2건** — 카드 ⑨ 가 개정하는 `PLAN-SoT` 앵커 `〈282〉-㉮`(승인 칸 글자 문안만 · 취소선·회색·열 제목 유지) · 카드 ⑩ 이 개정하는 `dev-package/prd/PRD-260905-적용전기획.md` 앵커 `미결-2 ⓐ`(기본 선택값만 · 「막지 않고 경고만」 유지) ＋ 반전 기재 자리 `PLAN-SoT §9 〈194〉`. 집행 방식 = 원문 유지 ＋ `⭑ ⟨개정 2026-09-13 · 〈N〉⟩` ／ 종전 표기 병기.
- 대장 `dev-package/work-items.yaml` = 이 회차 6항목을 `done` 으로 갱신(등재는 계획 확정 시점에 `open` 으로 선행) · **상태 변경은 대장을 먼저** 고치고 산문을 반영본으로 갱신.
- `dev-package/03-HANDOFF.md §1` = 해당 항목 상태 ＋ 상단 최종 갱신·현재 단계·다음 WU. 새 블로커는 `§4`.
- 게이트 `bash gates/run.sh work-item-consistency` 1회 green(대장·괄호 대조 ㈕).
- 마감 = `main` ff → dev 배포 green ＋ `deploy_doctor` **15/15 를 한 번의 실행으로**(`CLAUDE.md §0`). 재시도해 모은 15 는 15 가 아니고 부분 실행 둘을 합쳐 green 이라 하지 않는다. 태그는 `dev-YYYYMMDD-N`.
- 기획자 회신 2건(SUMMARY §5) = ⑴ 「할 일 함」은 오탈자가 아니라 정한 용어이므로 현 표기 유지 ⑵ 로그인 실패 시 이메일 삭제는 코드에서 재현되지 않으므로 관측 1건 요청(비밀번호 관리 도구를 끈 상태 포함). 작업 0.
- staging 은 리허설이다 — 완료 판정·배포 창 기록·사용자 확인을 staging 에서 하지 않는다(`CLAUDE.md §0`).

---

## 계획 자체 점검

### 16항목이 어디에 떨어지는가

| 항목 | 내용 | 떨어지는 자리 |
|---|---|---|
| `D-1` | 연구실 표기가 눌리는데 동작이 없다 | Task 6 |
| `D-2` | 프로젝트 카드가 키보드로 열리지 않는다 | Task 4 (표 3자리는 후속) |
| `D-3` | 계정 관리 본문 영역 중첩 | Task 1 |
| `D-4` | 비활성 계정이 구성원 표에서 현역으로 보인다 | Task 7 |
| `D-5` | 사용자 이름 `▾` 가 메뉴를 약속한다 | Task 6 |
| `D-6` | 화면 대표 제목 단계 | Task 7(`/lab-settings` 1화면 · 규약은 `frontend/README.md`) |
| `D-7` | 「할 일 함」 표기 | **작업 0** · Task 8 기획자 회신 |
| `I-1` | 가공 단계 안내·기본값·목록 표식·편집 칸 | Task 3 ＋ Task 5(목록 표식) · 사유 입력 절차는 후속 |
| `I-2` | 검색 범위 줄 불일치 | Task 2 |
| `I-3` | 승인 칸 표기 | Task 5 |
| `I-4` | 계정 표 좌우 이동 안내 | Task 1 |
| `I-5` | 본인 비활성화 가드 | Task 1(화면 가드 · 계정명 재입력은 후속) |
| `I-6` | 빈 소속 데이터셋 표 문면 | Task 4 |
| `I-7` | 로그인 실패 후 이메일 보존 | **작업 0** · Task 8 관측 요청(`[미확인]`) |
| `I-8` | 초기 비밀번호 자동완성 | Task 1 |
| `I-9` | 휴대전화 상단 기능 이름 | Task 6 |

- 계수 기준 = 피드백 원문 색인 1건 = 1항목(결함 7 ＋ 개선 9 = 16). 구현 착수 14 · 작업 0 2건(`D-7`·`I-7`).

### 이번 회차에 **들어가지 않는** 후속 항목 후보 (판정 정본 「후속 항목 후보」 8건)

- 사유 입력 ＋ 한 번 더 확인 절차(사유 저장 칸 ＋ 마이그레이션 1건 · **L**) — 카드 ⑩ ⓑ.
- 행 전체를 누르는 패턴 표 3자리(`ProjectTable`·`CatalogTable`·`ProjectDatasetTable` · **M**) — 카드 ⑥.
- 접근성 검사 게이트 신설 — 카드 ⑦ ⓒ. ⚠ 검사 부재 자체가 결함이라는 규칙(`colab-rules §3-3`) 대상이므로 **후보로 기재**하고 이번 회차에 신설하지 않는다.
- 연구실 고르개(읽기 op 의 연구실 인자 ＋ 계약 판정 · **L**) — 카드 ① ⓑ · ⑧ ⓑ.
- 상단 사용자 메뉴·모바일 더보기 메뉴 부품(**M**) — 카드 ② ⓑ · ③ ⓒ.
- 승인 상태 3값(목록 계약 열쇠 1개 ＋ 묶음 질의 · **M**) — 카드 ⑨ ⓑ.
- 본인 비활성화 확장(계정명 재입력 ＋ 활성 관리자 셈 · **M**) — 카드 ⑤ ⓑ.
- 전 화면 대표 제목 규약 적용 잔여분(화면 10+ · **M**) — 카드 ⑦ ⓑ.
- 그 밖 = 계정 관리 화면을 공용 디자인 시스템으로 옮기는 재구성 · 계정 표 이메일 열 고정 ＋ 모바일 카드 목록 · `accounts.py` 「SQL 수동」 주석 정정 · 프로젝트 표·계보 노드의 `level_pair` → `level_view` 확장.

### 판정 정본의 `[불일치]` 2건 처리

- 카드 ⑥ 대 `…-lth-a11y-empty-states.md` Q1b — 이 회차는 **카드 ⓐ**(카드 한 자리)로 집행하고 표 3자리는 후속으로 둔다. 근거 = 판정 정본이 카드 표의 선택 열을 결정값으로 고정한다.
- 카드 ③ 대 `…-lth-shell-header.md` 미해결 질문 — 이 회차는 **더보기 목록을 신설**(카드 ⓒ)하고 `▾` 제거를 같은 레인에 묶는다(Task 6). 갈린 것은 집행 회차뿐이므로 카드를 따른다.
- 두 처리는 Task 8 원장 기재에 한 줄씩 남긴다.

### 남은 위험

- 상태 투영 롤 권한 `[미확인]` — Task 7 선행 대조에서 닫는다. 열리지 않으면 Task 7 의 구성원 절반이 정지하고 제목 절반만 남는다.
- 실제 초점 링·390px 실화면은 jsdom 으로 재지 않는다 — `frontend-visual` 은 로그인 필요 화면을 잴 수 없다(spec §8-1). `[미확인]` 으로 남기고 사람 확인 몫으로 둔다.
- 기존 시험 정정 7파일(`shell`·`recs-20260903`·`auth`·`catalog`·`qa-20260903`·`search-verified-20260903`·`detail-edit`) — 수집 건수 감소가 곧 red 다.

## spec 추적 및 작업 종료 기준

- 추적 = 각 Task 블록의 「실패 시험」 번호가 spec §8-2 의 행 번호와 1:1이다. 번호가 빠지면 그 항목은 미착수로 계수한다.
- 작업 종료 기준 6 —
  1. Task 1~7 각 레인이 자기 단독 게이트 green(3계수 기록 · 준비 red 0).
  2. 통합 트리에서 전수 게이트 **1회** green(red(판정) 0 · red(준비) 0).
  3. spec §9 항목별 수용선 9묶음이 전건 충족(상단 · 계정 관리 · 구성원 · 제목 · 카드·빈 표 · 승인 칸 · 가공 단계 · 검색 · 문면·관측).
  4. 대장 6항목이 `done` ＋ `work-item-consistency` green ＋ `03-HANDOFF §1`·`PLAN-SoT §9` 반영.
  5. dev 배포 green ＋ `deploy_doctor` **15/15 를 한 번의 실행으로**.
  6. 기획자 회신 2건 발송 ＋ `I-7` 관측 결과 회수(미회수면 `[미확인]` 으로 남기고 후속 항목으로 적는다).
- WU 는 부분 완료로 닫지 않는다. 차단이 생기면 차단 해제를 별 항목으로 만든다(`CLAUDE.md §5`).
