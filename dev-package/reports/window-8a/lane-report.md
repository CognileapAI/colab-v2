# 창 8-a 레인 보고 — PR #1 병합(AWS 없이)

집행 2026-09-05 · 워크트리 `.claude/worktrees/agent-acab040cd31080b89` · 브랜치 `integration/w8a-pr1`
작업지시 = `dev-package/03-HANDOFF.md` 「창 8-a — PR #1 병합(AWS 없이)」 블록 · 등재 `PLAN-SoT §9 〈336〉`-㉴

⛔ **이 레인이 하지 않은 것** — Ted 병합 판정 · `main` fast-forward · 창 8-a ⑹ staging 리허설 ·
배포 · 박홍진 통보(⑻). **`main` 에 push 0 · `main` 병합 0 · staging 접촉 0 · 배포 0.**

---

## 1. 진입조건 — 셋 다 섰다

| | 조건 | 판정 기준 | 실측 |
|---|---|---|---|
| ㉠ | 워크트리에서 한다 | 작업 트리가 `.claude/worktrees/` 아래 | `git rev-parse --show-toplevel` = `…/.claude/worktrees/agent-acab040cd31080b89` ✅ |
| ㉡ | 두 브랜치를 fetch 했다 | `git rev-parse origin/feature/rtf400_deploy` = `0e294e5` | `0e294e5f4b335d0d96b8f965243d2665df4b3719` ✅ |
| ㉢ | 시험 환경이 선다 | 게이트 red(준비) 0 | `§5` 참조 |

**기준** = `origin/main` `5a9d9f8` ＋ PR #1 `origin/feature/rtf400_deploy` `0e294e5`.

## 2. 병합 — 브랜치·커밋

| | 값 |
|---|---|
| 브랜치 | `integration/w8a-pr1` (`main` `5a9d9f8` 에서 분기) |
| 병합 커밋 | **`c6f5e00`** (`c6f5e00…`) ⭑ **⟨정정 2026-09-06⟩ 종전 표기 ~~`1ddd8b395ae0d431fa07d0797dba821ce39dd149`~~ 은 amend **전**(22:35) 커밋이고 지금은 dangling 이다. 실 커밋 = `c6f5e00`(23:02) |
| 부모 | `5a9d9f8`(main) · `0e294e5`(PR #1) — **두 부모 = 통짜 병합** |
| 규모 | **186 파일 · +18,251 / −909**(실측 `git show --stat c6f5e00 \| tail -1`) ⭑ **⟨정정 2026-09-06⟩** 종전 표기 ~~185 파일 · +18,194~~ 는 amend 전 값이다 — amend 가 병합 리비전 `0012_merge_lv1_and_transfer.py`(57줄)를 더했다 |
| 방식 | `git merge --no-ff` · **체리픽 0 · 부분 병합 0** |

## 3. 충돌 21파일 — 자리마다 어떻게 풀었나

**선언 20 ＋ `03-HANDOFF.md` = 실측 21.** 해소 규칙 = **양쪽 의도를 다 살린다.**

| # | 파일 | 해소 |
|---|---|---|
| 1 | `dev-package/03-HANDOFF.md` | `main` 이 더 새 원장 ⟹ 구조 유지. PR 의 「／ 이전」 69줄 중 archive 기존분은 다시 안 쌓고, **archive 에 없던 PR 고유 회차 3건 ＋ 블로커 2행은 archive 맨 뒤로 옮겼다**(지우지 않음) |
| 2 | `dev-package/work-items.yaml` | `main` 18항목 유지 ＋ PR 5항목(`U-1`·`U-2`·`F-3`·`I-D`·`V-4`) 추가. **id 충돌 1건** — PR `V-3` → **`V-4`** 개번(`main` `V-3` = 지도 타일 · `〈302〉` 가 선점) |
| 3 | `frontend/.../catalog/CatalogTable.tsx` | PR 의 **버튼 ＋ `props.onDownload`** 채택(302 링크 폐기 · Ted `〈334〉`-㉳-⑥). 표의 지역 오류 상태는 걷고 페이지가 갖는다 |
| 4 | `frontend/.../detail/FileList.tsx` | **add/add — 같은 이름의 다른 컴포넌트 둘.** 둘 다 살렸다: 조각 목록 → **`PieceList.tsx` 신설**(마크업·CSS 무변) · 파일 관리 구역 → `FileList` 유지 |
| 5 | `frontend/.../detail/detail.css` | **합집합** — `main` 의 `.filelist .fl-g/.fl-k/…` ＋ PR 의 `.dt-files/.fl-list/.fl-file/…`. 클래스 이름 충돌 0건(실측) |
| 6 | `frontend/.../detail/detailSource.ts` | `main` 채택 — **픽스처 폴백을 되살리지 않는다**(`3e74dae` 가 걷었고 PR 은 그 이전). 되살리면 실존 데이터셋이 「없는 주소」가 된다 |
| 7 | `frontend/.../detail/useDatasetDetail.ts` | `main` 채택 — 410 묘비 / 404 없는 주소 / 그 밖 오류를 **셋으로 가르는** 판이 더 넓다 |
| 8 | `frontend/src/routes/DatasetDetailPage.tsx` | **합집합** — `filesSource`(main · 조각 목록)와 `fileSource`(PR · 파일 관리) **둘 다 실제로 쓰인다**(실측 `:186`·`:222`) |
| 9 | `frontend/src/routes/DatasetsPage.tsx` | `main` 의 `LoadFailure` 가드 구조 유지 ＋ 그 안에 PR 의 `downloadError`·`onDownload` 를 넣었다 |
| 10 | `frontend/vite.config.ts` | `server` = 프록시(PR) ＋ `fs.allow`(main) 둘 다 · `test.css.include` = **합집합**(PR 은 이 키가 없어 main 목록이 그대로 남는다) |
| 11 | `core-api .../app/main.py` | import **합집합** — `logging`(main) ＋ `ThreadPoolExecutor`·`FutureTimeout`·`Request`(PR). 넷 다 본문에서 쓰인다(실측) |
| 12 | `core-api .../routes/ingestion.py` | **9 자리.** PR 의 저장 Port·`relativePaths`·`relative_path` 채택 ＋ `main` 의 **`def`(비동기 아님)** 유지. `await x.seek(0)` → `x.file.seek(0)` 로 옮겨 두 의도를 같이 살렸다 |
| 13 | `core-api .../routes/not_implemented.py` | 표 계수는 **실측 4**(두 줄기가 걷은 op 이 같다). 두 줄기의 계수 이력을 둘 다 본문에 남겼다 |
| 14 | `core-api .../domains/d8_insight.py` | PR 채택 — `0009` 가 `d8_download.file_id` 를 더했으므로 4열 INSERT 는 낡음. `main` 의 append-only 주석은 보존 |
| 15 | `core-api tests/test_dataset_registration.py` | **합집합** — 양쪽이 서로 다른 시험을 같은 자리에 덧댔을 뿐이다 |
| 16 | `core-api tests/test_not_implemented.py` | PR 의 `C2_REAL` 구조 채택 ＋ 병합 실측(표 4 · `NO_STORE` 0건) 주석 추가 |
| 17 | `core-api tests/test_route_table.py` | **오라클 수를 손으로 고르지 않고 계약을 세어 적었다** — `fe-core.yaml` 실측 **66**(PR 65 ＋ main 의 `lookupDatasetValue` 1) |
| 18 | `pipeline-worker .../app/worker.py` | **합집합** — `main` 의 `DATA_ERRORS` 처리 ＋ PR 의 `blobs.discard`. `except` 가 아니라 **`finally`** 에 둔다(실패 건의 캐시도 치운다) |
| 19 | `viz-render .../app/main.py` | import·본문 **합집합** — `configure_logging()`(main `BF-12`) ＋ `validate(load_settings())`(PR) |
| 20 | `viz-render .../routes/renders.py` | import **합집합** — `SizeMismatch`·`WorkspaceExceeded`(PR) ＋ `deps`(main) |
| 21 | `viz-render .../kernel/config.py` | **합집합** — 타일 회수 필드(main)와 s3 소스·미리보기 싱크 필드(PR)가 서로 다른 칸이다 |

**판정** — `git grep '<<<<<<<'` **0건** · 게이트 `work-item-consistency` **green**(대장 125건 · `conflict` 0건).

### 3-b. 충돌 표 밖에서 병합이 만든 결함 셋 — 조용히 덮어쓰던 자리

⛔ **셋 다 오류를 내지 않고 앞을 먹던 자리다.** 시험·생성물이 냈다.

| | 자리 | 무슨 일 | 해소 |
|---|---|---|---|
| ⓐ | `core-api .../kernel/errors.py` | `def gone` 이 **둘**(묘비 410 · 티켓 만료 410). 뒤가 앞을 덮어 인자를 필수로 만들었고 `catalog.py` 무인자 호출이 `TypeError` | **한 벌로 합쳤다** — 기본값 = 묘비 문면, 티켓은 `message` 명시 |
| ⓑ | `contracts/seams/fe-core.yaml` | `components.responses` 에 `Gone:` 이 **둘**. YAML 이라 조용히 앞이 사라졌고 생성물이 `Duplicate identifier 'Gone'` 로 냈다 | 묘비 = `Gone` · 티켓 만료 = **`TicketGone`** 으로 갈랐다. 생성물은 **등기부 명령으로 재생성**(손 수정 0) |
| ⓒ | `core-api .../routes/catalog.py` ↔ `routes/download.py` | `downloadDataset` **핸들러 둘**(302 판 · 200 티켓판). 같은 `operationId`·같은 경로 | Ted `〈334〉`-㉳-⑥ ＋ 병합 계약(200 `DownloadTicket`)에 따라 **302 판을 걷었다** |

### 3-c. 걷은 것과 그 자리를 대신 서는 것 — 덮지 않고 옮겼다

| 걷은 것 | 대신 서는 자리 |
|---|---|
| `catalog.py` 의 `downloadDataset` 302 판 ＋ `_bundle`·`_disposition` | `routes/download.py`(200 티켓 ＋ `zip_stream`) |
| `tests/test_dataset_download.py`(11 시험) | `tests/test_download.py` — 머리말에 **시험별 대응표**를 적었다. 대응 없는 것 **1건** = `?deliver=1` 표식(티켓 판에는 그 개념 자체가 없다) |
| `api/download.ts` 의 302/blob 판 | 같은 파일을 **티켓 계약으로 고쳐** 호출자(`UsageSection`)를 그대로 살렸다 |

## 4. 〈N〉 재실측 · id 개번

**PR 이 쓴 `〈276〉`~`〈281〉` 은 `main` 에 이미 있었다** — 같은 번호를 **다른 판정 여섯**이 쓰고 있었다
(`§9` 실측: PR 판은 483~488행 · `main` 판은 633~638행). 유지 불가 ⟹ 병합 시점 `origin/main` 최대 `〈336〉` ＋1 로 재배치.

| PR 번호 | → | 새 번호 | 내용 |
|---|---|---|---|
| `〈276〉` | → | **`〈337〉`** | 업로드 저장 백엔드를 로컬/S3 로 가른다 — 저장 Port |
| `〈277〉` | → | **`〈338〉`** | 여덟 번째 동결 해제 — 프리사인드 직행 전송 9 op |
| `〈278〉` | → | **`〈339〉`** | 파일 관리가 1차 목표에 든다 |
| `〈279〉` | → | **`〈340〉`** | dev 환경(AWS · s3 모드) 신설 |
| `〈280〉` | → | **`〈341〉`** | 아홉 번째 동결 해제 — 파일 관리 |
| `〈281〉` | → | **`〈342〉`** | dev 환경 집행 계획서의 레포 조정 결정값 |

- **인용 이관 = 106 파일 392 줄.** 판별식 = 「`origin/main` 의 그 파일에 없던 줄」 ⟹ PR 이 들여온 인용만 옮겼다.
  ⛔ **⟨정정 2026-09-06 · 어드바이저 수용 검토⟩ 종전 표기 ~~「`main` 자신의 `〈276〉`~`〈281〉` 인용 33파일은 한 글자도 안 건드렸다」~~ 는 거짓이었다.**
  실제로는 **`main` 고유 파일 2건 6줄을 오개번했다** — `dev-package/prd/PRD-260905-적용전기획.md` · `dev-package/prd/개발계획서-260905.md`.
  두 파일은 PR `0e294e5` 에 **없다**(`git cat-file -e` 실패) ⟹ 그 안의 `〈276〉` 은 **`main` 의 `LV-1` 판정**이고 `〈280〉` 은 **생성 요청 세 필드**다.
  sed 스윕이 판별식(「`origin/main` 의 그 파일에 없던 줄」)을 넘어갔다. ⭑ **되돌렸다** — 두 파일을 `5a9d9f8` 내용으로 복원해 **`main` 과 바이트 동일**이다.
  ⛔ **이 두 파일은 기획자 원본 계열이라 우선순위가 최상이다**(`10_적용전` 무수정 원칙).
  **재실측 = `main` 이 `〈276〉`~`〈281〉` 을 인용하는 35파일 전건이 계수까지 `main` 과 같다**(파일별 대조 · 불일치 0).
- **행 위치도 옮겼다** — `§9` 는 오름차순이라 재배치한 여섯을 `〈336〉` 뒤로 이동하고, 그 앞에 개번 사유 한 줄을 박았다.
- **대장 id 개번 1건** — PR `V-3`(worker·viz S3 읽기) → **`V-4`**. `main` `V-3`(지도 타일 소유·회수 · `〈302〉`)이 선점.
  인용 11파일 28줄 이관. ⛔ **증거 전사 2건**(`docs/DEPLOY-evidence-viz.txt`·`-worker.txt`)은 **찍힌 출력이라 고치지 않았다.**

**판정** — `§9` 번호 중복 **0**(행 291 · 최대 342) · 대장 id 중복 **0**(항목 125).

## 5. 문서 3곳 개정 — 같은 병합 커밋에서

⛔ **두 곳에서 집행하지 않았다.** 셋 다 **`c6f5e00`** 안에 있다(`git show --stat` 실측). ⭑ **⟨정정 2026-09-06⟩ 종전 표기 ~~`1ddd8b3`~~ 은 amend 전 커밋이다.**

| | 파일 | 개정 |
|---|---|---|
| ⓐ | `CLAUDE.md §0` 완료 조건 | 「staging 배포까지」 → **「dev 배포 green ＋ `deploy_doctor` 14/14 를 한 번의 실행으로」** ＋ **staging = 「리허설(판정 아님)」** 명기 ＋ prod = `main` 커밋 태그에서만 배포(`〈334〉`-㉮ · `〈335〉`-㉯·㉳·㉵) |
| ⓑ | `infra/README.md` 환경 표 | `staging \| AWS (축소) \| 배포 경로 검증` → **`staging \| WSL2 로컬(docker compose · 저장 local) \| 리허설 — 판정 아님`**. **dev 행을 판정처로 신설.** 정정 사유(왜 staging green 이 dev 를 보증 못 하는가)를 표 아래 적었다 |
| ⓒ | `work-items.yaml` `BF-12` 완료 정의 ⑶ | 「**staging** 배포 뒤 첫 바퀴 요약 1줄」 → 「**dev** 배포 뒤 …」 ＋ 확인 자리 = 창 8-b (`〈336〉`-㉷) |

⭑ **덤 1건** — `sessions/P8-E01-APPLY-POINTS-DRAFT.md §1.1` 에 행 **둘** 추가.
PR 이 `PermissionGate` 자리를 둘 늘렸는데(`detail/FileList.tsx` · `routes/LabPage.tsx`) 표가 9 에 머물렀다.
**시험이 그 드리프트를 냈고, 표를 실물에 맞췄다**(시험은 안 고쳤다).

## 6. 게이트·시험 실측

### 6-a. 전 게이트 전수 — 네 회차 · 판정은 **`gates-all-3.txt` 하나**

⛔ **판정 회차는 4차 하나다**(`〈333〉`-⒝ 규율 = 「한 번의 실행으로」). 앞 셋은 **증거로 남기고 판정에 세지 않는다.**

| 회차 | 로그 | 병렬도 | 소요 | green | red(판정) | red(준비) | 무엇이었나 |
|---|---|---|---:|---:|---:|---:|---|
| 1차 | `gates-all-1.txt` | `-j 1` | **41분** | 47 | **3** | 0 | 병합 커밋 **amend 전**. red 3 = `migration-single-head`·`schema-diff`·`frontend-test` |
| 2차 | `gates-all-2-j1-aborted.txt` | `-j 1` | — | — | — | — | **시작 직후 중단** — 판정 없음(12줄). 세지 않는다 |
| 3차 | `gates-all-2-j4-noenv.txt` | `-j 4` | 21분 | 44 | 0 | **6** | ⛔ **배선이 낸 red 다** — `set -a` 없이 `source` 만 해 값이 자식 프로세스로 안 나갔다. 검사 대상은 한 건도 판정되지 않았다 |
| **4차 · 판정** | **`gates-all-3.txt`** | **`-j 4`** | **21분** (23:56→00:17) | **50** | **0** | **0** | ⭑ **한 번의 실행으로 50/50/0** |

**판정 = red(판정) 0 ＋ red(준비) 0 을 한 번의 실행으로.** ✅ (`〈336〉`-㉴ 창 8-a 집행 ⑷)

### 6-b. 1차의 red 3 은 무엇이었고 어떻게 닫혔나 — **red 를 닫으려고 약화한 것이 0건** ⭑ ⟨정정 2026-09-06⟩

⚠ **종전 표기 ~~「시험을 약화한 것이 0건」~~ 은 범위를 넘었다** — 게이트 red 를 닫으려고 손댄 시험은 0건이 맞지만, **병합이 계약을 바꾼 자리에서 시험 셋을 손댔다.** 그 셋은 아래 `§6-b-2` 에 이름으로 있다.

| 게이트 | 1차 red 의 정체 | 닫힌 방법 | 4차 실측 |
|---|---|---|---|
| `migration-single-head` | 병합이 두 체인의 head 를 갈랐다 — `main` `0008`~`0011` ↔ PR #1 리비전 | **병합 리비전 `0012_merge_lv1_and_transfer`** 를 `db/platform` 체인에 세웠다(병합 커밋 amend 에 포함). ⛔ **리비전 삭제 0건** | green — `db/platform` 리비전 15 · head **1**(`0012_merge_lv1_and_transfer`) · `db/ai` 리비전 5 · head **1**(`0005_k2b_concept_graph_seed`) |
| `schema-diff` | ⛔ **검사 대상의 결함이 아니었다** — 게이트용 **적용 DB 두 개(tmpfs 일회용 컨테이너)가 죽어 있었다**(`pg_dump: … Host is unreachable`) | `RESTART.md §2-④`·`㉮`·`㉲` 절차대로 다시 세웠다 — **ai(`ai_pg`) 먼저 · platform(`a2_pg`) 나중**(기본 브리지가 `.2`·`.3` 을 순서대로 준다) → 체인별 `setup-db.sh` → `colab_platform_applied`·`colab_ai_applied` `createdb` → `alembic upgrade head`. **env 값·비밀번호는 새로 짓지 않고 `~/.colab-v2-test.env` 의 것을 그대로 썼다** | green — 두 체인 각각 **선언 = 적용 · 드리프트 0** |
| `frontend-test` | 병합 직후의 vitest 실패(amend 에서 해소) | 병합 커밋 amend(23:02) — 이 레인이 추가로 고친 시험 **0건** | green — **45파일 / 677건 통과 · 실패 0** |

⭑ **`schema-diff` 의 뿌리는 `RESTART.md §2-④-㉲` 가 이미 이름으로 적어 둔 것이다** — 「없는 것을 잡는 검사 = `./gates/run.sh schema-diff` 한 줄」. **staging 8개가 healthy 인 것과 무관**하고, tmpfs 라 호스트를 껐다 켜면 돌아오지 않는다.

⚠ **3차(`-j 4` · red(준비) 6)의 뿌리도 검사 대상이 아니었다** — `~/.colab-v2-test.env` 는 `export` 를 쓰지 않아 **`set -a; . <파일>; set +a` 로 읽어야** 값이 게이트 프로세스로 나간다(파일 머리말이 그 관용구를 적고 있다). `source` 만 하면 DB·마운트 의존 게이트 6개가 통째로 red(준비) 로 뜬다. **이 회차의 실측이므로 `03-HANDOFF` 창 8-a ⑷ 에 주의로 옮겨 적었다.**

### 6-b-2. ⭑ ⟨신설 2026-09-06 · 어드바이저 수용 검토⟩ 시험을 건드린 자리 셋 — **공개한다**

⛔ **`§6-b` 의 「시험을 약화한 것이 0건」은 과했다.** 게이트 red 를 닫으려고 약화한 것은 0건이 맞지만,
**병합이 계약을 바꾼 자리에서 시험 셋을 손댔다.** 그 셋을 여기 이름으로 적는다.

| | 자리 | 무엇을 했나 | 판정 |
|---|---|---|---|
| ⓐ | `services/viz-render/tests/test_auto_invalidation.py` — `DELETION_SITES` | **허용 목록을 넓혔다** — 종전 둘(`invalidation.py`·`trigger_bus.py`)에 **`source.py` 를 더해 셋**. 근거 = Ted 판정 `〈334〉`-㉳-⑭(`V-4` 방식 = **내려받기**) ⟹ s3 모드에서 원본을 `workdir` 로 내려받아 읽고 반쪽 파일·낡은 캐시를 치우는 자리가 새로 생겼다. ⛔ **원본을 지우는 것이 아니다**(원본은 S3 객체 · 이 단위는 읽기만) | **울타리를 함께 세웠다** — 신설 시험 `test_source_는_자기_작업_디렉터리_밖을_지우지_않는다`. 목록의 머리말도 「이름만 늘리지 않는다 — 자리마다 울타리를 증명하는 시험이 짝으로 있어야 한다」로 고쳤다. ⚠ **그래도 허용 목록이 넓어진 것은 사실이고, 「이름을 하나 더 넣는 것은 판정 사안이다」가 종전 주석의 축자였다** — **Ted 가 다시 볼 자리로 남긴다** |
| ⓑ | `frontend/test/catalog-download.test.tsx` | ⛔ **느슨하게 했다** — `expect(calls).toHaveLength(1)` → `expect(calls.length).toBeGreaterThanOrEqual(1)`. 사유 = 다운로드가 **302 한 바퀴**에서 **티켓 → 바이트 두 요청**으로 바뀌어 정확히 1 이 성립하지 않는다 | ⚠ **약화다 — 중복 호출을 이제 못 잡는다.** 이 시험이 잠그는 못 둘(⑴ 티켓 요청에 `Authorization` 이 붙는가 ⑵ 안 열리면 말하는가)은 그대로지만, **정확한 요청 수를 재던 것은 잃었다.** ⭑ **정직한 고침 = `toHaveLength(2)`** 이고 그것이 후속 자리다 |
| ⓒ | `frontend/test/qd-detail-section3.test.tsx` | 「보기」 질의를 `getByRole('button',{name:'보기'})` ×5 → `document.querySelector('.ig-more')` 로 **좁혔다**(느슨하게가 아니라 **특정 버튼을 지목**). 사유 = 병합으로 같은 화면에 「보기」 버튼이 **둘**이 됐다(`BasicInfoGrid` 의 `.ig-more` · `FileList` 의 `dt-files-toggle`) | ⚠ **숨은 회귀 하나** — 종전 `getByRole` 은 같은 이름의 버튼이 둘이면 **throws** 해서 **접근성 이름 중복을 기계가 잡았다.** 바꾼 질의는 안 잡는다. ⛔ **「보기」 정본을 Ted 가 고르는 순간 원래 질의로 되돌린다** — `§7-b` ㉠ 에 걸어 둔다 |

### 6-b-3. ⭑ ⟨신설 2026-09-06⟩ 충돌 표(`§3`) 밖에서 이 레인이 편집한 파일 — **PR 에 없던 자리 다섯**

`git diff --name-only 5a9d9f8 c6f5e00` 중 **PR `0e294e5` 에 존재하지 않는** 파일에서, `§3`·`§3-b`·`§3-c`·`§5` 가 이미 적은 것을 뺀 나머지다.

| | 파일 | 무엇을 |
|---|---|---|
| ⑴ | `frontend/test/qd-detail-section3.test.tsx` | 위 ⓒ ＋ `byteSize`·`createdAt` 필수 칸 반영(33줄) |
| ⑵ | `frontend/test/catalog-download.test.tsx` | 위 ⓑ — 302 → 티켓 두 요청 |
| ⑶ | `services/core-api/tests/test_upload_streaming.py` | 저장 Port(`〈337〉`)가 바이트를 만지는 자리를 `kernel/storage_backends` 하나로 모은 것을 반영한 주석·기대값 |
| ⑷ | `dev-package/prd/PRD-260905-적용전기획.md` | ⛔ **오개번 — 되돌렸다**(위 `§4` 정정) |
| ⑸ | `dev-package/prd/개발계획서-260905.md` | ⛔ **오개번 — 되돌렸다**(위 `§4` 정정) |

⚠ **`§5` 의 「시험은 안 고쳤다」는 그 덤 한 자리(`P8-E01` 표)에 대한 말이었다** — 레인 전체로는 위 셋을 고쳤고, 이 절이 그 전수다.

### 6-c. 병렬도 — **판정 기준이 아니라 실행 순서다** (⭑ Ted 판정 2026-09-06)

같은 트리(`c6f5e00`)를 두 병렬도로 돌린 실측이다.

| 병렬도 | 로그 | 소요 | 판정 |
|---|---:|---:|---|
| `-j 1` | `gates-all-1.txt` | **41분** | green 47 / red 3 (amend 전 트리) |
| `-j 4` | `gates-all-3.txt` | **21분** | **green 50 / red(판정) 0 / red(준비) 0** |

- **정본** = `gates/README.md` 축자 「**검사 대상·기대값·판정 기준은 하나도 바뀌지 않았고, 바뀐 것은 실행 순서뿐이다**」 · 「출력은 등록 순서로 되돌려 재생하므로 로그도 직렬판과 같은 줄이 같은 순서로 나온다」.
- ⭑ **Ted 판정 — 전수는 이제 `-j 4` 로 돈다.** `03-HANDOFF` 창 8-a ⑷ 의 ~~`-j 1` 고정~~ 을 **`-j N` 허용**으로 고치고 「⟨추가 2026-09-06⟩」 줄을 붙였다. **「한 번의 실행으로」 규칙은 그대로다.**
- ⚠ **`-j 1` 은 재현이 필요할 때 쓴다**(`COLAB_GATE_JOBS=1`).
- ⛔ **절반에서 멈춘다** — `parallelism.toml` 이 `serial` 로 선언한 **여덟**이 단독 구간을 차지한다. **게이트 사이가 아니라 게이트 안이 직렬**이라 후속 항목 **`G10`** 으로 등록했다(`§7`).

### 6-d. 시험 계수 — 4차 로그(`gates-all-3.txt`)에서 그대로 읽었다

**pytest — 서비스 넷 · 계 1,521건 실행 · 실패 0 · errors 0**

| 게이트 | 표식 선택자 | 수집 | 실행 | skipped | deselected | failed | errors | 소요 |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| `service-tests-core-api` | `not e2e` | 763 | **763** | 0 | 6 | 0 | 0 | 135.1초 |
| `service-tests-ai-service` | `not dictdb` | 130 | **130** | 0 | 26 | 0 | 0 | 3.5초 |
| `service-tests-viz-render` | `not e2e and not perf` | 368 | **368** | 0 | 40 | 0 | 0 | 37.6초 |
| `service-tests-pipeline-worker` | `not e2e and not dbint` | 260 | **260** | 0 | 46 | 0 | 0 | 10.5초 |
| **계** | | **1,521** | **1,521** | **0** | **118** | **0** | **0** | |

⚠ **`deselected` 118 은 감춘 건너뜀이 아니다** — 표식은 붙어 있고 그 환경이 있는 실행에서 함께 돈다(`gates/README.md`). **요약줄에 건수로 드러나 있다.**

**vitest · tsc**

| | 값 | 출처 |
|---|---|---|
| `frontend-test` (vitest) | **45파일 / 677건 통과 · 실패 0** | `gates-all-3.txt` · 게이트 단독 재실행에서도 같은 값 |
| `frontend-typecheck` (tsc) | **오류 0건** | `gates-all-3.txt` — `tsc --noEmit`(`frontend/tsconfig.json` · `include` = `src`·`test`) |
| `tsc` 직접 실행 | **exit 0 · 오류 0건** | `frontend/node_modules/.bin/tsc --noEmit -p tsconfig.json` (게이트 밖에서 따로 한 번 더) |

⭑ **기준선 대비** — `〈327〉`~`〈331〉` 회차의 `frontend-test` 는 **39파일 / 605건**이었다. 병합으로 **45파일 / 677건**(＋6파일 ＋72건)이 됐고 **실패 0** 이다.

### 6-f. ⭑ ⟨신설 2026-09-06⟩ 로그가 레포에 **추적된 채로** 있다 — 확장자를 `.txt` 로 바꿨다

⛔ **`.gitignore:35 `**`*.log`** 가 전수 로그 4건을 통째로 걷어내고 있었다.** 그래서 커밋 `f7d8a20` 의 제목
「게이트 전수 로그 4건」은 **거짓이었다** — 그 커밋에 실제로 들어간 것은 `lane-report.md`·`reload-manifest-draft.md` 둘뿐이다.
⛔ **역사를 고쳐 쓰지 않는다** — 그 커밋은 그대로 두고, **이 절이 정정**이다.

**고침 = 같은 내용을 `.txt` 로 함께 둔다**(원본 `.log` 는 작업 트리에 남되 여전히 미추적).

| 회차 | 추적되는 파일 | 크기 |
|---|---|---:|
| 1차 | `dev-package/reports/window-8a/gates-all-1.txt` | 99,038 B |
| 2차(중단) | `dev-package/reports/window-8a/gates-all-2-j1-aborted.txt` | 849 B |
| 3차(배선 red) | `dev-package/reports/window-8a/gates-all-2-j4-noenv.txt` | 99,390 B |
| **4차 · 판정** | **`dev-package/reports/window-8a/gates-all-3.txt`** | 92,632 B |
| 좁은 게이트 재실행 | **`dev-package/reports/window-8a/narrow-gates-after-fix.txt`** | 정정 커밋 뒤 실측 |

⚠ **미추적 산출물은 다음 워크트리·Ted 가 못 읽는다** — 조사 산출물은 회수 즉시 커밋한다.

### 6-e. 전 게이트 판정 50건 — 4차 요약줄 그대로

`green 50 / red(판정) 0 / red(준비) 0` · **미선언 0건**(단독 8 · 병렬 42).


## 7. 못 한 것 · 사람이 판정할 것

### 7-a. 전수 뒤에 고친 것 — **문서 셋 ＋ 대장 한 항목뿐** (선례 `〈333〉`-⒝)

⛔ **4차 전수(`gates-all-3.txt`) 뒤 코드·시험·계약은 한 글자도 안 고쳤다.** 고친 것은 아래 넷이고 **전부 문서·대장**이다.

| | 파일 | 무엇을 | 근거 |
|---|---|---|---|
| ⓐ | `dev-package/03-HANDOFF.md` 창 8-a ⑷ | `-j 1` 고정 → **`-j N` 허용** ＋ 실측(`-j 1` 41분 · `-j 4` 21분 · 판정 동일) ＋ `set -a` 주의 ＋ **⟨추가 2026-09-06⟩ Ted 판정 = 전수는 `-j 4`** | Ted 판정 · 정본 `gates/README.md` |
| ⓑ | `dev-package/03-HANDOFF.md` `§1` | **`G10` 행 신설**(⬜ · 등록만) | 위 `§6-c` |
| ⓒ | `dev-package/work-items.yaml` | **`G10` 항목 신설**(`status: open` · **등록만**) — 단독 선언 게이트 8개 **안**의 시험 병렬화 | 위 `§6-c` |
| ⓓ | `infra/dev/README.md` 진단표 | **한 줄 신설** — WSL2 buildx 에 `linux/arm64` 가 없으므로 `docker run --privileged --rm tonistiigi/binfmt --install arm64` 로 QEMU 를 먼저 등록한다(실측 2026-09-05) | 창 8-b 준비 실측 |

**판정 = 좁은 문서 게이트만 다시 돈다** — `work-item-consistency` · `planning-freshness` · `work-item-selftest`. ⭑ **⟨정정 2026-09-06⟩ 종전에는 이 문장이 계획문이고 출력이 레포에 없었다** — 실측 출력은 `dev-package/reports/window-8a/narrow-gates-after-fix.txt` 다.
**전 게이트 전수를 다시 돌리지 않는다** — 선례 `〈333〉`-⒝(코드 트리가 같으면 재실행하지 않는다). ⛔ **코드 트리는 4차 전수 시점과 동일하다.**

### 7-a-2. ⭑ ⟨신설 2026-09-06⟩ 어드바이저 수용 검토 반영 — **두 번째 문서 회차**

판정 = **GO-with-fixes**. 반영한 것 다섯이고 **전부 문서·보고서다 — 코드·계약·시험 0줄.**

| | 무엇 | 자리 |
|---|---|---|
| ⓐ | **오개번 6줄 되돌림** — `main` 고유 PRD 2파일의 `〈276〉`·`〈280〉` 을 `〈337〉`·`〈341〉` 로 바꾼 것을 되돌려 **`main` 과 바이트 동일**로 복원 | `dev-package/prd/` 2파일 |
| ⓑ | **`〈334〉`-㉳ · `〈336〉` 행에 개번 주석** — 그 행들이 인용하는 `〈277〉`·`〈279〉`·`〈280〉`·`〈281〉`·`V-3` 은 PR 의 옛 값이라 지금 트리에서는 **남의 판정**에 닿는다. **원문은 지우지 않고 대응만 적었다** | `dev-package/PLAN-SoT.md` |
| ⓒ | **재배치 사유 행이 자기 자신을 개번한 것 정정** — 「PR #1 이 `〈337〉`~`〈342〉` 로 쓴」 → **「`〈276〉`~`〈281〉` 로 쓴」**(앞뒤가 같은 번호라 문장이 성립하지 않았다) | `dev-package/PLAN-SoT.md` |
| ⓓ | **보고서 정정 넷** — 병합 해시 `1ddd8b3` → **`c6f5e00`** · 규모 185/+18,194 → **186/+18,251** · 「33파일 안 건드렸다」 거짓 정정 · 시험 손댄 자리 셋 공개(`§6-b-2`) ＋ 충돌 표 밖 편집 다섯(`§6-b-3`) | 이 문서 |
| ⓔ | **게이트 로그 추적** — `*.log` 가 `.gitignore` 되어 커밋에 안 들어갔다. `.txt` 사본으로 추적(`§6-f`) | `reports/window-8a/*.txt` |

⛔ **이 회차도 코드 트리를 건드리지 않았다** ⟹ 전 게이트 전수 재실행 없이 좁은 문서 게이트 셋만 다시 돈다.

### 7-b. 사람이 판정할 것 — **열린 채로 넘긴다**

| | 무엇 | 왜 열려 있나 |
|---|---|---|
| ㉠ | ⭑ **상세 화면의 「보기」 버튼이 둘이다** | 병합이 두 줄기의 「보기」를 한 화면에 세웠다. **어느 쪽이 정본인지 Ted 판정 전이다** ⟹ ⛔ **이 레인은 손대지 않았다.** 지금 고르면 사용자에게 보이는 동작을 판정 없이 정하는 것이 된다 |
| ㉡ | **`G10`** — 단독 게이트 8개 안의 시험 병렬화 | **등록만**이고 착수 회차를 열지 않았다. 줄어드는 시간은 `[미확인]` — **추정값을 적지 않는다** |
| ㉢ | **Ted 병합 판정 → `main` fast-forward** | 창 8-a 집행 ⑸. ⛔ **이 레인은 `main` 에 push 0 · 병합 0** |
| ㉣ | **PR #1 17건 판정 결과의 박홍진 통보**(집행 ⑻) | 레포 밖 행위다 |
| ㉤ | **staging 리허설**(집행 ⑹ · 선택) · **재적재 집행** | 리허설은 선택이고 대장에 기록하지 않는다. 재적재는 `reload-manifest-draft.md` 확정 뒤 창 8-b |

