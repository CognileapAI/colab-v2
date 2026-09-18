# Intent: 계정 관리 화면 — 탭·목록 사이 여백을 컨테이너가 소유하고, 계정 목록 표의 액션 열을 잘리지 않게 한다
메타 — 발의자: [미확인] (이슈 #121 작성자 확인 안 함) · 방향 결정: Ted · 작성 2026-09-18 · 승인: Ted 지시 "121 번 이슈처리하자"(2026-09-18) · 개별 판단의 명시 승인 없음 — `## 확인` 참조

## 문제
- 계정 관리 화면(`/account-admin` · `frontend/src/routes/AccountAdminPage.tsx`)의 탭 줄(`div.settabs`) 아래와 계정 목록 카드(`section.login-card.account-list-card`) 위 사이에 보이는 내용 없는 빈 띠가 있다. 이슈 첨부 화면에서 그 띠는 약 117 CSS px 이고, 탭 줄 **위**에도 같은 크기의 띠가 있다(아래 [미확인] 참조).
- 같은 화면의 계정 목록 표가 카드 폭을 넘어 가로 스크롤을 만들고, 오른쪽 끝 액션 열(`td.account-row-actions`)이 잘린 채 그려진다. 이슈 첨부 화면에서 직접 보인다.
- 여백 쪽 원인 후보 — 이슈 첨부 화면의 문면이 「관리자 등록」·「관리자 지정/해제」다. 현재 코드는 같은 자리를 「사용자 생성」·「시스템 관리자 지정/해제」로 낸다(`315fb85f`, #84, 2026-09-17). 그 커밋 **이전** 빌드에는 `.login.account-admin { min-height: auto; align-items: start; }`(`frontend/src/auth/login.css`)가 없고, 공용 `.login { min-height: 100dvh; display: grid; place-items: center; }` 의 행 늘림이 위·아래 같은 크기의 띠를 만든다. 첨부의 「위·아래 같은 크기」 모양이 이 규칙과 일치한다. **이는 첨부 화면과 코드를 맞춰 본 추론이며 브라우저 계측이 아니다.**
- 여백 쪽 현 HEAD 의 실제 값 — `.settabs { margin-bottom: 14px }`(`frontend/src/components/members/members.css`) + `.account-list-card { margin-top: 24px }` = **38px**. 두 요소가 grid 항목이라 마진 상쇄가 없다. 약 200px 은 아니지만 이슈의 완료 조건 24~32px 을 6px 초과하므로 HEAD 에도 고칠 자리가 남아 있다.
- 표 쪽 원인 — ⑴ `.account-list-card { max-width: 960px }` 가 뷰포트보다 훨씬 작은 상한이다. `.login-card { padding: 32px 28px }` 를 물려받아 내용 상자는 904px 이다. ⑵ `.account-table th, .account-table td { white-space: nowrap }` 가 여덟 열 전부의 최소 폭을 부풀린다. 액션 셀 하나가 버튼 셋(「시스템 관리자 지정」/「시스템 관리자 해제」·「비밀번호 재설정」·「비활성화」/「재활성화」)을 `display: flex` 로 한 줄에 담고, 자기 줄에는 `span.account-row-note`(`자기 계정은 비활성화할 수 없어요`)가 더 붙는다. ⑶ `table-layout` 이 어디에도 없어 기본 `auto` 다 — 긴 이메일 하나가 모든 열의 폭을 바꾼다. ⑷ `.account-table`·`.account-table-scroll` 에 `min-width` 는 없다(이슈가 의심한 항목 ①은 원인이 아니다).

## 원한 결과 (proposed outcome)
- 탭 줄 아래와 계정 목록 카드 위 사이 간격이 **24~32px** 이고, 그 간격을 **컨테이너 한 곳이 소유**한다(형제 마진 두 개가 더해지는 꼴을 버린다).
- 계정 0건 상태에서도 같은 간격이다. 계정 0건 상태는 표 뒤에 `p.account-status`(`조건에 맞는 계정이 없어요.`)가 카드 **안**에 더 붙을 뿐 탭~카드 사이 DOM 은 같다.
- 뷰포트 가로 1440px 이상에서 계정 목록 표의 여덟 열 전부가 가로 스크롤 없이 보인다.
- 액션 열의 버튼 셋은 **어떤 뷰포트에서도 전체가 보이고 클릭 가능**하다. 1440px 미만에서 가로 스크롤은 허용하되, 액션 열은 스크롤 위치와 무관하게 보이는 영역 안에 남는다.
- 이메일이 길어져도 표 전체 폭과 각 열의 폭이 변하지 않는다. 잘린 값은 `title` 속성으로 전체를 읽을 수 있다.
- 본문 글자 크기, 열 구성(여덟 열), 행 높이는 그대로다.

## 완료 정의 (항목별 검증)
이슈의 완료 조건 6개 + 금지 조건 3개에 1:1 대응한다. 전부 실브라우저 계측으로 판정한다.
- ⓐ 탭 줄 하단과 카드 상단 간격이 24~32px(640px 초과 뷰포트 · 640px 이하는 `--space-section` 의 좁은 화면 값 20px 이 기대값) — `div.settabs` 와 `section.account-list-card` 의 `get box` 로 `card.top − tabs.bottom` 을 잰다(사용자 목록 탭, 계정 ≥1건, 1920×1080).
- ⓑ 1920×1080 에서 스크롤 없이 탭 + 필터(`.account-filters`) + 목록 5행이 보인다 — 5번째 `tbody tr` 의 `get box` 하단이 1080 이하임을 잰다.
- ⓒ 계정 0건 상태에서도 ⓐ 와 같은 간격 — 필터를 0건이 되게 맞춘 상태에서 ⓐ 를 다시 잰다(두 값의 차 0px).
- ⓓ 1440px 이상에서 가로 스크롤 없음 — 1920×1080 과 1440×900 에서 `.account-table-scroll` 의 `scrollWidth ≤ clientWidth`(또는 표 상자 폭 ≤ 래퍼 상자 폭)를 잰다.
- ⓔ 액션 버튼 전체 노출·클릭 가능 — **폭대별 정의(advisor ① 반영 · Ted 판정 대상).** 1024px 이상(1920×1080 · 1440×900 · 1280×800 · 1024×768): 가로 스크롤 위치와 무관하게 버튼 셋 각각의 `get box` 가 `.account-table-scroll` 의 보이는 상자 안에 완전히 들어가고, 마지막 버튼의 오른쪽 끝이 액션 셀 안쪽 패딩 안에 있다. 1024px 미만(390×844): 오른쪽 끝까지 민 상태에서 같은 포함 관계가 성립한다. 각 폭대에서 버튼 1개를 실제로 눌러 대화상자가 열림을 확인한다.
- ⓕ 긴 이메일이 표 폭을 바꾸지 않음 — 60자 이상 이메일 픽스처 유·무 두 상태에서 표와 각 열의 `get box` 폭이 같음을 잰다.
- ⓖ 본문 글자 크기 축소 없음 — `.account-table`(`var(--text-body-sm)` = 14px)·`.account-row-note`(`var(--text-caption)` = 13px) 선언이 그대로임을 CSS 원문 시험으로 잠그고, `frontend-visual` 이 실화면 computed font-size ≥ 13px 을 잰다.
- ⓗ 열 숨김·삭제 없음 — `frontend/test/account-admin.test.tsx` 의 `test('운영자가 전 연구실 계정 목록을 일곱 열로 본다', …)` 가 green 이고, 실화면에서 `th` 8개(레이블 7 + `aria-label="행 동작"`)가 모두 상자를 가진다.
- ⓘ 행 높이 변경 없음 — 같은 계정 데이터로 수정 **전(HEAD)** 과 **후** 에 같은 행의 `get box` 높이를 재어 값이 같음을 보인다. 자기 줄(note 가 붙는 줄)과 보통 줄 둘 다 잰다.

## 영향 범위
- 사용자 / 화면: 계정 관리 화면 하나(`/account-admin`). 탭~카드 간격, 카드 폭, 표의 열 폭 규칙, 액션 열의 고정.
- 파일: `frontend/src/auth/login.css`(`.login.account-admin`·`.account-list-card`·`.account-table*`·`.account-row-*` 만), `frontend/src/routes/AccountAdminPage.tsx`(자유 문자열 셀에 `title` 속성 추가), `frontend/test/account-admin.test.tsx` 및 신설 CSS 원문 시험.
- 서비스 · 스키마 · 계약: 프런트만. API·DB·마이그레이션 변경 없음.
- 계약 파괴 여부: 아니오.

## 제약
- 공용 규칙을 직접 고치지 않는다 — `.login` · `.login-card` · `.settabs` 기본 규칙. `.login`/`.login-card` 는 로그인 화면(`frontend/src/auth/LoginPage.tsx`)·비밀번호 변경 화면(`frontend/src/auth/PasswordChangePage.tsx`)과 공유하고, `.settabs` 는 연구실 설정 두 탭 화면과 공유한다. `login.css` 자체의 주석이 그 교훈을 남긴다: `공용 .login 을 직접 고치면 로그인 화면과 비밀번호 변경 화면이 함께 깨진다`.
- 폭 상한은 `.account-list-card` 에만 올린다. `.login-card { max-width: 360px }` 는 건드리지 않는다.
- 여백은 컨테이너가 소유한다(`.agents/skills/design-review/SKILL.md §0`). `.login.account-admin` 에 `row-gap` 성격의 소유자 하나를 두고 `.account-list-card { margin-top: 24px }` 를 없앤다. 형제 마진을 더 만들지 않는다.
- 토큰은 `frontend/src/shell/tokens.css` 의 것만 쓴다. 미정의 토큰 0. `--space-section` 은 640px 이하에서 20px 으로 내려가므로(토큰 파일 `@media (max-width: 640px)` 블록), 24~32px 판정이 걸리는 넓은 폭에서는 24px 이다.
- 액션 열 폭은 실제 버튼 문면에서 도출한다. 이슈 제안의 10% 같은 반올림 값을 쓰지 않는다 — 10% 는 버튼 셋을 담지 못하고, 담으려면 줄바꿈이 필요한데 줄바꿈은 행 높이를 바꿔 금지 조건에 걸린다.
- 스크롤 래퍼를 유지한다 — `div.account-table-scroll[role="region"][tabIndex={0}]` 과 `p.table-scroll-hint`. `frontend/test/account-admin.test.tsx` 의 `test('계정 목록 표에 좌우 이동 안내와 키보드 초점을 받는 래퍼가 있다', …)` 가 이 둘을 단언한다.
- 공용 `.table-scroll-hint` 의 1100px 분기(`frontend/src/shell/design-system.css`)를 바꾸지 않는다. 이 클래스는 `CatalogTable`·`ProjectTable`·`ProjectDatasetTable` 과 공유한다. 이슈 제안의 1280px 분기를 새로 만들면 1100~1280px 구간에서 표는 스크롤되는데 안내는 숨는 어긋남이 생긴다.
- `.account-admin` 수식 클래스는 최상위 `div` 에만 붙는다. `frontend/test/account-admin.test.tsx` 의 `test('#84 계정 관리 화면 최상위에만 세로 배치 수식 클래스가 붙는다', …)` 와 `test('#84 로그인·비밀번호 변경 화면에는 그 수식 클래스가 붙지 않는다', …)` 가 이를 잠근다.
- jsdom 은 배치를 계산하지 않는다. 두 결함 모두 단위 시험으로 증명되지 않는다 — CSS 원문 시험(레포 관행: `frontend/test/css-residual-rc11.test.ts`)과 실브라우저 계측이 함께 있어야 한다. 수정 **전** 값도 같은 방법으로 먼저 잰다.
- 이 이슈 1건 = intent 1건 = spec 1건 = PR 1건. PR 게시는 사용자가 한다.

## 설계트리
- Q1 첨부 화면의 약 200px 을 HEAD 에서 재현할 것인가 → A 아니다. HEAD 의 코드상 값은 38px 이고, 200px 대의 띠는 `315fb85f` 이전 빌드의 `.login { min-height: 100dvh; place-items: center }` 로 설명된다(추론). 레인은 **HEAD 를 먼저 실브라우저로 재어 전 값을 남기고**, 그 값이 38px 대이면 24~32px 로 줄이는 것이 이번 수정이다. 100px 대가 나오면 그때 원인을 다시 판정한다.
- Q2 여백 소유자를 어디에 둘 것인가 → A `.login.account-admin` 한 곳. `.settabs` 의 `margin-bottom` 은 공용이라 못 건드리고, 카드 `margin-top` 은 컨테이너 소유 원칙에 어긋난다. 컨테이너에 gap 을 두고 카드 마진을 없애면 소유자가 하나가 된다.
- Q3 카드 폭 상한을 `.login-card` 에서 올릴 것인가 → A 아니다. `.account-list-card` 에서만 올린다. 이미 이 파일이 960px 을 그렇게 얹고 있다.
- Q4 열 폭을 이슈 제안의 퍼센트로 줄 것인가 → A 아니다. `table-layout: fixed` 는 채택하되, 액션 열은 버튼 셋 + 자기 줄 note 의 실제 폭에서 도출한다. 나머지 자유 문자열 열(이메일·이름·연구실)은 생략 부호로 처리한다.
- Q5 액션 열을 `position: sticky; right: 0` 으로 고정할 것인가 → A 예. 1440px 미만에서는 가로 스크롤이 남는데, 그 상태에서도 「어떤 뷰포트에서도 전체가 보이고 클릭 가능」을 지키는 수단이 이것뿐이다. 이 레포의 표 CSS 에 **열** 고정 선례는 없으므로(`catalog.css` 의 `.tbl thead th` 머리글 고정만 있다) 1024px 이상에서만 걸고 불투명 토큰 배경을 명시해 행이 비쳐 보이지 않게 한다.
- Q6 가로 스크롤 임계를 1280px 으로 할 것인가 → A 아니다. 이슈의 완료 조건은 「1440px 이상에서 스크롤 없음」이다. 1280px 은 제안문에만 있는 수이며, 공용 `.table-scroll-hint` 의 1100px 과 어긋난다. 1440px 이상 무스크롤을 판정 기준으로 삼고 그 아래는 허용한다.
- Q7 「1920×1080 에서 5행」을 첨부 화면 기준으로 판정할 것인가 → A 아니다. 첨부는 DPR 1 이 아니다(아래 [미확인]). 판정은 `agent-browser` 뷰포트 = CSS px, DPR 1 기준 1920×1080 으로 한다.

## 미해결 질문
- 첨부 화면의 실효 뷰포트 폭. 원본 이미지 폭 1556px, 그 안의 카드 폭 1440px, 카드 CSS 폭 960px(`.account-list-card { max-width: 960px }`) → DPR 1.5, 실효 뷰포트 폭 **≈1037 CSS px**(1556 ÷ 1.5). 오케스트레이터가 전달한 「≈1280 CSS px」와 맞지 않는다. 또 이미지 세로가 1080 을 넘는 값이면 **뷰포트 캡처가 아니라 전체 페이지 캡처**다. **[미확인]** — 어느 쪽이든 「1920×1080 에서 5행」 판정에는 쓰지 않는다.
- 1920×1080 에서 5행이 실제로 들어가는지. 세로 예산은 `.login { padding: 24px }` + `h1` + `.settabs`(36px) + 새 gap + `.login-card { padding: 32px 28px }` + `.account-filters` + `.account-table-scroll { margin-top: 16px }` + `thead` + 행 5개이며, 행 높이는 `td { padding: 10px 12px }` + 버튼 높이(`.btn` 규칙 미확인)에 달렸다. **[미확인]** — 계측으로만 확정된다. 미달하면 남는 수단은 범위 밖(필터 레이아웃·행 높이)이므로 그 사실을 보고서에 남긴다.
- 실효 뷰포트가 1037~1280 CSS px 인 화면(첨부 화면 같은 경우)에서는 1440px 상한 미달이라 가로 스크롤이 남고, 5행 조건도 이번 범위 안 수단으로는 보장되지 않는다. 이 한계를 보고서에 수로 적는다.

## 범위 밖 (명시 제외)
- 카드 내부 디자인, 탭 버튼 스타일, 필터 영역 레이아웃(이슈 비범위).
- 열 추가, 정렬·페이지네이션(이슈 비범위).
- 공용 `.login`·`.login-card`·`.settabs`·`.table-scroll-hint` 규칙 변경.
- 첨부 화면을 만든 환경의 재배포·버전 확인.
- 본문 글자 축소, 열 숨김·삭제, 행 높이 변경(이슈 금지 조건).
- 다른 이슈, 커밋·push·PR 게시·배포·이슈 댓글·종결.

## 확인
- Ted 지시 문장(원문 그대로): "121 번 이슈처리하자"
- 개별 판단에 대한 Ted 의 명시 승인 문장은 **없다.** 아래 「수용한 판단」은 오케스트레이터가 이슈 본문·코드·advisor ① 판정에서 정한 가정이며, PR 검토에서 Ted 가 판정한다. 승인으로 세지 않는다.
- **Ted 판정이 필요한 해석 1건** — 이슈의 「액션 버튼은 어떤 뷰포트에서도 전체가 보이고 클릭 가능」을 폭대별로 나눠 정의했다(ⓔ). 1024px 이상은 스크롤 위치와 무관하게 노출, 1024px 미만은 오른쪽 끝까지 민 상태에서 노출. 까닭: 액션 열(버튼 셋, 추정 400px 대)이 좁은 스크롤 영역보다 넓어, 고정하면 왼쪽 버튼이 영구히 가려지고 나머지 일곱 열이 보이지 않는다.
- 수용한 판단(오케스트레이터 지시): ⑴ 이슈의 완료·금지·비범위가 구속력이며 「그대로 보낼 프롬프트」의 목표 상태는 제안일 뿐이다 ⑵ 여백 소유자는 컨테이너 하나 ⑶ 폭 상한은 `.account-list-card` 에만 ⑷ 액션 열 폭은 실제 문면에서 도출 ⑸ 액션 열 `position: sticky` ⑹ 1440px 기준 유지, 1280px 분기 신설 없음.
- 재개봉 금지: 예. 위 여섯 항목을 다시 묻지 않는다. 다만 계측 결과가 이와 어긋나면 그 값을 보고서에 남긴다.

## 참조
- 이슈: https://github.com/CognileapAI/colab-v2/issues/121
- 코드: `frontend/src/routes/AccountAdminPage.tsx`(`<div className="login account-admin">` · `<div className="settabs" role="tablist" aria-label="계정 관리 탭">` · `<section className="login-card account-list-card" data-testid="account-list">` · `<div className="account-table-scroll" role="region" …>` · `<td className="account-row-actions">` · `SELF_STATUS_REASON`), `frontend/src/auth/login.css`(`.login` · `.login-card` · `.login.account-admin` · `.account-list-card` · `.account-table` · `.account-row-actions` · `.account-row-note`), `frontend/src/shell/tokens.css`, `frontend/src/shell/design-system.css`(`.table-scroll-hint`), `frontend/src/components/members/members.css`(`.settabs`)
- 시험: `frontend/test/account-admin.test.tsx`, `frontend/test/css-residual-rc11.test.ts`(CSS 원문 시험 관행)
- 선례: `dev-package/intent/2026-09-17-issue-84-account-create-form.md`(같은 화면 · `.login.account-admin` 을 도입한 결정), `dev-package/intent/2026-09-18-issue-120-preview-map-viewport.md`(형식), `dev-package/reports/issue-120/`(증거 형식)
- 결정: 신규 legacy 결정번호 발급 없음.
