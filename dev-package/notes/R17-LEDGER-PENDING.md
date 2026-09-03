# R-17 — 대장 반영 대기분 (레인 `lane-r17` · 2026-09-03)

오케스트레이터가 배정한 결정 번호 = **〈303〉** (이 번호 하나).
레인은 `PLAN-SoT.md §9` 에 직접 쓰지 않는다 — 등재는 오케스트레이터가 한다.
회차 행은 `sessions/X2-FREEZE-PROTOCOL.md §1` 17차 · 정지 기록은 같은 문서 `§1-b`.

전제 = Ted 판정 2026-09-03 두 건(계약 동결 해제 17차) · 후속 2건의 출처 = `notes/QD-LEDGER-PENDING.md §5`
(「담당 칸」·「§9 묘비 문구 도달 불가」) · 정본 `Policy_데이터셋_상세` v2.8 §5·§9 · `Policy_공통_기반` §2.4.

---

## 1. 판정 ② — 자기 연구실 묘비만 구분한다 (**집행**)

**등급 = ㉯**(`X2 §5`) — 소비자 ≥ 1(`frontend/src/components/detail/detailSource.ts`) · 정본 개정 1건.
**인가 = Ted 판정 2026-09-03 ② 그 자체.** `contract-breaking` **ERR 0 · WARN 0 · INFO 1**.

### 무엇이 바뀌었나

| 층 | 변경 | 파일 |
|---|---|---|
| 계약 | 응답 컴포넌트 **`Gone` 신설** ＋ `getDataset` 에 `"410"` 1건. **스키마 무변 · op 총계 55 그대로** | `contracts/seams/fe-core.yaml` |
| 생성물 | 재생성(+26 −1) | `frontend/src/generated/fe-core.ts` |
| 커널 | `errors.gone()` — 410 · 코드 `GONE` · 기존 `ErrorEnvelope` 그대로(**새 봉투를 만들지 않았다**) | `kernel/errors.py` |
| D3 | `_TOMBSTONE` 질의 ＋ `is_own_lab_tombstone()` | `domains/d3_catalog.py` |
| 라우트 | `dataset_detail` 의 404 접힘에 **한 갈래**를 냈다. P-9·P-10 주석은 지우지 않고 **범위를 좁혀 다시 적었다** | `app/routes/catalog.py` |
| 화면 | `DatasetTombstone` 신설(404 의 `DatasetGone` 과 **다른 종류**) · `detailSource` 가 410/404 를 갈라 던진다 · 상태 `tombstone` 추가 · 묘비 패널 `data-testid="detail-tombstone"` | `components/detail/{types,detailSource,useDatasetDetail}.ts` · `routes/DatasetDetailPage.tsx` |
| 정본 | `Policy_데이터셋_상세` **v2.8 → 2.9** — §9 행을 둘로 가르고 근거 블록 ＋ §12 이력. 백업 `_backup_260903_R17/` · 패키지 재동기 | 정본 폴더 |

### 판정의 전부는 한 줄이다

`is_own_lab_tombstone` 의 질의에 **`lab_id` 조건을 적지 않는다.** 경계는 RLS `lab_boundary`
(`schema.sql:838` · `USING (lab_id = current_lab_id())`)가 이미 걸었고, 그래서 —

- 남의 연구실 묘비는 「묘비 아님」이 아니라 **「행 없음」**으로 떨어진다 ⟹ 404.
- 조건을 손으로 한 번 더 적으면 같은 규칙이 두 곳에 있게 되고, 그때 **한쪽만 고쳐지는 날**이 온다.

### 왜 이것이 누설 완화가 아닌가

| 경우 | 응답 | 새로 알려 주는 사실 |
|---|---|---|
| ⑴ 내 연구실 · 묘비 | **410 GONE** ＋ `§9` 묘비 문구 | **0** — 그 행은 지워지기 전에 이미 내 목록에 있었다 |
| ⑵ 남의 연구실 · 묘비 | 404 ＋ `§2.4` 중립 문구 | 「그 연구실에 그런 것이 있었다」 |
| ⑶ 남의 연구실 · 생존 | 404 ＋ 같은 문구 | 「그런 것이 있다」 |
| ⑷ 있었던 적 없는 id | 404 ＋ 같은 문구 | — |

**⑵⑶⑷ 는 본문까지 한 글자도 같아야 한다.** 상태코드만 맞추고 문구가 갈리면 존재는 그대로 샌다 —
시험이 세 응답의 **동일성을 직접 대조**한다(`test_the_three_hidden_cases_are_byte_identical`).

### 같은 접힘을 쓰는 다른 op — **손대지 않았다**

| op | 접는 자리 | 왜 안 열었나 |
|---|---|---|
| `createDataset` | `dataset_detail` 을 **공유**한다(`routes/ingestion.py:580`) | 방금 만든 행이라 `deleted_at` 이 `NULL` 이다 — **410 이 도달 불가**하다. 계약에 못 미치는 응답을 선언하지 않는다 |
| `listDatasetFiles` · 내려받기 · 값 조회 | `dataset_exists`(`deleted_at IS NULL`) | **본체 경로**다. 묘비를 갈라 줘도 화면이 쓸 자리가 없고, 갈래를 늘리면 누설 면적만 넓어진다 |
| `getDatasetLineage` · `getDatasetDeletionImpact` | 각자의 404 | Ted 판정 ② 의 문면은 **상세 화면**이다. 계보 그래프의 묘비 노드는 이미 자기 표기를 갖는다(`lineage-graph.test.tsx:189` 「지워진 데이터라 상세 화면이 없어요」) |

### 시험 — 넷을 한 벌로 잰다

- 서버 `services/core-api/tests/test_dataset_detail.py` — 신규 **5건**(⑴~⑷ ＋ 동일성 대조).
  **기존 1건은 오라클이 바뀌어 정정**했다(`test_tombstone_has_no_detail_screen` 404 → `test_own_lab_tombstone_is_410`).
  **느슨해진 것이 아니다** — 같은 파일에서 ⑵⑶⑷ 가 404 임을 새로 못 박았고, 종전에는 ⑵ 를 재는 시험이 **0건**이었다.
- 화면 `frontend/test/r17-tombstone.test.tsx` — 신규 **7건**. 응답 코드 → 상태 번역 3 ＋ 문구·자리 4.
  red 선확인 **5/7**(나머지 2 는 404 쪽이라 종전에도 green — 그 사실이 「누설 면적이 안 늘었다」의 오라클이다).

---

## 2. 판정 ① — 「담당」열 (⛔ **집행하지 않았다** · Ted 판정 대기)

전문은 `sessions/X2-FREEZE-PROTOCOL.md §1-b`. 요지 셋 —

1. **조인할 열이 없다** — `d6_project` 에 담당·owner·created_by 가 0건(`schema.sql:706-719`). D6 의 표는 둘뿐이다.
2. **따를 관례가 없다** — `ProjectDetail`(`fe-core.yaml:3372`)에 담당이 없다.
3. **정의가 없다** — `Policy_프로젝트`·`DataModel_공통_기반` 에 0건. 적은 한 줄은 **`[가정]` 표지**를 달고 있다.

기획(PRD·목업)에는 「담당 호랑이」로 **1인 계정**이 실재한다 ⟹ 「기획 누락」이 아니라 **DataModel·DB 로 내려오지 않은 것**이다.
갈래 = ⑴ 정본 델타(계약 0·DB 0) / ⑵ D6 속성 신설(마이그레이션 1 ＋ 입력 경로 ＋ 정본 정의 · 별도 레인).
**어느 갈래든 이 레인에서 계약을 건드리지 않았다.**

---

## 3. 이 회차가 재지 않은 것 (다음 회차의 진입조건)

- **staging 무접촉 · 배포 0 · push 0 · 병합 0.** 410 이 실서버에서 나는 것은 **배포 뒤에만** 잰다.
  staging 실측상 **묘비 데이터셋이 0건**이므로 ⑴ 경로는 staging 에서 아직 도달 불가다(값을 심어야 한다).
- **`〈299〉` 가 남긴 후속 둘 중 하나만 닫혔다** — 「§9 묘비 문구 도달 불가」는 닫혔고 「담당 칸」은 열려 있다.
- **활용 배지 N ↔ 카드 수 동일 출처 대조**(`QD-LEDGER-PENDING §5`)는 이 회차도 재지 않았다.
