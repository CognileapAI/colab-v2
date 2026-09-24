# Spec: design-review 20260924 fix — Ted 판정 21건 반영
출처 intent: `dev-package/intent/2026-09-25-design-fix-20260924.md`(Ted 판정·값 확정 2026-09-25).
판정표: `dev-package/sessions/design-review-20260924.md`(커밋 f07b7378 · §7 「Ted 판정 결과」 · §8 WU-A1–A4 · §9).
기준 트리: 브랜치 `worktree-design-review-apple-20260924` HEAD(레인 지시문이 SHA 를 명시 · advisor ① 반영 커밋 이후)(develop `7acd0fce` ＋ audit 커밋 5건). 레인 워크트리는 **이 HEAD 에서** 딴다(main 아님).
값: 열린 값 17건은 `values-to-confirm.md` 번호(값 n)로 가리킨다. **2026-09-25 Ted 확정 — 아래 「확정 값」 절.**

## 문제 진술
- 누름 피드백 `:active` 가 전체 2건이다(§2 #1). 기본·보조 단추 hover 가 없다(⑦-1).
- 다크 대비 미달 3건 — `.chip--off` 1.66:1 · `.de-req` 1.28:1 · `.btn-strong:hover` 1.05/1.10:1.
- 업로드 모달·달력 팝오버·미리보기 끌기·드롭 영역의 움직임이 입력을 따르지 않는다(#10 · #12 · #13 · #21–#24).
- 자간 리터럴 산재 · `--text-*` px · `.btn-sm` 정의 0 · 「불일치」 12px · 계정 관리 모달 층 120 · 계보 주석 불일치.

## 해법 개요
- 파일 면이 겹치지 않는 3레인(L1 CSS 공통·화면 · L2 업로드 · L3 미리보기 제스처) · PR 1.
- 레인마다 시험 작성 단계(RED) → `COLAB_FIX_LANE=1` 구현 단계(GREEN). 기존 시험·게이트 픽스처의 수정은 시험 작성 단계에서만 한다.
- 새 hex 0 — 값은 모두 기존 토큰 값이다. 새 토큰 이름은 3개(`--tracking-heading` · `--tracking-label` · `--color-on-text-body` — 이름은 값 8 · 13 확정에 따름).
- #13 · #15 는 코드 대신 합격선 예외로 정본에 적는다. #6 · #18 · #20 은 변경 없이 닫고 #21 은 다음 회차로 넘긴다.

## 1. 범위 표

| # | 판정 | 변경 | 파일(`frontend/src/` 기준) | 종류 | 레인 | 값 |
|---|---|---|---|---|---|---|
| WU-A1 | 즉시 후보 | plain · ghost · secondary 단추 `:active` 추가. `.btn-primary:active` 불변 | `shell/primitives.css` | CSS | L1 | 14 |
| 9 | ⓐ | `.btn-primary:hover` = primary-700 · `.btn-secondary` 를 hover 제외 목록(`:28`)에서 뺌 · `:27` 주석 갱신 | `shell/primitives.css` | CSS | L1 | 10 |
| 12 | ⓐ | `.btn-sm` 정의(＋ 640px 이하 높이 하한) | `shell/primitives.css` | CSS | L1 | 11 |
| 11 | ⓑ | `.chip` 배경 `#eef2f7` → 기존 토큰 · `:46` 주석 갱신 · 게이트 f 면제 줄 삭제 | `shell/primitives.css` · `gates/fixtures/frontend-design-lint/same-in-dark.txt:12` | CSS ＋ 게이트 목록 | L1 | 12 |
| 13 | ⓐ | 코드 값 무변. `.gnb`(`shell/shell.css:114`) · `.modal`(`primitives.css:122`) 에 「합격선 예외 #13」 주석 · 정본 예외 기록(§6) | `shell/shell.css` · `shell/primitives.css` · 문서 | 주석 · 문서 | L1 | — |
| 14 | ⓐ | `.account-modal-back` z-index 120 → 200 | `auth/login.css:187` | CSS | L1 | — |
| 7 | ⓐ | 자간 토큰 2개 신설 · 음수 8곳 · 양수 7곳 리터럴 치환(3＋1곳 값 변경) | `shell/tokens.css` · `shell/shell.css:123,430` · `components/search/search.css:7` · `dashboard/dashboard.css:206` · `project/project.css:31,362` · `detail/detail.css:15,64,96,130,143,164` · `members/members.css:20` · `catalog/catalog.css:66` · `lineage/lineageGraph.css:79` · (`auth/login.css:29` 는 값 9) | CSS | L1 | 8 · 9 |
| 8 | ⓐ | `--text-*` 6개 px → rem | `shell/tokens.css:89`–`94` | CSS | L1 | — |
| 17 | ⓐ | 「색 배경 위 글자」 토큰 신설(라이트·다크) · `.de-req` 글자색 치환 | `shell/tokens.css` · `components/detail/detail.css:166` | CSS | L1 | 13 |
| 15 | ⓐ | 코드 값 무변(9px 유지). `catalog.css:48` 에 「장식 글리프 · 합격선 예외 #15」 주석 · 정본 예외 기록(§6) | `components/catalog/catalog.css` · 문서 | 주석 · 문서 | L1 | — |
| 16 | ⓐ | `.lvl-mismatch` 12px → `var(--text-caption)` | `components/catalog/catalog.css:138` | CSS | L1 | — |
| 19 | ⓐ | 안내 줄 주석을 렌더(`--color-warning-600` · 흰 면 5.34:1)에 맞춤 | `components/lineage/lineage.css:165` | 주석 | L1 | — |
| WU-A2 | 즉시 후보(값 선행) | 셸 대화형 10종 `:active` | `shell/shell.css` | CSS | L1 | 15 |
| WU-A3 | 즉시 후보(값 선행) | `.tbl tr.clk:active td` | `components/catalog/catalog.css` | CSS | L1 | 16 |
| 1 | ⓐ | `@keyframes up-rise` → `transition` ＋ `@starting-style` · 닫기 상태 `data-state="closing"` · 전환이 끝난 뒤 언마운트(전환 시간 0 이면 즉시) · 닫는 중 다시 열기(값 2) | `components/upload/upload.css:18`–`32` · `upload/UploadModal.tsx` · (값 2 = 제안이면) `upload/UploadEntry.tsx:92` · `upload/GridAttachEntry.tsx:53` | TSX ＋ CSS | L2 | 1 · 2 |
| 2 | ⓐ | `.dr-pop` 기준점 ＋ 여는 전환(`@starting-style`) · 640px 이하 바닥 기준 | `components/upload/upload.css:484` · `:656` | CSS | L2 | 3 |
| 4 | ⓐ | 드롭 영역 끌어 들어옴·나감 상태(`is-dragover`) ＋ 시각 규칙 | `components/upload/FileDropCard.tsx:167`–`188` · `upload/upload.css:94` · `:564` | TSX ＋ CSS | L2 | 7 |
| 10 | ⓑ | `.btn-strong:hover` gray-50 → primary-700 · `:310` 주석 갱신 | `components/upload/upload.css:311` | CSS | L2 | — |
| WU-A4 | 즉시 후보(값 선행) | `.btn-strong` · `.dr-nav button` · `.dr-cal-d` · `.dr-useg button` · `.dr-field` `:active` | `components/upload/upload.css` | CSS | L2 | 17 |
| 3 | ⓐ | 마우스 이벤트 → 포인터 이벤트 ＋ `setPointerCapture` ＋ 시작 임계 · 끌기 성립 뒤 click 버림 · 공개 인터페이스 `onMouseDown` → `onPointerDown` | `components/preview/useZoomPan.ts:100` · `:175` · `:334`–`358` · `preview/PreviewPanels.tsx:314` · `preview/PreviewOverlay.tsx:51` · `upload/PreviewPanel.tsx:619` · `:780` | TSX | L3 | 4 |
| 5 | ⓐ(권고와 다름) | 이동 기록으로 놓을 때 속도 계산 → 관성 목표(투영 · `clampView`) → 임계 감쇠 스프링으로 인계 · 중단 · 동작 줄이기 분기 | `components/preview/useZoomPan.ts` · 신설 `preview/spring.ts`(값 5 = 제안) 또는 `frontend/package.json` ＋ `package-lock.json`(값 5 = 대안) | TSX(＋ 의존성) | L3(2단계) | 5 · 6 |

- 판정표 §8 의 「#1 은 전체 계수 행이라 WU-A1–A4 가 모두 닫는다」를 따른다 — #1–#3 · #5–#7 은 위 WU 행으로 닫힌다.
- `.btn-strong` 은 `.btn` 이지만 화면(screens) 층 규칙이라 WU-A1 의 프리미티브 `:active` 보다 WU-A4 의 화면 규칙이 이긴다(층 순서 · `docs/design-system.md` ①).

## 2. 범위 밖 · 변경 없이 닫힘

| # | 판정 | 처리 | 기록 자리 |
|---|---|---|---|
| 6 | ⓑ | 코드 0. `shell/shell.css:419`–`420` 전역 reduced-motion 규칙 유지. `prefers-contrast` 분기 없음(#20) | `docs/design-system.md` ⑦ 닫힘 표 없음(⑦ 항목 아님) → 이 spec 과 레인 보고서 「하지 않은 것」 |
| 18 | ⓑ | 코드 0. `.inp[readonly]` · `.lin .chip--warning` · `.login-input:focus-visible` · `.pcard` 초점 간격 — 오늘 렌더 유지 | `docs/design-system.md` ⑦-2 닫힘 |
| 20 | ⓑ | 코드 0. `.dl-keep` 투명 유지 | `docs/design-system.md` ⑦-7 닫힘 |
| 21 | ⓐ | 코드 0. 다음 회차 `routes/**` 담당 레인에 재판정 배정(`pd-closedbar` · `pd-linkempty` · D15 `NotFoundPage.tsx:12` · 실화면 D23 과 함께) | 레인 보고서 L1 「하지 않은 것」 ＋ 다음 design-review 회차 §0 이월 입력(`design-review/SKILL.md` §0 「이월·판정 대기」 행이 읽는 자리) |
| 13 | ⓐ | 규칙 예외 — 카드 그림자 0 합격선은 카드·대화상자에만 걸고, 상단 고정바 `.gnb` 와 전체화면 모달 `.modal.modal-takeover` 는 「항상 떠 있는 층」으로 제외 | (1) `.agents/skills/design-review/SKILL.md` §0 「정적 합격선」 칸의 「카드 그림자 0(팝오버 허용)」 → 「카드 그림자 0(팝오버 · 상단 고정바 `.gnb` · 전체화면 모달 `.modal-takeover` 허용 — design-review 20260924 #13)」 (2) `docs/design-system.md` ⑤ 「게이트 밖 항목」 3번째 줄에 같은 문구 (3) 코드 주석 2곳(§1). **게이트 목록 변경 없음** — 그림자를 재는 게이트가 없다(`css_audit.py` 열거만 · `.agents/skills/design-review/scripts/css_audit.py:8`) |
| 15 | ⓐ | 규칙 예외 — 13px 합격선에서 장식 글리프(가상 요소 `content` 화살표·점)를 뺀다 | (1) 같은 §0 칸 「글자 13px 이상」 → 「글자 13px 이상(장식 글리프 `::before`/`::after` 는 제외 — #15)」 (2) `docs/design-system.md` ⑤ 같은 줄 (3) `catalog.css:48` 주석. **`gates/fixtures/frontend-visual/allow.txt` 에 넣지 않는다** — `live_probe.js` 는 텍스트 노드만 재서(`.agents/skills/design-review/scripts/live_probe.js:31`–`32`) 가상 요소 글리프는 애초에 세지 않는다. 넣으면 `th` 의 실제 글자까지 접힌다 |

- 판정표 밖 잔여(이번에 고치지 않음 · 기록만): #13 을 적용하면 `.modal` 을 쓰되 `.modal--dialog` 가 아닌 가운데 대화상자 — `UploadModal.tsx:1751` 닫기 확인(`.confirm-back .modal`)과 `.modal.pvx`(`PreviewExpandOverlay.tsx:40`) — 가 `--shadow-sm` 을 가진 채 남는다. 다음 회차 재판정 후보로 L1 보고서에 적는다.
- `PreviewExpandOverlay` 는 열기·닫기 모두 즉시라 대칭이다 — #1 대상 아님(#13 행의 두 번째 파일).
- 그 밖: ⑦-10–16 · 러버밴드(apple §9) · 스크림(§12) · 소리·햅틱(§13) · px 글자 리터럴 194건 · `R-DESIGN-CONSISTENCY-FULL-20260912.md:39`–`46` 전체 장면 검증 체크 항목(이 spec 은 그 라운드의 「pointer-down 피드백」 제약 중 지목 선택자만 이행한다 · 라운드 체크박스를 닫지 않는다).

## 3. 레인 · 순서

### 파일 면 (겹침 0)

| 레인 | 이름 | 소유 파일(이 레인만 쓴다) | 종류 | 항목 |
|---|---|---|---|---|
| L1 | CSS 공통·화면 | `frontend/src/shell/{tokens,primitives,shell}.css` · `frontend/src/components/{catalog/catalog,detail/detail,members/members,search/search,dashboard/dashboard,project/project,lineage/lineage,lineage/lineageGraph}.css` · `frontend/src/auth/login.css` · `docs/design-system.md` · `.agents/skills/design-review/SKILL.md` · `gates/fixtures/frontend-design-lint/same-in-dark.txt` · `frontend/test/design-fix-20260924-L1.test.ts` · `dev-package/sessions/design-fix-20260924-L1.md` | CSS 전용(＋ 문서 · 게이트 목록 1줄) | WU-A1 · WU-A2 · WU-A3 · 7 · 8 · 9 · 11 · 12 · 13 · 14 · 15 · 16 · 17 · 19 |
| L2 | 업로드 | `frontend/src/components/upload/upload.css` · `upload/UploadModal.tsx` · `upload/UploadEntry.tsx` · `upload/GridAttachEntry.tsx` · `upload/FileDropCard.tsx` · `frontend/test/design-fix-20260924-L2.test.tsx` · `dev-package/sessions/design-fix-20260924-L2.md` | TSX ＋ CSS | 1 · 2 · 4 · 10 · WU-A4 |
| L3 | 미리보기 제스처 | `frontend/src/components/preview/{useZoomPan.ts,PreviewPanels.tsx,PreviewOverlay.tsx}` · 신설 `preview/spring.ts` · `frontend/src/components/upload/PreviewPanel.tsx` · (값 5 = 대안이면) `frontend/package.json` · `frontend/package-lock.json` · `frontend/test/design-fix-20260924-L3.test.tsx` · 기존 끌기 시험 5파일(아래) · `dev-package/sessions/design-fix-20260924-L3.md` | TSX | 3 → 5 |

- L2 는 TSX 레인이다. `design-review/SKILL.md` §3 은 TSX 항목을 CSS 레인에 섞지 말라고 한다 — L2 는 CSS 레인이 아니라 `upload.css` 까지 소유한 TSX 레인이다. #1 · #4 가 같은 파일(`upload.css`)의 CSS 와 TSX 를 함께 요구하고, 판정표 §8 「집행 순서」가 WU-A4 를 #1 · #2 · #10 과 한 레인으로 합치라고 적었다.
- L3 의 `upload/PreviewPanel.tsx` 는 `upload/` 폴더에 있지만 L2 소유 목록에 없다 — 파일 단위로 겹침 0.
- `docs/design-system.md` 는 L1 만 쓴다. L2 의 #10 결과(편차 목록 `.btn-strong:hover`)도 L1 이 판정 값(primary-700)으로 적는다. 한 PR 로 묶이므로 중간 불일치는 브랜치 안에만 있다.
- L3 가 고치는 기존 시험 5파일(시험 작성 단계에서만): `frontend/test/dataset-preview-zoom-latency.test.tsx:137` · `dataset-preview-tiles.test.tsx:197,400` · `preview-map-viewport-20260918.test.tsx:322,335,466` · `dataset-preview-zoom.test.tsx`(2곳) · `rev1-keep-regression.test.tsx:136` — 마우스 이벤트 끌기 9곳을 포인터 이벤트로 옮긴다. 단언 값은 바꾸지 않는다.

- 감시(수정 없이 green 확인): `prd39-rev2-build-20260906.test.tsx:497,512`(뷰포트 `mouseMove` = 커서 HUD · 끌기 아님 · L3) · `prd34-close-copy-20260907.test.tsx:352`(모달 배경 mouseDown · L2 #1 회귀) (advisor ① F7).

### 순서 · 의존

1. 값 17건 Ted 확정.
2. advisor ① — fan-out 전 계획 검토.
3-0. 레인 워크트리 준비 — `frontend/` 에서 `npm ci` · capture.py 브라우저 확인. 준비 실패는 78(준비)로 보고하고 진행하지 않는다(advisor ① F2).
3. 기준 캡처 1회 — `frontend/` 에서 visual:capture 를 라벨 `fix0924-base` 로(HEAD(레인 지시문이 SHA 를 명시 · advisor ① 반영 커밋 이후)).
4. L1 · L2 · L3a(#3) 구현 — 격리 워크트리 3개, 동시 가능. 각자 시험 작성(RED) → 구현(GREEN).
5. L3b(#5) — L3a GREEN 뒤 같은 레인에서.
6. 레인 게이트 — 한 번에 한 레인씩(아래).
7. 합치기 L1 → L2 → L3 → 통합 게이트 1회 → 캡처 대조(`fix0924-base` 대 합친 결과) → advisor ③ → PR 1(게시는 사용자).

의존 그림(글):

- 값 확정 → advisor ① → 기준 캡처 → { L1 ‖ L2 ‖ (L3a → L3b) } → 합치기(L1 → L2 → L3) → 통합 게이트 → 캡처 대조 → advisor ③ → PR.

- 게이트 실행은 **호스트에서 한 번에 한 레인**이다 — `frontend-test` 는 serial(`gates/config/parallelism.toml:148`–`156`)이고 호스트 뮤텍스(`gates/run.sh:170`)가 잡는다. 레인 게이트를 겹쳐 돌리면 판정이 오염된다. 판정은 `-j 1` 로 재현한 값만 쓴다.
- #5 는 #3 뒤다(같은 파일 `useZoomPan.ts` · 판정 문구 「3 이 선행 조건」). 같은 레인 안에서 커밋 2개로 나눈다. 값 5 · 6 이 확정되지 않으면 L3 는 #3 만 내고 #5 는 후속으로 남긴다(레인 보고서 「하지 않은 것」).
- 합치기 순서 L1 → L2 → L3: L1 이 토큰(rem · 자간 · 새 색)과 프리미티브를 바꿔 모든 화면의 기준이 바뀐다. L2 · L3 는 L1 위로 올린 뒤 통합 게이트에서 다시 잰다.
- 레인 수 3 이 최소다: `upload.css` 는 #1 · #2 · #4 · #10 · WU-A4 가, `useZoomPan.ts` 는 #3 · #5 가, `tokens.css` 는 #7 · #8 · #17 이 함께 쓰고 #7 이 화면 CSS 8파일을 따라간다 — 세 묶음은 파일을 나누지 않는다. 더 합치면 L2 · L3 의 TSX 가 L1 CSS 레인에 섞인다(§3 금지).
- lifecycle: 레인마다 `lifecycle begin` 으로 task 를 열고 산출물(레인 보고서 · 소유 파일)을 선언한다. 같은 워크트리 병렬 레인의 handoff 충돌(판정표 §10)은 격리 워크트리로 피한다.

## 4. 수용 기준 (시험 단언 형태)

시험 파일 = `frontend/test/design-fix-20260924-L1.test.ts` · `-L2.test.tsx` · `-L3.test.tsx`. CSS 단언은 선례 `frontend/test/design-fix-20260908.test.ts` 처럼 원문에서 주석을 걷고 선택자 블록을 잘라 잰다(jsdom 은 스타일을 계산하지 않는다). 대비 단언은 같은 선례의 WCAG 휘도 계산을 쓰고, 라이트 값은 `:root` 블록 · 다크 값은 `:root[data-theme="dark"]` 블록에서 읽는다. 「값 n」 자리에는 확정값을 넣는다.

### L1

| # | 단언 |
|---|---|
| WU-A1 | `primitives.css` 에 `.btn:where(:not(.btn-primary)):active` 블록이 있고 `background: var(<값 14>)` · `.btn-primary:active` 블록 원문 = `background: var(--color-primary-700);`(불변) · `primitives.css` 에 `!important` 0 |
| 9 | `.btn-primary:hover` 블록에 `var(--color-primary-700)` · hover 제외 목록 안에 `.btn-secondary` 0 · `--color-on-primary` 대 primary-700 대비 두 테마 ≥ 4.5 |
| 12 | `.btn-sm` 블록 = 값 11 의 네 선언 · 640px 이하 분기 안 `.btn-sm` 에 `min-height: var(--control-height)` |
| 11 | `.chip` 블록 `background: var(<값 12>)` · `primitives.css` 에 `#eef2f7` 0 · `same-in-dark.txt` 에 `.chip` 의 `f` 줄 0 · `--color-text-muted` 대 값 12 배경 두 테마 ≥ 4.5 · `--color-text` 대 같은 배경 두 테마 ≥ 4.5(`.chip--closed` · `.chip--info` · `.chip--success` 상속 글자) |
| 13 | 회귀 고정 — `.gnb` 와 `.modal` 의 `box-shadow: var(--shadow-sm)` · `.modal--dialog` 의 `box-shadow: none` 원문 불변 |
| 14 | `login.css` `.account-modal-back` 블록 `z-index: 200` = `primitives.css` `.modal-back` 의 z-index |
| 7 | `tokens.css` 에 값 8 의 두 토큰 · `frontend/src` 아래 CSS(tokens.css 제외)의 모든 `letter-spacing` 값이 `var(--tracking-heading)` · `var(--tracking-label)` · `var(--tracking-body)` · `0` · `normal` · `inherit` 중 하나(값 9 가 남기면 `.login-brand` 1곳 예외) · heading 참조 8 · label 참조 7 |
| 8 | `tokens.css` 의 `--text-h2` 1.75rem · `--text-h3` 1.125rem · `--text-section` 1rem · `--text-body` 0.9375rem · `--text-body-sm` 0.875rem · `--text-caption` 0.8125rem · px 로 끝나는 `--text-*` 0 |
| 17 | 라이트 · 다크 블록 모두 값 13 이름 정의 · `detail.css` `.de-req` 블록 `color: var(<값 13 이름>)` · 그 글자 대 `--color-text-body`(라이트는 `#21272ae0` 를 흰 면에 합성) 대비 두 테마 ≥ 4.5 |
| 15 | 회귀 고정 — `.tbl thead th > .thf::before` 의 `font-size: 9px` 불변(예외 · 고치지 않음) |
| 16 | `.lvl-mismatch` 블록 `font-size: var(--text-caption)` · `catalog.css` 에 `font-size: 12px` 0 |
| 19 | `lineage.css` **주석 포함 원문**에 `#5b6472` 0 · 안내 줄 주석에 `--color-warning-600` |
| WU-A2 | `shell.css` 10개 선택자(`.backlink` 문맥 · `.mainnav a` · `.gnb-settings` · `.gnb-upload` · `.gnb-more` · `.gnb-more-item` · `.gnb-logout` · `.loadfail-retry` · `.theme-switcher` · 모달 닫기 `.x` 문맥) 각각에 `:active` 블록과 선언 1개 이상(값 15) · reduced-motion 블록 원문 불변 · 기존 `:hover` 블록 원문 불변 |
| WU-A3 | `.tbl tr.clk:active td` 블록 `background: var(<값 16>)` · `.tbl tr.clk td` transition 원문 불변 |
| 문서 | `design-docs.mjs --check` 종료 0 — 게이트 `frontend-design-lint` h 가 잰다(시험에서 다시 부르지 않는다) |

### L2

- #1 추가 단언: `UploadModal.tsx` 안 `props.onClose` 직접 호출 0 — `useWorkProtection.discard` 등 모든 닫기 경로가 닫기 요청 함수 하나(closing → transitionend/타이머 → onClose)만 부른다(advisor ① F6).

| # | 단언 |
|---|---|
| 1 CSS | `upload.css` 에 `@keyframes up-rise` 0 · `animation: up-rise` 0 · `.modal.modal-takeover` 블록에 transform · opacity `transition`(값 1) · `@starting-style` 안 같은 선택자에 시작 모양(값 1) · `[data-state="closing"]` 규칙에 같은 끝 모양 · (값 2 = 제안) 닫는 중 배경 `pointer-events: none` |
| 1 동작 | RTL. 계산된 전환 시간을 0.3s 로 스텁한 경우: × 누름 → `upload-modal` 이 남고 `data-state="closing"` · `transitionend` 뒤 언마운트(`onClose` 1회) · `transitionend` 가 없어도 가짜 타이머로 전환 시간 ＋ 50ms 뒤 언마운트 · 여는 도중 닫기 → 곧바로 `closing`. 전환 시간이 0(jsdom 기본 · 전역 reduced-motion 규칙)이면 × 누름과 같은 틱에 언마운트 — 기존 닫기 시험(`prd34-close-copy-20260907` · `register-steps-20260907`)이 수정 없이 green. (값 2 = 제안) 닫는 중 업로드 단추 → `closing` 해제 · 입력값 유지 · `onClose` 0회 · 완전히 닫힌 뒤 다시 열면 ① 단계(PRD-13) |
| 2 | `.dr-pop` 블록에 `transform-origin`(값 3) · opacity · transform 전환 `var(--ease)` · `@starting-style` 안 `.dr-pop` 시작 모양 · 640px 이하 분기 안 `.dr-pop` `transform-origin: bottom center` |
| 4 | RTL. 드롭 영역(`up-drop`)에 dragEnter → `is-dragover` 부여 · 자식 요소의 dragEnter/dragLeave 짝이 와도 유지 · 바깥 dragLeave 로 해제 · drop 뒤 해제 · dragOver 는 여전히 `preventDefault` ＋ `stopPropagation`(두 번 접수 방지 · `FileDropCard.tsx:170`–`172` 주석) · CSS `.dropzone.is-dragover` 와 `.up-empty .dropzone.is-dragover` 블록에 값 7 두 선언 |
| 10 | `.btn-strong:hover` 블록 `background: var(--color-primary-700)` · `--color-on-primary` 대 primary-700 두 테마 ≥ 4.5 |
| WU-A4 | `.btn-strong` · `.dr-nav button` · `.dr-cal-d` · `.dr-useg button` · `.dr-field` 각각 `:active` 블록(값 17) |

### L3

- #3: `setPointerCapture` 는 optional-call(`?.`)로 부른다 — jsdom 29.1.1 은 PointerEvent 는 있고 capture 는 없다. 기존 5파일은 스텁 없이 green 이어야 한다(advisor ① F5).

| # | 단언 |
|---|---|
| 3 | RTL(상세 미리보기 · 업로드 미리보기 둘 다). pointerDown(pointerId 1 · 300,300 · button 0) → pointerMove 305 → 변환 불변 → pointerMove 311 → 이동량 = 누른 자리 기준 11px · `setPointerCapture(1)` 호출(jsdom 에 없으면 시험이 스텁) · pointerType touch · pen 도 같다 · 끌기가 성립한 뒤의 click 은 값 조회를 부르지 않고 임계 안의 click 은 부른다 · `useZoomPan.ts` 와 호출부 3곳에 `onMouseDown` 0 · 확대 도구 줄(`PreviewOverlay`) 위 pointerDown 은 뷰포트로 새지 않는다(`preview-map-viewport-20260918.test.tsx:466` 이관분) · 기존 5파일 단언 값 불변 |
| 5 | 단위 — 스프링 함수(값 5): t=0 위치 = 시작 · 속도 = 놓은 속도 · damping 1.0 에서 목표를 넘지 않는다 · response(값 6)의 정해진 배수 안에 0.5px 안으로 선다. 동작 — 가짜 rAF 로 끌기 → 놓기 → 놓은 뒤에도 같은 방향으로 이어지다 `clampView(투영 목표)` 에 선다 · 관성 중 pointerDown → 그 프레임 값에서 멈춤(튀지 않음) · 휠 · 확대 단추 · 더블클릭도 멈춤 · reduced-motion 매체 질의가 참이면 관성 0 · `dataset-preview-zoom-latency` 의 「끌기 중 렌더 재요청 0」 유지. (값 5 = 대안) `package.json` 에 `motion` 고정 버전 1개 · 다른 의존성 증감 0 |

### 실화면 증거 (agent-browser · 판정은 사람) — **통합 단계에서 1회**(advisor ① F3)

- 레인은 vitest ＋ §5 게이트만 돈다. 아래 표의 「레인」 칸은 증거를 요구한 출처 표시이며, 실제 측정은 합치기(L1 → L2 → L3) 뒤 audit 빌드 1회에서 오케스트레이터가 한다 — 레인 트리는 다른 레인의 토큰 변경이 없어 출하 화면이 아니다.

- 도구 = `.agents/skills/agent-browser/SKILL.md` ＋ `.agents/skills/design-review/scripts/live_audit.sh`. 산출 = `dev-package/reports/design-review/20260924/fix/live/`(스크린샷 커밋).
- 대상 = 로컬 스택이 있으면 그 화면. 없으면 audit 빌드(`frontend/` 의 audit:build → audit:preview 포트 4187 · `/audit-design.html?design=full&scene=<장면>`). audit 장면은 픽스처 화면이라고 보고서에 적는다. staging · dev 에 쓰지 않는다.

| 항목 | 증거 | 레인 |
|---|---|---|
| 1 | 업로드 모달 열기 0.3초 안에 × → 연속 스크린샷(되돌아감) · 닫기 전환 · reduced-motion 에뮬레이션에서 즉시 | L2 |
| 2 | 기간 칸 누름 → 첫 프레임 스크린샷(칸 쪽에서 커짐) · 375px 바닥 시트 | L2 |
| 4 | 파일 끌어 오기 중 스크린샷. agent-browser 가 OS 파일 끌기를 만들 수 없으면(읽기 전용 eval 규칙상 합성 이벤트 주입도 불가) **미실행으로 적고** vitest 증거 ＋ Ted 수동 확인으로 넘긴다 — 성공으로 보고하지 않는다 | L2 |
| 3 · 5 | 확대 뒤 drag 6px(움직임 없음) · 20px(따라옴) · 빠르게 끌고 놓기 → 연속 스크린샷(미끄러짐 · 경계에서 멈춤) · 터치 에뮬레이션은 도구 지원 여부를 먼저 확인 | L3 |
| 9 · 10 · 12 · WU-A1–A4 | hover · 누름 상태 스크린샷(도구가 누른 채 멈춤을 지원할 때) · `live_probe.js` activeRules 가 기준값 2 보다 크다 · `.btn-sm` computed 높이 1440px 에서 29px · 375px 에서 44px | L1 · L2 |
| 11 · 17 | 다크 멤버 · 업로드 · 상세 편집 화면 lowContrast 0 · `.chip--off` · `.de-req` computed 색쌍 | L1 |
| 14 | 계정 관리 모달을 연 상태 스크린샷(GNB 위) | L1 |
| 7 · 8 | 제목 3곳 computed letter-spacing · `--text-h2` 요소 computed 28px(기본 글자 16px) | L1 |

## 5. 게이트 (레인별)

- `audit:preview`(포트 4187)는 한 번에 하나만 띄우고, 레인 게이트가 끝나면 종료한다(advisor ① F3).

실행 = 저장소 루트에서 `bash gates/run.sh <게이트>` 를 하나씩, `gate-runner` 로 3계수(green · red(판정) · red(준비 78))를 회수한다. 레인 사이 · 게이트 사이 모두 순차. 병렬 실행 결과는 판정에 쓰지 않는다.

| 게이트 | L1 | L2 | L3 | 통합(합친 뒤) | 비고 |
|---|---|---|---|---|---|
| `frontend-typecheck` | ○ | ○ | ○ | ○ | `design-review/SKILL.md` §3 필수 |
| `frontend-test` | ○ | ○ | ○ | ○ | 필수 · serial |
| `frontend-fixture-reach` | ○ | ○ | ○ | ○ | 필수 |
| `frontend-design-lint` | ○ | ○ | ○ | ○ | CSS · 토큰 · 목록이 바뀐다(a · c · e · f · h). L3 는 CSS 무변이어도 TSX 인라인 style(g)을 잰다 |
| `frontend-design-lint-selftest` | ○ | — | — | ○ | L1 이 게이트 목록 파일 `same-in-dark.txt` 를 바꾼다 |
| `frontend-visual` | ○ URL 선언 | ○ URL 선언 | ○ URL 선언 | ○ URL 선언 | `COLAB_VISUAL_URLS` 선언 필수. CSS 가 바뀌므로 `COLAB_VISUAL_EXEMPT=1` 금지. 대상 없으면 red(준비 78)를 그대로 보고한다 |
| production build(`frontend/` 의 build) | — | — | ○(값 5 = 대안이면 필수) | ○ | 새 의존성 · rem 전환 확인 |

- `COLAB_VISUAL_URLS`(audit 빌드 · 포트 4187 · 모두 `/audit-design.html?design=full&scene=` 뒤에 장면 이름):
  - L1 = primitives · catalog · detail · members · settings · projects · project-detail · login · account-admin · lineage-picker · search · gnb-more
  - L2 = upload · upload-classify · upload-metadata · upload-link
  - L3 = preview · detail
  - 통합 = 위 합집합
  - 장면 이름은 `frontend/scripts/visual-baseline/scenes.json`(34장면)에 있는 것만 쓴다. 다크는 `live_audit.sh` 가 테마를 바꾸는 방식이 audit 장면에 먹는지 첫 실행에서 확인하고, 안 먹으면 `&theme=dark` URL 을 따로 선언한다.
- selftest 규칙: 새 시험이 `frontend/src` · `frontend/test` 밖의 파일을 읽거나 import 하면(예 `gates/fixtures/frontend-design-lint/same-in-dark.txt` · `frontend/scripts/*.mjs`) 그 파일을 소유한 게이트의 selftest 를 레인 게이트에 더한다. L1 시험은 `same-in-dark.txt` 를 읽으므로 `frontend-design-lint-selftest` 가 필수다.
- 게이트 밖 증거(판정 아님 · advisor ③ 입력): 캡처 대조 — `frontend/` 에서 visual:capture 를 레인 라벨(`fix0924-L1` 등)로 찍고 visual:diff 로 `fix0924-base` 와 대조한다. 차이는 0 이 아니다(시각 변경 회차). 레인 보고서에 「바뀐 장면 → 원인 항목 #」 표를 적고, 원인 없는 차이가 있으면 멈춘다.
- 레인 완료 = 위 게이트 green ＋ 레인 보고서 `dev-package/sessions/design-fix-20260924-L<n>.md`(before → after 표 · 수용 기준 · 「하지 않은 것」 · 부수 간격 변화 · 실화면 증거 경로 · 미실행 항목).

## 6. `docs/design-system.md` 갱신 (L1)

- ② · ③ 생성 표: `tokens.css` · `primitives.css` · `same-in-dark.txt` 를 바꾼 뒤 `node frontend/scripts/design-docs.mjs` 로 다시 쓴다(손으로 고치지 않는다 · 게이트 h). 예상 변화 — ③ btn 행 `.btn-sm` 「정의 없음」 → 규칙 수 · `.btn-primary` 규칙 2 → 3 · `.btn` 규칙에 `:active` 추가 · 색 리터럴 면제 1 → 0 · 입력 sha256 4개 갱신.
- ② 손글(표지 밖): 「`--color-on-text-body` 는 한 화면(상세 편집)만 쓰지만 다크 값이 필요해 정본에 둔다 — 화면 범위에서는 다크 값을 줄 수 없다(d) · 정본 계열 이름은 화면 범위 금지(a)」 한 줄. 자간 두 토큰의 쓰임(제목 · 작은 라벨) 한 줄.
- ③ 손글 표 btn 행: `.btn-sm`(아래 표의 「정의 없음」 참고) → `.btn-sm`(작은 단추 · 640px 이하에서는 `--control-height`).
- ③ 화면 편차 목록 btn 행: `upload.css` `.btn-strong:hover { background: gray-50 }` → `primary-700`(#10).
- ⑤ 게이트 밖 항목 3번째 줄: 「카드 그림자 0」에 상단 고정바 · 전체화면 모달 예외(#13), 「글자 13px 이상」에 장식 글리프 예외(#15)를 적고, 「누름 피드백 = hover 의 한 단 진한 값(`:active`)」 한 줄을 더한다.
- ⑦ 시각 값: 1–9 행을 표에서 빼고 새 소절 「닫힘 — design-review 20260924」 표(항목 · 판정 · 처리 · 레인)로 옮긴다.

| ⑦ | 판정표 묶음 | 판정 | 처리 |
|---|---|---|---|
| 1 억눌린 hover | 9 | ⓐ | primary-700 · secondary gray-50(값 10) · L1 |
| 2 억눌린 상태 4종 | 18 | ⓑ | 그대로 · 코드 0 |
| 3 `.btn-sm` | 12 | ⓐ | 작은 단추 정의(값 11) · L1 |
| 4 `.chip--off` 배경 | 11 | ⓑ | `.chip` 배경을 기존 토큰으로(값 12) — 6 과 함께 닫힘 · L1 |
| 5 `.btn-strong:hover` | 10 | ⓑ | primary-700 · L2 |
| 6 `.chip` `#eef2f7` | 11 | ⓑ | 기존 토큰 · 게이트 f 면제 0 · L1 |
| 7 `.dl-keep` 바탕 | 20 | ⓑ | 그대로 · 코드 0 |
| 8 계보 안내 줄 주석 | 19 | ⓐ | 주석을 렌더에 맞춤 · L1 |
| 9 `.de-req` 다크 | 17 | ⓐ | 새 뜻 토큰(값 13) · L1 |

- ⑦ 10 · 11–16 은 그대로 남는다.
- 정본 스킬: `.agents/skills/design-review/SKILL.md` §0 「정적 합격선」 칸 두 곳(#13 · #15 · §2 표의 문구). 프론트매터 · 다른 절은 건드리지 않는다.

## 7. 위험

| # | 위험 | 대응 |
|---|---|---|
| 1 | **한꺼번에 넓은 시각 변경** — #8 rem(`font-size: var(` 133곳 · 판정표 #31 재계수 — 대부분 `--text-*`) · #12 `.btn-sm`(60회 · 40 → 29px) · #7 제목 3곳 · #11 라이트 칩 배경이 한 PR 에 모인다. 캡처 대조 차이가 크고 advisor ③ 판단 부담이 크다. 브라우저 기본 글자를 키우면 px 고정 높이 상자(`.btn` 32/40px · `.chip` 24px · `.dr-cal-d` 32px)가 잘릴 수 있다 | 레인 보고서의 「바뀐 장면 → 원인 #」 표 · 3폭 × 2테마 · 원인 없는 차이면 멈춤. 큰 글자 설정 확인은 도구가 기본 글자 크기를 못 바꾸면 [미상]으로 적는다 |
| 2 | **#3 포인터 이관이 기존 시험을 깬다** — 5파일 · 끌기 9곳이 마우스 이벤트다. 구현 단계는 시험을 못 고친다(`test-file-guard`). jsdom 의 PointerEvent · `setPointerCapture` 지원이 모자라면 좌표가 빠진 이벤트가 온다. 끌기 뒤 click(값 조회)을 버리는 것은 동작 변경이다 | 시험 작성 단계에서 5파일을 먼저 옮기고 RED 를 확인한다 · 스텁 필요 여부를 그 단계에서 판정 · click 버림은 수용 기준에 명시 |
| 3 | **#1 지연 언마운트** — PRD-13 리셋이 언마운트에 기대고(`UploadModal.tsx:352`–`362`), 전역 reduced-motion 규칙(`transition: none !important`)에서는 `transitionend` 가 오지 않는다. Esc 층(`upload/escLayer.ts`) · 포커스 복귀 · 배경 누름 확인 흐름이 「닫는 중」 상태를 모른다 | 계산된 전환 시간이 0 이면 즉시 언마운트 · 아니면 `transitionend` ＋ 시간 초과 대비 타이머 · 닫는 중에는 Esc · 배경 누름을 다시 받지 않는다 · 기존 닫기 시험 green 을 수용 기준에 둠 |
| 4 | #5 수단이 판정 문구(「라이브러리」)와 권고(직접 구현)로 갈린다. 관성 중 매 프레임 `setView` 가 타일 · 렌더 재요청을 부를 수 있다 | 값 5 명시 확정 · 관성 종료 뒤 한 번만 재요청되는지 L3 시험으로 잰다 |
| 5 | #11 은 판정 행(`.chip--off`) 밖의 `.chip--closed` · `.chip--info` · `.chip--success` 모양도 바꾼다(오늘 다크 1.00:1 까지 → 해소). 값 12 = gray-100 이면 라이트에서 칩 테두리가 바탕과 같아진다 | advisor ③ 에 영향 목록으로 올린다 · 캡처 대조에 세 칩이 나오는 장면(projects · project-detail · upload-link)을 넣는다 |
| 6 | 게이트 목록 `same-in-dark.txt` 는 `gates/` 라 구현 단계에서 못 고친다. 안 고치면 `.chip` 리터럴이 사라진 순간 게이트 c/f 가 「면제 목록 구멍(낡음)」 red | L1 시험 작성 단계에서 그 줄을 지운다(그 시점 RED 가 기대값) |
| 7 | `frontend-visual` 대상 서버 — 로컬 스택이 꺼져 있으면 audit 빌드에 기대는데, 픽스처 화면이라 실제 데이터 상태(D23 류)는 못 본다 | 픽스처라고 보고서에 적는다 · 실데이터 확인은 §9 목록으로 남긴다 |
| 8 | #13 을 적용하면 가운데 대화상자 2종(`.confirm-back .modal` · `.modal.pvx`)이 그림자를 가진 채 남는다(판정표 행 밖) | 고치지 않고 L1 보고서 · 다음 회차 이월 입력에 적는다 |
| 9 | L1 이 14항목 · 약 16파일로 크다 — 레인 턴 한도에서 잘릴 수 있다 | 레인 보고서 골격을 먼저 쓰고 항목마다 채운다 · 잘리면 남은 항목만 좁혀 재개 |
| 10 | 레인 워크트리 기준 브랜치 — 기본 `fresh` 는 main 기준이다 | 스폰 전에 기준을 레인 지시문의 SHA(이 브랜치 HEAD · advisor ① 반영 spec 포함)로 확인한다 |

## 정책 대조

- 계약 · 스키마 · 서비스 · 데이터 변경 없음. 계약 동결 해제 필요: 아니오.
- 새 토큰 이름 · 값은 Ted 확정 뒤에만(`design-review/SKILL.md` §4). 판정표에 지목되지 않은 자리는 고치지 않는다.
- PR 게시 · 병합 · 결정 번호 발급은 이 spec 이 주지 않는다. PR 본문은 저장소 밖에 둔다.

## 산출 계획

- intent `dev-package/intent/2026-09-25-design-fix-20260924.md` · spec `dev-package/prd/specs/S-DESIGN-FIX-20260924.md`(이 초안) · 레인 보고서 3 · 시험 3 · 실화면 증거 폴더 1 · PR 1.
- 라운드 파일은 만들지 않는다(레인 3 · PR 1 의 한 회차 · 선례 흐름 intent → spec → advisor ①② → 레인 → PR).

## 확정 값 (Ted · 2026-09-25)

- 값 5 = **직접 구현**(`components/preview/spring.ts` · 새 의존성 0). 판정 #5 ⓐ 문구 「라이브러리를 들여」와 다르며 Ted 가 명시 확정했다(질문 「무엇으로 만들까요?」 → 「직접 구현」). 동작(스프링 ＋ 속도 인계)은 판정 ⓐ 그대로.
- 값 11 = **29px**(v2 목업값 · 640px 이하 44px 하한 유지).
- 값 12 = **`--color-gray-100`**(제안값 · Ted 「권고대로」). 라이트에서 칩 테두리(`--color-border` #e8ecf2)와 바탕이 같아지는 문제는 값 18 로 해소.
- 값 1–4 · 6–10 · 13–17 = **제안값 그대로**(Ted 「전부 제안대로」).
- 값 18(신규 · advisor ① F4 · Ted 「테두리 진하게」 2026-09-25) = `.chip` `border-color: var(--color-border-strong)`(기존 토큰 · L #dfe3e8 · D #45566a). 칩 윤곽 대비 L 1.09:1(오늘 #eef2f7 대 #e8ecf2 = 1.05:1 보다 뚜렷) · D 1.61:1. L1 · `primitives.css`. 수용 단언: `.chip` 블록 `border-color: var(--color-border-strong)`.
- 착수 조건 충족: 값 17건 확정. 남은 것은 advisor ① 뿐.

## 부록 — 값 목록(확정 전 제안 원문)


- 입력: `dev-package/sessions/design-review-20260924.md` §7 「Ted 판정 결과」 · §8 WU-A1–A4.
- 형식: 번호 · 제안값 · 근거(path:line 또는 정본 §) · 대안 1개. 대비는 WCAG 상대휘도(L = 라이트 · D = 다크).
- 새 hex 는 만들지 않았다. 모든 제안은 기존 토큰 값이다.
- 경로는 `frontend/src/` 기준. 목업 = `40 COLAB-기획/00_기획원본/Co-Lab_ver2_1차마일스톤_목업패키지_260818_이태헌/mockups/제품_260817.html`(v2 · `tokens.css:2` 가 가리키는 값 정본). v1 목업 `01 CoLAB-Plan/design/` 은 참고만.

## 모달·팝오버 전환 (#1 · #2)

**1. #1-가 업로드 모달 열기·닫기 전환**
- 제안: `@keyframes up-rise` 를 없애고 `transition: transform 0.3s cubic-bezier(0.2, 0, 0, 1), opacity 0.3s cubic-bezier(0.2, 0, 0, 1)` 로 바꾼다. 시작·끝 모양 = `translateY(3%)` · `opacity: 0`. 열기는 `@starting-style`, 닫기는 `data-state="closing"`. 열기·닫기 같은 길·같은 시간.
- 근거: apple §3(keyframes 는 중간에 되돌릴 수 없고 transition 은 현재 값에서 되돌아간다) · §4 표 Drawer/sheet response 0.3 · §4 「메뉴처럼 스스로 나타나는 것은 튕김 없이」 · §7 같은 길 · 현행 `components/upload/upload.css:24`–`28`(0.46s ease · 시작 opacity 0.4).
- 대안: 시간·곡선·시작값은 현행 그대로(0.46s ease · opacity 0.4 → 1)이고 방식만 transition 으로 바꾼다.

**2. #1-나 닫는 도중 다시 열기**
- 제안: 닫는 동안 배경은 누름을 통과시킨다(`pointer-events: none`). 그 사이 업로드 단추를 다시 누르면 닫기를 되돌려 같은 창으로 돌아온다(입력 상태 유지). 완전히 닫힌 뒤 다시 열면 지금처럼 ① 단계부터다(PRD-13 · `components/upload/UploadModal.tsx:352`–`362`). 부모 두 곳(`UploadEntry.tsx:92` · `GridAttachEntry.tsx:53`)이 「열림」과 「그려 둠」 두 상태를 든다.
- 근거: apple §3 「전환 중 입력을 막지 않는다」 · 「닫히는 모달을 다시 잡으면 되돌아온다」.
- 대안: 닫는 0.3초 동안 배경이 입력을 막고 되돌리기는 없다. TSX 는 `UploadModal.tsx` 하나만 바뀌고 부모는 그대로다.

**3. #2 달력 팝오버 여는 전환**
- 제안: `.dr-pop { transform-origin: top left; transition: opacity var(--ease), transform var(--ease); }` ＋ `@starting-style { opacity: 0; transform: scale(0.96); }`. 640px 이하 바닥 시트(`upload.css:656`)는 `transform-origin: bottom center`. 닫기는 지금처럼 즉시(판정 문구가 「여는 전환」만 말한다 · TSX 0).
- 근거: apple §7 기준점 · `--ease` 0.14s 재사용(`shell/tokens.css:118`) · 팝오버 자리 `upload.css:484`(칸 아래 6px · 왼쪽 정렬).
- 대안: 크기 변화 없이 투명도만(0 → 1 · 0.14s).

## 끌기 (#3 · #5)

**4. #3 끌기 시작 임계**
- 제안: 10px. 넘기 전에는 그림이 움직이지 않고, 넘는 순간 누른 자리 기준으로 따라붙어 그 뒤 1:1. 끌기가 성립하면 뒤이은 click(값 조회 · `components/preview/PreviewPanels.tsx:274`)은 버린다.
- 근거: apple §10 「약 10px」 · §2 잡은 자리 유지.
- 대안: 마우스 4px · 터치·펜 10px(`pointerType` 로 나눈다).

**5. #5 탄성 움직임 구현 수단 (권고와 다른 판정)**
- 제안(권고): 새 의존성 없이 직접 구현. 임계 감쇠(damping 1.0) 스프링의 닫힌 식 `x(t) = 목표 + (x0 + (v0 + ω·x0)·t)·e^(−ω·t)`(ω = 2π / response · x0 = 목표까지 남은 거리) · X·Y 를 따로 · `requestAnimationFrame`. 순수 함수 약 30줄(`components/preview/spring.ts` 신설). 번들 증가 1KB 미만 · 의존성 0 · vitest 에서 시간값으로 바로 잰다.
- 근거: colab-ponytail 순서(재사용 → 표준 → 플랫폼 → 최소 구현 → 의존성) · 적용 면이 확대·이동 1곳 · apple §3(X·Y 분리) · §4 · §5. `frontend/package.json` 에 motion·스프링 계열 의존성 0.
- 대안: `motion@13.4.3`(MIT · npm 최신 확인). `spring` 생성기만 쓰면 min 4.3KB · gzip 1.9KB, `animate()` 를 쓰면 min 55KB · gzip 20KB(esbuild 실측). 나중에 튕김(damping < 1)을 쓸 계획이면 이쪽이 쉽다.
- ⚠ Ted 판정 ⓐ 문구는 「라이브러리를 들여」다. 제안(직접 구현)을 고르면 문구와 달라지므로 명시 확정이 필요하다. 동작(스프링 ＋ 속도 인계)은 두 안이 같다.

**6. #5-나 스프링·관성 값**
- 제안: damping 1.0 · response 0.4s · 놓을 때 속도 = 마지막 100ms 이동 기록의 평균 · 목표 = 현재 위치 ＋ (v / 1000)·0.998 / (1 − 0.998) 을 `clampView` 로 자른 자리 · 새로 누르기·휠·확대 단추·더블클릭이 오면 즉시 멈추고 그 자리에서 이어받는다 · 「동작 줄이기」 켜짐이면 관성 없이 놓은 자리에 선다.
- 근거: apple §4 표(Move/reposition · 1.0 · 0.4) · §6 투영식 · §3 중단 · §14.
- 대안: 감속률 0.99(덜 미끄러진다).

## 드롭 (#4)

**7. #4 파일을 끌어 오는 동안의 드롭 영역**
- 제안: `.dropzone.is-dragover { border-color: var(--color-primary-600); background: var(--color-primary-50); }`(점선 유지). `.up-empty .dropzone`(바탕 surface-alt · `upload.css:564`) 위에서도 이기도록 같은 특이도로 한 줄 더 둔다. 분석 장면(`upload.css:605` 테두리 0)은 그대로.
  - 대비: 큰 글자 L 16.44 · D 10.51 · 보조 글자 L 6.11 · D 6.33 · 테두리(글자 아님 · 3:1 기준) L 4.49 · D 6.41.
- 근거: 같은 화면의 강조 선례 `.dr-field[aria-expanded="true"]` 테두리 primary-600(`upload.css:467`) · apple §1.
- 대안: 목업 `.dropzone:hover` 값(테두리 gray-400 · 바탕 surface-hover · 목업 :611) — 약한 반응.

## 글자 (#7)

**8. #7 자간 토큰 이름·값**
- 제안: `--tracking-heading: -0.02em` · `--tracking-label: 0.05em`(`tokens.css:97` `--tracking-body` 옆).
  - 음수 8곳 → heading. 값이 바뀌는 곳 3: `components/project/project.css:31`(31px · −0.03em) · `components/detail/detail.css:15`(28px · −0.03em) · `components/members/members.css:20`(28px · −0.023em). 나머지 5곳은 이미 −0.02em(`search.css:7` · `dashboard.css:206` · `project.css:362` · `shell/shell.css:123` · `shell.css:430`).
  - 양수 소형 라벨 7곳 → label. 바뀌는 곳 1: `components/catalog/catalog.css:66`(0.04em). 나머지 6곳 0.05em(`detail.css:64,96,130,143,164` · `lineage/lineageGraph.css:79`).
  - `0` · `normal` · `inherit` 리터럴은 그대로(본문 0 = `--tracking-body` 와 같은 값).
- 근거: grep 실측(−0.02em 5 · −0.03em 2 · −0.023em 1 · 0.05em 6 · 0.04em 1 · 0.01em 1) · apple §15(크기별 자간).
- 대안: 목업 이름·값으로 크기별 토큰(`--tracking-h2: -0.023em` 등 · 목업 :107–112).

**9. #7-나 `.login-brand` 0.01em(`auth/login.css:29`)**
- 제안: 로고 글자라 두 구간 밖으로 두고 리터럴 유지 ＋ 「브랜드 예외」 주석. `.brand`(`shell.css:123` · 17px −0.02em)는 heading 토큰으로 바꾼다(값 같음).
- 대안: label 토큰(0.05em)으로 바꾼다(시각 변경).

## 버튼 (#9 · #12)

**10. #9 `.btn-secondary` hover**
- 제안: `shell/primitives.css:28` 제외 목록에서 `.btn-secondary` 를 빼서 기본 `.btn` hover(gray-50)를 그대로 쓴다. 글자 대비 L 17.41 · D 12.75. `.btn-primary:hover` = primary-700(흰 글자 L 5.46 · D 10.12 — 같은 값이 #10 `.btn-strong:hover` 에도 간다).
- 근거: 목업 `.btn-secondary:hover{background:var(--color-gray-50)}`(:167) · 규칙 재사용.
- 대안: 목업 그대로 테두리도 `--color-gray-400` 으로 바꾼다.

**11. #12 `.btn-sm` 크기**
- 제안: `.btn-sm { height: 29px; min-height: 29px; padding: 0 11px; font-size: var(--text-caption); }` ＋ 640px 이하 `min-height: var(--control-height)`(44px 터치 하한 유지).
- 근거: v2 목업 `.btn-sm{height:29px;padding:0 11px;font-size:var(--text-caption)}`(:161) · 현 `.btn` 실효 높이 40px(`primitives.css:15`–`16` · `--control-height`). v1 목업 `.ds-btn-s{padding:6px 12px;font-size:13px}`(참고).
- 대안: 높이 32px(`.btn` 에 이미 적힌 `height: 32px`) · 나머지 같음.
- 영향: TSX 60회 · 17파일의 작은 단추가 40px → 29px 로 준다(데스크톱).

## 색 (#11 · #17)

**12. #11 칩 기본 배경 — 두 기존 토큰 중 하나**
- 제안: `--color-gray-100`(L #e8ecf2 · D #2b3745).
  - `.chip--off` 글자(muted): L 5.70 · D 6.48(오늘 L 6.01 · D 1.66).
  - 이 배경을 함께 쓰는 수식자 3종 — `.chip--closed`(프로젝트 3곳) · `.chip--info`(`RegisterArea.tsx:828`) · `.chip--success`(`UploadModal.tsx:1399`)는 CSS 정의가 없어 오늘도 `#eef2f7` 위에 부모 글자색을 쓴다. 부모가 본문색이면 D 1.00:1. gray-100 이면 L 15.34 · D 10.75.
  - 라이트 바탕이 #eef2f7 → #e8ecf2 로 조금 진해진다. 라이트에서 칩 테두리(`--color-border` #e8ecf2)와 바탕이 같아 테두리가 안 보인다.
- 근거: 선례 `.chip--lineage` · `.chip--neutral` 이 gray-100(`primitives.css:64`–`65`) · 수식자 없는 칩(surface-alt · `:67`)과 모양이 갈린다.
- 대안: `--color-surface-alt`(L #f5f7fa · D #202b37) — muted L 6.30 · D 7.69, 본문색 L 16.95 · D 12.75. 테두리는 보이지만 수식자 없는 칩과 같은 모양이 된다.

**13. #17 「색 배경 위 글자」 토큰 (`.de-req` · `components/detail/detail.css:166`)**
- 제안: 이름 `--color-on-text-body`(바탕 토큰 `--color-text-body` 의 짝 · 기존 `--color-on-primary` · `--color-on-danger` 와 같은 짓기) · L `#ffffff` · D `#1a222c`(다크 `--color-surface` 와 같은 값). 대비 L 10.34(오늘과 같음) · D 12.50(오늘 1.28).
- 근거: 기존 값 재사용. `tokens.css` 에 둔다 — 화면 범위에서는 다크 값을 줄 수 없고(게이트 d 가 화면 CSS 의 `:root` 선택자를 막는다) 정본 계열 이름은 화면 범위에 못 둔다(게이트 a). 한 화면만 쓰므로 `tokens.css:3` 「둘 이상 화면」 규칙의 예외로 주석을 단다.
- 대안: 이름 `--color-on-inverse` · 다크 `#11161d`(14.15).
- 참고: 토큰 없이 `color: var(--color-surface)` 로도 같은 값이 나온다. 판정 ⓐ(새 토큰)와 달라 제안하지 않는다.

## 누름 피드백 (WU-A1–A4)

규칙 하나로 정한다 — **누름 = hover 의 한 단 진한 값.** 파란 채움은 선례(`.btn-primary:active` primary-700 · `primitives.css:32`)를 따른다.

**14. WU-A1 버튼(`primitives.css`)**
- 제안: `.btn:where(:not(.btn-primary)):active { background: var(--color-gray-100); }` — plain · ghost · secondary 에 걸린다(hover gray-50 의 한 단 진함). 글자 L 15.34 · D 10.75. `.btn-primary:active` 는 그대로. 화면이 배경을 따로 주는 단추(`.btn-strong` · `.btn-danger` 편차)는 층 순서상 화면 규칙이 이긴다.
- 근거: apple §1 · 선례 `primitives.css:32`.
- 대안: 목업 `.btn:active{transform:translateY(.5px)}`(:159)를 함께 둔다.

**15. WU-A2 셸(`shell/shell.css`)**
- 제안: 흰 면·투명 단추 `.gnb-settings` · `.gnb-more` · `.gnb-more-item` · `.gnb-logout` · `.loadfail-retry` · `.theme-switcher` · 모달 닫기 `.x` · `.backlink` · `.mainnav a` → 바탕 `--color-gray-100`(muted 글자 L 5.70 · D 6.48 · 본문색 L 8.72 · D 9.43). `.gnb-upload` → primary-700(hover 와 같음 · 선례).
- 근거: 각 hover 값(gray-50 · surface-hover) 의 한 단 진함 · `shell.css:419`–`420` reduced-motion 블록 무변.
- 대안: 파란 단추만 `--color-primary-800`(흰 글자 L 7.56 · D 12.56)로 hover 와 구분한다.

**16. WU-A3 표 행(`components/catalog/catalog.css`)**
- 제안: `.tbl tr.clk:active td { background: var(--color-gray-100); }`(hover surface-hover 의 한 단 진함 · 왼쪽 파란 줄은 hover 규칙이 계속 준다).
- 대안: `--color-primary-50`(고른 행 느낌).

**17. WU-A4 업로드(`components/upload/upload.css`)**
- 제안: `.btn-strong:active` primary-700 · `.dr-nav button:active` gray-100 · `.dr-cal-d:active` primary-200(hover primary-100 의 한 단 진함 · 글자 L 7.01 · D 5.91) · `.dr-useg button:active` gray-100(`.on` 은 primary-600 유지) · `.dr-field:active` 테두리 primary-600.
- 대안: `.dr-cal-d:active` 도 gray-100.

## 열린 값이 아닌 것(참고 · spec 에 적음)

- #8 rem 변환 = 28px → 1.75rem · 18 → 1.125 · 16 → 1 · 15 → 0.9375 · 14 → 0.875 · 13 → 0.8125(뿌리 글자 16px 가정 · `html` 에 font-size 선언 0건 실측).
- #16 `.lvl-mismatch` = `font-size: var(--text-caption)`(13px · #8 뒤 0.8125rem).
- #10 = `.btn-strong:hover { background: var(--color-primary-700); }`(판정 ⓑ 로 값 확정).
- #14 = `.account-modal-back { z-index: 200; }`.

열린 값 = 17건(1–17).
