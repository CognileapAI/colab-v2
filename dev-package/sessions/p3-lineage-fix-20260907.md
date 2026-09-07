# WU-B10 · 상세 계보 수정·추가 — 레인 `p3-lineage-fix` (2026-09-07)

- 라운드 R-B · 근거 파일 `dev-package/prd/rounds/R-B-3-frontend.md` §2 WU-B10 · PRD-31(＋PRD-22 편집 대상 확장 · PRD-30 표시층) · 크기 M.
- 기준 HEAD = `652712e`(`integration/r-b` · ff-only 확인). 브랜치 `lane/p3-lineage-fix`.
- 계층 = **FE 단독**. 계약 0 · 서버 0 · 스키마 0 · 마이그레이션 0 · **새 op 0**.
- 선행 = WU-B5(Lv 연결 규칙 · `is-over` · 사유 문면) · WU-B8(판정식 · `lineageUnknown`). 둘 다 통합 브랜치에 있다.

## 1. 완료 조건 ↔ 판정 ↔ 근거

| 완료 조건 (`R-B-3-frontend.md §5` WU-B10) | 판정 | 근거 (파일:행) |
|---|---|---|
| 상세에 `계보 수정 · 추가` 진입 | 충족 | `frontend/src/components/lineage/LineageSection.tsx` `fixEntry` — 구역 **헤더**(`lin-sec-head`)에 선다. 종전 아래쪽 `lin-act` 자리는 걷었다(진입점 둘을 만들지 않는다) |
| `기록 없음` 상세가 빈 상태 3문면 ＋ `계보 채우기` | 충족 | 같은 파일 `lin-empty` — 제목·버튼·보조 문구가 PRD-31 ⑵ 축자. 버튼이 같은 모달을 연다 |
| `가공 방식` 이 `d4_lineage_edge.method` 로 저장되고 계보 행·엣지 라벨이 읽는다 | 충족 | `lineageEditSource.ts` `AddParentBody.method` → `addLineageParent` · 표시는 `LineageSection.tsx` 계보 행 `가공 방식: …` · 엣지 라벨 `lin-method` |
| 파생 행 읽기 전용 ＋ `여기서는 못 고쳐요` | 충족 | `LineageSection.tsx` `DetailRow` `hist`(`derived` 갈래) — 기존 코드이고 이 WU 가 시험으로 잠갔다 |
| 권한 없는 계정 = 버튼 미노출 ＋ API 거절 | 충족 | 화면 = `canEdit`(서버가 `업로드·편집` 로 계산 · `routes/lineage.py` `lineage_graph`) 아래에서만 진입점이 **DOM 에 존재**한다 / 서버 = `services/core-api/tests/test_lineage_confirm.py::test_lineage_edits_need_the_upload_edit_switch`(403 · 기존 시험) |
| `contracts/`·`db/`·`services/` 변경 0건 | 충족 | `git diff --stat` 6파일 전부 `frontend/` 아래 ＋ 신규 4건도 `frontend/` |

## 2. 수용 기준 6 ↔ 시험

시험 파일 = `frontend/test/lineage-fix-20260907.test.tsx` (**9건**).

| 수용 기준 (축자) | 시험 |
|---|---|
| ⑴ 빈 상태 3문면 ＋ `계보 채우기` 가 눌린다 | `⑴ … 세 문면이 축자로 서고 `계보 채우기` 가 눌려 모달이 열린다` ＋ 헤더 진입점 1건 |
| ⑵ 부모 1건 추가 → `직접 연결` ＋ 상태가 `확인 필요`/`확정` | `⑵ … 저장하면 그 부모가 `직접 연결` 로 서고 상태가 `확인 필요` 로 바뀐다` — 호출 인자 3열쇠까지 대조 |
| ⑶ 초과 부모는 등록 ③ 과 **같은 사유 문구**로 막힌다 | `⑶ … 초과 후보가 목록에 남고, 버튼이 비활성이며, 사유가 같은 상수에서 온다` |
| ⑷ 권한 없으면 버튼 미노출 ＋ API 거절 | `⑷ … `계보 수정 · 추가` 도 `계보 채우기` 도 서지 않는다`(화면) ＋ 서버는 기존 core 시험 인용 |
| ⑸ 파생 행 읽기 전용 ＋ `여기서는 못 고쳐요` | `⑸ … 파생 행에 문구가 읽히고 그 행에는 편집 컨트롤이 없다` |
| ⑹ `가공 방식` 을 계보 행과 엣지 라벨이 읽는다 | `⑹ … 저장 뒤 재조회 없이 두 자리가 같은 값을 보인다` |
| (범위 밖 규율 2건) 모달 층 · PRD-22 편집 대상 | `모달 층 규율 …`(`data-esc-layer="계보 수정"` · Esc/배경/× 한 곳) · `PRD-22 — 편집 화면은 계보 표를 그리지 않고 이 모달로 보낸다` |

## 3. 재사용 증거 — 사본이 아니라 **한 벌**

| 무엇 | 어디 | diff 가 보이는 것 |
|---|---|---|
| 찾기·연결 UI | `frontend/src/components/lineage/ParentPicker.tsx` (신규) | `LineageStep.tsx` 안에 있던 `picker()` 본문을 **들어올렸다** — 그 파일의 diff 는 `-` 51행(본문 삭제) ＋ `+` 11행(`<ParentPicker …/>` 호출)이다 |
| 초과 사유 문면 | 같은 파일 `parentOverReason()` | 종전 `LineageStep.tsx` 의 `overReason()` 이 사라지고 두 화면이 이 함수를 import 한다 |
| 후보 출처 | `LineageSection.tsx` 기본값 `apiLineageSource()` | 등록 ③ 이 쓰는 **그 출처**다(`lineageSource.ts`) — 새 조회 경로를 만들지 않았다 |
| 토스트 문면 | `common/toastCopy.ts` `PRE_LINEAGE_ADDED` | 이미 있던 상수를 부른다(다시 적지 않았다) |
| 쓰기 경로 | `lineageEditSource.ts` → `addLineageParent` | `routes/lineage.py:169` 의 기존 op 하나. `_ALLOWED_PARENT_FIELDS` 3열쇠만 보낸다 |
| Esc 층 규율 | `upload/escLayer.ts` `ESC_LAYER_ATTR`·`useEscLayer` | A9R·B3 이 세운 것을 그대로 쓴다 — 표식 `계보 수정` |

**상세 재동기 방식 = 재조회가 아니라 응답 그래프 채택.** `addLineageParent` 는 갱신된 그래프를 본문으로 돌려주므로 `LineageSection` 이 그것을 `saved` 상태로 세운다. 낙관적 갱신이 아니다 — 화면이 값을 조립하지 않는다.

## 4. RED → GREEN · 게이트 (`COLAB_GATE_REPORT_DIR=dev-package/reports/R-B/p3-lineage-fix`)

- RED 실측(구현 전) — `Failed to resolve import "../src/components/lineage/ParentPicker" from "test/lineage-fix-20260907.test.tsx"` · `Test Files 1 failed (1) / Tests no tests`. GREEN — `Tests 9 passed (9)`.

```
frontend-typecheck      green — tsc --noEmit(include=src·test) 오류 0건
frontend-test           green — vitest 62 파일 · 868건 통과 · 실패 0건
frontend-fixture-reach  green — 진입점 도달 151개, 금지 모듈 0건
```
계 : green 3 / red(판정) 0 / red(준비) 0. 전수 `all` 은 병합 직전 오케스트레이터 몫이다.

## 5. 자기 표시

- **기준값 출처 차이 = 결함 · F1 로 정정(사람 값 우선).** 종전엔 「이 데이터」 노드의 `processingLevel`(서버 파생값 · 부모 없으면 0 · 상한 Lv2)을 기준 Lv 로 삼았으나, 서버의 400 판정은 `user_set_level()`(사람이 ①에서 고른 값)을 쓴다 — 두 기준이 갈리면 화면이 정상 후보까지 막거나(파생<사람) 서버가 거절할 후보를 화면이 허용(파생>사람)했다. advisor gate ② F1 로 정정.

### advisor ② 반영 (F1·F2)

- **F1** — `DatasetDetailPage.tsx` 가 `selfLv={levelOf(shown.basicInfo?.processingLevelUserSet)}`(`DetailHeader.tsx` 와 같은 `levelOf`)를 `LineageSection` → `LineageFixModal` 로 내려보낸다. `LineageSection.tsx` 의 노드 기반 계산은 **사람 값이 없을 때만** 쓰는 대비로 물러났다(잠긴 상세처럼 `basicInfo` 가 없는 경우).
  - RED(선실측, `frontend/test/lineage-fix-20260907.test.tsx`): `그래프 노드는 Lv0(기록 없음 실값)이어도 사람 값 Lv2 가 기준이라 Lv1·Lv2 후보가 열린다` — `expected true to be false`(고정 전 `PARENT`(Lv1) 후보가 막혀 있었다).
  - GREEN: 같은 시험 통과, ⑶ 기존 초과 후보 시험도 그대로 green.
- **F2** — `lineageEditSource.ts` 의 `addParent` 가 관례(`approvalSource.ts` `fail`·`datasetPreviewSource.ts` `messageOf`)를 따라 `r.error` 의 `message` 를 그대로 올린다(빈 봉투일 때만 고정 문구 「계보를 고치지 못했어요.」).
  - RED(선실측): `apiLineageEditSource().addParent 는 서버 봉투의 message 를 그대로 올린다` — `Received: '계보를 고치지 못했어요.'` (서버 문구가 삼켜졌다).
  - GREEN: 같은 시험 통과 · UI 단 `addParent` 거절 시 `lin-fix-error` 축자 노출·모달 유지 시험도 통과(기존 오류 경로에 서버 문구 축자 검증 추가).
- **아래쪽 `lin-act` 진입점을 걷고 헤더 하나로 모았다.** 라운드 파일 축자가 「구역 헤더에」이고, 둘을 두면 같은 모달로 가는 버튼이 두 개가 된다. 종전 버튼의 `data-fills-in="E-04 검색 창 미연결"` 표식도 함께 사라졌다(연결됐으므로).
- **모달은 부모 추가 하나만 연다** — `removeLineageParent`·`confirmLineage` 는 수용 기준 밖이라 화면 진입을 만들지 않았다(경로는 서버에 이미 있다). `.lin-fix` CSS 는 폭·두 줄뿐이고 전역 모달 이름(`members.css` 정본)을 다시 정의하지 않았다.

## 6. 하지 않은 것 · §후속

- **Ted 판정 대기 8건(1·2·3·4·5·6·7·10·12)을 건드리지 않았다.** 그중 1(`LineageSection` 문면 「가공 방식은 화살표 라벨 …」)은 이 WU 가 만진 파일 안에 있으나 **그 문자열을 고치지 않았다**(`HINT` 상수 무변).
- **후속 ⑴ — Lv 표시 규칙 갈림(B5 이월).** `routes/lineage.py` 의 그래프 노드 Lv 와 `project.py` 의 파생값이 서로 다른 규칙으로 선다. **서버 사안**이라 FE 단독 계층 밖이고 이 레인은 손대지 않았다. 어느 검사에도 걸리지 않는다 — 게이트·Dockerfile·배포 어디에도 두 값을 대조하는 자리가 없다. 판정 자리를 세우는 WU 가 필요하다.
- **후속 ⑵ — 상세에서 사후 `기록 없음` 선언.** 이 모달에 넣지 않았다. 이유는 실측이다: `lineageUnknown` 은 `createDataset` 쪽 열쇠 하나뿐이고(`routes/ingestion.py` `lineage_unknown = bool(body.get("lineageUnknown"))`), `confirmLineage` 는 **본문을 받지 않으며** `addLineageParent` 는 `_ALLOWED_PARENT_FIELDS` 3열쇠 밖을 400 으로 거절한다. 즉 **기존 경로로는 불가능**하고 넣으려면 계약＋서버를 열어야 한다 — 이 WU 의 「계약·서버 0」과 어긋난다.
- **후속 ⑶ — `가공 방식` 을 나중에 고치는 길.** 지금은 연결을 **더할 때만** 적는다. 이미 붙은 관계의 `method` 를 고치는 op 이 서버에 없다(수정은 지우고 다시 잇는 두 걸음이다). 수용 기준 밖이라 만들지 않았다.
- `dev-package/03-HANDOFF.md`·`PLAN-SoT.md`·`contracts/`·`db/`·`services/`·`40 COLAB-기획/` 무변. 대장은 `in_progress` 까지만 — `done` 확정은 오케스트레이터 몫이다.
