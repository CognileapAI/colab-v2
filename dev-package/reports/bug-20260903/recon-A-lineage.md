# A. 계보 그래프 — 근본 원인 조사 (2026-09-03)

대상 컴포넌트: `frontend/src/components/lineage/LineageSection.tsx` (376줄, 전문 통독)
스타일: `frontend/src/components/lineage/lineageGraph.css`
데이터: `services/core-api/src/colab_core/app/routes/lineage.py:47` `lineage_graph()` (D4 · `getDatasetLineage`)
계약: `contracts/seams/fe-core.yaml:3221` `LineageNode` · `:3257` `LineageEdge` · `:3283` `LineageGraph`

---

## 0. 구조 요약 (세 버그의 공통 지반)

- 가로축은 **노드 종류로 고정된 4칸**이다 — `columnOf()` 가 `kind` 를 그대로 0/1/2/3 에 대응 (`LineageSection.tsx:46-64`), 배열도 고정 4칸 (`:214`).
- 칸 사이 레일(화살표 자리)은 **고정 3개**, `i < 3` 이면 무조건 렌더 (`:286-305`).
- 레일 안 화살표 `→` 는 `rails[i].map()` **바깥**에 있어 조건 없이 항상 1개 출력 (`:301-303`).
- CSS 가 빈 칸에도 폭을 준다 — `.lin-col { min-width: 178px }` (`lineageGraph.css:23`), `.lin-axis { min-width: 820px }` (`:21`), `.lin-rail { padding: 0 14px }` (`:24`).
- 서버는 **1-hop 그래프**만 준다 — 자기 자신 + 직계 부모(가공 전) + 직계 자식(파생) + `source_label` 있을 때 원천 표기 (`routes/lineage.py:84-92`).
- **원천 노드에는 대응하는 edge 가 없다** — `source_label` 문자열에서 만든 표기일 뿐 (`routes/lineage.py:89-92`).

---

## A-1. Lv0 앞·Lv1 뒤에 고아 화살표 — **확정**

**근본 원인**: 레일 화살표가 무조건부 렌더다.

- `LineageSection.tsx:301-303` — `<span className="lin-arw">→</span>` 가 `rails[i]` 길이·인접 칸 노드 유무와 무관하게 항상 출력.
- `LineageSection.tsx:286` — 레일 자체도 `i < 3` 만 보고 렌더. `cols[i]`/`cols[i+1]` 이 비었는지 보지 않음.
- bug03 장면 = col0(원천) 비어 있음 → **rail0 화살표만 남음(왼쪽 고아)**, col1=Lv0(가공 전), rail1=「이중선형보간」+→, col2=Lv1(이 데이터), col3(파생) 비어 있음 → **rail2 화살표만 남음(오른쪽 고아)**.

**최소 수정 방향**: 레일을 렌더하는 조건을 「양쪽 칸에 노드가 있음」으로 좁힌다 — `cols[i].length > 0 && cols[i+1].length > 0` 일 때만 `lin-rail` 을 그리고, 화살표도 그 조건 안에서만 출력.

**실패 테스트 초안**
```
그래프에 원천·파생이 없으면 양 끝에 화살표를 그리지 않는다
  graph = { nodes: [가공전 Lv0, 이데이터 Lv1], edges: [부모→자기(method 있음)] }
  assert container.querySelectorAll('.lin-arw').length === 1   // 지금 3
```

---

## A-2. Lv0(루트) 왼쪽에 화살표 2개 + 빈 칸 2개 — **확정**

**근본 원인**: A-1 과 같은 뿌리 + 빈 칸이 폭을 유지한다.

- `LineageSection.tsx:214-215` — `cols` 를 항상 4칸으로 만들고 `:273-277` 에서 4칸 전부 `lin-colwrap` 으로 렌더. 노드 0개인 칸도 DOM 에 남는다.
- `lineageGraph.css:23` — 빈 `.lin-col` 도 `min-width: 178px` 를 차지. `:21` `.lin-axis { min-width: 820px }` 가 축 전체 폭을 강제.
- bug05 장면 = 자기 자신이 Lv0(이 데이터, col2), 파생 4건(col3). col0·col1 이 비었는데도 178px×2 + 화살표 2개가 그대로 남음.

**최소 수정 방향**: 빈 칸의 `lin-colwrap` 자체를 렌더하지 않는다 (`cols` 를 렌더 전에 `nodes.length > 0` 으로 걸러 인덱스와 함께 넘긴다). `.lin-axis` 의 `min-width: 820px` 는 4칸 전제 값이므로 함께 낮추거나 제거.

**실패 테스트 초안**
```
루트(부모 없음) 데이터셋은 왼쪽에 빈 칸을 두지 않는다
  graph = { nodes: [이데이터 Lv0, 파생 Lv1 x2], edges: [자기→자식 x2] }
  cols = screen.getAllByTestId('lin-col')
  assert cols.map(c => c.dataset.col) === ['2','3']   // 지금 ['0','1','2','3']
  assert container.querySelectorAll('.lin-arw').length === 1
```

---

## A-3. 원천(NMSC) 상자와 Lv0 사이의 「→ · 빈 칸 · →」 — **확정**

**근본 원인**: 두 겹이다.

1. 원천 노드는 col0 에 서지만(`columnOf` `:48-49`) **대응 edge 가 없다** — 서버가 `source_label` 로만 만든다 (`routes/lineage.py:89-92`). 따라서 rail0 에는 라벨이 붙을 edge 가 원리적으로 없다.
2. `railOf()` 는 레일 번호를 **자식 노드의 칸**에서 뽑는다 (`LineageSection.tsx:67-71`). 서버가 1-hop 만 주므로 모든 edge 의 자식은 col2(자기) 또는 col3(파생) — 레일 1 또는 2 로만 간다. **rail0 은 어떤 경우에도 라벨을 받지 못하는 죽은 레일**이다.
3. 그 상태에서 부모(가공 전) 데이터셋이 없으면 col1 이 비고, rail0·rail1 화살표 2개가 원천과 Lv0 사이에 남는다 = bug07 장면 (원천 → 화살표 → 빈 칸 → 화살표 → Lv0).

**최소 수정 방향**: A-1·A-2 의 「빈 칸·빈 레일 제거」를 적용하면 rail0 과 col1 이 사라져 원천 바로 옆에 Lv0 가 붙는다. 추가로 원천→이 데이터 사이에 화살표를 남기려면 col0 와 col2 가 **인접 렌더**된 뒤 그 사이 레일 1개만 그리도록 레일을 「칸 배열 인덱스 기준」으로 재계산 (레일을 `kind` 고정 번호가 아니라 렌더된 칸 순서의 사이사이로 세운다).

**실패 테스트 초안**
```
원천만 있고 가공 전이 없으면 원천과 이 데이터 사이 화살표는 1개다
  graph = { nodes: [원천, 이데이터 Lv0, 파생 Lv1], edges: [자기→자식(method)] }
  cols = screen.getAllByTestId('lin-col')
  assert cols.map(c => c.dataset.col) === ['0','2','3']   // 지금 ['0','1','2','3']
  assert container.querySelectorAll('.lin-arw').length === 2  // 원천↔Lv0, Lv0↔Lv1. 지금 3
```

---

## 공통 원인 여부

**세 버그 모두 하나의 근본 원인이다** — 가로축이 「노드 종류 = 고정 칸 번호」로 설계되어, 종류가 없는 칸도 DOM·폭·화살표를 그대로 유지한다.

- 공통 지점 ①: `LineageSection.tsx:214-215` + `:273-277` (빈 칸 무조건 렌더)
- 공통 지점 ②: `LineageSection.tsx:286` + `:301-303` (빈 레일·화살표 무조건 렌더)
- 공통 지점 ③: `lineageGraph.css:21,23` (빈 칸 폭 유지)
- A-3 만 추가 요인: `railOf()` (`:67-71`) 가 1-hop 응답에서 rail0 을 죽은 레일로 만든다

수정 1건(빈 칸·빈 레일 제거 + 레일 인덱스를 렌더 순서 기준으로)이 A-1·A-2·A-3 을 함께 닫는다.

---

## 기존 테스트 · 실행 명령

- 파일: `frontend/test/lineage-graph.test.tsx` (451줄, 계보 그래프 정본 대비 시험)
- 화살표·빈 칸을 재는 단언은 **없다** — `lin-arw`·`lin-rail` 을 참조하는 테스트 0건.
- 실행: `cd frontend && npm test` (vitest run) / 단건 `cd frontend && npx vitest run test/lineage-graph.test.tsx`
- 설정: `frontend/vite.config.ts` (별도 vitest.config 없음), 환경 jsdom, setup `frontend/test/setup.ts`

---

## 위험 · 주의

1. **기존 테스트가 버그를 고정하고 있다** — `frontend/test/lineage-graph.test.tsx:62-65` 가 `cols.length === 4` 와 `['0','1','2','3']` 을 단언. 빈 칸을 걷으면 이 테스트가 깨진다. **정본 의도(축 순서)를 지키되 「빈 칸도 4개」를 요구하지 않도록 단언을 고쳐야 한다.**
2. `LineageSection` 은 `frontend/src/routes/DatasetDetailPage.tsx:186` 한 곳에서만 사용. `lineageGraph.css` 도 이 컴포넌트만 import. 다른 화면 영향 없음.
3. `frontend/src/components/lineage/LineageStep.tsx` 는 **업로드 모달 ③ 계보 확정 단계**로 별개 컴포넌트다 (`upload/UploadModal.tsx:178`). 이번 수정 대상 아님.
4. 정책 문구 `Policy_데이터셋_상세 §8` 「축은 원천 → 가공 전 → 이 데이터 → 파생」은 **순서** 규정이지 「빈 칸도 자리를 지킨다」는 규정이 아니다 (`LineageSection.tsx:5-6` 주석). 빈 칸 제거는 정책 위반이 아니다 — 다만 advisor 게이트에서 정본 해석 확인 권장.
5. bug05 에서 파생 4건에 라벨 4개가 붙고 화살표는 1개다 (`:288-303` — 라벨은 edge 마다, 화살표는 레일마다). Ted 접수에는 없으나 같은 코드 지점의 인접 결함.
6. `git log` — `9488f81` 계보 그래프 신설, `40edc65` 검수 소수리, `3e74dae` 픽스처 폴백 제거. **세 버그는 신설(`9488f81`) 시점부터 존재**한 설계 결함이며 최근 커밋이 넣은 회귀가 아니다.
