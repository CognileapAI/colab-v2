# recon C — 레이아웃·문안 4건 (C-1 ~ C-4) 근본 원인

> 조사 전용. 레포 무수정. 경로는 레포 루트(`30 CoLAB-v2`) 기준 상대.
> 스크린샷 `bug01`·`bug02`·`bug09`·`bug12` 확인 완료.

## 0. 한 줄 결론

- C-1·C-3 = **같은 원인 하나** — `project.css` 에 화면 뿌리(`.project-page`·`.project-detail`) 규칙이 없다. **같은 파일 = 한 레인**.
- C-2 = `.gnb-settings` 에 `gap` 선언 누락. 형제 버튼 셋은 전부 있다.
- C-3 은 stub 아님 — `P5` 는 `done`(`work-items.yaml:1170~1179`). 화면은 다 서 있고 CSS 만 없다.
- C-4 = 사용자 입력도 생성도 아님. **시드 매니페스트에 사람이 손으로 적은 `／`**(`infra/staging/manifest-s2.json`).

## 1. 관례 — 화면 뿌리가 자기 여백을 직접 갖는다

`shell/AppLayout.tsx:9` 의 `<main className="appmain">` 은 껍데기뿐이다 — `shell/shell.css:212` 가 `.appmain { display: block; }` 한 줄이다. **공용 `PageShell`·컨테이너 클래스가 없다.** 각 화면 CSS 가 자기 뿌리에 여백을 적는 것이 관례다.

| 화면 | 뿌리 클래스 | 여백 선언 |
|---|---|---|
| S-03 카탈로그 | `.catalog-page` | `components/catalog/catalog.css:24` `padding: 24px 20px 40px` |
| S-05 데이터셋 상세 | `.detail-page` | `components/detail/detail.css:27` `max-width:1200px; margin:0 auto; padding:32px 24px 96px` |
| S-06 검색 결과 | `.search-page` | `components/search/search.css:22` `padding:24px 20px 40px; max-width:880px` |
| **S-02 프로젝트 목록** | `.project-page` | **없음** |
| **S-02b 프로젝트 상세** | `.project-detail` | **없음** |

`components/project/project.css` 전 483행에 `.project-page {` · `.project-detail {` 형태의 뿌리 규칙이 **0건**이다. 첫 등장이 `:4~11` 의 `.project-page .page-head, .project-detail .pd-head` — 자식 선택자로 바로 들어간다.

## 2. C-1 프로젝트 목록 좌측 여백 없음

- 증거 — `routes/ProjectsPage.tsx:28` `<div className="project-page" data-screen="S-02">` / `components/project/project.css:4` 이 뿌리를 건너뛰고 자식부터 적음.
- 결과 — 제목·설명·툴바·카드가 전부 뷰포트 좌단(0px)에 붙는다. bug01 에서 카드뿐 아니라 **제목 `프로젝트` 도 같이 붙어 있다** — 카드 목록만의 문제가 아니다.
- 곁가지(같이 봐야 함) — `project.css` 에 `h1` 규칙이 0건이라 제목이 브라우저 기본 `2em`(≈30px)이다. 카탈로그는 `catalog.css:26` 이 `var(--text-h2, 24px)` 로 잡는다. **글자 크기도 다른 화면과 어긋난다.**
- 최소 수정 — `project.css` 머리에 한 줄. `.project-page { padding: 24px 20px 40px; }` (카탈로그와 같은 값). 제목 크기는 `.project-page .page-head h1 { font-size: var(--text-h2, 24px); margin: 0; }`.

## 3. C-2 「연구실 설정」 아이콘·글자 간격

- 증거 — `shell/shell.css:148~161` `.gnb-settings` 에 `display:inline-flex; align-items:center` 는 있으나 **`gap` 이 없다**.
- 형제 대조 — `.gnb-upload` `gap: 6px`(`:170`) · `.avatar` `gap: 6px`(`:191`) · `.labswitch` `gap: 7px`(`:82`). 셋 다 있고 이것 하나만 빠졌다.
- 마크업은 정상 — `shell/Gnb.tsx:103~108` 이 `<Icon>` ＋ `<span className="lbl">연구실 설정</span>` 으로 형제 버튼과 같은 구조다. 컴포넌트가 다르거나 아이콘이 인라인인 문제가 아니다.
- 최소 수정 — `.gnb-settings` 에 `gap: 6px` 한 줄. ⚠ 반응형 사다리 확인 — `shell.css:259` 가 880px 이하에서 `.gnb-settings { display:none }` 이므로 `gap` 추가는 넓은 폭에만 영향.

## 4. C-3 프로젝트 상세가 raw HTML 수준

**stub 아니다.** `routes/ProjectDetailPage.tsx` 243행이 개요·연결 주소·소속 데이터셋 세 카드 ＋ 모달 셋(F-03/F-04/F-05)까지 다 서 있다. `dev-package/work-items.yaml:1170` `P5 프로젝트 목록·상세(S-02/S-02b)` = **`status: done`**.

원인은 CSS 결손 넷이다.

| 결손 | 위치 | 데이터셋 상세의 대응물 |
|---|---|---|
| 페이지 여백·최대폭 없음 | `.project-detail` 뿌리 규칙 부재 | `detail.css:27` |
| 카드에 면·그림자 없음 | `project.css:197~201` `.project-detail .card` = border ＋ radius ＋ padding 뿐 | `catalog.css:29~32` `.catalog-page .card` 는 `background: var(--color-surface)` ＋ `box-shadow` |
| 제목 크기 미지정 | `project.css` 에 `h1` 규칙 0건 | `detail.css:44~47` `.detail-page .dt-header h1 { font-size:31px … }` |
| 되돌아가기 줄 무스타일 | `.backrow`·`.backlink` 는 `detail.css:30~39` 에서 **`.detail-page` 로 스코프**돼 프로젝트 상세에 안 닿는다 | 같은 마크업(`ProjectDetailPage.tsx:41~46`)인데 규칙만 없다 |

카드에 면이 없으니 `--color-bg: #f9fafb`(`shell/tokens.css:16`)가 그대로 비쳐 카드가 배경에 녹는다 — bug09 의 「개요」 상자가 그 모습이다.

또 하나 — `project.css` 는 `--line`·`--fg-muted`·`--surface-2`·`--warn`·`--surface` 를 쓰는데 **`shell/tokens.css` 에 이 이름이 하나도 없다.** 전부 폴백 리터럴로만 그려진다(예 `:198` `var(--line, #e3e6ea)`). 다른 화면은 `--color-border`·`--color-text-muted` 계열을 쓴다. 토큰 계보가 갈라져 있어 색이 미묘하게 어긋난다.

- 문서 근거 — `work-items.yaml:1179` 축자: 「목업 대비 화면 검증의 실측 기록은 모달 셋과 데이터셋 표에는 있고, **목록·상세 골격(`ProjectCards`·`ProjectTable`·`ProjectToolbar`)에는 없다**」. 그 축은 `G1b`(`:399`, `status: open` · `stage: after_stage2`)로 넘겼다. **미검수 상태 그대로 배포된 것이 이번 버그다.**
- 최소 수정 — `project.css` 머리에 뿌리 규칙 2개(`.project-page`·`.project-detail`) ＋ `.project-detail .card` 에 `background: var(--color-surface); box-shadow: var(--shadow-sm)` ＋ `h1` 크기 ＋ backrow/backlink 를 `detail.css` 에서 이식(또는 두 화면 공용으로 승격).

## 5. C-4 데이터셋 설명의 `／` — 출처와 표시 제안

### 출처

- **시드다.** `infra/staging/manifest-s2.json` 의 `datasets[].summary` 에 사람이 손으로 적은 전각 슬래시. 건별 개수 = D-01 2 · D-02 1 · D-03 4 · D-04 4 · D-05 3 · D-06 4 · D-07 4 · D-08 2 · D-09 3 · D-13 5 · D-15 5 · D-16 5 (**12건 42개**).
- 원문 = `dev-package/sessions/S2b-DATASET-DESCRIPTIONS.md`(2026-08-25 초안 · 2026-08-26 Ted 일괄 승인). `／` 는 **원천 동봉 문서 여러 문단을 한 필드에 이어 붙인 이음매**다 — 계보·가공 단계에서 자동 생성한 것이 **아니다**.
- 통과 경로 — `infra/staging/load-seed.py:201` 이 `summary` 를 손대지 않고 API 로 그대로 넘긴다. 저장은 `db/platform/schema.sql:371` `summary text`(길이 제약 없음).
- 사용자 입력분은 다른 모양 — `components/upload/RegisterArea.tsx:196~204` 가 `<input maxLength={300}>` **한 줄 입력**이라 사람이 넣는 설명은 짧고 `／` 관례가 없다. 즉 **`／` 는 시드 12건만의 성질**이다.
- 표시 지점 둘 — `components/detail/DetailHeader.tsx:24~28` `.dh-sum`(현재 릴리스) · `components/search/SearchHitCard.tsx:66` `.hit-summary`(검색 화면은 stage 3).

### 제안 3안 (Ted 판정용)

| 안 | 내용 | 저장 | 장점 | 단점 | 공수 |
|---|---|---|---|---|---|
| **A. 표시만 분할** | `DetailHeader` 에서 `summary.split('／')` → `<ul>` 불릿 또는 문단 목록 | 그대로 | 시드·DB·계약 무접촉. 되돌리기 쉬움. 사용자 입력 설명(`／` 없음)은 1항목이라 지금과 동일 | 구분자를 코드가 안다는 암묵 규약이 생김. `／` 를 본문에 쓴 설명이 나중에 오면 오분할 | **S** (1파일 ＋ CSS ＋ 시험 1건) |
| **B. 표시 분할 ＋ 라벨 붙인 정의형** | 조각을 `개념 / 원천 / 규격 / 범위 / 한계` 로 라벨링해 `<dl>`. 라벨은 시드에 필드로 추가 | 매니페스트 스키마 개정 ＋ 재시드 | 데이터셋 상세가 「라벨:값」 관례(`infogrid`)와 한 결. 검색 색인도 필드 단위 | 조각 수·의미가 12건마다 달라(1~5개) 공통 라벨 집합이 안 나옴. 재시드 = 운영 접촉 | **L** |
| **C. 첫 조각만 노출 ＋ 나머지 접기** | 첫 문단을 요약으로 보이고 「자세히」로 나머지 펼침 | 그대로 | 헤더가 짧아져 칩·기본정보가 접힘선 위로 올라옴(bug12 에서 설명이 화면 4줄 차지) | 접힌 내용은 안 읽힘. 상세 화면 정본이 「줄마다 한 가지」(DetailHeader.tsx:1) 라 접기 관례가 화면에 아직 없음 | **M** |

- 권고 = **A 를 기본**, 필요하면 A ＋ C(조각 3개 초과일 때만 접기). **저장 형식은 건드리지 않는다** — 시드 재적재는 운영 접촉이고 `S2b` 승인문(줄 단위 Ted 승인)을 다시 열게 된다.
- 판정 필요 — 정본 `Policy_데이터셋_상세` 가 `.dh-sum` 을 「한 줄 요약」으로 못 박고 있다(`DetailHeader.tsx:2` 축자 「③ 한 줄 요약」). **여러 줄로 펼치는 것이 정본 위반인지** Ted/advisor 판정 대상.

## 6. 시험 가능성 · 실행법

- Playwright 없음. `frontend/package.json` = `vitest run` ＋ jsdom ＋ testing-library 뿐. **스크린샷 시험은 이번 회차에 불가**(도구 신설 필요).
- **계산값 시험은 가능하다.** `frontend/vite.config.ts` 의 `test.css = { include: [/catalog\.css$/] }` 가 카탈로그 CSS 만 싣고 있다. 여기에 `/project\.css$/`·`/shell\.css$/` 를 더하면 `getComputedStyle` 로 잴 수 있다. 선례 = `frontend/test/catalog.test.tsx:293`·`:375`.
  - C-1 — `.project-page` 의 `paddingLeft !== '0px'`
  - C-2 — `.gnb-settings` 의 `columnGap` 이 `.gnb-upload` 와 같음
  - C-3 — `.project-detail` 의 `padding`, `.project-detail .card` 의 `backgroundColor`
  - C-4 — `dh-sum` 안 항목 수 = `summary` 의 `／` 개수 ＋ 1 (CSS 불필요, 순수 DOM)
- 실행 — `cd frontend && npm test`(＝`vitest run`) · 타입 `npm run typecheck` · 게이트 `gates/run.sh frontend-test`(`gates/tools/frontend-test.sh`, 수집 0건이면 red).

## 7. 레인 배치 (동일 파일 주의)

| 레인 | 파일 | 버그 |
|---|---|---|
| L1 | `frontend/src/components/project/project.css` (＋ `routes/ProjectDetailPage.tsx` 무수정 가능) | **C-1 ＋ C-3 — 반드시 한 레인** |
| L2 | `frontend/src/shell/shell.css` | C-2 |
| L3 | `frontend/src/components/detail/DetailHeader.tsx` ＋ `components/detail/detail.css` | C-4 (판정 후) |

- 겹침 없음 — L1/L2/L3 파일 교집합 0. 병렬 가능.
- ⚠ C-3 에서 backrow/backlink 를 `detail.css` 에서 **공용으로 승격**하는 안을 택하면 L1 과 L3 이 `detail.css` 에서 충돌한다. 그 경우 프로젝트 쪽에 복제하는 쪽을 택하거나 직렬로 돌린다.

## 8. 최근 이력

- `project.css` — `40edc65`(2026-09-03 「게이트 frontend-test 신설 ＋ 화면 검수 소수리 8건 〈291〉」) · `e43574f` · `2a0c489`(최초). **여백 결손은 최초 커밋부터 있었고 소수리 8건에도 안 잡혔다.**
- `shell.css` — `3e74dae` · `3023bee`(〈296〉 GNB 반응형 사다리 정정) · `5a74c27` 외. `.gnb-settings` 의 `gap` 은 어느 회차도 건드리지 않았다.
- `manifest-s2.json` — `f1f40d0` · `6c6f590`(D-16 적재) · `7c3b9ac`(최초 적재).
- 곁가지 발견 — `routes/LabPage.tsx:36` 도 뿌리 클래스가 없고 `dashboard.css:5` `.dash-columns` 에 좌우 여백이 없다. 히어로(`search.css:5` `padding: 40px 20px 28px`)만 여백을 갖는다. **S-01 도 같은 결손일 가능성** — Ted 접수 목록에는 없으나 확인 권고.
