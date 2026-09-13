# 이태헌 1차 검증 — 조사 C (프로젝트 · 데이터셋 · 가공 단계)

- 입력 = `dev-package/reports/issues/2026-09-13-lth-review-1-raw.md` 의 D-2 · I-6 · I-3 · I-1.
- 대조 트리 = 워크트리 `lth-review-260913` · HEAD `2e45ce9a`(dev 배포 sha `6ff0eecd` 의 코드와 동일 · 이후 커밋은 문서).
- 조사 범위 = 읽기 전용. 코드·계약·대장 무수정. 게이트 미실행.
- 인용은 `경로:앵커문자열` 로 지목한다(행 번호 미기재).

---

## D-2 프로젝트 카드가 키보드로 열리지 않음

### 1. 재현/확인 — **확인됨**

- 카드 요소 = `<article>` ＋ `onClick` 하나. `role`·`tabIndex`·링크·버튼 없음.
  근거 `frontend/src/components/project/ProjectCards.tsx` 앵커 `<article` 블록 —
  > ```tsx
  > <article
  >   key={row.projectId}
  >   className="pcard"
  >   data-testid={`project-card-${row.projectId}`}
  >   data-closed={row.status === '닫힘' ? 'true' : undefined}
  >   onClick={() => props.onOpen(row.projectId)}
  > >
  > ```
- 카드 안의 이동 안내도 비대화형이다 — 같은 파일 앵커 `data-testid="card-cta"` 는 `<span>` 둘(`cta-t`·`cta-a`)이고 `aria-hidden="true"` 화살표를 포함한다. 주석 축자 「카드 전체가 이미 클릭 대상이라 **그 안에 또 하나의 클릭 대상을 세우지 않는다**」.
- CSS 에 포커스 규칙 부재 — `frontend/src/components/project/project.css` 의 `.pcard` 선택자는 `.pcard {`·`.pcard[data-closed='true'] {` 둘뿐이고 `:focus-visible` 규칙이 없다.
- 같은 성질이 표 보기에도 있다 — `frontend/src/components/project/ProjectTable.tsx` 는 `<tr … onClick={() => props.onOpen(row.projectId)}>` 이고 행에 `tabIndex` 가 없다. 카탈로그 표도 같은 모양이다(`frontend/src/components/catalog/CatalogTable.tsx` 앵커 `className={`clk${…}`}` ＋ `onClick`). ⟹ **카드 단독 결함이 아니라 「행·카드 전체를 클릭 대상으로 쓰는 패턴」 공통 결함**이다.
- 호출처 = `frontend/src/routes/ProjectsPage.tsx` 앵커 `state.view === '카드'` 의 `<ProjectCards rows={state.rows} onOpen={open} />`.
- 근본 원인 = 이동 수단을 onClick 하나로 두고 대화형 역할·포커스를 부여하지 않음. 접근성 검사 게이트 부재(`gates/` 에 a11y·axe 게이트 없음 — `gates/` 목록은 `README.md`·`config`·`fixtures`·`requirements.txt`·`run.sh`·`tools` 뿐)로 잠복.

### 2. 의도 대조 — **미결정(대장 항목 없음)**

- `dev-package/work-items.yaml` 에 프로젝트 카드 키보드·포커스 항목 부재 — `grep -n "프로젝트 카드\|카드 보기\|tabIndex\|초점"` 결과 1건(`활용 프로젝트 카드와 다운로드 버튼` · 무관)뿐.
- 접근성 항목은 **대비(contrast)** 만 등재돼 있다 — 같은 파일 앵커 `WU-A11 이 있음 으로 판정한 항목만 고친다`(note 축자 「대비 3건(Lv 칩 · 연결 불가 후보 · 그래프 라벨)이 접근성 합격선」). 키보드 조작은 그 판정 범위 밖.
- 「카드 안에 또 하나의 클릭 대상을 세우지 않는다(§8)」는 `ProjectCards.tsx` 주석의 설계 근거이나, 카드 자체를 링크로 만드는 것과 충돌하지 않는다(카드 = 링크 1개, 내부 링크 0개).

### 3. 원인 분류 — **결함(접근성) · 대장 항목 없음**

### 4. 수정 범위 추정

- 파일 = `frontend/src/components/project/ProjectCards.tsx`(카드를 링크/버튼으로) ＋ `project.css`(`:focus-visible`) ＋ 시험 1건. 범위를 행 패턴까지 넓히면 `ProjectTable.tsx`·`CatalogTable.tsx`·`ProjectDatasetTable.tsx` 가 더해진다.
- 계약·core-api·스키마 변경 **없음**. 계약 파괴 **없음**.
- 크기 = **S**(카드만) / **M**(행 클릭 패턴 전체 ＋ 회귀 시험).

### 5. 판정 질문 (Ted)

- 사용자가 보는 것 = 마우스 없이 키보드·화면 읽기 프로그램만 쓰는 사람이 프로젝트 목록에서 상세로 들어갈 수 있는지.
- 두 갈래의 대가 = ⑴ 카드만 링크로 바꾼다 — 이번 회차에 작게 끝나고, 목록 표·카탈로그 표의 같은 문제는 남는다. ⑵ 「영역 전체를 눌러 이동」 패턴 네 자리를 한 번에 고친다 — 회차가 커지고 표 행의 빠른 작업 버튼과 포커스 순서를 다시 정해야 한다.
- 권고 = ⑴ 로 시작하고, 표 세 자리는 같은 회차의 후속 항목으로 등재.

---

## I-6 빈 프로젝트 상세 표에 안내 문구가 없음

### 1. 재현/확인 — **확인됨**

- 소속 데이터셋 표에 0행 분기 부재. `frontend/src/components/project/ProjectDatasetTable.tsx` 의 `<tbody>` 는 `{props.rows.map(…)}` 하나이고, 0행 문면·`colSpan` 행이 없다.
- 표는 조건 없이 그려진다 — `frontend/src/routes/ProjectDetailPage.tsx` 앵커 `<ProjectDatasetTable` 은 `rows={detail.datasets}` 로 무조건 렌더된다(길이 검사 없음).
- 0행에서도 좌우 이동 안내가 선다 — 같은 표 파일 앵커 `className="table-scroll-hint"` 의 「표를 좌우로 밀면 나머지 항목과 작업을 볼 수 있어요.」 가 행이 없어도 출력된다.
- 기존 빈 상태 패턴(대조 대상) = 표 안 `colSpan` 행 — `frontend/src/components/catalog/CatalogTable.tsx` 앵커 `<td colSpan={9} className="empty">` 의 「조건에 맞는 데이터가 없어요. 조건을 하나 풀어 보세요.」 ⚠ 그 행은 `rows.length === 0 && state.hasConditions` 일 때만 선다 — 조건 없는 0건에는 카탈로그도 문면이 없다(별개 자리).
- 문단형 패턴 = `frontend/src/components/detail/PieceList.tsx` 앵커 `<p className="fl-none">본체 조각이 없어요</p>` · `frontend/src/components/dashboard/TodoInbox.tsx` 앵커 `<p className="dash-zero">확인할 계보가 없어요.</p>`.
- 같은 화면 안에 이미 빈 상태 문면이 둘 있다 — `ProjectDetailPage.tsx` 앵커 `'아직 설명이 없어요 — 무엇을 하는 과제·논문인지 몇 줄만 적어 두세요.'` · 앵커 `<p className="pd-linkempty">아직 적지 않았어요.</p>`. ⟹ 표 한 자리만 패턴에서 빠져 있다.
- 근본 원인 = 표 컴포넌트에 0행 분기를 두지 않음.

### 2. 의도 대조 — **미결정(해당 표에 대한 항목 없음) · 다만 빈 상태 규칙은 이미 있다**

- 빈 상태 문면 자체는 기존 판정 대상이다 — `dev-package/work-items.yaml` 앵커 `FE 소형 5건 — VISIBILITIES 3값 · submit 400 표면화 · 기간 인라인 철거 · Lv0 안내 사람 Lv · 빈 상태 3문면 권한 무관 (R-B §5-16·31·14·28·43)`(`status: done`), 완료 정의 축자 「`canEdit=false` 계정도 빈 상태 3문면」. 그 3문면에 소속 데이터셋 표는 포함되지 않았다(위 실물이 근거).
- 「0건 패널도 빈 상태로 남는다」 규칙의 선례 = 같은 대장 앵커 `국가과제·논문 두 패널이 각각 행을 쌓고, 0건 패널도 빈 상태로 남는다`. ⟹ 제품 규칙 방향은 이미 정해져 있고, 이 표가 그 규칙의 미적용 자리다.
- `dev-package/prd/specs/*.md` 에 「소속 데이터셋」 빈 상태 문면 지정 없음(`grep` 0건).

### 3. 원인 분류 — **결함(기존 빈 상태 규칙 미적용) · 문면 신설 1건 포함 · 대장 항목 없음**

### 4. 수정 범위 추정

- 파일 = `ProjectDatasetTable.tsx`(0행 `colSpan` 행 ＋ 문면, 0행일 때 `table-scroll-hint` 숨김) ＋ 시험 1건. 문면 문안은 「연결된 데이터셋이 없어요」 계열로 기존 3문면과 같은 어투.
- 계약·core-api·스키마 변경 **없음**. 계약 파괴 **없음**. 크기 = **S**.

### 5. 판정 질문 (Ted)

- 사용자가 보는 것 = 데이터셋이 한 건도 없는 프로젝트를 열었을 때, 표 제목 행만 보이는가 / 「없다 ＋ 다음에 무엇을 하라」가 보이는가.
- 두 갈래의 대가 = ⑴ 문면 한 줄만 넣는다 — 가장 작고, 연결 방법은 사용자가 스스로 찾는다. ⑵ 문면 ＋ 연결 진입(업로드 또는 데이터셋에서 소속 지정) 안내를 함께 넣는다 — 화면 안에서 다음 행동이 끝나지만 진입점이 하나 늘고 권한(프로젝트 생성 스위치)별 분기가 생긴다.
- 권고 = ⑵ 의 문면까지만 이번에 넣고 버튼 신설은 보류(진입점 증설은 범위 확대).

---

## I-3 미검증 상태의 표현(취소선 `Verified`)

### 1. 재현/확인 — **확인됨(의도된 구현)**

- 카탈로그 표 — `frontend/src/components/catalog/CatalogTable.tsx` 앵커 `className="verified verified--pending"` —
  > ```tsx
  > <span
  >   className="verified verified--pending"
  >   data-testid="verified-pending"
  >   aria-disabled="true"
  >   title="승인 처리가 아직 도착하지 않았다"
  > >
  >   Verified
  > </span>
  > ```
- 프로젝트 상세의 소속 데이터셋 표도 같은 표기 — `frontend/src/components/project/ProjectDatasetTable.tsx` 앵커 `data-testid="dataset-verified"` 의 `row.verified ? '승인됨' : <span className="verified verified--pending" …>Verified</span>`.
- 시각 규칙 = `frontend/src/components/catalog/catalog.css` 앵커 `.verified--pending` —
  > `.verified--pending { background: var(--color-gray-100); color: var(--color-text-muted); text-decoration: line-through; cursor: not-allowed; }`
  · 프로젝트 상세 쪽 보강은 `frontend/src/components/project/project.css` 앵커 `.project-detail .verified--pending`.
- 원천 필드 = 불리언 하나(`row.verified`). 3값 이상의 상태 필드 없음 — 칩이 그릴 수 있는 상태는 **둘**(승인됨 / 승인 도착 전)이다. 「요청 없음 / 검토 대기」를 그릴 입력이 현재 응답에 없다 [미확인 — 승인 요청 상태를 내려보내는 열쇠 유무는 `contracts/` · `services/core-api/.../routes/approval*` 확인으로 닫힌다].
- 배지 컴포넌트는 **미승인에 아무것도 그리지 않는다** — `frontend/src/components/approval/VerifiedBadge.tsx` 축자 「⚠ **미승인에 회색 배지를 두지 않는다.** 배지는 1종이고(§4 용어 정의) 없으면 없는 것이다」, 구현도 `if (!props.verified) return null;`. ⟹ **표(칸)와 배지(카드·헤더)가 서로 다른 규칙이고, 그 차이는 의도적이다** — `frontend/src/components/search/SearchHitCard.tsx` 축자 「⚠ **카탈로그의 `verified--pending` 취소선을 여기로 옮기지 않는다** — 그 표기는 「칸을 비우지 않는다」가 이유이고(`〈282〉`-㉮ · `Policy §8 Verified 열`), 카드는 애초에 칸이 아니라 배지 자리다」.
- 시험 고정 = `frontend/test/catalog.test.tsx`(앵커 `expect(cell.className).toContain('verified--pending');` · 앵커 `not.toContain('verified--pending')`) · `frontend/test/qa-20260903.test.tsx` 앵커 `expect(c.querySelector('.verified--pending')).not.toBeNull();` · `frontend/test/search-verified-20260903.test.tsx` 앵커 `expect(card.querySelector('.verified--pending')).toBeNull();`.

### 2. 의도 대조 — **이미 판정됨(Ted 2026-09-02) · 판정 재개봉 금지 대상**

- 요지 = 승인 처리가 도착하지 않은 `Verified` 칸은 글자를 남기고 취소선·회색·꺼진 조작 모양으로 그린다. 칸을 비우면 「승인이 아니다」와 「아직 안 왔다」가 화면에서 갈리지 않는다.
- 근거 축자 `dev-package/PLAN-SoT.md` 〈282〉 행 —
  > **㉮ Ted 판정 = 승인 처리가 아직 오지 않은 행의 `Verified` 칸은 글자를 그대로 두되 취소선·회색·꺼진 조작 모양으로 그린다.** ⭑ **종전 실물은 그 칸을 비워 두었다**(`CatalogTable.tsx` `{row.verified && …}`) — **비면 「승인이 아니다」와 「아직 안 왔다」가 화면에서 갈리지 않는다.**
- 같은 행 축자(집행 범위) —
  > **집행** = `frontend/src/components/catalog/CatalogTable.tsx` 8번째 칸이 `verified` 가 거짓일 때 `verified verified--pending` 스팬에 글자 `Verified` 를 그린다(`aria-disabled`) · 규칙은 `catalog.css` `.verified--pending`(`text-decoration: line-through` · `--color-gray-500` · `cursor: not-allowed`) · 시험 **3건**(`frontend/test/catalog.test.tsx`).
- ⟹ 기획자가 권고한 「미검증·요청 없음·검토 대기 를 한국어로」는 **이 판정의 반전 요청**이다. 새 근거 = 기획자(lth) 1차 검증 의견. 판정 재개봉은 Ted 만 가능.
- `C1`~`C4`·`R2`·`T-1` 은 이 건과 무관하다 — 전부 `stage: after_stage2` 이고 내용은 레포 이관·지식 추출·`ts_config` 한국어 재작성이다(`dev-package/work-items.yaml` 앵커 `id: C1` ~ `id: C4` · `id: R2` · `id: T-1`). `T-1` 의 「한국어 재작성」은 전문검색 설정(`ts_config`)이고 화면 표기가 아니다.
- 영어 라벨 `Verified` 자체는 정본 용어다 — 열 이름이 계약 값 집합에 있다(`frontend/src/components/catalog/columns.ts` 앵커 `'Verified'` · 같은 파일 앵커 `if (column === 'Verified') return value === true ? 'Verified' : '승인 전';` — **필터 메뉴는 이미 한국어 「승인 전」을 쓴다**). ⟹ 한 제품 안에 `Verified`(열·칩)와 `승인 전`(필터 값)·`승인됨`(프로젝트 상세 표)이 공존한다.

### 3. 원인 분류 — **설계 차이(Ted 재판정 필요)** · 부수적으로 **문면 불일치**(같은 상태를 `Verified`(취소선) · `승인 전` · `승인됨` 세 표기로 쓰는 자리)

### 4. 수정 범위 추정

- 갈래 ⓐ 표기만 한국어로(취소선 유지 또는 제거) = `CatalogTable.tsx` · `ProjectDatasetTable.tsx` · `catalog.css` · `project.css` ＋ 시험 4건 정정(위 4개 시험 파일). 계약 무변(`columns.ts` 의 열 이름 `Verified` 는 계약 값이라 **열 이름을 바꾸면 계약 변경**). 크기 **S**.
- 갈래 ⓑ 상태를 3값 이상으로(요청 없음 / 검토 대기 / 승인됨) = 승인 요청 상태를 응답에 싣는 작업이 선행. 계약 `DatasetRow` 열쇠 신설 ＋ core-api ＋ 화면. 계약 파괴는 **아니다**(열쇠 추가). 크기 **M~L** [미확인 — 승인 요청 테이블·상태 유무 확인 필요].
- 갈래 ⓒ 열 이름까지 한국어 = `CatalogColumn` 값 집합 변경 ⟹ **계약 파괴**(필터·정렬 값이 열 이름 문자열). 크기 **M**, 계약 동결 해제 필요.

### 5. 판정 질문 (Ted)

- 사용자가 보는 것 = 아직 승인을 받지 않은 데이터 줄의 승인 칸. 지금은 영어 `Verified` 에 취소선이 그어져 있고, 색과 선을 자세히 보지 않으면 「승인 완료」로 읽힌다는 지적이 왔다(기획자 검증).
- 두 갈래의 대가 = ⑴ 2026-09-02 판정을 유지한다 — 「값이 없음」과 「아직 안 왔음」이 계속 구분되고, 오독 지적은 남는다. ⑵ 칸의 글자를 한국어 상태말(예 「승인 전」)로 바꾼다 — 오독이 줄고, 같은 상태를 가리키는 말이 화면마다 하나로 모인다(필터는 이미 「승인 전」을 쓴다). 대가 = 2026-09-02 판정을 뒤집는 것이고 시험 4건을 함께 정정한다.
- 권고 = ⑵. 단 취소선·회색은 유지해 「칸을 비우지 않는다」는 원래 이유를 지키고, 열 제목은 그대로 둔다(열 제목 변경은 검색·정렬 계약 파괴).

---

## I-1 계산된 가공 단계와 선택한 단계가 달라도 별도 확인 없이 허용됨 (긴급)

### 1. 재현/확인 — **확인됨(전건 의도된 구현)**

#### (a) 계산 자리 — core-api 한 곳, 화면은 미리보기만

- 판정 조립 = `services/core-api/src/colab_core/domains/d3_catalog.py` 앵커 `def level_view(` —
  > ```python
  > derived = processing_level(summary)
  > human = user_set_level(core)
  > return {
  >     "processingLevel": derived if human is None else human,
  >     "processingLevelDerived": derived,
  >     "processingLevelMismatch": human is not None and human != derived,
  > }
  > ```
  같은 함수 독스트링 축자 — 「⛔ 불일치는 **경고 신호**이지 차단이 아니다(미결-2 ⓐ). 이 함수는 아무것도 raise 하지 않는다.」
- 사람 값 파싱 = 같은 파일 앵커 `raw = core.processing_level_user_set` (`Lv<digit>` 만 정수로, 그 밖은 `None`).
- 파생 규칙 축자 = `contracts/schemas/common.json` 앵커 `"description": "가공 단계 Lv. 원자료 = 0, 부모가 있으면 (주입력 부모 중 최대 Lv) + 1.` ＋ 같은 설명 축자 「두 값은 **병존**하고 어긋나면 경고만 낸다(등록을 막지 않는다).」
- 저장 칸은 사람 값 하나뿐 — `db/platform/schema.sql` 앵커 `processing_level_user_set text` ＋ `CHECK (… IN ('Lv0', 'Lv1', 'Lv2', 'Lv3'))`. **파생값·불일치 칸은 테이블에 없다**(요청마다 계산).
- 화면 계산은 등록 중 미리보기 한 자리뿐 — `frontend/src/components/lineage/LineageStep.tsx` 앵커 `const mismatch = selfLv !== null && derivedPreview !== null && derivedPreview !== selfLv;` · 그 위 앵커 `const derivedPreview =` 은 **확인된 부모가 0건이거나 부모 Lv 를 모르면 `null`** 이다(같은 파일 독스트링 축자 「부모 Lv 를 하나라도 모르면 미리보기를 만들지 않는다.」).
  ⟹ **[추론] 부모를 한 건도 연결하지 않은 등록에서는 불일치 경고가 등록 화면에 뜨지 않는다** — 기본값 `Lv2` 가 서 있고 파생값은 0 이지만 미리보기가 `null` 이라 비교가 성립하지 않는다. 기획자가 든 사례(선택 Lv2 · 계산 Lv0)가 그 모양이다.
- 표시 규칙(사람 값 우선)은 화면 한 자리 — `frontend/src/components/common/processingLevel.ts` 앵커 `export function displayLevel(` ＋ 같은 파일 축자 「⚠ **불일치를 여기서 판정하지 않는다** — 어긋남은 경고이지 차단이 아니고 (`processingLevelMismatch` · 미결-2 ⓐ), 그 문면은 상세 헤더가 쥔다.」

#### (b) 문면과 렌더 자리 — **같은 문장이 두 곳**

- 데이터셋 상세 헤더 — `frontend/src/components/detail/DetailHeader.tsx` 앵커 `data-testid="dh-lv-mismatch"` —
  > ```tsx
  > {`고른 가공 단계는 Lv${levelOf(d.basicInfo.processingLevelUserSet)}이고, 연결한 데이터로 계산하면 Lv${d.basicInfo.processingLevelDerived}이에요. 그대로 두어도 등록돼요.`}
  > ```
  조건 = 앵커 `{d.basicInfo?.processingLevelMismatch ? (`. 같은 자리 주석 축자 「**막지 않는다** — 이 줄이 뜬 상태로도 수정·저장이 성공한다(미결-2 ⓐ).」
- 등록 ③ 연결 단계 — `frontend/src/components/lineage/LineageStep.tsx` 앵커 `data-testid="lin-lv-mismatch"` —
  > ```tsx
  > {`고른 가공 단계는 Lv${selfLv}이고, 연결한 데이터로 계산하면 Lv${derivedPreview}이에요. 그대로 두어도 등록돼요.`}
  > ```
  바로 위 주석 축자 「⭑ **⟨PRD-10⟩ 불일치는 경고만이다 — 저장을 막지 않는다.**」
- 응답 열쇠 공급 = `services/core-api/src/colab_core/app/routes/catalog.py` 앵커 `"processingLevelMismatch": d3_catalog.level_view(core, summary)["processingLevelMismatch"],`(상세 `basicInfo`) · 목록은 앵커 `**d3_catalog.level_view(core, summary),`(행 전개).

#### (c) 확인·사유 단계 — **등록 흐름 어디에도 없음**

- 등록 선택 칸 = `frontend/src/components/upload/RegisterArea.tsx` 앵커 `data-testid="reg-level"` 셀렉트. 바로 위 주석 축자 「⚠ 빈 선택지가 없다 — 기본값 `Lv2` 가 늘 서 있어 「비어 있음」이 성립하지 않는다.」 ⟹ **기본값은 계산값이 아니라 고정 `Lv2`** 다(같은 파일 앵커 `⚠ 가공 단계는 기본값 `Lv2` 가 늘 서 있어 빈 상태가 성립하지 않는다.` 에서도 재확인).
- 최종 제출은 버튼 하나 — 같은 파일 앵커 `{props.submitting ? '저장 중…' : props.submitLabel ?? '데이터셋 만들기 →'}`. 불일치에 대한 확인 모달·체크박스·사유 입력 칸 **0건**(`RegisterArea.tsx` 에 사유/확인 관련 식별자 부재).
- 사유를 담을 저장 칸도 없다 — `db/platform/schema.sql` 의 `d3_dataset` 에 불일치 사유 열 부재(위 (a) 근거).
- 등록 **뒤** 사람 값을 고치는 화면 칸도 없다 — `frontend/src/components/detail/editFields.ts` 의 편집 칸은 7개(`name`·`summary`·`sourceLabel`·`sourceUrl`·`sourceDownloadedOn`·`crs`·`gridDescription`)이고 가공 단계·분류 3축이 없다. `DatasetEditForm.tsx`·`useDatasetEdit.ts` 에 `category`·`dataType`·`processingLevelUserSet` 참조 0건.
  ⟹ **[추론] 잘못 고른 Lv 를 화면에서 되돌리는 경로가 없다** — 계보(부모)를 고쳐 파생값을 움직이는 길만 남는다. [미확인 — 계약 `DatasetUpdate` 에는 `processingLevelUserSet` 이 있다(`contracts/seams/fe-core.yaml` 앵커 `DatasetUpdate:` · 같은 블록 앵커 `processingLevelUserSet:`; `contracts/schemas/common.json` 은 그 사실을 설명문으로만 적는다); 다른 화면에 그 칸이 있는지는 업로드·상세 밖 전수 grep 으로 닫힌다.]

#### (d) 목록·검색·검토 노출 — **데이터는 내려가고 화면이 그리지 않는다**

- 카탈로그 목록 응답에 불일치 열쇠가 실린다 — `services/core-api/src/colab_core/app/routes/catalog.py` 앵커 `**d3_catalog.level_view(core, summary),`(주석 축자 「세 값이 한 벌로 나간다」 ＋ 「필터·정렬이 읽는 것도 이 `processingLevel` 이다 — … 파생값은 선언이 아니라 경고 신호다」).
- 화면은 읽지 않는다 — `frontend/src/components/catalog/CatalogTable.tsx` 는 `displayLevel(row)` 한 값만 그리고 `processingLevelMismatch` 참조 0건(프런트 전체에서 그 열쇠를 읽는 자리는 `DetailHeader.tsx` 하나 · 생성물 제외 grep 결과).
- 프로젝트 상세 표·계보 노드는 **불일치 열쇠를 애초에 받지 않는다** — `services/core-api/src/colab_core/app/routes/project.py` 앵커 `**d3_catalog.level_pair(core, summary),` · `routes/lineage.py` 앵커 `else d3_catalog.level_pair(c, summaries.get(node_id))`. `level_pair` 는 두 값만 싣는다(`d3_catalog.py` 앵커 `def level_pair(`).
- 검색 결과 카드에 Lv 불일치 표기 없음(`frontend/src/components/search/SearchHitCard.tsx` — 승인 배지·잠김 칩만).
- 검토 화면(홈 「내 일」) = `frontend/src/components/dashboard/TodoInbox.tsx` 는 계보 확인·승인 요청만 센다 [미확인 — 불일치를 모수에 넣을 자리가 있는지는 `dashboardSource.ts` 확인으로 닫힌다].
- 불일치 자체는 **저장되지 않는다** — 사람 값 ＋ 계보에서 매 요청 계산(위 (a)).

### 2. 의도 대조 — **이미 판정됨(Ted 2026-09-05 · 미결-2 ⓐ) · 판정 재개봉 금지 대상**

- 요지 = 가공 단계는 사람이 고르고, 계보 계산값과 달라도 등록을 막지 않으며 화면에 한 줄만 낸다.
- 근거 축자 `dev-package/prd/PRD-260905-적용전기획.md` 미결-2 행 —
  > | 미결-2 | 사람이 고른 Lv 와 계보 계산값의 불일치 | **ⓐ 경고만** — 사람이 Lv0~Lv3 을 고르고, 파생값과 달라도 등록을 막지 않고 화면에 사유 한 줄을 낸다. `processing_level_user_set` 열을 재신설하고 `PLAN-SoT §9 〈194〉` 반전을 원장에 기재한다 | 부모를 나중에 붙이는 흐름에서 불일치는 정상 중간 상태다. 차단하면 등록을 못 끝내고, 덮어쓰면 고른 값이 사라져 선택 칸이 무의미해진다 | **확정 (Ted 2026-09-05)** |
- 수용 기준 축자(같은 파일) —
  > - Given 사람 Lv 와 파생 Lv 가 어긋남, When `createDataset`, Then **성공하고 경고만 뜬다**(400 이 아니다 — 미결-2 ⓐ).
- 기본값 축자(같은 파일) —
  > - 기본 선택값 = **Lv2**(rev1 `<option selected>`). **상한은 Lv3 이다**(미결-7 ⓐ 확정 …). 값은 사람이 고르고, 파생 계산값과 어긋나도 **경고만 내고 등록을 막지 않는다**(미결-2 ⓐ 확정 · PRD-10).
- 같은 판정의 반영본 = `dev-package/prd/개발계획서-260905.md` 축자 「미결-2 ⓐ — 가공 단계를 **사람이 고르고**, 계보 계산값과 어긋나면 **경고만** 낸다(등록을 막지 않는다)」 · `WU-B5` 행 축자 「… 사후 충돌이 연결을 지우지 않고 `확인 필요` 로 막고, 불일치는 경고만 낸다」.
- ⟹ **기획자가 든 네 권고 중 ③(사유 ＋ 명시 확인)은 이 판정의 반전 요청**이다. ①(두 값·이유 함께 표시)은 현재 부분 충족(두 값은 보이고 **이유는 안 보인다**), ②(기본값을 계산값으로)는 판정문의 「기본 선택값 = Lv2」 반전, ④(목록·검토 표시)는 판정문이 금지한 적이 없는 **미구현**이다.
- 관련 대장 항목 = `LV-3`·`LV-4` 는 이 건을 덮지 않는다(`dev-package/work-items.yaml` 앵커 `id: LV-3` = 「CoLAB에서 가공됨」 표식 · 앵커 `id: LV-4` = 계보 삭제 시 부모 이름 상수 보존 · 둘 다 `stage: after_stage2` · `status: open`). 불일치 확인·사유 항목은 대장에 **없다**.
- 표시 규칙 선례(같은 계열의 안내 전용 결정) = `dev-package/work-items.yaml` 앵커 `사람 Lv0＋파생≠0 행에 출처 안내`(`status: done`) — 불일치 계열 안내를 **차단 없이** 더한 기존 사례. 구현 자리 = `frontend/src/components/detail/BasicInfoGrid.tsx` 앵커 `const lv0SourceMissing =` ＋ 같은 자리 주석 축자 「⛔ 안내로만이다 — 저장을 막지 않고 재입력을 강제하지 않는다.」

### 3. 원인 분류

- ⑴ 「확인 없이 허용」 = **설계 차이(Ted 재판정 필요)** — 현재 동작이 2026-09-05 확정 판정 그대로다.
- ⑵ 「불일치가 목록·검토에 안 보인다」 = **미구현(대장 항목 없음)** — 판정에 저촉되지 않고 응답 열쇠는 이미 있다.
- ⑶ 「이유가 안 보인다」 = **판정 이행 미달(미결-2 ⓐ 「화면에 사유 한 줄을 낸다」)** — 현재 문장은 두 값만 말하고 왜 갈렸는지는 말하지 않는다. 판정문이 요구한 「사유 한 줄」이 아직 문장에 없다.
- ⑷ 「부모 0건 등록에서 경고가 안 뜬다」 = **설계 차이 · 요약표 ⑵(기본값 Lv2 고정)과 동일 판정** — 상세에서는 뜨고 등록 화면에서는 안 뜬다.
  - 미결-2 ⓐ 근거대로면 부모를 나중에 붙이는 등록은 정상 중간 상태라, 부모 0건마다 「계산하면 Lv0」 경고를 내는 것이 원하는 동작인지 자체가 판정이다.
- ⑸ 「등록 뒤 Lv 수정 칸 없음」 = **미구현**(대장 항목 없음 · 위 (c) [미확인] 해소 전제).

### 4. 수정 범위 추정 — 기획자 권고 4건을 갈라서

| 권고 | 무엇을 바꾸는가 | 파일·계약 | 계약 파괴 | 크기 | 기존 판정과의 관계 |
|---|---|---|---|---|---|
| ① 두 값 ＋ 갈린 이유를 함께 보여 준다 | 현 경고 한 줄에 근거(사람이 고른 값 / 부모 최대 Lv＋1 · 부모 0건이면 0)를 덧붙인다 | `DetailHeader.tsx` · `LineageStep.tsx` ＋ 시험 | 없음 | **S** | 저촉 없음(안내 보강) |
| ② 기본값을 계산값으로 맞춘다 | 등록 ① 셀렉트 기본값을 고정 `Lv2` → 파생값 추종(부모 0건이면 `Lv0`), 부모 연결 시 재계산 | `RegisterArea.tsx` · `UploadModal.tsx`(기본값 주입 자리) ＋ 시험 | 없음 | **M** | **판정문 「기본 선택값 = Lv2」 반전 — Ted 필요** |
| ③ 다른 단계를 유지하려면 사유 ＋ 명시 확인 | 제출 직전 확인 단계 ＋ 사유 입력 ＋ 사유 저장 칸 | `RegisterArea.tsx`(확인 UI) · 계약 `DatasetCreate`·`DatasetUpdate` 열쇠 추가 · `db/platform` 마이그레이션 1건(사유 열) · `routes/catalog.py` · `d3_catalog.py` ＋ 시험 | 없음(열쇠 추가 · 필수화하면 파괴) | **L** | **미결-2 ⓐ 「경고만 · 막지 않는다」 반전 — Ted 필요** |
| ④ 불일치를 목록·검토에도 표시 | 카탈로그 표 Lv 칸에 불일치 표식, 검토 함에 모수 추가 | 목록은 `CatalogTable.tsx` 만(열쇠 이미 내려옴 · **서버 무변**) / 프로젝트 표·계보 노드까지 넓히면 `routes/project.py`·`routes/lineage.py` 를 `level_pair`→`level_view` 로(계약 열쇠 추가) | 없음 | **S**(카탈로그만) / **M**(표·노드·검토 함) | 저촉 없음 — 미구현 |

- 추가 항목(기획자 권고 밖, 위 분류 ⑷⑸) = 등록 화면에서 부모 0건일 때도 경고를 내는 수정(**S** · `LineageStep.tsx` 의 `derivedPreview` 를 부모 0건에서 `0` 으로) · 상세 편집에 가공 단계 칸 신설(**M** · `editFields.ts` 확장 ＋ 계약 `DatasetUpdate` 기존 열쇠 사용).

### 5. 판정 질문 (Ted)

- 사용자가 보는 것 = 데이터 등록에서 「가공 단계」를 직접 고른다. 기본값은 항상 Lv2 로 서 있다. 연결한 데이터(부모)로 계산하면 다른 값이 나오는 경우, 상세 화면에 「고른 가공 단계는 Lv2이고, 연결한 데이터로 계산하면 Lv0이에요. 그대로 두어도 등록돼요.」 한 줄만 뜨고 그대로 저장된다. 부모를 한 건도 연결하지 않은 등록에서는 그 줄조차 뜨지 않는다. 목록·검색·검토 화면에는 이 차이가 전혀 보이지 않는다.
- 이미 내려진 결정 = 2026-09-05 에 「사람이 고르고, 계산값과 달라도 막지 않고 경고만 낸다」로 확정됐다. 사유 = 부모를 나중에 붙이는 흐름에서 차이는 정상 중간 상태이고, 막으면 등록을 끝낼 수 없고 덮어쓰면 고른 값이 사라진다.
- 두 갈래의 대가 =
  - ⑴ 결정을 유지하고 **보이는 것만 고친다** — 등록 화면에서도 빠짐없이 경고를 내고, 차이가 갈린 이유를 한 줄 더 쓰고, 목록·검토 화면에 표식을 붙인다. 등록을 멈추게 하는 것이 없어 기존 흐름이 그대로이고 작업이 작다. 대가 = 사용자가 표식을 보고도 넘길 수 있어 잘못된 단계가 확정되는 길은 남는다.
  - ⑵ 결정을 **바꿔** 차이가 있는 상태로 저장할 때 사유를 적고 한 번 더 확인하게 한다. 잘못된 단계가 확정되는 길이 좁아지고 나중에 왜 그렇게 골랐는지 읽을 기록이 남는다. 대가 = 등록 단계가 하나 늘고, 사유를 담는 저장 칸과 마이그레이션이 생기고, 부모를 나중에 붙이는 흐름에서는 같은 확인을 두 번 받게 된다(등록 때 · 부모 붙인 뒤).
- 권고 = ⑴ 을 이번 회차에, 그 중 「기본값을 계산값으로 맞춘다」는 함께 판정받는다(기본값만 바꿔도 차이가 생기는 건수가 줄어든다). ⑵ 는 별도 항목으로 대장에 등재하고 사유 칸 설계와 함께 다음 회차에서 판정.

---

## 요약표

| 항목 | 확인 결과 | 분류 | 기존 결정/항목 | 크기 | Ted 판정 필요 |
|---|---|---|---|---|---|
| D-2 프로젝트 카드 키보드 | 확인 — `<article>` ＋ `onClick`, `role`·`tabIndex`·`:focus-visible` 부재. 표 행 3자리 동일 패턴 | 결함(접근성) | 대장 항목 없음(접근성 항목은 대비만) | S(카드) / M(행 패턴 전체) | 범위(카드만 / 패턴 전체)만 |
| I-6 빈 소속 데이터셋 표 | 확인 — `<tbody>` 0행 분기 부재, 표가 무조건 렌더, 0행에도 좌우 이동 안내 출력 | 결함(기존 빈 상태 규칙 미적용) | 「0건 패널도 빈 상태」 선례 있음 · 이 표는 미적용 | S | 문면 확정만 |
| I-3 취소선 `Verified` | 확인 — 의도된 구현(`verified--pending` · 시험 4건 고정) | 설계 차이 ＋ 문면 불일치(`Verified`/`승인 전`/`승인됨`) | `PLAN-SoT 〈282〉`-㉮ Ted 판정 2026-09-02 | S(칸 글자) / M~L(상태 3값) | **필요 — 판정 반전** |
| I-1 ⑴ 확인 없이 허용 | 확인 — 경고 한 줄만, 확인·사유 단계 0건, 사유 저장 칸 0건 | 설계 차이 | PRD 미결-2 ⓐ Ted 확정 2026-09-05 | L | **필요 — 판정 반전** |
| I-1 ⑵ 기본값 Lv2 고정 | 확인 — `reg-level` 기본값 고정 Lv2(계산값 무관) | 설계 차이 | 판정문 「기본 선택값 = Lv2」 | M | **필요 — 판정 반전** |
| I-1 ⑶ 목록·검토 미표시 | 확인 — 목록 응답에 `processingLevelMismatch` 내려오나 화면 미사용, 프로젝트 표·계보 노드는 열쇠 미수신 | 미구현(대장 항목 없음) | 저촉 없음 | S(카탈로그) / M(표·노드·검토) | 불필요 |
| I-1 ⑶-b 불일치 이유 미표시 | 확인 — 문장이 두 값만 말한다 | 판정 이행 미달(미결-2 ⓐ 「화면에 사유 한 줄을 낸다」) | 미결-2 ⓐ 이행분 | S | 불필요 |
| I-1 ⑷ 부모 0건 등록에 경고 없음 | 확인 — `derivedPreview` 가 부모 0건에서 `null` ⟹ 비교 불성립 | 설계 차이 · ⑵(기본값 Lv2 고정)과 동일 판정 | 미결-2 ⓐ 의 「정상 중간 상태」 해석이 판정 대상 | S | 예(⑵ 와 한 묶음) |
| I-1 ⑸ 등록 뒤 Lv 수정 칸 없음 | 확인 — `editFields.ts` 7칸에 가공 단계·분류 3축 없음 | 미구현(대장 항목 없음) | [미확인] 다른 화면의 수정 칸 유무 | M | 불필요 |

### 후속 항목 (이 조사에서 고치지 않음)

- `CatalogTable` 0건 빈 상태는 `state.hasConditions` 일 때만 뜬다 — 조건 없는 0건에 문면이 없다(I-6 과 별개 자리).
- 행·카드 전체를 클릭 대상으로 쓰는 패턴 4자리(`ProjectCards`·`ProjectTable`·`CatalogTable`·`ProjectDatasetTable`)에 키보드 경로 부재.
- 접근성 검사 게이트 부재(`gates/` 에 a11y 게이트 없음) — 같은 계열 결함이 다시 잠복한다.
- 같은 승인 상태의 표기 3종(`Verified` 취소선 · `승인 전` · `승인됨`) 통일 여부.

### 미확인 목록

- 승인 요청 상태(요청 없음 / 검토 대기)를 내려보내는 계약 열쇠 유무 — `contracts/` ＋ 승인 라우트 grep 으로 닫힌다(I-3 갈래 ⓑ 크기 확정 전제).
- 가공 단계 수정 칸이 상세 편집 밖 다른 화면에 있는지 — `processingLevelUserSet` 프런트 전수 grep 으로 닫힌다.
- 검토 함(`TodoInbox`) 모수에 불일치를 더할 자리 — `frontend/src/components/dashboard/dashboardSource.ts` 확인으로 닫힌다.
- 사례 데이터셋 `TEST Stage12 Preview HDF5 20260911` 의 실제 저장값(사람 Lv · 부모 건수) — dev DB 조회 필요(이 조사 범위 밖).

---

## 추가 실측 (미확인 2건 해소 · 2026-09-13)

### I-3 갈래 ⓑ(상태 3값) — 입력이 서버에 이미 있다

- 「검토 대기」의 판정원이 존재한다 — `services/core-api/src/colab_core/app/routes/catalog.py` 앵커 `verification_pending = d2_access.pending_verification_of(db, dataset_id) is not None`. **상세 라우트 한 곳에서만** 계산된다.
- 상세 응답의 승인 한 벌 = 같은 파일 앵커 `"verification": {` 아래 `verified`·`approver`·`approvedAt`·`cancelledBy`·`cancelledAt`·`cancellationReason`. 목록 행(`DatasetRow`)에는 `verified` 불리언 하나뿐.
- ⟹ 3값 표기(승인됨 / 검토 대기 / 요청 없음)는 **계약 열쇠 추가 ＋ 목록용 묶음 질의**로 성립한다. 행마다 부르면 N+1 이라 ids 묶음 판정 함수 신설이 필요하다(선례 = 같은 파일 앵커 `unknown = d4_lineage.unknown_dataset_ids(db, ids)`).
- 크기 재산정 = **M**(ⓑ · L 가능성 제거). 계약 파괴 없음(열쇠 추가).
- 승인 요청 행동은 이미 화면에 있다 — `frontend/src/components/approval/types.ts` 앵커 `Verified 승인 요청 — 올린 사람·소유자가 상세 헤더에서 직접 누른다 (§1.2).`

### I-1 ⑸ 등록 뒤 가공 단계 수정 칸 — **부재 확정**

- 프런트에서 `processingLevelUserSet` 을 **쓰는**(전송) 자리는 업로드 흐름 둘뿐 — `frontend/src/components/upload/UploadModal.tsx` 앵커 `processingLevelUserSet: level,` · 같은 파일 앵커 `if (level) out.processingLevelUserSet = level;`.
- 그 밖의 참조는 전부 **읽기**다 — `common/processingLevel.ts` · `lineage/LineageSection.tsx` · `lineage/LineageStep.tsx`(앵커 `const selfLv = levelOf(ctx.processingLevelUserSet);`) · `upload/RegisterArea.tsx`(앵커 `{props.ctx.processingLevelUserSet === LV0 ? (`) · `routes/DatasetDetailPage.tsx`(앵커 `selfLv={levelOf(shown.basicInfo?.processingLevelUserSet)}`).
- ⟹ **[미확인] 해소** — 등록 완료 뒤 사람이 고른 가공 단계를 화면에서 고치는 경로는 없다. 계약 `DatasetUpdate` 에는 열쇠가 있어 화면 칸 신설만으로 닫힌다(크기 **S~M** · 계약·스키마 무변).
