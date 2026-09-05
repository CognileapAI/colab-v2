# BF-9 레인 보고 — core-api 계보 그래프 · 원천 → 루트 edge

- 항목 `BF-9` · 브랜치 `bf-9/lineage-source-edge` · 기반 `main` `b0c1f34`
- 의존 `BF-1` = `done` (대장 실측 · `work-items.yaml`)
- staging 무접촉 · 병합 없음 · `PLAN-SoT §9`·`work-items.yaml`·`03-HANDOFF.md` 무수정

---

## 1. 계약 판정 — **개정 0건 · 동결 해제 불필요**

진입조건의 `[미확인]`(「계약이 원천을 edge 끝점으로 허용하는가」)을 스키마 필드로 판정했다.
정본 = `contracts/seams/fe-core.yaml` `components.schemas.LineageEdge`.

| 필드 | 선언 | 원천 관계가 채우는 값 | 개정 필요 |
|---|---|---|---|
| `childDatasetId` | `$ref common.json#/$defs/Ulid` | 원천 표기를 든 데이터셋 ID | 없음 |
| `parentDatasetId` | `oneOf: [Ulid, {type: "null"}]` · 산문 축자 **「원천 표기가 부모 자리인 관계는 데이터셋이 아니므로 null 이다」** | `null` | **없음 — 계약이 이 자리를 이미 열어 두었다** |
| `parentRole` | `$ref ParentRole` · `enum: [주입력, 보조입력]` · `default: 주입력` | `주입력` | 없음 |
| `method` | `type: [string, "null"]` | `null` (완료 정의 ⑴ 축자) | 없음 |
| `origin` | `$ref LineageOrigin` · `enum: [ai, manual, processed]` | `manual` | 없음 |
| `confirmedBy` | `$ref AccountRef` · **required · nullable 아님** | `d3_dataset.uploader_account_id` ＋ `d1_account.name` | 없음 |
| `confirmedAt` | `$ref Timestamp` · **required · nullable 아님** | `d3_dataset.uploaded_at` | 없음 |

- `additionalProperties: false` · `required` 7개 전부 충족 — **필드를 더하지도 비우지도 않았다.**
- `confirmedBy`·`confirmedAt` 이 유일한 판단 지점이었다(원천 관계에는 `d4_lineage` 확정 행이 없다).
  **지어내지 않고 실재하는 사실을 썼다** — 원천 표기는 업로드 때 사람이 손으로 적는 값(`sourceLabel` · `ingestion.py`)이므로
  확인자 = 올린 사람, 확인 시각 = 올린 시각. `_ONE` 질의가 `JOIN d1_account u` 라 두 값 다 non-null 이다.
- 판정 = **`X2-FREEZE-PROTOCOL` 회차 불필요 · 동결 해제 행 0건** (완료 정의 ⑷).
- 이 판정을 시험이 잠갔다 — `test_the_contract_already_allows_a_null_parent_endpoint`.
  계약이 뒤로 좁혀지면 이 시험이 red 가 되고, 그때는 코드가 아니라 동결 해제가 먼저다.

## 2. 재실측

- `services/core-api/.../routes/lineage.py` `lineage_graph()` — `core.source_label` 이 있으면 노드 하나(`kind: 원천`·`datasetId: null`)를 붙였고, `edges` 는 `d4_lineage.edges_of()` 결과만 실었다. **관계 0건.** 진입조건 축자 그대로.
- 프론트(`LineageSection.tsx`)는 이미 `parentDatasetId: null` 관계를 **완전히 수용**하고 있었다 — 픽스처 `graphFixture.ts` 의 기본 장면(`SELF`)이 그 모양 관계를 **2건** 들고 있다. 즉 결손은 뒷단 한쪽뿐이었다.
  - 레일 라벨: `g.edges` 중 `e.method` 가 truthy 인 것만 담는다 → `method: null` 은 라벨을 만들지 않는다.
  - 상세 행: `parentEdges` 가 `parentDatasetId !== null` 로 걸러 낸다 → 원천 행이 겹쳐 생기지 않는다.
  - 화살표: `shown.length − 1` — 관계 수와 무관하다.
- **딱 한 자리가 갈렸다** — 빈 상태 판정 `empty = g.edges.length === 0 && g.unknownParents`.
  원천 표기가 있으면서 `d4_lineage_unknown` 행이 있는 데이터셋은 종전에 「기록 없음」 빈 상태였는데, 관계가 하나 실리는 순간 그래프로 뒤집혔다. **edge 유무로 그림이 갈리는 유일한 지점**이라 완료 정의 ⑵ 가 이 자리를 잡는다.
- 생성물(`frontend/src/generated/fe-core.ts`)은 손대지 않았다 — 계약이 안 바뀌었으므로 재생성 대상도 없다(`generated-up-to-date` green 이 확인).

## 3. 고친 것 — 4파일 +176 / −6

| 파일 | 변화 | 내용 |
|---|---|---|
| `services/core-api/src/colab_core/app/routes/lineage.py` | +26 / −3 | 원천 노드를 세울 때 `source_edges` 한 줄을 함께 만들고 응답 `edges` 에 잇는다 |
| `services/core-api/tests/test_lineage_graph_read.py` | +59 | 계약 판정 1 ＋ 응답 판정 3 (④ 절 신설) |
| `frontend/src/components/lineage/LineageSection.tsx` | +14 / −3 | `empty` 판정에서 원천 관계를 빼고, 낡은 주석(「원천에는 대응하는 edge 가 없다」)을 실물에 맞춘다 |
| `frontend/test/lineage-graph.test.tsx` | +83 / −2 | 픽스처 `SOURCE_ROOT_CHILD_WITH_EDGE` ＋ 같은 그림 시험 2건 · 기존 순회 2건에 새 픽스처 추가 |

- CSS·`vite.config.ts` 무수정(형제 레인 소유).
- 기존 「edge 없는」 픽스처 `SOURCE_ROOT_CHILD` 와 그 시험을 **지우지 않았다** — 두 모양이 같은 그림을 낸다는 것이 판정이다.

## 4. RED → GREEN (축자)

### core-api

RED (`./gates/run.sh service-tests-core-api`) —
```
FAILED tests/test_lineage_graph_read.py::test_a_source_label_carries_an_edge_into_its_root
  - AssertionError: 0000000000000000000000DSA1 의 원천 관계: 기대 1 · 실측 0 — []
FAILED tests/test_lineage_graph_read.py::test_the_source_edge_does_not_displace_the_dataset_edges
  - AssertionError: 0000000000000000000000DSA1 의 전체 관계: 기대 2 · 실측 1 — ...
2 failed, 629 passed, 6 deselected in 92.19s
```

GREEN —
```
631 passed, 6 deselected in 95.02s
service-tests-core-api — 선택자 «not e2e» · 수집 631 · 실행 631 · skipped 0 · deselected 6 · failed 0 · errors 0
```

### frontend

RED (`empty` 판정을 종전 식으로 되돌린 채 `npx vitest run test/lineage-graph.test.tsx`) —
```
 ❯ test/lineage-graph.test.tsx:306:21
   expect(screen.getByTestId('lin-empty')).toBeInTheDocument();
 Test Files  1 failed (1)
      Tests  1 failed | 40 passed (41)
```
※ 신규 2건 중 「원천 관계가 실려 와도 같은 그림」은 **수정 전에도 통과**한다 — 프론트가 그 모양을 이미 받고 있었다는 재실측의 확인이고, 사실이 아닌 red 를 만들지 않았다.

GREEN — 아래 게이트 계수.

## 5. 게이트 (단독 · 하나씩 · 축자 계수)

| 게이트 | 판정 | 계수 |
|---|---|---|
| `service-tests-core-api` | green | 수집 **631** · 실행 **631** · skipped 0 · deselected 6 · failed 0 · errors 0 · 95.0초 |
| `contract-lint` | green | seam **3**건 · 룰 위반 **0** |
| `contract-breaking` | green | 기준 HEAD **3**건 대비 파괴적 변경 **0** (`No changes detected`) |
| `generated-up-to-date` | green | 등기부 **4**건 전부 재생성 일치 · 등기부 밖 자칭 생성물 **0** |
| `frontend-typecheck` | green | `tsc --noEmit` 오류 **0** |
| `frontend-test` | green | **38파일 / 597건** 통과 · 실패 **0** (이 레인 신규 **2**건 포함 — 기반 `b0c1f34` 은 595) |

- 건너뜀·범위 축소·비활성화 **0건**.
- 준비 red 2건을 **준비로 해소**했다(판정 red 아님) — 이 체크아웃에 `services/core-api/.venv`·`frontend/node_modules` 가 없어 각각 `python3 -m venv .venv && pip install -r requirements.txt -r requirements-dev.txt && pip install -e .` · `npm ci` 를 돌린 뒤 재실행했다. 둘 다 `.gitignore` 대상이라 커밋에 없다.
- `~/.colab-v2-test.env` 는 **쓰지 않았다** — `service-tests-core-api` 는 게이트가 일회용 postgres 를 스스로 세운다(`_pg.sh` ＋ `fixtures/setup-db.sh` · 접속 문자열 미출력). staging 접촉 0.

## 6. 대장 `evidence:` 초안 (BF-5 형식)

```yaml
    evidence: >-
      커밋 `026d4d8`(기반 `b0c1f34` · 4파일 +176/−6 — `routes/lineage.py`·`test_lineage_graph_read.py`·`LineageSection.tsx`·`test/lineage-graph.test.tsx`).
      **계약 개정 0 · 동결 해제 행 0** — `LineageEdge.parentDatasetId` 가 이미 `oneOf: [Ulid, null]` 이고 산문이 「원천 표기가 부모 자리인 관계는 데이터셋이 아니므로 null 이다」로 이 자리를 지정한다. `method` 는 `[string, "null"]`.
      필수 4칸(`parentRole`·`origin`·`confirmedBy`·`confirmedAt`)은 nullable 이 아니라 실재값으로 채웠다 — `주입력` · `manual` · 올린 사람(`uploader_account_id`＋`d1_account.name`) · 올린 시각(`uploaded_at`).
      RED — core-api **2 failed / 629 passed**(`원천 관계: 기대 1 · 실측 0`) · frontend **1 failed / 40 passed**(빈 상태가 원천 관계 하나로 뒤집혔다) → GREEN — `service-tests-core-api` **수집 631 · 실행 631 · skipped 0 · failed 0** · `frontend-test` **38파일 / 597건** · `frontend-typecheck` 0 · `contract-lint` 위반 0 · `contract-breaking` 변경 0 · `generated-up-to-date` 등기부 4건 일치.
      ⑵ 는 「edge 없는 픽스처」를 남긴 채 「edge 있는 픽스처」를 더해 **칸·화살표·레일·라벨·상세행 5계수가 같음**을 대조한다. 근거 `reports/bf-9/lane-report.md`.
```

## 7. `PLAN-SoT §9` 초안 (번호 없음 — 병합 직전 `origin/main` 최댓값 ＋1 로 재실측)

> **〈N〉 계보 그래프의 원천은 노드로만 서 있었다 — 관계를 함께 싣는다 (`BF-9`).**
> `getDatasetLineage` 는 `source_label` 에서 `kind: 원천` 노드를 만들면서 그에 대응하는 관계를 내지 않았다.
> 화면은 그것을 「라벨 없는 화살표」로 수용했지만(`BF-1`), **화살표를 뒷받침하는 사실이 응답에 없었다** —
> 그림은 맞고 데이터는 비어 있는 상태였고, 화면 밖에서 이 응답을 읽는 쪽은 원천이 무엇에 붙는지 알 수 없었다.
> **계약은 이 자리를 처음부터 열어 두고 있었다** — `LineageEdge.parentDatasetId` 는 `oneOf: [Ulid, null]` 이고
> 산문이 「원천 표기가 부모 자리인 관계는 데이터셋이 아니므로 null 이다」라고 그 뜻을 지정한다.
> **개정 0 · 동결 해제 회차 불필요**(`X2-FREEZE-PROTOCOL` 진입 안 함). 결손은 계약이 아니라 구현이었다.
> ⑴ 원천 노드 1개당 관계 1개 — `parentDatasetId: null` · `childDatasetId` = 그 데이터셋 · `method: null`
> (가공 방식은 관계에 붙는 값인데 원천에는 없다 — **지어내지 않는다**).
> ⑵ nullable 이 아닌 필수 4칸은 실재하는 사실로 채운다 — `parentRole: 주입력` · `origin: manual`(사람이 업로드 때
> 손으로 적은 값이다) · `confirmedBy` = 올린 사람 · `confirmedAt` = 올린 시각. **`d3_dataset` 이 두 값을 다 든다.**
> ⑶ 화면은 edge 유무와 무관하게 같은 그림을 낸다 — 다만 빈 상태 판정 한 곳이 갈렸다.
> 「기록 없음」은 **가공 전 데이터를 모른다**는 뜻이고 연구실 밖 출처 표기는 그 물음에 답하지 않으므로,
> `empty` 판정에서 원천 관계를 뺀다. 나머지(레일 라벨·상세 행·화살표 수)는 이미 이 모양을 받고 있었다 —
> 기본 픽스처가 `parentDatasetId: null` 관계를 2건 들고 있었다.

## 8. `[미확인]`

- **원천이 여럿인 데이터셋** — `d3_dataset.source_label` 은 `text` 한 칸이라 데이터셋당 원천 노드는 최대 1이다.
  프론트 기본 픽스처는 원천 노드 2개를 그리지만(목업 유래), **서버가 그 모양을 낼 경로는 지금 없다.**
  정본이 다중 원천을 요구하는지 `[미확인]` — 이 레인은 스키마를 건드리지 않았다.
- **`parentRole` 값 선택** — 정본이 원천 관계의 역할을 명시하지 않는다. `default: 주입력` 을 따랐고,
  원천은 Lv 계산에 들어가지 않으므로(부모 수는 `d4_lineage` 관계로만 센다) `보조입력` 과 결과가 갈리지 않는다. 판정 `[미확인]`.
- **`origin` 값 선택** — `manual`(사람이 적은 값)로 읽었다. `LineageOrigin` 에 「원천 표기」를 가리키는 값은 없고,
  값을 늘리는 것은 계약 개정이라 **하지 않았다.** 정본 판정 `[미확인]`.
- **원천 표기의 수정 시각** — `sourceLabel` 은 `updateDataset` 으로 고칠 수 있는데(`test_dataset_update.py`)
  `d3_dataset` 은 그 칸의 수정 시각을 따로 들지 않는다. `confirmedAt` 은 업로드 시각이라 **표기를 고쳐도 움직이지 않는다.**
  화면이 이 값을 「원천을 확인한 날」로 읽지는 않는다(원천 행은 `confirmedAt` 을 그리지 않는다). 판정 `[미확인]`.

## 9. 이탈

- 없음. 지시받은 절차(재실측 → 계약 판정 → RED → 구현 → 프론트 ⑵ → 단독 게이트 → 커밋 → 보고)를 순서대로 밟았다.
- 지시에 없던 변경 1건 — `LineageSection.tsx` 의 `empty` 판정과 낡은 주석.
  전자는 완료 정의 ⑵(「edge 유무와 무관하게 같은 그림」)를 만족시키기 위한 최소 변경이고 RED 로 근거를 남겼다.
  후자는 주석이 실물보다 낡는 것을 막는다(`CLAUDE.md §0`). 둘 다 CSS·`vite.config.ts` 밖이다.
