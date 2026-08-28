# STAGE2-PARALLEL-MAP — Stage 2 병렬 착수 충돌 지도

／ 작성 2026-08-28 · 읽기 전용 조사(편집·커밋 0) · 대상 15 항목(`J-1` 은 Ted 유예로 제외)
／ 근거 = `dev-package/work-items.yaml`(정본 대장 · 84 항목) ＋ 이번 회차 실측

---

## 0. 착수 전 실측 — 상태 기호가 아니라 게이트를 돌렸다

`./gates/run.sh work-item-consistency` **2026-08-28 이번 회차 실행** 결과:

```
work-item-consistency: 대장 84건 · ㈐ 진실원 대조 48행 · ㈏ 체크리스트 대조 41건
                     · ㈑ 착수 후보 33행 · ㈒ 기한 5건 · ㈓ conflict 12건
::error::work-item-consistency — 불일치 13건
```

**⚠ 지시문과 레포의 차이 1건 — 진행 전 정정한다.**
지시문은 「13 known `conflict` items」라 적었으나 **실물은 `conflict` 12 건**이다.
13 은 `conflict` 12 ＋ ㈑ `I0` 1(`deferred` 인데 착수 후보 표에 실려 있음)의 **불일치 합계**이지
conflict 계수가 아니다. 근거 = `03-HANDOFF` 머리말 「불일치 13 = conflict 12 ＋ ㈑ `I0` 1」.
아래 판정은 **conflict 12 건 기준**이다.

`conflict` 12 건 (실행 출력 그대로):
`S2b` · `I1` · `I3` · `X-2` · `R-1` · `J-1` · `P2` · `P6` · `S1` · `PA` · `S2` · `2단-BC120`

게이트가 스스로 밝힌 **검사 대상 밖 9 건**이 있다 — green 이 「전부 봤다」가 아니다.
그중 이 문서에 걸리는 것 = **㈒ `PA-G` 기한 발동 여부 `unknown` — 사람이 판정해야 한다.**

---

## 1. 항목별 판정 15건

각 항목: ① 실제 진입 상태 ② 완료 정의(축자 출처) ③ 파일 면 ④ 규모

### T-1 — `ts_config` 한국어 재작성

① **진입조건 실제로 성립.** `depends_on: []` · `entry_conditions: ["stage 2 초반 — 「지금이 가장 싸다」(데이터셋 12)"]`.
   **conflict 항목 의존 0.** 15 건 중 이것 하나만 의존이 비어 있고 진입조건이 시점 진술뿐이다. → **착수 가능**
② 완료 정의 **있음** — `WORK-UNITS §10.2` 「↳ T-1 완료 정의 (2026-08-27 확장 · `〈167〉-㉱`)」 4항:
   ⓐ `ts_config` 한국어 재작성 ＋ 전 행 재생성 ⓑ 온톨로지 어휘·관계 확장을 같은 회차에(`〈164〉-㉮`)
   ⓒ `public` 밖 객체 재측정(`〈165〉-㉰`) ⓓ 검색 평가셋 A층 실패 8건 재측정·보수(`S2b-SEARCH-EVALSET`
   · 기대값은 정본·판정에서만 도출하고 검색을 돌려 역산하지 않는다)
③ 파일 면 —
   - `db/platform/versions/` (신규 마이그레이션 · 기존 `0005_s1_search_index.py`·`0006_s1_trgm_matching.py` 계승)
   - `db/platform/schema.sql` · `db/platform/tests/0005-assertions.sql` · `0006-assertions.sql` · `0006-drift.sh`
   - `services/core-api/src/colab_core/domains/d3_catalog.py` · `services/core-api/tests/test_search_execution.py`
     · `services/core-api/tests/fixtures/setup-db.sh`
   - ⓑ 로 **`db/ai/seed/` · `db/ai/versions/` · `services/ai-service/src/colab_ai/domains/d9_ontology.py`**
   - ⓓ 로 `eval/k4-search/` · `dev-package/sessions/S2b-SEARCH-EVALSET.md`
④ 규모 — 파일 10~14 · **DB 필요(전 행 재생성)** · **staging 필요**(적재분 재생성). 큼.

### F-1 — S-08 화면 (미등록 미리보기 화면 자체)

① **진입조건 실제로 성립.** `depends_on: []` · `entry_conditions: ["P3 와 병렬 가능"]`.
   **conflict 항목 의존 0.** → **착수 가능**
   ⭑ **실측 — 화면 파일은 이미 있다.** `frontend/src/routes/UnregisteredPreviewPage.tsx` **142 행 실재**이고
   `frontend/src/app/routes.tsx:13` 이 「S-08(미등록 미리보기 화면)은 stage2 대기 — **라우트만 뺀다. 파일은 유지한다**」로
   라우트를 명시적으로 뺀 상태다. 즉 F-1 은 신규 작성이 아니라 **라우트 복원 ＋ 등록 진입 경로 복원**이다
   (`WORK-UNITS §1` 2행 — 「되살리면 `handoff.ts` 의 등록 진입 경로까지 함께 돌아온다」).
② **완료 정의 미작성** — 대장 `completion_def: 완료 정의 미작성` · `WORK-UNITS §10.2` F-1 행에 완료 정의 열 없음
   · `03-HANDOFF §1` 에 행 자체가 없음. **지어내지 않는다.**
③ 파일 면 —
   - `frontend/src/app/routes.tsx` (라우트 복원)
   - `frontend/src/routes/UnregisteredPreviewPage.tsx`
   - `frontend/src/components/preview/handoff.ts` · `PreviewPanels.tsx` · `PreviewControls.tsx` · `types.ts` · `preview.css`
   - `frontend/src/shell/nav.ts` · `frontend/test/preview.test.tsx`
④ 규모 — 파일 4~8 · **DB 불필요 · staging 불필요**(단, 완료 정의가 생기면 `§4` I2 이후 공통의 staging 배포 green 이 붙을 수 있다 `[미확인]`). 작음.

### V-1 — 팔레트 선택 재렌더

① **불성립.** `depends_on: [P3]` · `P3` 는 `open` 이고 그 `P3` 가 `depends_on: [P2, D5]` 이며
   **`P2` 는 conflict 12 건 중 하나(미실측)** → **착수 불가**(2단 건너 conflict).
② **완료 정의 미작성** (대장 `completion_def: 완료 정의 미작성`).
   ⚠ 범위 경계만 있다 — 「서버측 재렌더 경로까지 · 팔레트 **선택 UI** 는 `§J-6` 이고 `J-1` 묶음에 남는다」(`〈167〉-㉵`). 범위는 완료 정의가 아니다.
③ 파일 면 — `services/viz-render/src/colab_viz/domains/d7_visualization/palettes.py` · `colormap.py` · `cache.py`
   · `services/viz-render/src/colab_viz/app/routes/style.py` · `renders.py` · `contracts/seams/core-viz.yaml` · `services/viz-render/tests/`
④ 규모 — 파일 5~8 · DB 불필요 · staging 필요(배포 green). 중간.

### V-2 — 값 조회

① **불성립.** `depends_on: [P3]` → `P3 ⊇ P2(conflict)` → **착수 불가**.
② **완료 정의 미작성.**
③ 파일 면 — `services/viz-render/src/colab_viz/domains/d7_visualization/raster.py` · `readers.py` · `coords.py` · `grid.py`
   · `app/routes/renders.py` · `contracts/seams/core-viz.yaml` · `services/core-api/src/colab_core/ports/relay.py`
   · `frontend/src/components/preview/` (지도 클릭 경로)
④ 규모 — 파일 6~10 · DB 불필요 · staging 필요. 중간.

### Y-1 — 자동 무효화

① **불성립.** `depends_on: [P3, D5]` · `P3 ⊇ P2(conflict)` · `D5` 는 `partial` → **착수 불가**.
② 완료 정의 **있음** — `WORK-UNITS §10.2-b` Y-1 행(2026-08-27 작성 · `〈168〉-㉶`) 6항 ⓐ~ⓕ:
   ⓐ 무효화 대상 = 렌더 산출물뿐 ⓑ 트리거 3종 각각 시험 ⓒ 수동 「미리보기 다시 만들기」 흡수
   ⓓ stage 1 의 「자동 재생성 안 함」이 여기서만 뒤집힘 ⓔ 경계(무효화·재생성 D7 · 트리거 발신 D5 · Port 경유) ⓕ staging 배포 green
③ 파일 면 — `services/viz-render/src/colab_viz/domains/d7_visualization/cache.py` · `jobs.py` · `services/viz-render/src/colab_viz/ports/source.py`
   · `services/pipeline-worker/src/` (트리거 발신 D5) · `contracts/seams/core-viz.yaml` · `db/platform/versions/`
④ 규모 — 파일 8~12 · **DB 필요 · staging 필요**. 큼.

### P3 — 계보 그래프 · 2D 시각화 3종 · createScreenshot · 렌더 표현 확장

① **불성립.** `depends_on: [P2, D5]` — **`P2` 가 conflict** (「`§11` 은 🟧 · `§10.2`/`§10.3` 은 P3 ⊇ P2(✅)」로 갈림) · `D5` 는 `partial`.
   → **착수 불가.** 이것이 Stage 2 병목의 뿌리다 — `V-1`·`V-2`·`Y-1`·`S3`·`P6` 이 전부 여기 매달린다.
② 완료 정의 **있음** — 「각 P 의 완료 판정」 4항(`WORK-UNITS §7` 말미 — 수용 기준 · 도메인 게이트 green · staging 배포 green · 목업 대비 화면 검증). ＋ 타일 서빙·확대 · `createScreenshot` 이 완료 정의로 올라옴(`§10.2` 말미).
③ 파일 면 — `contracts/seams/core-viz.yaml` · `contracts/seams/fe-core.yaml`
   · `services/viz-render/src/colab_viz/domains/d7_visualization/` **전면**(`tiles.py`·`raster.py`·`grid.py`·`scale.py`·`cache.py`·`preview.py`)
   · `services/viz-render/src/colab_viz/app/routes/renders.py`
   · `services/core-api/src/colab_core/domains/d4_lineage.py` · `app/routes/lineage.py` · `app/routes/preview.py` · `ports/relay.py`
   · `services/pipeline-worker/src/` (COG) · `frontend/src/components/preview/` · `frontend/src/components/lineage/` · `db/platform/versions/`
④ 규모 — 파일 25＋ · **DB 필요 · staging 필요**. 매우 큼(「P3 은 stage 2 전체다」 `〈74〉`).

### P6 — 승인 처리

① **불성립 · 이중.** ㉮ 자기 자신이 **conflict**(`I4 ── P6` 사슬을 `§10.2-b` 는 끊었다 하고 `§10.3`·`§9` 그래프는 남겨 둠).
   ㉯ `depends_on: [P1, P2, P3, P4, P5]` 에서 **`P2` conflict · `P3` open · `P5` partial** → **착수 불가**.
② 완료 정의 **있음** — 「각 P 의 완료 판정」 4항(`§7` 말미). ⚠ `§10.2-b` 가 「열린 것 `⑭`(접근 승인 조기 회수 규칙)가 이 WU 를 향해 미판정」이라 적는다.
③ 파일 면 — `services/core-api/src/colab_core/domains/d2_access.py` · `app/routes/` 다수 · `contracts/seams/fe-core.yaml`
   · `frontend/src/permission/` · `frontend/src/placeholders/{VerifiedBadgeSlot,LockIndicatorSlot}.tsx`
   · **앞 화면 7곳**(`frontend/src/routes/` 대부분) · `frontend/test/permission.test.tsx`
④ 규모 — 파일 20＋ · DB 가능 · staging 필요. 매우 큼. **프론트 전면을 잠근다.**

### P7 — 연구실 대시보드

① **불성립.** `depends_on: [P6]` — **`P6` 가 conflict** → **착수 불가**.
② 완료 정의 **있음** — 「각 P 의 완료 판정」 4항(`§7` 말미).
③ 파일 면 — `services/core-api/src/colab_core/domains/d8_insight.py` · `d1_identity.py` · `app/routes/identity.py`
   · `contracts/seams/fe-core.yaml` · `frontend/src/routes/LabPage.tsx` · `frontend/src/placeholders/TodoInboxSlot.tsx`
④ 규모 — 파일 10~15 · DB 필요 · staging 필요. 큼.

### P8 — E-01 적용 지점 표

① **불성립.** `depends_on: [P7]` → `P7 ⊇ P6(conflict)` → **착수 불가**(3단 건너).
② 완료 정의 **있음** — 「각 P 의 완료 판정」 4항(`§7` 말미).
③ 파일 면 — `services/core-api/src/colab_core/domains/d2_access.py` · `contracts/seams/fe-core.yaml` · `frontend/src/permission/`
④ 규모 — 파일 5~10 · DB 불필요 추정 `[미확인]` · staging 필요. 중간.

### K3 — 계보 제안 서비스

① **경계 판정 — 진입조건은 성립, 의존에 conflict 1건.**
   `entry_conditions: ["K2(✅) · D2(✅) — 열려 있다", "`P2` 산출만 필요해 `D5`·`P3` 과 병렬"]` · `depends_on: [K2, D2, P2]`.
   `K2`·`D2` 는 `done` 실측 확인. **그러나 `P2` 는 conflict 12 건 중 하나** → **규칙상 착수 불가.**
   ⚠ 이것이 15 건 중 **가장 얕게 막힌 항목**이다 — `P2` 실측 1회로 풀린다.
   ⭑ 추가 — `X-5` note 가 「`suggestLineage` 는 **판정 아님, `K3` 착수 순서로 이관**」이라 적어 착수 시 첫 판정이 딸려 온다.
② 완료 정의 **있음** — `WORK-UNITS §8` / `§10.2-b` K3 행: 「평가셋 대비 제안 품질 ＋ **`D4` 쓰기 경로 부재 음성 테스트 green**」.
③ 파일 면 — `services/ai-service/src/colab_ai/domains/d10_ai_services.py` · `d9_ontology.py`(읽기)
   · `services/ai-service/src/colab_ai/app/interpret.py` · `ports/` · `contracts/seams/core-ai.yaml`
   · `services/ai-service/tests/` · `db/ai/` (평가셋·시드) · `eval/`
④ 규모 — 파일 8~12 · DB(`db/ai`) 필요 · staging 필요. 큼.

### K5 — 제안 원장

① **불성립.** `depends_on: [K3]` · `K3` 는 `open` 이고 그 위가 `P2`(conflict). **「엄격 직렬 K5 ⊇ K3」**(대장 note) → **착수 불가**.
② 완료 정의 **있음** — 「원장 왕복 테스트」(`WORK-UNITS §8`).
③ 파일 면 — `services/ai-service/src/colab_ai/domains/d10_ai_services.py` · `db/ai/versions/`(원장 테이블 신규) · `contracts/seams/core-ai.yaml` · `services/ai-service/tests/`
④ 규모 — 파일 5~8 · **DB(`db/ai`) 필요** · staging 필요. 중간.

### S3 — 실데이터 4종 E2E

① **불성립 · 이중.** `depends_on: [S2, P3]` — **`S2` 가 conflict**(staging 실물 계수가 문단마다 다름) · `P3` 는 open.
   → **착수 불가**.
   ⚠ 대장에 `S3-e2e-4종` 이라는 **중복 계상 항목**이 따로 있다(`WORK-UNITS §11` 무식별자 줄 · 스스로 「= S3」이라 밝힘). 두 에이전트에 나눠 주면 같은 일을 두 번 한다.
② 완료 정의 **있음** — `WORK-UNITS §8.5` S3 행: 「4종 각각 최소 1건이 시각화 화면에 그려지고 계보가 확정 상태로 남는다. GeoTIFF 를 가장 먼저 돌린다. 실패 파일은 목록으로 남긴다」.
   ⚠ 이름은 「4종」인데 `㊿`·`〈77〉` 은 5종(＋NumPy)으로 올림 — 이름과 값이 어긋난다.
③ 파일 면 — **코드 면이 아니라 운영 면이다.** `infra/staging/`(적재·검증 스크립트) · staging 실물 · `dev-package/sessions/` 산출
   · 회귀 시 `services/pipeline-worker/` · `services/viz-render/`
④ 규모 — 코드 파일 0~5 · **DB 필요 · staging 필수(실물 접촉)**. 큼 · 운영 경계 규율(`SKILL §6`) 적용 대상.

### I3 — 배포 자동화

① **불성립.** 자기 자신이 **conflict**. 한 문서 세 절이 갈렸다 — `03-HANDOFF §1 T-I` ⬜＋「✅ 차단 해제」 · `§10` 「⛔ 판정 7건 남음」 · `§10.2-b` 「✅ 차단 해제」 · `§10.3` 「⛔ I3 7건 판정이 선행」 · `§11` ⬜.
   → **착수 불가.** 사람이 `sessions/TED-DECISIONS-OPEN.md §A` 의 7건을 세어 판정할 자리.
   ⭑ `X-5` 가 남긴 `[미확인]` 1건(**staging 실물의 `403`**)이 `I3` 에 딸려 있다.
② 완료 정의 **있음** — 「파이프라인 1회 완주」(`WORK-UNITS §4` · 정본 `§10.2-b`).
③ 파일 면 — `.github/workflows/ci.yml` · `infra/staging/deploy.sh` · `rollback.sh` · `compose.i2.yml` · `gates/`
④ 규모 — 파일 5~10 · DB 불필요 · **staging 필수**. 중간.

### I4 — 운영 준비 (추적·알람·복구 리허설)

① **불성립.** `depends_on: [I3]` — **`I3` 가 conflict** → **착수 불가**.
   ⚠ 대장 note — 「`R-1` 과 복원 리허설 재료가 겹치는데 한쪽이 다른 쪽을 흡수하는지 두 문서 모두 미기재」이고 **`R-1` 도 conflict** 다. 의존이 conflict 둘에 걸린다.
② 완료 정의 **있음** — 「복원 리허설 성공」(`WORK-UNITS §4` · 정본 `§10.2-b`).
③ 파일 면 — `infra/staging/backup/` · `infra/staging/restore/` · `infra/staging/compose.i2.yml` · `gates/` · `.github/workflows/ci.yml`
④ 규모 — 파일 8~12 · DB 접촉(읽기 전용 규율) · **staging 필수**. 큼.

### PA-G — 구글 IdP 어댑터

① **불성립 · 이중.** ㉮ `depends_on: [PA]` — **`PA` 가 conflict**(✅ 와 「상태 글리프 자체가 없음」이 갈림).
   ㉯ `deadline.fired: unknown` — **이번 회차 게이트가 「`PA-G`: 기한 발동 여부가 `unknown` — 사람이 판정해야 한다」를 검사 대상 밖으로 출력했다**(실측).
   진입조건이 「stage 1 완료 판정」인데 그 판정이 나 있지 않다. → **착수 불가**.
② 완료 정의 **있음** — `WORK-UNITS §10.2-b` PA-G 행(2026-08-27 작성 · `〈168〉-㉷`) 6항 ⓐ~ⓕ:
   ⓐ 어댑터가 `kernel/authn.py` **한 파일에만** ⓑ 비밀번호 발급 경로 제거(`PasswordIssuer`·`CredentialStore` 제거 · 공존시키지 않는다)
   ⓒ `credentials.json`·`ops/set-password.py` **폐기** ⓓ `admin` 계정 처리 ＋ 「비밀번호로 로그인되는 경로 0」 음성 시험
   ⓔ PA ①②③⑤⑥ 재통과 ⓕ staging 배포 green. **⚠ PA ④(마이그레이션 0)는 승계하지 않는다.**
③ 파일 면 — `services/core-api/src/colab_core/kernel/authn.py`(실재 확인) · `credentials.py` · `password.py` · `session_token.py`
   · `services/core-api/ops/set-password.py`(삭제 대상 · 실재 확인) · `frontend/src/auth/{LoginPage.tsx,AuthGate.tsx,store.ts}`
   · `contracts/seams/fe-core.yaml` · `frontend/test/auth.test.tsx` · staging 호스트의 `credentials.json` 실물
④ 규모 — 파일 8~12 · DB 여부 **`[미확인]`**(완료 정의 ⓕ 주석이 「저장이 필요한지 근거 없이 단정할 수 없다 — 착수 회차가 실물로 판정」이라 명시) · **staging 필수**. 큼 · **비가역 요소 포함**(자격 파일 삭제).

### J-1 — 편의 기능 묶음 — **제외(Ted 유예)**

지시대로 분석 대상에서 뺀다. 단 **충돌 정보 1건만 남긴다** — `V-1` 의 **팔레트 선택 UI** 는 `§J-6` 으로 `J-1` 묶음 안에 있다(`〈167〉-㉵`).
`V-1` 을 여는 회차는 그 UI 를 건드리지 않는다. 또 대장 `J-1` 은 **conflict**(§J 계수가 10 건/9 건으로 갈림)이다.

---

## 2. 충돌 행렬 — 같은 파일 면을 쥐는 조합

축약: **CTR**=`contracts/seams/` · **VIZ**=`services/viz-render/.../d7_visualization/` · **CORE**=`services/core-api/src/colab_core/`
· **AI**=`services/ai-service/src/colab_ai/` · **FE**=`frontend/src/` · **DBP**=`db/platform/` · **DBA**=`db/ai/` · **INF**=`infra/staging/` ＋ `.github/workflows/`

| | T-1 | F-1 | P3 | V-1 | V-2 | Y-1 | P6 | P7 | P8 | K3 | K5 | S3 | I3 | I4 | PA-G |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **T-1** | — | · | DBP | · | · | DBP | · | · | · | **AI·DBA** | DBA | DBP | · | · | · |
| **F-1** | · | — | **FE preview** | · | FE preview | · | **FE routes** | · | · | · | · | · | · | · | · |
| **P3** | DBP | **FE preview** | — | **VIZ·CTR** | **VIZ·CTR** | **VIZ·CTR** | **CTR·FE** | CTR | CTR | · | · | staging | · | · | CTR |
| **V-1** | · | · | **VIZ·CTR** | — | **VIZ·CTR** | **VIZ cache** | CTR | CTR | CTR | · | · | · | · | · | CTR |
| **V-2** | · | FE preview | **VIZ·CTR** | **VIZ·CTR** | — | VIZ | CTR | CTR | CTR | · | · | · | · | · | CTR |
| **Y-1** | DBP | · | **VIZ·CTR** | **VIZ cache** | VIZ | — | CTR | CTR | CTR | · | · | staging | · | · | CTR |
| **P6** | · | **FE routes** | **CTR·FE** | CTR | CTR | CTR | — | **CORE·CTR·FE** | **CORE d2·CTR** | · | · | · | · | · | **CTR·FE auth** |
| **P7** | · | · | CTR | CTR | CTR | CTR | **CORE·CTR·FE** | — | **CORE·CTR** | · | · | · | · | · | CTR·FE |
| **P8** | · | · | CTR | CTR | CTR | CTR | **CORE d2·CTR** | **CORE·CTR** | — | · | · | · | · | · | CTR |
| **K3** | **AI·DBA** | · | · | · | · | · | · | · | · | — | **AI d10·CTR·DBA** | · | · | · | · |
| **K5** | DBA | · | · | · | · | · | · | · | · | **AI d10·CTR·DBA** | — | · | · | · | · |
| **S3** | DBP | · | staging | · | · | staging | · | · | · | · | · | — | **staging·INF** | **staging·INF** | staging |
| **I3** | · | · | · | · | · | · | · | · | · | · | · | **staging·INF** | — | **INF** | staging |
| **I4** | · | · | · | · | · | · | · | · | · | · | · | **staging·INF** | **INF** | — | staging |
| **PA-G** | · | · | CTR | CTR | CTR | CTR | **CTR·FE auth** | CTR·FE | CTR | · | · | staging | staging | staging | — |

**굵게 = 동시 실행 금지(같은 파일을 두 에이전트가 쥔다).** `·` = 충돌 없음.

### 충돌 덩어리 5개

1. **VIZ 덩어리** — `P3`·`V-1`·`V-2`·`Y-1`. 넷이 `d7_visualization/` 과 `core-viz.yaml` 을 공유한다.
   `V-1`·`Y-1` 은 `cache.py` 를 함께 쥔다. **동시 최대 1.**
2. **CORE/권한 덩어리** — `P6`·`P7`·`P8`. `d2_access.py`·`fe-core.yaml`·`frontend/src/permission/` 공유. 게다가 엄격 직렬(`P8 ⊇ P7 ⊇ P6`). **동시 최대 1.**
3. **AI 덩어리** — `K3`·`K5`(엄격 직렬 `K5 ⊇ K3`) ＋ **`T-1` ⓑ**(온톨로지 어휘·관계 확장이 `db/ai/seed` 와 `d9_ontology.py` 를 건드린다). **동시 최대 1.**
   ⚠ **이것이 이 지도에서 가장 놓치기 쉬운 충돌이다** — `T-1` 은 이름이 「검색 사전」이라 AI 면과 무관해 보이는데 완료 정의 ⓑ 가 `db/ai` 를 끌어온다.
4. **INF/staging 덩어리** — `I3`·`I4`·`S3` ＋ (`PA-G` staging 배포). 운영 스택 하나를 공유한다. **동시 최대 1** — 파일이 겹치지 않아도 **staging 실물이 하나**라 병렬 불가.
5. **CTR 전역** — `contracts/seams/*.yaml` 은 거의 모든 항목이 스친다.
   `SKILL §1` 「한 파일 면은 한 에이전트에게만 준다」에 따라 **계약 파일을 여는 에이전트는 회차당 1** 로 묶는다.
   ⚠ 계약 수정은 `generated-up-to-date` 로 프론트 생성물(`frontend/src/generated/fe-core.ts`)까지 끌고 온다.

### `T-1` ↔ `F-1` — **충돌 0 (실측)**
`T-1` 파일 면에 `frontend/` 없음 · `F-1` 파일 면에 `db/`·`services/` 없음 · **계약(`contracts/seams/`) 도 양쪽 다 건드리지 않는다**
(`F-1` 은 라우트 복원이라 계약 표면 변화 없음 — 다만 완료 정의가 서면 계약 표면이 붙을 수 있다 `[미확인]`).

---

## 3. 권고 병렬 배치

세 조건(ⓐ 진입조건 실제 성립 · ⓑ 파일 면 서로소 · ⓒ 실재하는 완료 정의)을 **전부** 통과하는 항목:

> **T-1 하나뿐이다.**

`F-1` 은 ⓐ·ⓑ 를 통과하지만 **ⓒ 를 통과하지 못한다**(완료 정의 미작성). 지어내지 않는다.

### 권고 — 에이전트 2, 소유는 이렇게 가른다

| 에이전트 | 항목 | 소유 파일 면 (배타) | 조건 |
|---|---|---|---|
| **A-T1** | `T-1` | `db/platform/**` · `db/ai/**` · `services/core-api/.../d3_catalog.py` ＋ `services/core-api/tests/**` · `services/ai-service/.../d9_ontology.py` · `eval/k4-search/**` · `dev-package/sessions/S2b-SEARCH-EVALSET.md` | 3 조건 전부 통과. **즉시 착수 가능** |
| **A-F1** | `F-1` | `frontend/**` 전부 | ⓐⓑ 통과 · **ⓒ 미통과 — Ted 가 완료 정의를 쓴 뒤에만 연다** |

**두 에이전트에게 명시할 경계 —**
- A-T1 은 `frontend/` 에 손대지 않는다. A-F1 은 `db/`·`services/` 에 손대지 않는다.
- **둘 다 `contracts/seams/` 를 열지 않는다.** 계약 표면 변경이 필요해지면 **멈추고 보고한다.**
- A-T1 은 staging 접촉이 필요하다 → `SKILL §6` 운영 경계 7항을 지시문에 그대로 박는다(운영 DB 읽기 전용 · 파괴 플래그 금지 · 컨테이너 정지·재기동·`down` 금지 · 접속 문자열 미출력 · 일회용 인스턴스는 `--rm`＋tmpfs＋`PGDATA`).
- A-T1 의 완료 정의 ⓓ 는 「기대값은 정본·판정에서만 도출하고 **검색을 돌려 역산하지 않는다**」를 지시문에 축자로 넣는다 — 이것을 빼면 평가셋이 오라클이 아니게 된다.

### ⚠ 「대규모 fan-out」이 성립하지 않는다는 것이 이번 조사의 결론

지시는 「병렬로 진짜 돌 수 있는 모든 항목」이었다. 실측 결과 **15 중 13 이 막혀 있고, 막힌 뿌리는 코드가 아니라 미판정 `conflict` 다.**
가장 값싼 다음 수는 에이전트를 늘리는 것이 아니라 **`P2` 한 건을 실측 판정하는 것**이다 —
`P2` 가 닫히면 `P3`·`K3` 이 열리고, `P3` 이 닫히면 `V-1`·`V-2`·`Y-1`·`S3`·`P6` 다섯이 뒤따라 열린다.

---

## 4. 착수 가능해 보이지만 아닌 것 — 그리고 각각을 푸는 한 가지

| 항목 | 착수 가능해 보이는 이유 | 실제 막는 것 | **푸는 한 가지** |
|---|---|---|---|
| **K3** | `§10.2-b` 가 「`K2`(✅) · `D2`(✅) — **열려 있다**」라 못박고 「`D5`·`P3` 과 병렬」이라 적는다 | `depends_on` 에 **`P2`(conflict)** | **`P2` 실측 판정 1회** — 저장 배치 회귀 시험과 `addDatasetFile` 202 저장 자리를 실물로 잰다(`§4` #21·#26). **15 건 중 가장 얕게 막혔다** |
| **I3** | `§10.2-b`·`03-HANDOFF` 비고가 「✅ 차단 해제 2026-08-27 — 7건 전부 판정」이라 적고 진입조건이 「없음 — stage 2 본체와 병렬 가능」이다 | 자기 자신이 **conflict** — 같은 문서 `§10`·`§10.3` 은 「⛔ 판정 7건 남음」 | **사람이 `sessions/TED-DECISIONS-OPEN.md §A` 의 7건 실물을 세어 판정** |
| **F-1** | `depends_on: []` · 「`P3` 와 병렬 가능」 · **화면 파일이 이미 142 행 실재** | **완료 정의 미작성** — 무엇을 하면 닫히는지가 어느 문서에도 없다 | **Ted 가 F-1 완료 정의를 쓴다**(라우트 복원만인가 · `handoff.ts` 등록 진입 경로까지인가 · staging 배포 green 포함인가) |
| **PA-G** | 진입조건이 「stage 1 완료 판정」이고 stage 1 은 대부분 ✅ 다 | **`PA`(conflict)** ＋ **`deadline.fired: unknown`**(게이트가 이번 회차에 「사람이 판정해야 한다」로 출력) | **stage 1 완료 판정 1회** — `§1.5` 잔여 둘(조건 3 D8 · 조건 7 계보 확정 완주)이 stage 1 안인지 밖인지 판정 |
| **P6** | `§10.2-b` 가 「`I4` 는 `P6` 의 시작을 막지 않는다」로 판정을 이미 내렸다 | 자기 자신 **conflict**(`§10.3`·`§9` 그래프는 `I4 ── P6` 그대로) ＋ 선행 `P2`(conflict)·`P3`(open)·`P5`(partial) | **`§10.3` 말미 경고문과 `§9` 그래프를 판정에 맞춰 고친다** — 그래도 `P2`·`P3` 이 남으므로 **단독으로는 안 풀린다** |
| **I4** | `I3` 만 걸린 단일 의존이다 | `I3`(conflict) ＋ **`R-1`(conflict)** 과 복원 리허설 재료 중복이 미기재 | **`R-1` 이 `I4` 를 흡수하는지 판정** ＋ `I3` 7건 판정 |
| **V-1 · V-2** | `viz-render` 는 stage 1 에서 이미 90 passed 로 살아 있다 | `P3`(open) → `P2`(conflict) **2단 건너** ＋ **완료 정의 미작성** | **`P2` 판정 → `P3` 착수·완료** ＋ **Ted 가 V-1·V-2 완료 정의 작성** |
| **S3** | 실데이터·staging 이 이미 서 있다 | `S2`(conflict — staging 계수가 문단마다 다름: 파일 122/123/129/139 · 계보 5/6 · 데이터셋 11/12) ＋ `P3`(open) | **staging 실물을 한 번 세는 것** — 그것이 `S2` 판정이다 |
| **Y-1** | 완료 정의 6항이 2026-08-27 에 새로 쓰였다(가장 잘 정의된 항목 중 하나) | `P3`(open) ＋ `D5`(partial) | **`P2` 판정 → `P3`** · 그리고 **`D5` stage 2 파트(파싱·좌표계·COG) 완주 판정** |
| **P7 · P8 · K5** | 각각 단일 의존이다 | 전부 **위가 막혀 있다** — `P7⊇P6`(conflict) · `P8⊇P7` · `K5⊇K3⊇P2`(conflict) | 각각 **선행 1건이 닫히는 것** 외에 지름길 없음 |

---

## 5. `[미확인]` 목록 — 이번 회차에 재지 않은 것

| 자리 | 무엇이 미확인인가 | 무엇을 하면 풀리나 |
|---|---|---|
| `F-1` 규모 | staging 배포 green 이 완료 조건에 붙는지 | F-1 완료 정의 작성(§4 표) |
| `P8` 규모 | DB 마이그레이션 동반 여부 | 「화면별 적용 지점 표」를 실제로 작성해 정책 재생성 범위를 본다 |
| `PA-G` 규모 | 구글 신원 연결에 저장(마이그레이션)이 필요한지 | 완료 정의가 스스로 「착수 회차가 실물로 판정한다」로 미룬 자리 |
| `X-5` 잔 1건 | **staging 실물의 `403`** — 로컬 green 이고 staging 배포 전 | `I3` 배포 후 `PATCH` 2회 |
| 각 항목 규모 수치 | 「파일 N~M」은 파일 면에서 **추정**한 값이고 실제로 연 파일을 센 값이 아니다 | 각 항목 착수 회차의 실측 |

**이번에 세지 않은 판단기준(다음 회차 진입조건)** — ⓐ 각 항목의 시험 건수 ⓑ `contracts/seams/` 표면 변경 여부 ⓒ staging 배포 필요 여부의 항목별 확정.

---

## 6. 이 조사가 하지 않은 것

- **편집 0 · 커밋 0** — 읽기 전용으로 수행했다.
- **`conflict` 를 하나도 고르지 않았다** — 대장 규칙(「어느 한쪽을 고르거나 평균하거나 「해소」하지 않는다」)을 지켰다.
- **완료 정의를 하나도 지어내지 않았다** — 6 건이 `완료 정의 미작성` 으로 남는다(`F-1`·`V-1`·`V-2` ＋ 대장의 다른 셋).
- **staging 실물에 접촉하지 않았다** — `S2`·`S3` 판정에 필요한 계수는 재지 않았고 `[미확인]` 으로 남긴다.
