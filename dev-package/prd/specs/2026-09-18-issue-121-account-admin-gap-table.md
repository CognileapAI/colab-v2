# Spec: 계정 관리 화면 — 탭~목록 간격의 소유자 단일화와 계정 목록 표의 열 폭 고정·액션 열 고정 (#121)
출처 intent: `dev-package/intent/2026-09-18-issue-121-account-admin-gap-table.md`
**읽는 순서 — `## advisor ① 검토 결과` 절이 본문(구현 결정·시험 결정)과 충돌하면 그 절이 우선한다.**

## 문제 진술
- `frontend/src/routes/AccountAdminPage.tsx` 의 최상위는 `<div className="login account-admin">` 이고 그 직계 자식은 `<h1>계정 관리</h1>` · `<div className="settabs" role="tablist" aria-label="계정 관리 탭">` · `<div hidden={tab !== 'create'}>`(생성 패널) · `<div hidden={tab !== 'list'}>`(목록 패널) 넷이다. 목록 패널 안에 `<section className="login-card account-list-card" data-testid="account-list">` 가 있다.
- 두 패널 래퍼는 클래스가 없고 일치하는 CSS 규칙이 없다. 숨은 패널은 UA `[hidden] { display: none }` 으로 상자를 만들지 않는다. 따라서 탭 줄 하단과 카드 상단 사이 코드상 간격은 `.settabs { margin-bottom: 14px }`(`frontend/src/components/members/members.css`) + `.account-list-card { margin-top: 24px }`(`frontend/src/auth/login.css`) = **38px** 이다. 부모가 grid(`display: grid`)라 마진 상쇄가 없다. 이슈의 완료 조건 24~32px 을 6px 넘는다.
- 이슈 첨부 화면의 약 200px 띠는 HEAD 코드로 재현되지 않는다. 첨부의 문면(「관리자 등록」·「관리자 지정/해제」)이 `315fb85f`(#84, 2026-09-17) 이전 빌드의 것이고, 그 이전에는 `.login.account-admin { min-height: auto; align-items: start; }` 가 없어 공용 `.login { min-height: 100dvh; display: grid; place-items: center; }` 가 탭 줄 위·아래로 같은 크기의 띠를 만든다. **첨부 화면과 코드를 맞춰 본 추론이며 계측이 아니다.**
- 표 쪽 — `.account-list-card { max-width: 960px }` 에 `.login-card { padding: 32px 28px }` 가 걸려 내용 상자 904px. `.account-table th, .account-table td { white-space: nowrap }` 가 여덟 열의 최소 폭을 부풀리고, 액션 셀(`<td className="account-row-actions">` · `display: flex; gap: 8px`)은 `.btn.btn-secondary` 셋(「시스템 관리자 지정」/「시스템 관리자 해제」 · 「비밀번호 재설정」 · 「비활성화」/「재활성화」)을 한 줄에 담는다. 자기 줄에는 `<span className="account-row-note">` 가 `SELF_STATUS_REASON`(`자기 계정은 비활성화할 수 없어요`)을 더 붙인다. 표의 내재 폭이 904px 을 넘어 `.account-table-scroll { overflow-x: auto }` 가 스크롤을 만들고 마지막 열이 보이는 영역 밖으로 나간다.
- `table-layout` 이 어디에도 없어 기본 `auto` 다. 긴 이메일 하나가 모든 열의 폭을 바꾼다 — 이슈의 셋째 완료 조건이 구조적으로 위반된 상태다.
- `.account-table`·`.account-table-scroll` 에 `min-width` 는 없다. 이슈가 의심한 ①은 원인이 아니다.

## 해법 개요
- 탭~카드 간격의 **소유자를 컨테이너 하나로** 만든다. `.login.account-admin` 이 `row-gap` 을 갖고, 이 화면 범위 안에서 `.settabs` 의 `margin-bottom` 과 `.account-list-card` 의 `margin-top` 을 0 으로 덮는다. 공용 기본 규칙은 건드리지 않는다.
- 계정 목록 카드에만 폭 상한을 올리고, 표를 `table-layout: fixed` 로 바꿔 열 폭을 **실제 내용에서 도출한 값**으로 고정한다. 자유 문자열 열은 생략 부호 + `title` 로 처리한다.
- 액션 열을 `position: sticky; right: 0` + 불투명 토큰 배경으로 고정해, 가로 스크롤이 남는 좁은 폭에서도 버튼 셋이 보이는 영역 안에 있게 한다.
- 스크롤 래퍼·안내 문단·열 구성·글자 크기·행 높이는 그대로 둔다.

## 사용자 스토리
1. 서비스 운영자로서 계정 관리 화면에 들어가면 스크롤 없이 목록이 보이기를 원한다, 진입할 때마다 스크롤하지 않기 위해.
2. 서비스 운영자로서 넓은 화면에서 계정 목록의 모든 열이 한 번에 보이기를 원한다, 가로로 밀지 않고 상태를 읽기 위해.
3. 서비스 운영자로서 권한 지정·해제 버튼이 잘리지 않고 눌리기를 원한다, 이 화면의 핵심 조작을 확실히 하기 위해.
4. 서비스 운영자로서 긴 이메일 한 건이 표 전체 모양을 바꾸지 않기를 원한다, 계정마다 열 자리가 달라지지 않게.
5. 서비스 운영자로서 잘린 이메일의 전체 값을 확인할 수 있기를 원한다, 계정을 잘못 짚지 않기 위해.

## 구현 결정
- **D1 구속력** — 이슈의 완료 조건 6개·금지 조건 3개·비범위가 구속력이다. 이슈 본문의 「그대로 보낼 프롬프트」에 적힌 목표 상태(1600px · 퍼센트 열 폭 · 1280px 분기)는 **제안**이며, 코드와 대조해 살아남는 항목만 채택한다.

- **D2 여백(결함 1)** — `frontend/src/auth/login.css`:
  - `.login.account-admin` 에 `row-gap: var(--space-section)` 을 더한다(정의값 24px · `frontend/src/shell/tokens.css`). 미정의 토큰 신설 없음.
  - 같은 화면 범위에서만 형제 마진을 지운다: `.login.account-admin .settabs { margin-bottom: 0; }` 와 `.account-list-card` 규칙에서 `margin-top: 24px` 삭제. **`.settabs` 기본 규칙(`members.css`)·`.login`·`.login-card` 기본 규칙은 고치지 않는다.**
  - 결과 간격 = row-gap 24px 하나. 24~32px 안이다.
  - **다른 간격에 미치는 영향(같은 grid 의 다른 행)** — `row-gap` 은 `h1` ↔ `.settabs` 사이에도 걸린다. 현재 그 간격은 `h1` 의 UA 마진(`.colab-ui` 계열 규칙 중 `h1` 마진을 지우는 것을 찾지 못했다 · [미확인])이고, row-gap 을 더하면 그만큼 커진다. 소유자 단일화를 여기서도 지킨다: `.login.account-admin > h1 { margin: 0; }` 를 함께 두어 `h1`↔탭 간격도 24px 한 값이 되게 한다. 레인은 **HEAD 의 `h1` 마진 실측값을 먼저 남기고** 전후를 비교한다.
  - 생성 탭(`tab === 'create'`)에서는 탭 줄 ↔ `.login-card.account-card` 간격도 14px → 24px 로 바뀐다. 의도한 변화로 선언하고 전후 스크린샷을 남긴다.
  - 카드 **안**의 간격(`.account-filters { margin: 16px 0 0 }` · `.account-table-scroll { margin-top: 16px }` · `.account-status { margin: 16px 0 0 }`)은 grid 항목이 아니라 영향을 받지 않는다. 손대지 않는다(이슈 비범위 = 카드 내부 디자인).
  - 목록 패널 뒤의 `{message ? <p className="account-status" …> : null}` 는 `.login.account-admin` 의 직계 자식이라 **row-gap 이 걸린다.** 현재는 자기 `margin: 16px 0 0` 만 있어 16px, 변경 뒤 24+16 = 40px 이 된다. 이 문단은 조작 직후에만 나타나므로 회귀로 보지 않되, 소유자 단일화를 지켜 `.login.account-admin > .account-status { margin-top: 0; }` 로 24px 한 값으로 맞춘다.
  - 0건 상태는 탭~카드 사이 DOM 이 같다(0건 안내 `p.account-status` 는 표 뒤 카드 **안**). 같은 값이 나와야 한다 — ⓒ 로 잰다.

- **D3 표(결함 2)** — 같은 파일:
  - 폭 상한은 `.account-list-card` 에만 올린다: `max-width: 1600px`(이슈 제안 수치를 채택 · `.login-card { max-width: 360px }` 는 불변). `.login { padding: 24px }` 는 공용이라 그대로 둔다 — 이슈 제안문의 「좌우 패딩 32px **유지**」는 현행(24px)과 다른 서술이므로 채택하지 않고 24px 을 유지한다.
  - `justify-items: center`(공용 `.login { place-items: center }` 에서 살아남음)는 카드 폭에 영향이 없다. `.login-card { width: 100%; min-width: 0 }` 이므로 카드는 grid 열(`minmax(0, 1fr)`) 폭까지 늘고 `max-width` 에서 멈춘다. 별도 `justify-self` 를 넣지 않는다. `h1`·`.settabs` 는 종전대로 가로 가운데에 선다(우려 5).
  - `.account-table { table-layout: fixed; }` 를 더한다. `width: 100%` 는 그대로.
  - **열 폭은 실제 내용에서 도출한다.** 레인은 고치기 전에 실브라우저에서 ⑴ `.btn.btn-secondary` 버튼 셋 각각의 `get box` 폭 ⑵ `.account-row-note` 의 `get box` 폭 ⑶ 각 `th` 의 `get box` 폭을 재어 JSON 으로 남기고, 그 값으로 열 폭을 정한다. 코드에서 나오는 하한은 `.btn { min-height: var(--control-height); padding: 10px 18px; font-size: var(--text-body-sm) }`(`design-system.css` · `body.colab-ui` 가 `frontend/index.html` 에 있으므로 이 규칙이 적용된다) + `.account-row-actions { gap: 8px }` + `td { padding: 10px 12px }` 이며, 글자 폭은 폰트 의존이라 **코드만으로는 확정되지 않는다 [미확인]**.
  - 이슈 제안의 퍼센트(22/12/8/20/8/8/12/10)는 쓰지 않는다. 액션 열 10% 는 버튼 셋을 담지 못하고, 담으려면 줄바꿈이 필요한데 줄바꿈은 행 높이를 바꿔 금지 조건에 걸린다.
  - 폭 지정 방식: `.account-table` 에 열 번호 선택자(`th:nth-child(n)`)로 액션 열과 좁은 열(역할·상태·시스템 관리자·최근 로그인)에 px 값을 주고, 이메일 열은 `auto` 로 남은 폭을 받는다. `table-layout: fixed` 에서 열 폭은 첫 행(`thead`)의 지정을 따르므로 `td` 에는 폭을 주지 않는다.
  - `.account-table { min-width: <열 폭 합계>px }` 를 두어, 좁은 폭에서 열이 뭉개지는 대신 가로 스크롤이 나게 한다(1440px 미만에서 스크롤 허용).
  - 자유 문자열 셀(이메일·이름·연구실)에 TSX 에서 클래스와 `title` 을 단다: `<td className="account-cell-text" title={row.email}>{row.email}</td>` · `title={row.name}` · `title={row.labName ?? '없음'}`. CSS 는 `.account-table td.account-cell-text { overflow: hidden; text-overflow: ellipsis; }`(`white-space: nowrap` 은 공용 셀 규칙에서 이미 온다).
  - 액션 열 고정: `.account-table th:last-child, .account-table td.account-row-actions { position: sticky; right: 0; background: var(--color-surface); border-left: 1px solid var(--color-border); }`. 배경은 카드 표면 토큰과 같아야 행이 비쳐 보이지 않는다. 이 레포의 표 CSS 에 `position: sticky` 선례가 없으므로(신규 패턴) 실화면 계측으로 확인한다.
  - `.account-row-note` 는 액션 셀 안에서 `min-width: 0; overflow: hidden; text-overflow: ellipsis` 를 갖고 `title={SELF_STATUS_REASON}` 를 단다(TSX). 전체 문면은 DOM 과 `title` 에 남아 기존 시험(`…자기 줄 비활성화는 처음부터 눌리지 않고 이유가 화면에 적혀 있다`)이 green 이고, 줄바꿈이 없어 행 높이가 바뀌지 않는다. 자기 줄 note 를 **열 폭 산정의 필수 요소로 넣지 않는다**(우려 1).
  - `.account-table-scroll` 의 `role="region"` · `aria-label` · `tabIndex={0}` 과 `p.table-scroll-hint` 는 그대로 둔다. 공용 `.table-scroll-hint` 의 1100px 분기(`design-system.css`)를 고치지 않고, 1280px 분기를 새로 만들지 않는다.
  - `@media (max-width: 640px) { .account-row-actions { flex-wrap: wrap; } }` 는 그대로 둔다 — 좁은 화면의 종전 동작이며 이번 변경 대상이 아니다. 단 390×844 계측(ⓔ)은 이 분기 안에서 재는 값임을 보고서에 적는다.

- **D4 금지 조건 준수** — 본문 글자 크기 선언을 바꾸지 않는다(`.account-table { font-size: var(--text-body-sm) }` = 14px · `.account-row-note { font-size: var(--text-caption) }` = 13px). 열을 숨기거나 지우지 않는다(`th` 8개 유지). 행 높이를 바꾸지 않는다 — `td { padding: 10px 12px }` 와 `.btn { min-height: var(--control-height) }` 를 손대지 않고, 액션 셀 안에서 줄바꿈이 생기지 않게 한다. **「행 높이 불변」의 판정 방법**: 같은 계정 데이터로 수정 전(HEAD)과 후에 같은 행의 `get box` 높이를 실브라우저에서 재어 값이 같음을 보인다(보통 줄·자기 줄 각각).

- **D5 뷰포트 규약** — 「1920×1080」·「1440px」·「1280px」은 **DPR 1 의 CSS px** 이며 `agent-browser` 뷰포트 설정값이다. 이슈 첨부 화면은 DPR 1 이 아니다(우려 4 · 미확인).

- **스키마 · 마이그레이션**: 없음. **API 계약**: 변경 없음. **문면**: 새로 만들지 않는다(`title` 속성은 기존 값의 복제다).
- **커밋·PR 단위**: 이슈 1건 = PR 1건. 커밋 3개 — ⑴ intent+spec ⑵ 수정(CSS+TSX+시험) ⑶ 증거 보고서. 브랜치 `claude/issue-121-account-admin-gap-table`, base `develop`. PR 본문은 저장소에 커밋하지 않는다.

## 시험 결정
- 외부 행위 기준 검증 항목:
  - ⑴ CSS 원문 — `.login.account-admin {` 에 `row-gap: var(--space-section)`; `.account-list-card {` 에 `margin-top` 없음; `.login.account-admin .settabs {` 에 `margin-bottom: 0`; `.account-table {` 에 `table-layout: fixed` 와 `min-width`; 액션 열 규칙에 `position: sticky`·`right: 0`·`background: var(--color-surface)`; `.account-cell-text` 규칙에 `overflow: hidden`·`text-overflow: ellipsis`.
  - ⑵ CSS 원문(금지 조건 잠금) — `.account-table {` 의 `font-size: var(--text-body-sm)` 와 `.account-row-note {` 의 `font-size: var(--text-caption)` 가 그대로; `.account-table th, .account-table td {` 의 `padding: 10px 12px` 와 `white-space: nowrap` 이 그대로; `.login {`·`.login-card {`·`members.css` 의 `.settabs {` 원문이 그대로.
  - ⑶ TSX — 이메일·이름·연구실 셀의 `title` 이 화면에 그려진 값 전체와 같다(잘린 표시가 아니라 원값). 60자 이상 이메일 픽스처에서도 같다.
  - ⑷ TSX — 자기 줄 `.account-row-note` 에 `title={SELF_STATUS_REASON}` 이 있고 문면이 DOM 에 남아 있다.
  - ⑸ 기존 단언 유지 — 일곱 열 + 행 동작 열 · 스크롤 래퍼(`role="region"`·`tabIndex`)와 `.table-scroll-hint` 존재 · `.account-admin` 수식 클래스가 최상위에만 · 로그인/비밀번호 변경 화면에는 없음.
- 시험 파일: 신설 `frontend/test/account-admin-layout-20260918.test.ts`(CSS 원문 · 레포 관행 `frontend/test/css-residual-rc11.test.ts` 의 `String(readFileSync(resolve(process.cwd(), rel), 'utf8')).replace(/\/\*[\s\S]*?\*\//g, '')` 를 그대로 쓴다)와 기존 `frontend/test/account-admin.test.tsx`(⑶⑷ 추가 · ⑸ 유지).
- 재사용 seam: `frontend/test/account-admin.test.tsx` 의 기존 렌더 seam. 신설 seam 없음.
- red → green 순서: ⑴⑵⑶⑷ 시험을 먼저 추가해 **red 를 관측하고 실패 문구를 기록한 뒤** CSS·TSX 를 고친다. red 관측 기록(시험 이름 + 실패 문구)을 보고서에 남긴다.
- green-by-skip 방지: ⑶ 은 짧은 이메일(생략 부호 없음)과 60자 이상 이메일 두 케이스를 **쌍**으로 둔다. ⑵ 는 「없어야 할 것이 없다」가 아니라 「있어야 할 원문이 있다」로 쓴다. 수집 0건은 게이트가 red 로 잰다.
- **jsdom 한계** — jsdom 은 배치를 계산하지 않는다. ⓐ~ⓕ·ⓘ 는 단위 시험으로 판정되지 않는다. 실브라우저 계측이 **필수**다.
- 실브라우저(`agent-browser` · 판정은 사람) — 뷰포트 1920×1080 · 1440×900 · 1280×800 · 1024×768 · 390×844, 수정 **전(HEAD)과 후** 각각:
  - `div.settabs` 와 `section.account-list-card` 의 `get box` → `card.top − tabs.bottom`(ⓐ). 계정 ≥1건 상태와 0건 상태 둘 다(ⓒ).
  - `h1` · `.settabs` 의 `get box` → `h1`↔탭 간격(회귀 확인).
  - `.account-table-scroll` 과 `.account-table` 의 상자 폭 비교(가능하면 `scrollWidth`/`clientWidth`) → 1920·1440 에서 넘침 0(ⓓ).
  - 액션 셀 버튼 셋 각각의 `get box` 가 `.account-table-scroll` 의 보이는 상자 안에 완전히 포함(ⓔ). 가로 스크롤이 있는 폭에서는 스크롤 좌·우 양 끝에서 각각.
  - 같은 행의 `get box` 높이 전후 비교(ⓘ · 보통 줄·자기 줄).
  - 60자 이상 이메일 픽스처 유·무에서 표와 각 `th` 의 `get box` 폭 동일(ⓕ).
  - 1920×1080 에서 5번째 `tbody tr` 하단이 1080 이하(ⓑ).
  - 좌표는 JSON 으로 `dev-package/reports/issue-121/` 에 남긴다(워크트리 가드가 `eval` 을 막으므로 `get box` 만 쓴다).
  - 라이트·다크 스크린샷을 남긴다(sticky 배경이 다크에서도 불투명한지 눈으로 확인 · 우려 3).
- 해당 서비스 단독 게이트: `frontend-typecheck` · `frontend-test` · `frontend-visual` · `frontend-fixture-reach`. `frontend-visual` 은 `COLAB_VISUAL_URLS` 에 계정 관리 화면 URL 을 **실선언**한다(CSS 를 만지므로 `COLAB_VISUAL_EXEMPT=1` 금지). 준비 실패·미실행을 green 으로 세지 않는다. 3계수·종료코드를 그대로 회수한다.

## 정책 대조 (작성 시점 제약)
대조 원본은 `.agents/rules/product.md` §3(불변 규칙)·§5(절대 하지 않는 것)다. **[미확인] — 이 spec 작성 중 원문을 열어 읽지 않았다.** 아래는 변경 범위(프런트 CSS 1파일 + TSX 1파일 + 시험)에서 도출한 대조이며, 레인이 원문으로 재확인한다.
- 도메인 테이블 참조 · AI→계보 쓰기 · 마이그레이션 체인 · core-api geo import · 연구실 경계 · 정규 ID 타입: **저촉 없음.** 조회·DB·백엔드를 건드리지 않는다.
- 생성물 손수정: **저촉 없음** — `src/generated/` 를 만지지 않는다. 절대경로: **준수.**
- 게이트 우회: **저촉 없음** — 네 게이트 실선언, `frontend-visual` 면제 없음.
- 「나중에」로 남기기: **부분 해당 — 드러내 둔다.** 이슈 첨부 화면 같은 좁은 실효 뷰포트(1440px 미만)에서는 가로 스크롤이 남고 5행 조건도 보장되지 않는다. 완료로 세지 않고 보고서에 수로 적는다(우려 4).
- 범위 늘리기: **저촉 없음.** `h1` 마진·`message` 문단 마진을 0 으로 덮는 것은 row-gap 도입의 동반 필수다(같은 grid 의 다른 행이 함께 벌어지는 것을 막는다). 우려 2 로 올린다.
- 용어: 계정 관리 · 계정 목록 · 시스템 관리자 · 연구실. `DOMAINS.md` 정본 표기를 건드리지 않는다. 새 문면 없음.
- 결정 로그: 신규 legacy 결정번호 발급 없음.

### 디자인 제약 확인
정본 = `frontend/src/shell/tokens.css`. 판정 기준 = `.agents/skills/design-review/SKILL.md §0`(대비 4.5:1 · 글자 13px 이상 · 미정의 토큰 0 · 음수 여백 0 · 카드 그림자 0(팝오버 허용) · 보더 2층 토큰 분리 · 여백은 컨테이너 소유).
- 토큰: `--space-section`(24px) · `--color-surface` · `--color-border` 만 쓴다. 미정의 토큰 0. 새 색 없음. 열 폭 px 값은 토큰이 아니라 **실측에서 도출한 치수**이므로 토큰화 대상이 아니다.
- 글자: 14px(`--text-body-sm`) · 13px(`--text-caption`) 그대로. 축소 없음 — 13px 하한을 지킨다.
- 대비: 액션 열이 `position: sticky` 로 다른 셀 위에 겹치므로 **불투명 `--color-surface` 배경**을 갖는다. 반투명을 쓰지 않는다 — `frontend-visual` 이 상속 배경으로 재므로 반투명은 판정이 서지 않는다. 다크에서 `--color-surface` 위 본문 대비는 실화면으로 잰다.
- 그림자: 0. 고정 열은 팝오버가 아니라 표의 일부이므로 보더로만 구분한다.
- 보더 2층: 셀 구분선 `--color-border` 와 고정 열 왼쪽 경계 `--color-border` 가 같은 층이다. 컨트롤 보더(`--color-border-control`)와 섞지 않는다.
- 여백: 탭~카드 간격의 소유자는 `.login.account-admin` 한 곳(row-gap)이다. 형제 마진을 더하지 않는다. 음수 여백 0.
- 인터랙션: 새 전환·애니메이션 없음 → `prefers-reduced-motion` 분기 신설 없음. 버튼 최소 높이 `--control-height` 유지(≤640px 에서 44px).
- 판정: **조건부 통과.** 다크 모드 고정 열 배경과 열 폭 확정값은 실화면 계측으로 확정한다(우려 1·3).

## advisor ① 검토 결과 (2026-09-18)
판정: **조건부 진행.** 레인 1개·PR 1건·CSS 원문 시험 + 실브라우저 계측 구조는 유지. 아래 A1~A9 는 본문보다 우선한다. CSS 동작 판단은 코드와 CSS 규격에 근거한 것이며 브라우저에서 재지 않았다 — 레인이 실화면으로 확정한다.

- **A1 액션 셀 구조(D3 sticky 규칙 교체)** — `login.css` 의 `.account-row-actions { display: flex }` 가 `<td className="account-row-actions">` 자체에 걸려 `td` 가 table-cell 이 아니게 된다. 그 위의 `position: sticky` 는 붙지 않는다(익명 셀이 containing block). 액션 `td` 는 table-cell 로 남기고 새 클래스 `account-row-actions-cell` 을 단다. flex 는 안쪽 `<div className="account-row-actions">` 로 옮긴다. sticky·배경·경계는 `td.account-row-actions-cell` 과 `thead th:last-child` 에 건다. `td` 에 `display` 를 선언하지 않는다. 기존 시험은 `account-row-actions`·`closest('td')` 를 참조하지 않는다(advisor 확인) — 레인이 grep 으로 재확인한다.
- **A2 카드가 grid 열 폭까지 늘게 한다(D3 「카드는 grid 열 폭까지 늘고」 전제 정정)** — grid 항목은 카드가 아니라 `<div hidden={tab !== 'list'}>` 래퍼이고, 공용 `.login { place-items: center }` 의 `justify-items: center` 가 래퍼를 fit-content 로 줄인다. 목록 패널 래퍼에 클래스 `account-list-panel` 을 달고 `justify-self: stretch; min-width: 0` 을 준다. 카드는 `margin-inline: auto` 로 가운데. **그 클래스에 `display` 를 선언하지 않는다(`[hidden]` 이 깨진다).** 생성 패널 래퍼는 건드리지 않는다. 계측에 카드 폭 기대값을 더한다: 1920 에서 1600px, 1440 에서 뷰포트 − 48 − (세로 스크롤바).
- **A3 sticky 는 `@media (min-width: 1024px)` 안에서만 건다.** 390px 에서 스크롤 영역은 약 284px 이고 액션 열은 추정 400px 대라, 고정하면 왼쪽 버튼이 영구히 가려진다. ≤640px 에서는 `table-layout: fixed` 가 열을 px 로 고정해 기존 `@media (max-width: 640px) { .account-row-actions { flex-wrap: wrap } }` 가 죽은 규칙이 되므로, 그 분기 안에서 액션 `th` 폭을 좁은 값으로 덮어 HEAD 와 같은 줄바꿈이 실제로 나게 한다. 이 폭대의 행 높이(ⓘ)는 **같은 뷰포트의 HEAD 실측**과 비교한다. ⓔ 의 폭대별 정의는 intent 의 완료 정의 ⓔ 를 따른다(Ted 판정 대상 해석).
- **A4 고정 열 경계** — `.account-table { border-collapse: collapse }` 에서 sticky 셀의 테두리는 셀을 따라오지 않을 수 있다. 1차안은 `border-left: 1px solid var(--color-border)`. 실화면에서 경계가 따라오지 않으면 `td` 의 `::before`(absolute · 폭 1px · `background: var(--color-border)`)로 대체한다. `box-shadow`(css_audit 축)와 `border-collapse` 변경(행 높이 ⓘ 위협)은 쓰지 않는다.
- **A5 열 폭 합계 정의** — 이름·연구실에도 px 폭을 준다. 이메일 열만 `auto`. `min-width` = Σ(px 열) + 이메일 하한(실측 뒤 결정 · 기준 ≥200px). 폭은 `thead th` 에만 준다(우려 6).
- **A6 1440px 폭 예산과 대비 순서** — 예산은 1336px 이 아니라 **1334px**(카드 테두리 2px 포함 · 세로 스크롤바가 나오면 실측값). 넘칠 때 순서: ① 이름·연구실을 하한까지 줄인다(생략 부호 + `title`) ② `.account-row-note` 에 가시 하한 폭(실측값)을 주고 나머지는 생략 부호 + `title`(+ 비활성 버튼의 `title`) ③ 그래도 넘으면 수치를 보고하고 멈춘다. 글자 크기·열 수·줄바꿈·세로 패딩은 어느 단계에서도 건드리지 않는다. note 가 0px 로 줄어 화면에서 사라지는 것은 허용하지 않는다(#84 「거절의 까닭을 화면에 적는다」 · 본문 D3 의 「note 를 폭 산정에 넣지 않는다」는 이 항으로 대체).
- **A7 `--space-section` 은 640px 이하에서 20px** — ⓐ 의 24~32px 판정은 640px 초과 뷰포트에 적용한다. 390×844 는 기대값 20px 로 선언하고 보고서에 그 까닭(토큰의 좁은 화면 값)을 적는다. 리터럴 24px 로 고정하지 않는다.
- **A8 `h1` 은 `margin-block-end: 0` 만 덮는다.** `margin: 0` 은 제목 위 여백까지 지워 화면 전체가 올라간다. `h1` 의 위쪽 `get box` 를 전후 계측해 변화 0 을 보인다.
- **A9 계측 보강** — ⑴ lane 첫 단계에 픽스처 요건을 고정한다: 계정 ≥5행 · 자기 줄 · 60자 이상 이메일 · 0건 필터. ⑵ `.account-table-scroll` 을 가로로 미는 수단(agent-browser 의 요소 스크롤 명령 · 키보드 초점 + 화살표 키)을 lane 시작 시 확인하고, 없으면 `미측정 + 이유` 에 적는다. ⑶ 「눌린다」는 `get box` 로 증명되지 않는다 — 폭대별로 버튼 1개를 실제 클릭해 대화상자가 열림을 확인한다. ⑷ 「마지막 버튼의 오른쪽 끝 ≤ 액션 `td` 의 오른쪽 끝 − 12px」를 더한다(버튼이 고정 열 밖으로 넘치는 경우를 잡는다). ⑸ ⓑ(5행)는 HEAD 에서도 충족될 가능성이 높다(CSS 어림 ≈890px) — 전후 값을 둘 다 적고 수정 효과의 근거로 쓰지 않는다. ⑹ 본문의 「표 CSS 에 sticky 선례 없음」은 「**열** 고정 선례 없음」으로 읽는다(`catalog.css` 에 `.tbl thead th { position: sticky }`).
- advisor 가 확인하지 않은 것: fixed 표의 max-content 를 Chrome 이 계산하는 방식(A2 의 근거) · collapse 표에서 sticky 셀 테두리의 실제 그림(A4) · agent-browser 요소 스크롤 명령 유무 · `frontend-visual` 의 `/account-admin` 접근(로그인 필요) · 다크 `--color-surface` 대비 · 버튼·note·머리글 실제 폭.

## 우려 항목 (판정 필요)
| # | 항목 | ⓐ | ⓑ | 권고 |
|---|---|---|---|---|
| 1 | **액션 열 폭이 1440px 예산을 넘을 수 있다.** 버튼 셋(「시스템 관리자 해제」·「비밀번호 재설정」·「비활성화」)은 `padding: 10px 18px` 와 `gap: 8px` 을 포함해 한 줄이어야 하고, 자기 줄에는 note 가 더 붙는다. 1440px 뷰포트의 카드 내용 상자는 `1440 − .login padding 48 − .login-card padding 56 = 1336px` 이고, 나머지 일곱 열(「시스템 관리자」 머리글만도 상당한 폭)이 그 안에 함께 들어가야 한다. 폰트 폭을 모르면 ⓓ 달성 여부를 코드로 단정할 수 없다 **[미확인]** | 고치기 전에 버튼·note·머리글 폭을 실측해 JSON 으로 남기고, note 는 생략 부호+`title` 로 열 폭 산정에서 빼고, 남는 폭을 이메일 열에 준다. 합계가 1336px 을 넘으면 그 수를 보고하고 판정을 받는다 | 제안된 퍼센트를 그대로 넣고 넘치면 스크롤을 둔다 | ⓐ — ⓑ 는 완료 조건 ⓓ 를 만족하지 못하면서 만족한 것처럼 보인다 |
| 2 | **`row-gap` 은 같은 grid 의 모든 행에 걸린다.** 탭~카드만이 아니라 `h1`↔탭, 탭↔생성 카드, 목록 패널↔`message` 문단 간격도 함께 바뀐다 | 같은 커밋에서 `.login.account-admin > h1` 과 `> .account-status` 의 세로 마진을 0 으로 덮어 소유자를 하나로 만들고, 네 간격 전부를 전후 실측해 보고한다 | 탭~카드만 재고 나머지는 보지 않는다 | ⓐ — ⓑ 는 보이지 않는 회귀를 남긴다 |
| 3 | **`position: sticky` 는 이 레포의 표 CSS 에 선례가 없다.** 배경이 불투명하지 않거나 `z-index`·보더 처리가 빠지면 행이 비쳐 보이거나 구분선이 끊긴다. 다크 모드에서 더 드러난다 | 불투명 `--color-surface` + `border-left: 1px solid var(--color-border)` 를 명시하고, 라이트·다크 스크린샷과 스크롤 좌·우 양 끝 `get box` 로 확인한다 | 배경 없이 `sticky` 만 건다 | ⓐ |
| 4 | **이슈 첨부 화면의 실효 뷰포트가 1440px 미만이다.** 원본 1556px 안의 카드 1440px, 카드 CSS 폭 960px → DPR 1.5, 실효 폭 ≈1037 CSS px. 그 화면에서는 이번 수정 뒤에도 가로 스크롤이 남고(1440px 상한 미달), 「스크롤 없이 5행」도 범위 안 수단으로는 보장되지 않는다. 오케스트레이터가 전달한 「≈1280 CSS px」와도 어긋난다 **[미확인]** | 판정 기준을 DPR 1 · CSS px 로 못 박고, 좁은 폭의 한계를 실측 수와 함께 보고서에 적는다. 5행 미달이면 남는 수단이 범위 밖(필터 레이아웃·행 높이)임을 명시한다 | 첨부 화면 기준으로 판정한다 | ⓐ — ⓑ 는 판정 자체가 서지 않는다 |
| 5 | **카드를 넓히면 `h1`·탭 줄과 카드의 가로 정렬이 어긋나 보인다.** 공용 `.login { place-items: center }` 의 `justify-items: center` 가 살아 있어 `h1`·`.settabs` 는 줄어든 폭으로 가운데에 서고, 카드만 1600px 까지 넓어진다 | 이번 범위에서는 손대지 않고 전후 스크린샷으로 드러낸다(탭 버튼 스타일·필터 레이아웃은 이슈 비범위) | 같은 커밋에서 `justify-items: start` 로 바꾼다 | ⓐ — ⓑ 는 비범위를 침범하고 로그인 화면과 같은 규칙에 손대는 유혹을 만든다 |
| 6 | **`table-layout: fixed` 는 열 폭을 첫 행에서만 읽는다.** `th` 에 폭을 주지 않고 `td` 에 주면 무시되어 시험은 green 인데 화면은 안 바뀐다 | 폭은 `thead` 의 `th` 에만 준다. CSS 원문 시험이 그 선택자를 단언하고, 실화면 `get box` 로 각 열 폭을 확인한다 | `td` 선택자에 준다 | ⓐ |
| 7 | **`.account-row-note` 생략 부호는 이유 문면을 화면에서 줄인다.** 문면 자체는 DOM·`title` 에 남지만 읽는 사람에게는 잘려 보일 수 있다 | 액션 열 폭을 note 가 대개 온전히 들어갈 만큼 잡되(실측 뒤 결정), 넘치면 생략 부호 + `title`. 실화면에서 잘리는지 확인해 보고한다 | note 를 지우거나 숨긴다 | ⓐ — ⓑ 는 #84 가 세운 「거절의 까닭을 화면에 적는다」를 되돌린다 |
| 8 | **HEAD 의 탭~카드 간격이 38px 인지 실측되지 않았다.** 코드 산술값이며, 100px 대가 나오면 원인 판정이 달라진다 **[미확인]** | 레인이 고치기 전에 HEAD 를 먼저 재어 전 값을 JSON 으로 남긴다. 38px 대가 아니면 멈추고 보고한다 | 코드 산술값을 전 값으로 적는다 | ⓐ |

## 범위 밖
- 카드 내부 디자인, 탭 버튼 스타일, 필터 영역 레이아웃(이슈 비범위).
- 열 추가, 정렬·페이지네이션(이슈 비범위).
- 공용 `.login` · `.login-card` · `.settabs`(`members.css`) · `.table-scroll-hint`(`design-system.css`) 기본 규칙 변경. 1280px 분기 신설.
- 본문 글자 축소, 열 숨김·삭제, 행 높이 변경(이슈 금지 조건).
- 이슈 첨부 화면을 만든 환경의 재배포·버전 확인.
- 다른 이슈, 커밋·push·PR 게시·배포·이슈 댓글·종결.

## 산출 계획
- 예상 레인 수: **1 (직렬).** CSS 1파일·TSX 1파일을 같이 만진다. 쓰기 주체 하나.
- 커밋 3개(intent+spec / 수정 / 증거), PR 1건(`Closes #121`). PR 본문은 task runtime 에 두고 저장소에 커밋하지 않는다.
- 보고서 `dev-package/reports/issue-121/` — `README.md`(`dev-package/reports/issue-120/README.md` 형식: `## 전` · `## 후` 에 ⓐ~ⓘ 별 `###` · `## 원한 결과 대조` · `## 미측정 + 이유` · `## 조건` · `## 게이트 — gate-summary.json` · `## 후속으로 올리는 것`), `images/`(라이트·다크·뷰포트별 전후), 계측 JSON(간격·표 폭·버튼 상자·행 높이·긴 이메일·0건 상태), 게이트 요약 사본.

## 미확인 (이 spec 작성 중 확인하지 못한 것)
- `.agents/rules/product.md` §3·§5 원문을 열지 않았다. 정책 대조는 변경 범위에서 도출한 것이다.
- HEAD 의 탭~카드 실측 간격(코드 산술 38px), `h1` 의 실제 마진, 5행 세로 예산, 버튼·note·머리글의 실제 폭. 전부 실브라우저 `get box` 로만 확정된다.
- 이슈 첨부 화면의 실효 뷰포트(≈1037 CSS px 추정 vs 전달받은 ≈1280 CSS px) 와 캡처 방식(뷰포트/전체 페이지).
- 다크 모드에서 고정 열 배경 위 본문 대비 실측값.
- `.agents/skills/apple-design/SKILL.md` 본문을 열어 읽지 않았다. 인터랙션 하한은 `design-review §0` 표 항목과 `--control-height` 토큰에 근거한다.
