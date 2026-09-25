# design-fix 20260924 · L1(CSS 공통·화면) 레인 보고

- spec: `dev-package/prd/specs/S-DESIGN-FIX-20260924.md` §1 · §3 · §4 「L1」 · §5 · §6 · 「확정 값」(값 8–18)
- intent: `dev-package/intent/2026-09-25-design-fix-20260924.md`
- 기준 HEAD: `e8fc4e13`(브랜치 `worktree-design-review-apple-20260924`) · 레인 브랜치 `worktree-agent-a6ad039bf930a5172`
- lifecycle task: `1659c1675fd8404d84d97b8f07cb0e3a`(role lane-worker · 선언 게이트 6)
- 준비(3-0): `frontend/` 에서 `npm ci` 종료 0

## 1. 단계 · 커밋

| 단계 | 커밋 | 내용 |
|---|---|---|
| 시험 작성(RED) | `06b7efb0` | `frontend/test/design-fix-20260924-L1.test.ts` 55건 · `same-in-dark.txt` `.chip` f 줄 삭제 |
| 구현 1 | `01b2de10` | 토큰·글자 — #7 · #8 · #17 · #14 |
| 구현 2 | `735285dd` | 버튼·칩·누름 — WU-A1–A3 · #9 · #11 · #12 · #13 · #15 · #16 · #19 |
| 문서 | `d5925018` | `docs/design-system.md` ②③⑤⑦ · `design-review/SKILL.md` §0 |

RED 확인(시험 작성 단계 · 구현 전): `Tests 38 failed | 17 passed (55)`. 실패 사유는 모두 선택자 블록 부재 · 값 불일치(예 `expected '28px' to be '1.75rem'` · `선택자 블록 수: .btn-sm : expected +0 to be 1` · `expected 'z-index: 120' to be 'z-index: 200'`). 구현 전 green 17 = 회귀 고정(#13 원문 · 기존 hover 7 · reduced-motion · `.tbl tr.clk td` transition) ＋ 대비(#9 · #11 두 테마) ＋ same-in-dark f 줄 0(같은 커밋에서 지움) ＋ `.btn-primary:active` 불변(그대로 primary-700) ＋ `primitives.css` `!important` 0. 〔정정 2026-09-25 · 통합 F-int〕 목록이 15건만 적어 17 과 어긋났다 — 뒤 두 건(`frontend/test/design-fix-20260924-L1.test.ts`:176 · :179)이 빠져 있었다(acceptance A9).

## 2. before → after (항목별)

| # | 파일 | before | after | 값 |
|---|---|---|---|---|
| WU-A1 | `shell/primitives.css` | `:active` = `.btn-primary` 1건 | `.btn:where(:not(.btn-primary)):active { background: var(--color-gray-100) }` 추가 · `.btn-primary:active` 불변 | 14 |
| 9 | `shell/primitives.css` | `.btn:where(:not(.btn-primary, .btn-secondary)):hover` · `.btn-primary:hover` 없음 | `.btn:where(:not(.btn-primary)):hover`(secondary 도 gray-50) · `.btn-primary:hover { background: var(--color-primary-700) }` | 10 |
| 12 | `shell/primitives.css` | `.btn-sm` 정의 0 | `.btn-sm { height: 29px; min-height: 29px; padding: 0 11px; font-size: var(--text-caption) }` ＋ `@media (max-width: 640px) { .btn-sm { min-height: var(--control-height) } }` | 11 |
| 11 | `shell/primitives.css` · `gates/fixtures/frontend-design-lint/same-in-dark.txt` | `.chip { background: #eef2f7 }` · f 면제 1 | `background: var(--color-gray-100)` · f 면제 0 · 주석 갱신 | 12 |
| 값 18 | `shell/primitives.css` | `.chip` 테두리색 `--color-border` | `border-color: var(--color-border-strong)`(`border` 뒤) | 18 |
| 13 | `shell/shell.css` `.gnb` · `shell/primitives.css` `.modal` | 주석 없음 | 「합격선 예외 #13」 주석 2곳 · 값 무변 | — |
| 14 | `auth/login.css` | `.account-modal-back { z-index: 120 }` | `z-index: 200`(＝ `.modal-back`) | — |
| 7 | `shell/shell.css:123,430` 외 8파일 | 리터럴 15곳(−0.02em 5 · −0.03em 2 · −0.023em 1 · 0.05em 6 · 0.04em 1) | `var(--tracking-heading)` 8 · `var(--tracking-label)` 7 · `.login-brand` 0.01em 은 브랜드 예외 주석 | 8 · 9 |
| 8 | `shell/tokens.css` | `--text-*` 6개 px | 1.75rem · 1.125rem · 1rem · 0.9375rem · 0.875rem · 0.8125rem | — |
| 17 | `shell/tokens.css` · `components/detail/detail.css` | `.de-req { color: var(--color-white) }` · 다크 1.28:1 | `--color-on-text-body`(L `#ffffff` · D `#1a222c`) · `.de-req { color: var(--color-on-text-body) }` · 다크 12.50:1 | 13 |
| 15 | `components/catalog/catalog.css` | 주석 없음 | `.thf::before` 위 「장식 글리프 · 합격선 예외 #15」 주석 · 9px 무변 | — |
| 16 | `components/catalog/catalog.css` | `.lvl-mismatch { font-size: 12px }` | `var(--text-caption)` | — |
| 19 | `components/lineage/lineage.css` | 주석 「안내 줄 #5b6472 on #f7f8fa = 5.63:1」 | 「안내 줄(`.lin-over-why` · `.lin-unknown-why`) `--color-warning-600` #a85400 on 흰 면 #ffffff = 5.34:1」 | — |
| WU-A2 | `shell/shell.css` | 셸 `:active` 0 | 10종(11 선택자) `:active` — `.gnb-upload` primary-700 · 나머지 gray-100 · 기존 hover · reduced-motion 원문 불변 | 15 |
| WU-A3 | `components/catalog/catalog.css` | `.tbl tr.clk` hover 만 | `.tbl tr.clk:active td { background: var(--color-gray-100) }` · transition 원문 불변 | 16 |
| 문서 | `docs/design-system.md` · `.agents/skills/design-review/SKILL.md` | ⑦ 시각 값 1–9 열림 · §0 합격선 예외 없음 | spec §6 대로(생성 표 재생성 · 손글 · 닫힘 표 · §0 두 곳) | — |

## 3. 수용 기준(spec §4 L1) 대조

`frontend/test/design-fix-20260924-L1.test.ts` 55건 — 구현 뒤 `Tests 55 passed (55)`.

| # | spec §4 단언 | 시험 | 결과 |
|---|---|---|---|
| WU-A1 | `.btn:where(:not(.btn-primary)):active` gray-100 · `.btn-primary:active` 원문 불변 · `!important` 0 | 3 | 충족 |
| 9 | `.btn-primary:hover` primary-700 · 제외 목록에 `.btn-secondary` 0 · on-primary 대 primary-700 두 테마 ≥ 4.5 | 4 | 충족(L 5.46 · D 10.12 · 값 10 근거값) |
| 12 | `.btn-sm` 네 선언 · 640px 분기 `min-height: var(--control-height)` | 2 | 충족 |
| 11 | `.chip` 배경 gray-100 ＋ `border-color: var(--color-border-strong)`(값 18) · `#eef2f7` 0(주석 포함) · f 줄 0 · muted · 본문색 대 gray-100 두 테마 ≥ 4.5 | 5 | 충족 |
| 13 | `.gnb` · `.modal` shadow-sm · `.modal--dialog` none 원문 불변 ＋ 예외 주석 2곳 | 2 | 충족 |
| 14 | `.account-modal-back` z-index 200 = `.modal-back` | 1 | 충족 |
| 7 | 토큰 두 개 · 자간 값이 토큰 · 0 · normal · inherit(`.login-brand` 예외 1) · heading 8 · label 7 | 3 | 충족 |
| 8 | `--text-*` 6개 rem · px `--text-*` 0 | 7 | 충족 |
| 17 | 두 테마 정의 · `.de-req` 글자 토큰 · 대비 두 테마 ≥ 4.5(라이트는 `#21272ae0` 를 흰 면에 합성) | 4 | 충족 |
| 15 | `.thf::before` 9px 불변 ＋ 예외 주석 | 1 | 충족 |
| 16 | `.lvl-mismatch` caption · catalog.css `font-size: 12px` 0 | 1 | 충족 |
| 19 | 주석 포함 원문 `#5b6472` 0 · 안내 줄 주석 `--color-warning-600` | 1 | 충족 |
| WU-A2 | 10종(11 선택자) `:active` 값 15 · reduced-motion 원문 불변 · 기존 hover 7 블록 원문 불변 | 19 | 충족 |
| WU-A3 | `.tbl tr.clk:active td` gray-100 · `.tbl tr.clk td` transition 불변 | 2 | 충족 |
| 문서 | `design-docs.mjs --check` 종료 0 | 게이트 h | 충족(`문서 표 갈림 0`) |

## 4. 게이트

vitest 전체: 시험 작성 단계 직후 `Tests 38 failed | 1630 passed (1668)`(실패 38 = 이 레인 새 시험) → 구현 뒤 `1668 passed · 실패 0`. 기존 시험 1613건은 수정 없이 green.

레인 단독 사전 실행(저장소 루트 · 하나씩 · task 미지정):

| 게이트 | green | red(판정) | red(준비 78) | 요약줄 |
|---|---:|---:|---:|---|
| `frontend-typecheck` | 1 | 0 | 0 | tsc 오류 0건 |
| `frontend-design-lint` | 1 | 0 | 0 | 파일 21 · 다크 누락 0(면제 6) · 색 리터럴 0(면제 0) · 프리미티브 맨 정의 밖 0 · 문서 표 갈림 0 |
| `frontend-design-lint-selftest` | 1 | 0 | 0 | 검사 26건 전건 기대대로(green 6 · red 14 · red(준비) 6) |
| `frontend-fixture-reach` | 1 | 0 | 0 | 도달 207 · 금지 모듈 0 |
| `frontend-test` | 1 | 0 | 0 | 통과 1668 · 실패 0 |
| `frontend-visual` | 1 | 0 | 0 | 페이지 20건 · 13px 미만 0 · 대비<4.5 0 · 스크린샷 40장 |

`frontend-visual` 대상 = audit 빌드(`npm run audit:build` → `audit:preview --port 4187`) · 장면 12 × (라이트 · `&theme=dark`) = URL 24(spec §5 L1 목록). **픽스처 화면**이다(실데이터 아님). `live_audit.sh` 의 `set media dark` 는 probe 뒤에 스크린샷만 찍어 다크 계측이 안 되므로 `&theme=dark` URL 을 따로 선언했다(spec §5 지시).

### 4-1. task 증거 실행

`COLAB_TASK_ID=1659c1675fd8404d84d97b8f07cb0e3a bash gates/run.sh task`(선언 게이트 6 · 한 번에 · 위 URL 24 선언).

| run_id | 커밋(보고서 기재 전) | 계 | 증거 |
|---|---|---|---|
| `3634da1442634e0ba0c951717163b88d` | `1a73ec78` | green 6 / red(판정) 0 / red(준비) 0 | `.git/colab-harness/d37b49847bbd17cdfae1cb5ec5bc1bd8/1659c1675fd8404d84d97b8f07cb0e3a/3634da1442634e0ba0c951717163b88d/logs/0.log`–`5.log` |

- 게이트별: typecheck 오류 0 · frontend-test 1668 통과 · 실패 0(호스트 뮤텍스 대기 662s — 아래 §6 뮤텍스 누수) · fixture-reach 도달 207 · 금지 0 · design-lint 전 조건 0 · 문서 표 갈림 0 · selftest 26건 기대대로 · visual 페이지 20 · 13px 미만 0 · 대비<4.5 0.
- 이 run 뒤 이 보고서에 run_id 를 적어 파일 hash 가 바뀐다. 인계(`handoff --mode complete`) 증거는 이 커밋 뒤 같은 명령을 다시 돌린 run 이며 그 run_id 는 레인 최종 메시지의 `COLAB_HANDOFF` 줄에 있다. 제품 파일은 두 run 사이에 같다.

## 5. 하지 않은 것

- 실화면 증거(spec §4 「실화면 증거」 L1 행 · §5 캡처 대조) — spec F3 에 따라 통합 단계(합친 뒤 audit 빌드 1회)에서 오케스트레이터가 한다. 이 레인은 vitest ＋ §5 게이트만 돌았다.
- #6 · #18 · #20 — 코드 0(변경 없이 닫힘). #6 전역 reduced-motion 규칙(`shell.css` `@media (prefers-reduced-motion: reduce)`) 원문 불변을 시험이 고정한다.
- #21 — 코드 0. 다음 회차 `routes/**` 담당 레인에 재판정 배정(`pd-closedbar` · `pd-linkempty` · D15 `NotFoundPage.tsx:12` · 실화면 D23 과 함께). 다음 design-review 회차 §0 이월 입력.
- 판정표 밖 잔여(spec §2 · 위험 8): #13 적용 뒤에도 가운데 대화상자 2종 — `UploadModal.tsx:1751` 닫기 확인(`.confirm-back .modal`) · `.modal.pvx`(`PreviewExpandOverlay.tsx:40`) — 가 `--shadow-sm` 을 가진 채 남는다. 다음 회차 재판정 후보.

- 캡처 대조(spec §5 「게이트 밖 증거」 · `visual:capture` 레인 라벨 `fix0924-L1` 대 `fix0924-base`) — 미실행. 기준 캡처 `fix0924-base` 는 오케스트레이터 체크아웃의 `frontend/.visual/` 에 있고 이 레인 워크트리에는 없다. 지시문대로 실화면·캡처는 통합 단계 몫으로 넘긴다. 따라서 「바뀐 장면 → 원인 항목 #」 표는 아래 §6 예상 영향 목록으로 대신하며 실측이 아니다.
- `COLAB_FIX_LANE=1` — 이 세션의 훅 프로세스 환경에 값을 넣을 수단이 없어(`echo` 결과 unset) 훅 강제는 걸리지 않았다. 규율로 지켰다: 구현 커밋 3개(`01b2de10` · `735285dd` · `d5925018`)의 변경 파일은 `frontend/src/**` · `docs/design-system.md` · `.agents/skills/design-review/SKILL.md` 뿐이고 `frontend/test/**` · `gates/**` · `contracts/**` · `services/*/tests/**` 는 0(`git diff --name-only 06b7efb0 HEAD`).

## 6. 부수 변화 · 남은 위험

예상 시각 영향(캡처 대조 미실행 · 통합 단계에서 대조할 목록):

| 변화 | 영향 면 | 항목 |
|---|---|---|
| `--text-*` px → rem | 뿌리 16px 에서 계산값 동일. 브라우저 기본 글자를 키우면 글자만 커지고 px 고정 높이 상자(`.btn` 32/40px · `.chip` 24px · `.btn-sm` 29px)는 그대로라 잘릴 수 있다(spec 위험 1 · [미상 · 도구가 기본 글자 크기를 못 바꾸면]) | 8 |
| `.btn-sm` 40px → 29px(데스크톱) | TSX 60회 · 17파일의 작은 단추 · 640px 이하 44px 유지 | 12 |
| `.btn-secondary` hover gray-50 · `.btn-primary` hover primary-700 | 모든 보조·기본 단추 hover | 9 |
| 누름 gray-100 / primary-700 | `.btn`(primary 제외) · 셸 10종 · 카탈로그 표 행 | WU-A1–A3 |
| `.chip` 라이트 배경 `#eef2f7` → `#e8ecf2` · 테두리 `#e8ecf2` → `#dfe3e8` · 다크 배경 `#eef2f7` → `#2b3745` | 수식자 없는 칩 외 모든 칩. 수식자 CSS 가 없는 `.chip--closed`(프로젝트 3곳) · `.chip--info` · `.chip--success` 의 다크 글자 대비 1.00:1 → 10.75:1(spec 위험 5) | 11 · 값 18 |
| 자간 값 변경 4곳 | `.project-detail .pd-head h1` −0.03 → −0.02em · `.detail-page .dt-header h1` −0.03 → −0.02em · `.settings-page h1` −0.023 → −0.02em · 카탈로그 열 메뉴 `.colmenu .cm-s` 0.04 → 0.05em | 7 |
| `.lvl-mismatch` 12px → 13px | 카탈로그 「불일치」 표식 | 16 |
| `.de-req` 다크 글자 흰색 → `#1a222c` | 상세 편집 필수 표식(다크만) | 17 |
| 계정 관리 모달 층 120 → 200 | GNB(100) 위로 | 14 |

남은 위험 · 판정 밖 발견(고치지 않음):

- **`.chip--off` 의 테두리** — `.chip--off { border: 1px solid var(--color-border) }` 단축 선언이 값 18 의 `.chip` `border-color: var(--color-border-strong)` 를 같은 층·같은 특이도·뒤 순서로 되돌린다. 그래서 판정 행 자체인 `.chip--off` 는 라이트에서 테두리 `#e8ecf2` = 배경 gray-100 `#e8ecf2` 로 윤곽이 안 보인다(값 18 이 푼 문제가 `.chip--off` 에만 남음). 확정 값 밖이라 고치지 않았다 — 선택지: `.chip--off` 의 `border` 선언 삭제(테두리는 `.chip` 이 이미 준다) 또는 그대로. Ted 판정 필요.
- `live_probe.js` 의 `activeRules` · `reducedMotionBlocks` 는 최상위 `cssRules` 만 훑는다(`.agents/skills/design-review/scripts/live_probe.js:39`–`42`). 모든 CSS 가 `@layer` 블록 안이라 audit 빌드에서 둘 다 0 으로 나온다(이번 실행 24 URL 전부 `:active rules 0` · `reduced-motion blocks 0` — `shell.css` 에 reduced-motion 블록이 실제로 있다). spec §4 실화면 증거의 「activeRules 가 기준값 2 보다 크다」는 이 probe 로는 판정할 수 없다. 어느 게이트도 이 값을 판정하지 않는다(`frontend-visual` 은 small · lowContrast 만 잰다) — 후속.
- `live_audit.sh` 의 파일 이름(slug)이 60자에서 잘려 `&theme=dark` URL 4개(primitives · project-detail · account-admin · lineage-picker)가 라이트 URL 과 같은 이름이 된다. 증거 파일이 덮이고 `frontend-visual` 요약의 「페이지」가 24 가 아니라 20 으로 찍힌다. index 표에는 24행 모두 small 0 · lowContrast 0 으로 남는다. `frontend-visual` 게이트 판정부 쪽 결함 — 후속.
- **호스트 뮤텍스 누수** — `frontend-visual` 이 부른 `live_audit.sh` 의 `agent-browser --session design` 데몬(와 chrome)이 게이트 종료 뒤에도 살아 남아 뮤텍스 fd(`/tmp/colab-v2-gate-host-mutex/host`)를 물려받은 채 쥐고 있었다. 이 레인의 사전 `frontend-visual`(00:40) 뒤 약 13분 동안 다른 레인의 `frontend-test` 와 이 레인 task run 이 `flock -w 900` 에서 대기했다(대기 누계 662s). `agent-browser --session design close` 로 풀었고, 이후 visual 실행마다 같은 명령으로 닫았다. `live_audit.sh`/`frontend-visual.sh` 가 데몬에 fd 를 넘기지 않거나 끝에서 세션을 닫아야 한다 — 어느 게이트도 이 누수를 재지 않는다 — 후속.
- 판정표 밖 잔여 대화상자 그림자 2종(§5).
