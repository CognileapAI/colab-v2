# R-C-1 · 계약·DB·서버 계층 — WU-C6 · WU-C10 · WU-C7 · WU-C9 — spec: `dev-package/prd/specs/R-C.md` (출처 intent `dev-package/intent/2026-09-08-r-c.md` 우산 · `dev-package/intent/2026-09-08-preview-slot.md` 축 ①)

> ⛔ **착수 조건 = Ted 가 intent 2건을 커밋(승인) ＋ 21차 승인 문장 기입. 그 전에는 이 파일로 세션을 열지 않는다.**
> 이 파일 하나로 세션을 시작한다. 라운드 = **R-C** · 계층 = **계약·DB·서버** · WU **4건**(순서 고정 C6 → C10 → C7 → C9).
> 통합 브랜치 `integration/r-c` · 워크트리 `.claude/worktrees/r-c` · 기점 = `main` tip(**해시를 박지 않는다** · `git rev-parse HEAD` 로 읽는다).
> 계약 동결 해제 **21차**(등급 전망 ㉮ · 첨가 6건 · `contract-breaking` 출력으로 병합 직전 확정) · 마이그레이션 **2건 전망**(`0020`·`0021` · head 1개) ＋ `db/ai` 1건 전망.
> spec 이 「무엇을·왜·어떤 결정으로」의 정본이고 이 파일은 실행 뷰다. 어긋나면 spec 이 우선한다(`prd/specs/README.md`).

---

## 0. 읽기 규칙 — 이 파일이 유일한 부트스트랩

> ⛔ **아래 4개를 통째로 열지 않는다.** 세션이 느려지는 원인이 이것이다.
> `dev-package/03-HANDOFF.md`(약 127 KB) · `dev-package/PLAN-SoT.md`(1.17 MB) · `dev-package/work-items.yaml`(513 KB) · `dev-package/WORK-UNITS.md`(138 KB)

- **허용된 접근은 아래 세 줄뿐이다.**
  1. 결정 번호 최대값 — `bash dev-package/prd/tools/max-decision.sh`
  2. 대장에서 항목 하나 — `grep -n -A14 '^  - id: WU-C1' dev-package/work-items.yaml`
  3. 게이트 이름 확인 — `grep -n -A18 '^ALL_GATES=(' gates/run.sh` (`ALL_GATES` 배열)
- `03-HANDOFF.md` · `CLAUDE.md` · `RESTART.md` 는 **머리 부분만** 읽는다. 본문 통독 금지.
- 요구사항 정본은 spec `R-C.md` ＋ intent 2건 ＋ 이 파일이다. R-B 판정 축자가 필요하면 `dev-package/sessions/R-B-ROUND-20260908.md` **§5 의 해당 번호 줄만** 읽는다.
- **코드 파일은 고칠 때만 연다.** 현황 정찰·grep 스윕·다수 파일 읽기는 `researcher` 에 위임하고 결론만 회수한다.
- 이 파일의 `path:line` 은 **트리 `d969f34` 실측값**이다. 코드를 고친 뒤에는 다시 잰다. 못 재면 `[미상]` 이고 지어내지 않는다.

### 세션 시작

```bash
cd "<작업공간>/30 CoLAB-v2" && claude --add-dir "../40 COLAB-기획"
git -C .claude/worktrees/r-c rev-parse HEAD        # 현재 HEAD 를 읽는다(값을 미리 적지 않는다)
git -C .claude/worktrees/r-c status --porcelain    # 0행
bash dev-package/prd/tools/max-decision.sh          # 착수 시점 참고값(근거 아님)
```

- 에이전트 역할 — `advisor`(fable · 계획 검토 ① · 수용 검토 ②) · `lane-worker`(opus · `isolation: "worktree"`) · `researcher`(sonnet · 조사) · `gate-runner`(haiku · 게이트 실행·계수 회수).
- 의존성(워크트리 `node_modules` · 서비스 `.venv`)은 H2 `worktree-setup.sh` 가 스폰마다 건다. 손으로 `npm ci`·`uv venv` 를 치지 않는다.
- 시험 환경은 `gates/run.sh` 가 스스로 `~/.colab-v2-test.env` 를 source 한다.

---

## 1. 확정 결정 — 다시 열지 않는다

다르게 구현할 사유를 찾으면 **고치지 말고 보고한다.** 기획자에게 받아야 하는 답은 **0건**이다(프론티어 공집합 · intent `## 확인`).

- 2026-09-05 확정 16 — 미결-1 · 2 · 3 · 4 · 5 · 6 · 7 · 9 · 11 · 12 · 13 · 14 · 15 · 16 · 17 · 18(`R-B-1-db.md §1` 축자).
- 2026-09-06 확정 12 — 미결-r2-1~3 · 판정-1·2 · III-A~G(`R-A2.md §1`).
- 2026-09-08 R-B 61건 판정 — `R-B-ROUND-20260908.md §5` 「판정 A」 전부 확정. 이 파일이 쓰는 것:
  - §5-11 **변수명 중복 허용 유지** — `name UNIQUE` 를 만들지 않는다(§6 문면 「변수명 UNIQUE」는 판정과 어긋난 낡은 줄 · intent Q6).
  - §5-9 `ordinal` 1부터 재부여 유지 · **0행 읽기 퇴행 제거 = R-C**.
  - §5-19 **공개 범위 내림 = 소유자 한정**.
  - §5-20 **이관 빈틈 보정 마이그레이션 · 배포 전 실측 선행**.
  - §5-27·41 **Lv 표시 사람 값 우선 통일**(계약 21차) · §5-23 제안에 부모 Lv · §5-24 `ProjectDatasetRow` 사람 값.
  - §5-33 `LabDataMap.byCategory`(21차) · §5-42 사후 「기록 없음」 선언 ＋ `method` 수정 op(21차).
  - §5-3·4·17·30 게이트 승격 3종을 **한 WU** 로.
  - §5-5 `d9_topic_synonym` 4값 ↔ 분류 5값 이관(우산 intent Q7 · S 묶음).
- 2026-09-08 축 ① 16 판정 — `intent/2026-09-08-preview-slot.md ## 미해결 질문 → 판정`. 이 파일이 쓰는 것: **변수＋시각 목록 「대상 기술(describe)」 조회 1건 신설 = 21차 ⑴** · core 는 릴레이만.
- 우산 intent Q1~Q7 — 한 intent 두 축 · 21차 패키지 6건 · 배포 창 실측 3건은 R-C 밖 · `WU-C1…` · 변수명 UNIQUE 제외.
- **21차 패키지 = 첨가 6건**(spec 「API 계약」) — ⑴ `core-viz` `describe` ＋ `fe-core` 릴레이 ⑵ `processingLevelUserSet` optional 첨가(계보 노드·`ProjectDatasetRow`) ⑶ `DataMap.byCategory` ⑷ `declareLineageUnknown` ＋ `updateLineageParentMethod` 신설 2 ⑸ `ParentCandidateSuggestion.parentProcessingLevel` ⑹ = ⑵ 포함. ⛔ 서버가 `processingLevel` 에 사람 값을 덮어 쓰면 ㉯ — 하지 않는다(spec 우려 3).

---

## 2. 범위 — 이 파일의 WU 4건

### WU-C6 · 게이트 승격 3종 (질의 3·4·17·30) — 계층 게이트 · 크기 M · 레인 `rc-gate-drift`

- **의존**: 없음 — 맨 앞. 계약 0 · 스키마 0 · 마이그레이션 0.
- **현재 코드** — 오라클 `db/platform/tests/*-drift.sh` **11벌**(`ls | wc -l` = 11 · 0004~0019 · §6 「7벌」은 낡은 수) 이 어느 게이트에도 안 걸린다. `gates/run.sh:156` `ALL_GATES` 에 `schema-diff` 는 있고 `migration-drift` 는 없다 · dispatch `gates/run.sh:273-276`(`schema-diff) exec gates/tools/schema-diff.sh`). `alembic` 은 `services/core-api/requirements*.txt`·`gates/requirements.txt` 전부 **0건**(`grep -c alembic`).
- **할 일** — ⑴ 게이트 `migration-drift` 신설(`gates/tools/migration-drift.sh` ＋ `ALL_GATES` 등재 ＋ `migration-drift-selftest` 짝 · `gates/README.md:37` 「selftest 없는 게이트는 집합에 없다」) — 11벌 전부를 돌고 **센 건수를 출력**에 드러낸다 ⑵ `schema-diff` 준비 단계에 적용 DB `alembic upgrade head` 를 넣는다(안 돌리면 선언 변경을 드리프트로 읽는 것이 질의 17 의 현상) ⑶ `alembic` 을 `services/core-api/requirements-dev.txt`·`gates/requirements.txt` 에 핀 버전으로.
- **수용 기준** — Given 오라클 11벌 전부 존재, When `./gates/run.sh migration-drift`, Then green 이고 출력에 `오라클 11` 이 보인다 · Given 1벌을 빼거나 대상 0건, Then **red** · Given `alembic` 부재, Then **red(준비)**(skip 아님) · selftest ⓐ 대조군 green ⓑ 되돌린 델타 red ⓒ 대상 0건 red ⓓ alembic 부재 red(준비) · `schema-diff` 가 `upgrade head` **뒤에만** 비교한다.
- **시험 seam** — `gates/tools/*-selftest.sh` 선례 · `db/platform/tests/0019-drift.sh:1-20` 형태.
- **좁은 게이트** — `migration-drift` · `migration-drift-selftest` · `schema-diff` · `migration-single-head` · `exec-bit` · `work-item-consistency`.

### WU-C10 · 계약 동결 해제 21차 패키지 집행 (첨가 6건) — 계층 계약·서버 · 크기 L · 레인 `rc-contract-21`

- **의존**: WU-C6. ⛔ **Ted 21차 승인 문장이 `intent/2026-09-08-r-c.md ## 확인` 에 기입된 뒤에만** `contracts/` 를 연다. 승인 커밋이 `contracts/` 첫 수정보다 **먼저** 있었음이 커밋 순서로 보여야 한다.
- **승인 요청 패키지** — `dev-package/sessions/R-C-C21-REQUEST-<날짜>.md`(**미작성** · 20차 선례 `R-B-C20-REQUEST-20260907.md` 양식 · 이 레인의 첫 산출물). 승인 전 `contracts/` **무접촉**.
- **현재 코드** — `contracts/seams/core-viz.yaml:386-431`(`RenderTarget`·`RenderRequest.variable`·`instant` — 변수 목록 조회 0건) · `fe-core.yaml:574`(`GET /uploads/{uploadId}/files`)·`:1070`(`/datasets/{datasetId}/files`) · `:4599`(`ProjectDatasetRow`)·`:4726`(`DataMap`)·`:4508`(`LineageEdge.method`)·`:4529`(`unknownParents`)·`:1471,1505,1521`(`addLineageParent`·`removeLineageParent`·`confirmLineage`) · `core-ai.yaml:308`(`ParentCandidateSuggestion`) · core 릴레이 선례 `services/core-api/src/colab_core/app/routes/preview.py:83`(`listPalettes`) ＋ `_require_target_access :56`.
- **할 일** — ⑴ `core-viz` `GET /targets/describe`(가칭 · 패키지가 이름 확정 · 입력 `RenderTarget` · 출력 = drawable 변수명 배열 ＋ 시각 목록(건수·첫·끝) ＋ 서버 기본값 · 읽기 전용 · 캐시 키 무접촉) ＋ viz-render 라우트(`readers.py:341-343` drawable 규칙 · `:295-333 _time_index` 그대로) ＋ core 릴레이 1건 ⑵ `processingLevelUserSet` optional 첨가 — `LineageGraph` 노드 · `ProjectDatasetRow`(`processingLevel` required 유지) ⑶ `DataMap.byCategory` optional(`byTopic` 유지 · 5값 전부 줄 유지) ⑷ `declareLineageUnknown` · `updateLineageParentMethod` 신설(형제 경로 모양 · 사람 호출 · D10→D4 아님) ⑸ `ParentCandidateSuggestion.parentProcessingLevel` optional ⑹ `generated-up-to-date` 재생성 ＋ 서버 수용 목록 동시 집행(§5-㉰-4 「집행 없는 신설」 금지).
- **수용 기준** — `contract-lint`·`generated-up-to-date` green · `contract-breaking` 출력 축자 = **파괴 0**(㉯ 가 나오면 멈추고 보고) · `describe` 시험 = NetCDF 픽스처 drawable 배열이 `_pick_default` 와 같은 순서 · GeoTIFF = `band1..N` · `declareLineageUnknown` 이 확정 부모 있는 데이터셋에 **400** · `method` 수정이 `confirmedAt` 을 바꾸지 않음 · `byCategory` 5값 전부(0 이어도 줄 유지) · `ai-no-lineage-write` green.
- **시험 seam** — viz-render `tests/test_upload_target_and_partial.py`·`test_instant_and_grid_digest.py` · core-api `tests/test_preview_relay.py`·`test_lineage_unknown.py`·`test_dashboard.py`.
- **좁은 게이트** — `contract-lint` · `contract-breaking` · `generated-up-to-date` · `seam-consistency` · `ai-no-lineage-write` · `service-tests-viz-render` · `service-tests-core-api` · `frontend-typecheck`(생성 타입).
- ⛔ §5-㉰-6(묶음 쪼개기) 금지 — 6건을 WU 별로 쪼개 각각 ㉮ 로 통과시키지 않는다. 목적 단위로 판정한다.

### WU-C7 · 서버 소형 ＋ 마이그레이션 2건 (질의 9·19·20·36·5 ＋ R-A′ 이월) — 계층 DB·서버 · 크기 L · 레인 `rc-server-fix`

- **의존**: WU-C10(계약 없이 되는 항목이 대부분이나 head 순서를 위해 뒤에 선다).
- **현재 코드** — 프로젝트 이름: `db/platform/schema.sql:1047`(`CREATE TABLE d6_project` · UNIQUE 0) · 앱 방어선 `routes/project.py:148` 뿐 → **DB 제약 추가**(앱 400 은 이미 있다 · WU-A7R). 공개 범위 내림: `routes/catalog.py:1113,1393`(`업로드·편집` 스위치 보유자 전원). 이관 빈틈: `db/platform/versions/0017_rb4_access_state_3.py:23-25`(`NULL → NULL`). `ordinal`: `services/core-api` `grep -rn ordinal` 0행 퇴행 분기. `replace_variables`: `d3_catalog.py:280`(행별 트리거 N+1). `d9_topic_synonym`: `db/ai/schema.sql:85`(4값) ↔ `db/platform/schema.sql:440`(`category` 5값). 현 head = `0019_rb7_search_index_m10`(`versions/0019_…py:75-76`).
- **할 일** — ⑴ `0020_rc7_project_name_unique`(`down_revision = 0019` · `UNIQUE (lab_id, name)` · 기존 중복 행 있으면 **멈추고 건수 보고 · 지우지 않는다**) ⑵ `0021_rc7_access_state_gap`(`down_revision = 0020` · 조건 = `0017:25` NULL 행 ∧ 연구실 기본 `잠김` ∧ 유효 grant ≥1 → `지정 공개` · 이동 행 수 출력 · 실물 건수는 배포 창이 적는다 · 0 이어도 체인에 남긴다) ⑶ 각각 `db/platform/tests/00NN-drift.sh`＋`-assertions.sql` 짝 ⑷ 내림 권한 소유자 한정(403) ⑸ `ordinal` 0행 읽기 퇴행 제거 ⑹ `replace_variables` statement-level 트리거 ⑺ `db/ai/versions/0004_*`(down = `0003_k2_ontology_seed`) `d9_topic_synonym` 5값 CHECK ＋ 이관(ai-service 소유 · `db/ai/tests/0004-0005-drift.sh` 선례).
- **수용 기준** — 같은 연구실 같은 이름 INSERT 가 **DB 에서** 거절(앱 우회) · 다른 연구실 성공 · 내림 요청 소유자 아니면 **403** · 소유자 200 · `0021` 픽스처 3종(NULL∧잠김∧grant / NULL∧열림 / 잠김∧grant0) 중 **첫 것만** `지정 공개` 이고 이동 행 수 1 이 출력에 보인다 · `ordinal` 0행 요청이 옛 배열로 퇴행하지 않음 · N행 `replace_variables` 에 트리거 실행 **1회** · `d9` 5값 CHECK · `state='잠김' ∧ 유효 grant ≥1` 행 **어느 시점에도 0건**(R-B 경계 증명 유지) · drop 0 · head 1.
- **되돌림** — 제약 DROP ＋ `지정 공개`→`잠김` 역이관(값 소실 0). 축자를 〈N〉 ④ 에 적는다.
- **시험 seam** — core-api `tests/test_project_name_duplicate.py`·`test_access_state_three.py`·`test_variable_rows.py` · `db/platform/tests/00NN-drift.sh` 형태.
- **좁은 게이트** — `migration-single-head` · `schema-diff` · `migration-drift`(C6 신설) · `rls-coverage` · `rls-effect` · `db-boundary` · `service-tests-core-api` · `service-tests-ai-service`.

### WU-C9 · Lv 표시 사람 값 통일 ＋ 제안 Lv ＋ ProjectDatasetRow (질의 27·41·23·24) — 계층 서버·FE · 크기 M · 레인 `rc-lv-unify`

- **의존**: WU-C10(첨가 ⑵⑸ 계약).
- **현재 코드** — 계보 노드 `services/core-api/src/colab_core/app/routes/lineage.py:75-76`(파생값) · 프로젝트 표 `routes/project.py:250`(파생값) · 카탈로그·상세 = 사람 값 우선(R-B B5·B10) · 상세 모달 기준 Lv(B10 advisor 845d68d 사람 값). 화면 충돌 판정은 서버 400 이 받는다(§5-23).
- **할 일** — 서버 조립 함수 **하나**(사람 값 ＋ 파생값 둘 다 싣는다 · `processingLevel` 의미 무변 · `processingLevelUserSet` 첨가) → 노드·프로젝트 표가 그것을 쓴다 · FE 4자리(카탈로그·상세·계보 노드·프로젝트 표)가 **같은 표시 규칙 함수**(사람 값 우선 · 없으면 파생값)를 부른다 · AI 제안에 `parentProcessingLevel` 을 실어 화면 충돌 판정이 그 값을 쓴다.
- **수용 기준** — 사람 값 ≠ 파생값 픽스처에서 4자리 표시 Lv **동일** · 제안 응답에 `parentProcessingLevel` · 제안 선택 시 화면 충돌 판정이 서버 400 전에 그 값으로 뜬다 · `processingLevel` 열쇠 값은 종전과 같다(회귀).
- **시험 seam** — core-api `tests/test_lineage_graph_read.py`·`test_lv_parent_rules.py` · `frontend/test/detail.test.tsx` · ai-service 제안 시험.
- **좁은 게이트** — `service-tests-core-api` · `service-tests-ai-service` · `frontend-typecheck` · `frontend-test` · `contract-breaking`(재확인).

### 마이그레이션 — 한 head

- 현 head = **`0019_rb7_search_index_m10`**. `0020` → `0021` 이 잇는다 · `migration-single-head` 가 잰다 · `db/ai` 는 별 체인(`0004`).
- ⛔ drop 0 · 컬럼 삭제 0 · 사람 입력값 자동 변경 0(중복 이름 자동 개명 금지 · spec 우려 6).
- ⛔ `0021` 실물 건수는 **배포 창 실측**이 적는다(판정 20 축자) — 레인은 픽스처로 짓는다.

---

## 3. 지켜야 하는 규약 — 명령으로

### ㉮ 워크트리 레인
- WU 하나에 레인 하나 = `rc-gate-drift`(C6) · `rc-contract-21`(C10) · `rc-server-fix`(C7) · `rc-lv-unify`(C9). 통합 브랜치 `integration/r-c` 에서 딴 자기 워크트리 · 병합은 **ff** · 병합 뒤 브랜치 정리. **직렬**(C7 의 head 가 C10 뒤 · C9 가 C10 뒤).

### ㉯ 착수 전 — `work-items.yaml` 등재는 **이미 끝났다**
- `WU-C1`~`WU-C12` 12 블록이 대장에 있다(`status: open`). 확인 = `grep -n -A14 '^  - id: WU-C6' dev-package/work-items.yaml`. 이 세션이 하는 것은 **상태 갱신**(완료 시 `done` ＋ `evidence`). ⛔ 원장 행 없이 마이그레이션을 만들지 않는다.

### ㉰ 계약 동결 해제 — **21차 · 등급 전망 ㉮ · Ted 승인 필수**
- 근거 = `dev-package/sessions/X2-FREEZE-PROTOCOL.md §5`. 직전 회차 = **20차(R-B)**. 회차 번호 발급처 = `PLAN-SoT §9`.
- 승인 요청 패키지 = `dev-package/sessions/R-C-C21-REQUEST-<날짜>.md` → Ted 승인 문장(원문 그대로)이 `intent/2026-09-08-r-c.md ## 확인` 에 실린다 → 그 뒤 `contracts/` 개방.
```bash
./gates/run.sh contract-breaking     # ⑴ 파괴 판정을 출력으로 낸다(주장하지 않는다)
grep -rn 'describe\|processingLevelUserSet\|byCategory\|declareLineageUnknown\|updateLineageParentMethod\|parentProcessingLevel' contracts/ services/ frontend/src | wc -l   # ⑵ 소비자 수
```
- ⛔ 승인 없이 `contracts/` 를 고치지 않는다 · ⛔ §5-㉰-4 집행 없는 신설 · ⛔ §5-㉰-6 묶음 쪼개기.

### ㉱ 결정 번호 〈N〉 — 예약하지 않는다
```bash
git fetch origin main && bash dev-package/prd/tools/max-decision.sh   # 병합 직전에 다시 잰다
```
- 착수 시점 참고값 = **〈374〉**(2026-09-08 실측 · 근거 아님). 병합 직전 `origin/main` 최대 ＋ 1. 행 문안은 `R-C-3-verify.md ㉱`(intent:·spec: 두 필드 포함). ⛔ HANDOFF 에 값을 적지 않는다.

### ㉲ 게이트 — 작업 중엔 단독, 병합 전엔 전건
```bash
COLAB_GATE_REPORT_DIR=dev-package/reports/R-C/<레인> ./gates/run.sh <좁은 게이트>   # §2 각 WU 의 목록
./gates/run.sh all -j 1                                                          # 라운드 끝 · R-C-3 에서 한 번
```
- ⛔ 게이트를 끄거나 대상을 줄이지 않는다 · 구현 전 **red 를 눈으로 확인**한다 · 대상 0건은 red 다.

### ㉳ 커밋 문면
```
계약·DB R-C-1 <WU 제목> (WU-C_)

- <바뀐 자리 1~3줄>
- 계약 21차 첨가 <n>건 · 마이그레이션 <n>건(head 1 · 앞 head 0019_rb7_search_index_m10) 또는 0
- RED 선실측 → GREEN: <시험 파일>:<건수>
```

### ㉴ 금지
- ⛔ `main` 직접 push · ⛔ staging DB 직접 쓰기 · ⛔ 원장 행 없이 마이그레이션 · ⛔ 승인 전 `contracts/`.
- ⛔ 서버가 `processingLevel` 에 사람 값을 덮어 쓰기(㉯ 화) · ⛔ 변수명 UNIQUE · ⛔ 중복 프로젝트 이름 자동 개명 · ⛔ core 가 NetCDF 를 열어 변수 목록 생성(`CLAUDE.md §3-4`).
- ⛔ `〈194〉`·`〈276〉` 원문 · POL-021 원문 지우기 — 반전은 **덧붙이는 것**이다.

---

## 4. 산출물과 근거

| 무엇 | 어디 |
|---|---|
| 승인 패키지 | `dev-package/sessions/R-C-C21-REQUEST-<날짜>.md` — 첨가 6건 · `contract-breaking` 출력 축자 · 소비자 수 · 되돌림 |
| 게이트 | `gates/tools/migration-drift.sh` ＋ selftest · `gates/run.sh` `ALL_GATES` · README 표 1행 |
| 계약 | `contracts/seams/core-viz.yaml`(describe) · `fe-core.yaml`(릴레이 · `processingLevelUserSet` · `byCategory` · 계보 op 2) · `core-ai.yaml`(`parentProcessingLevel`) · `generated/` 재생성 |
| 마이그레이션 | `db/platform/versions/0020_…`·`0021_…` ＋ `tests/0020-drift.sh`·`0021-drift.sh` 짝 · `db/ai/versions/0004_…` |
| 서버 | `routes/preview.py`(릴레이) · `routes/catalog.py`(내림 권한) · `routes/lineage.py`·`routes/project.py`(조립 함수) · `d3_catalog.py:280` · viz-render `app/routes/` describe |
| 세션 노트 | `dev-package/sessions/rc-gate-drift-<YYYYMMDD>.md` · `rc-contract-21-…` · `rc-server-fix-…` · `rc-lv-unify-…` — 각 ≤ 60행 |
| 대장 | `work-items.yaml` — 4 블록 완료 시 `status: done` ＋ `evidence` |

**HANDOFF 갱신문(오케스트레이터가 붙인다 · 5줄 이하 · 세션은 `03-HANDOFF.md` 를 직접 고치지 않는다)**
```
R-C-1(계약·DB) 완료 — WU-C6·C10·C7·C9, 레인 rc-gate-drift · rc-contract-21 · rc-server-fix · rc-lv-unify, 병합 <sha>
계약 21차 첨가 6건 · 등급 <㉮/㉯ 실측> · Ted 승인 <일자> · 마이그레이션 0020·0021 head 1 ＋ db/ai 0004 · 게이트 migration-drift 신설(오라클 11)
게이트: 좁은 집합 green · contract-breaking 출력 = <축자> · 0021 이동 행(픽스처) = 1 · 실물 건수 = 배포 창
근거: dev-package/sessions/rc-*-<YYYYMMDD>.md 4건
다음 = R-C-2-frontend.md(C1~C5·C8·C11)
```

---

## 5. 완료 판정

- **WU-C6** — `migration-drift` 가 11벌을 돌고 건수를 출력한다 · 1벌 부재·대상 0건·alembic 부재가 각각 red · selftest 짝 4케이스 · `schema-diff` 가 `upgrade head` 뒤에만 비교.
- **WU-C10** — 승인 커밋 → `contracts/` 첫 수정 순서 · 첨가 6건 · `contract-breaking` 파괴 0(㉯ 면 멈춤) · `generated-up-to-date` green · describe·계보 op 2·byCategory 서버 집행 동시.
- **WU-C7** — `0020`·`0021` head 1 · drop 0 · DB 제약 실거절 · 내림 403/200 · `0021` 픽스처 1행 이동 · `ordinal` 퇴행 0 · 트리거 1회 · `d9` 5값 · `잠김 ∧ grant ≥1` 0건.
- **WU-C9** — 4자리 Lv 동일 · `parentProcessingLevel` · `processingLevel` 회귀 0.
- **절차** — 21차 승인이 `contracts/` 첫 수정보다 먼저(커밋 순서) · 〈N〉 병합 직전 실측 · POL-021 반전은 R-C-2(C5) 소관이나 원문 무삭제 원칙은 여기서도 같다.

### 다음 파일
`dev-package/prd/rounds/R-C-2-frontend.md`(C1 · C2 · C3 · C4 · C5 · C8 · C11) → `R-C-3-verify.md`(C12 ＋ 종료 검증). C3 은 C10 의 describe 계약이 병합된 뒤에만 착수한다.
