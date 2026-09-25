# design-fix 후속 20260925 · 실화면 근거(live) — 부록 D 1–8

spec `dev-package/prd/specs/S-DESIGN-FIX-FOLLOWUPS-20260925.md` 부록 D 1–8 을 실브라우저로 잰 결과다. 9행(`frontend-visual` 최종 ＋ 캡처 대조)은 E1 이 맡았다. 판정은 사람이 한다. 아래 판정 칸은 기대값과 실측값을 대조한 값이다. not-run 은 통과로 세지 않는다.

## 0. 조건

- 트리: 브랜치 `worktree-design-fix-followups-grill` @ `9812d41f`. 추적 파일은 바꾸지 않았다.
- 대상: **audit 빌드 픽스처 화면**(로컬 모의 응답 · staging·dev 접속 0). E1 이 만든 빌드 `.codex/upload-preview-audit`(17:50, HEAD 커밋 17:43 뒤)를 `npm --prefix frontend run audit:preview -- --port 4291 --strictPort` 로 띄웠다. 주소는 `/audit-design.html?design=full&scene=<장면>` · `/audit-upload.html?<질의>` 두 가지다.
- 도구: agent-browser 0.27.0(headless Chrome 152) · 세션 `fxe2`. 계산 스타일은 `get styles`, 위치는 `get box` 로 쟀다. 누름은 `mouse down` 을 유지한 채 쟀다. `eval` 은 쓰지 않았다. 시각 기록은 읽기 전용 init script `dev-package/reports/design-review/20260925-followups/live/probe-init.js` 를 썼다. 이 스크립트는 `<html data-probe-log>` 에만 기록하고 `get attr html data-probe-log` 로 읽는다(선례 `dev-package/reports/design-review/20260924/fix/live/probe-init.js`).
- 테마: 다크 = `theme=dark` 질의(`<html data-theme="dark">`) ＋ `set media dark`. 기본 뷰포트는 1440×900 이다.
- 누름: `mouse down` 뒤 400ms(batch `wait 400`)에 쟀다. 그 뒤 요소 밖으로 옮겨서 놓았다. click 은 나지 않았다(대화상자·모달 개수가 그대로 남았다).
- 터치(6행): `set device "iPad"`(0.27 이 지원하는 태블릿 이름 중 하나)로는 `(pointer: coarse)` 가 켜지지 않았다(폭 820 · `--control-height` 40px · `.btn-sm` 29px). 그래서 같은 세션 이름으로 브라우저를 `--args "--blink-settings=primaryPointerType=2"` 를 주어 다시 띄웠다. 이렇게 하면 주 포인터 종류가 coarse 로 바뀌고 `(pointer: coarse)` 가 켜진다(`--control-height` 44px 로 확인). 터치 이벤트 에뮬레이션이 아니라 **주 포인터 종류 에뮬레이션**이다. 이 브라우저는 6행만 재고 닫았다.
- 대비: WCAG 상대 휘도식으로 계산했다.

## 1. 결과

| # | 측정 | 대상 URL·폭·테마 | 기대 | 실측 | 판정 |
|---|---|---|---|---|---|
| 1-a | 비활성 opacity · cursor — btn 계열 5 | `audit-design.html?design=full&scene=primitives` · 1440 · light | 0.5 · not-allowed | `.btn` · `.btn-primary` · `.btn-secondary` · `.btn-ghost` · `.btn-danger` disabled 5개 모두 0.5 · not-allowed. 같은 줄 활성 6개는 흐리지 않다(`1-primitives-disabled-1440-light.png`) | pass |
| 1-b | 〃 — strong | `scene=account-admin` → 「비밀번호 재설정」 모달 · 1440 · light | 0.5 · not-allowed | 「재설정」(`.btn.btn-strong`, 빈 입력으로 비활성) 0.5 · not-allowed · 배경 #1369e9. 부모 `.account-modal` opacity 1(`1-account-modal-strong-disabled-1440-light.png`) | pass |
| 1-c | 〃 — login-submit | `scene=login` · `scene=password-change` · 1440 · light | 0.5 · not-allowed | 빈 입력의 `.login-submit` 2곳 모두 0.5 · not-allowed. 로그인 배경은 #1369e9(회색 채움 없음)(`1-login-disabled-1440-light.png` · `1-password-change-disabled-1440-light.png`) | pass |
| 1-d | 〃 — 업로드 | `audit-upload.html` → 파일 고르기 → 「다음」 → ① 분류 · 1440 · light | 0.5 · not-allowed | 「다음 →」(`reg-next`, `.btn.btn-primary`) 0.5 · not-allowed. `.regsteps button:disabled`(②·③ 2개, btn 밖) 0.5 · not-allowed. 부모 `.regsteps` · `.reg-actions` opacity 1(`1-upload-classify-disabled-1440-light.png`) | pass |
| 1-e | 〃 — btn 밖 대시보드 | `scene=lab&operator=1` · 1440 · light | 0.5 · not-allowed | `.dash-section-label:disabled`(「우리 연구실 ›」 · 운영자에게 대상 연구실 없음) 0.5 · not-allowed. 부모 opacity 1(`1-lab-operator-section-label-disabled-1440-light.png`) | pass |
| 1-f | 〃 — btn 밖 나머지 4 선택자 | `.titem button` · `.pv-zoom button` · `.pj-x` · `.thumbrow .th-slot` | 0.5 · not-allowed | — | not-run — 아래 §2 사유. CSS 단언(L1·L2 시험)이 대체 근거다 |
| 2-a | 누른 채 배경 `.btn-primary` | `scene=primitives` · 1440 · light / dark | primary-800 #0b4eb6 / #d4e7ff · 뗀 뒤 기본 | L 쉼 #1369e9 → 누름 rgb(11, 78, 182)=#0b4eb6 → 뗀 뒤 #1369e9. D #92c2ff → rgb(212, 231, 255)=#d4e7ff → #92c2ff(`2-btn-primary-press-1440-{light,dark}.png`) | pass |
| 2-b | 〃 `.btn-strong` | `audit-upload.html` 닫기 확인창 「닫고 나가기」 · 1440 · light / dark | 〃 | L #1369e9 → #0b4eb6 → #1369e9. D #92c2ff → #d4e7ff → #92c2ff. 뗀 뒤에도 확인창 1개가 남았다(`2-btn-strong-press-1440-{light,dark}.png`) | pass |
| 2-c | 〃 `.gnb-upload` | `audit-upload.html?register=ok` 「업로드」(UploadEntry) · 1440 · light / dark | 〃 | L #1369e9 → #0b4eb6 → #1369e9. D #92c2ff → #d4e7ff → #92c2ff. 뗀 뒤 모달 0개(`2-gnb-upload-press-1440-{light,dark}.png`) | pass |
| 3-a | 닫기 확인창 computed | `audit-upload.html` → 파일 → 분류 입력 → × · 1440 · light / dark | box-shadow none · 1px border-strong(#dfe3e8 / #45566a) | `[data-testid=upload-close-confirm]` box-shadow none · 네 변 1px solid. L rgb(223, 227, 232)=#dfe3e8 · D rgb(69, 86, 106)=#45566a(`3-close-confirm-1440-{light,dark}.png`) | pass |
| 3-b | 미리보기 확대창 computed | 같은 모달 ② 단계 → ⤢(`pv-expand`) · 1440 · light / dark | 〃 | `.modal.pvx` box-shadow none · 1px solid. L #dfe3e8 · D #45566a(`3-preview-expand-1440-{light,dark}.png`) | pass(값). 겹침 관찰은 §3-1 |
| 4-a | 뒤판 transition | `audit-upload.html?register=ok` → 「업로드」 · 1440 · light | background-color 0.3s `cubic-bezier(0.2, 0, 0, 1)` | `.modal-back.mb-takeover`: transition-property background-color · duration 0.3s · timing cubic-bezier(0.2, 0, 0, 1) · delay 0s. 열린 값 rgba(15, 20, 28, 0.45). 여는 프레임은 마운트 뒤 0 → 0.45 에 약 285ms | pass |
| 4-b | 닫는 중 배경 ＋ 스크린샷 2장 | 같은 자리 · × 클릭 | 투명 쪽으로 이동 | 프로브 프레임(closing 시작 기준 · × 클릭 +1ms): +5ms 0.45 → +38ms 0.36 → +72ms 0.204 → +122ms 0.094 → +172ms 0.04 → +222ms 0.016 → +288ms 0. 언마운트 +306ms. 닫는 동안 inert 참. 스크린샷 `4-closing-100ms-1440-light.png`(뒤판이 흐리게 남음) · `4-closing-200ms-1440-light.png`(거의 투명). 두 캡처 시각은 명목값이다(batch `wait 100` 뒤 캡처 → `wait 60` 뒤 캡처 · 캡처 지연은 재지 않음). 원자료 `4-probe-backdrop-open-close-1440-light.json` | pass |
| 4-c | 동작 줄이기 | 같은 자리 · `set media light reduced-motion` | 즉시 | 뒤판 · 모달 transition-property none · 0s. 여는 첫 프레임 0.45 · opacity 1.00. × 뒤 언마운트 +1ms, closing 상태 기록 없음(`4-reduced-motion-after-close-1440-light.png` · `4-probe-reduced-motion-1440-light.json`) | pass |
| 5-a | 팝오버 아래 끝 대 단추줄 위 끝 | `audit-upload.html` → ② 메타데이터 → 「기간」 · 1440×900 · light | 아래 끝 ≤ 단추줄 위 끝 | 열기 전: 기간 칸 y 522.2 · `.reg-actions` y 835. 열고 600ms 뒤: `.dr-pop` y 365.77 + h 465 = **아래 끝 830.77** ≤ `.reg-actions` **위 끝 835**(여유 4.2px). 기간 칸 y 275.2(본문이 247px 스크롤됨). `.dr-pop` opacity 1 · transform none · scroll-margin-bottom 88px(`5-period-popover-1440-light.png`) | pass |
| 5-b | 375 시트 위치 | 같은 흐름 · 375×812 · light | B0 과 같음 | position fixed · left/right/bottom 12px · 박스 x 12 · y 150.4 · 351×649.6(아래 끝 800 = 812 − 12) · transform-origin 175.5px 649.594px(`5-period-sheet-375-light.png`). 이번 B0 캡처에는 팝오버를 연 장면이 없다. 그래서 직전 실측 `dev-package/reports/design-review/20260924/fix/live/index.md` §3-e(375 다크: x 12 · y 150.4 · 351×649.6)와 대조했고 값이 같다 | pass(대조 기준 = 20260924 실측) |
| 6-a | `.btn-sm` 높이 · 768 터치 | `scene=primitives` · 768×1024 · light · coarse 포인터 | 44 | `--control-height` 44px · `.btn-sm` height 44px · min-height 44px. 업로드 모달 ⤢(`pv-expand`, `.btn-sm`)도 44px(`6-primitives-btn-sm-768touch-light.png`) | pass |
| 6-b | 〃 · 768 마우스 | `scene=primitives` · 768×1024 · light | 29 | 29px(min-height 29px) | pass |
| 6-c | 〃 · 1440 마우스 | `scene=primitives` · 1440×900 · light | 29 | 29px(min-height 29px) | pass |
| 6-d | 768 터치 넘침 기록(우려 1 ⓐ · 기록만) | detail · members · settings · catalog · 업로드 ① 분류 · 768 · light · coarse | — | 5개 화면에서 이번 44px 하한 때문에 새로 넘치거나 줄바꿈된 자리는 보지 못했다. catalog 표 가로 스크롤(안내 문구가 있는 기존 설계)과 detail 계보 그래프 오른쪽 잘림이 보이는데, detail 은 768 마우스 캡처 `frontend/.visual/fixfu0925-final/detail-light-768.png` 에도 같은 잘림이 있다. catalog 는 마우스 캡처와 대조하지 않았다(`6-overflow-{detail,members,settings,catalog}-768touch-light.png` · `6-upload-classify-768touch-light.png`) | 기록(판정 밖) |
| 7-a | 등록 성공 → 0.3초 안 × → 입구 → 단계 | `audit-upload.html?register=ok` · 「업로드」(UploadEntry) · 1440 · light | 첫 단계 | 파일 → 분류 → 메타데이터(설명 · 간격 1일 · 기간) → 연결(「가공 전 데이터를 못 찾았어요」 체크) → 「데이터셋 만들기」 클릭. 등록 성공이 스스로 닫기를 시작했다(클릭 +4ms closing). closing 시작 +53ms 에 × 자리를 눌렀는데 inert 라 `main.appmain` 에 닿았다. +71ms 에 「업로드」를 눌렀고 곧바로 옛 모달이 언마운트되고 새 모달이 마운트됐다(`register` · `pick` · 「파일 올리기」). 원자료 `7-probe-upload-entry-1440-light.json` · `7-upload-entry-reopen-first-step-1440-light.png` | pass |
| 7-b | 〃 | 같은 주소 · 「기준 격자 추가」(GridAttachEntry) · 1440 · light | 첫 단계 | 파일 → 「이 데이터셋에 반영」(`grid-attach-confirm`) → +2ms closing → +60ms × 자리 누름(`main.appmain` 에 닿음) → +76ms 「기준 격자 추가」 → 새 모달 마운트(`grid-attach` · `pick` · 「기준 격자 추가」). 원자료 `7-probe-grid-attach-1440-light.json` · `7-grid-attach-reopen-first-step-1440-light.png` | pass |
| 8-a | 계정 관리 모달 층 | `scene=account-admin` → 「비밀번호 재설정」 · 1440 · light | z-index 200 | `.account-modal-back`(모달 층) position fixed · z-index 200(`8-account-modal-1440-light.png`) | pass |
| 8-b | 「불일치」 글자 | `scene=catalog&mismatch=1` · 1440 · light | 13px | `[data-testid=lvl-mismatch]` 1개(문구 「계산값과 다름」) font-size 13px · weight 600 · color #a85400(`8-mismatch-catalog-1440-light.png`) | pass |
| 8-c | 다크 「필수」 대비 | `audit-upload.html?theme=dark` → ② 메타데이터 · 1440 · dark | ≥ 4.5 | `.reqtag` 「필수」 color rgb(255, 173, 182)=#ffadb6. 바탕은 `.reqtag` · 부모 · `.form-row` · `.card-b` 가 모두 투명이고 가장 가까운 불투명 조상 `.card.is-on` 이 rgb(26, 34, 44)=#1a222c 다. 대비 **9.09:1**(`8-reqtag-register-1440-dark.png`) | pass |
| 8-d | 열 메뉴 라벨 자간 | `scene=catalog&mismatch=1` → 「주제」 열 메뉴 · 1440 · light | `--tracking-label` 값 | `.colmenu .cm-s`(「정렬」) letter-spacing 0.65px = `--tracking-label` .05em × font-size 13px(`8-colmenu-1440-light.png`) | pass |
| 8-e | 닫는 중 누름 차단 | `audit-upload.html?register=ok` → 「업로드」 → 파일 → 「다음」 → × · 1440 · light | inert 참 ＋ 도구 패널 누름 무반응 | × 뒤 `upload-backdrop` data-state closing · `inert` 속성 있음(프레임 기록 inert true). × 클릭 +78ms 에 ⤢ 좌표(152, 136)를 눌렀다. 닿은 대상은 `html`(모달 밖)이고 확대창 마운트는 0이었다. 대조: 열린 상태에서 같은 좌표를 누르면 `button[pv-expand]` 에 닿고 확대창이 마운트된다. 언마운트는 × 클릭 +328ms. 원자료 `8-probe-closing-inert-click-1440-light.json` · `8-closing-tool-click-1440-light.png` | pass(대상 주의 §2) |

소계: pass 25 · not-run 1(1-f, 4 선택자) · 판정 밖 기록 1(6-d).

## 2. not-run 사유 · 대상 주의

- 1-f `.titem button:disabled`: 거절 사유 확인 단추다(`TodoInbox.tsx:191`, 사유가 빌 때 비활성). lab 장면의 할 일은 「계보 확인 →」 3건뿐이고 접근 요청 항목이 없어서 거절 흐름을 열 수 없다.
- 1-f `.pv-zoom button:disabled`: audit 빌드의 `preview-done` · `detail` 장면에 `.pv-zoom` 이 0개다(실측). 업로드 모달 미리보기도 그리기 결과가 없어서(픽스처 `getRender` 오류) 확대 줄이 서지 않는다.
- 1-f `.pj-x:disabled`: 제출이 진행 중일 때만 비활성이다. `project-dialog` 장면의 `onSubmit` 은 곧바로 거절하는 픽스처라 진행 중 상태를 잡아 둘 수 없다.
- 1-f `.thumbrow .th-slot:disabled`: `representativeDisabled={submitting}` 이라 등록 요청이 진행 중일 때만 비활성이다. 평소에는 `.th-slot` 1개 · `:disabled` 0개(실측)이고, `register=ok` 등록은 곧바로 끝난다.
- spec 부록 D 1행은 「장면 없음(대시보드)」을 미실행으로 예상했다. 그런데 `scene=lab` 이 대시보드 화면이고, 기존 계정 질의 `operator=1` 로 `.dash-section-label:disabled` 에 닿았다(1-e).
- 8-e 대상: 판정 문구의 「도구 패널」(`.pv-overlay` 의 `.pv-zoom` 등, 명시 `pointer-events: auto`)은 위 사유로 픽스처에 서지 않는다. 그래서 모달 안 미리보기 줄의 ⤢(`pv-expand`) 단추를 눌렀다. 이 단추는 누르면 확대창이 열리는 것으로 반응 여부를 판별할 수 있다. 또 `inert` 는 모달(`upload-modal`)이 아니라 부모 뒤판 `.modal-back.mb-takeover` 에 붙는다(`UploadModal.tsx:1396`). 모달은 그 하위라 함께 inert 가 된다.
- 7행 「× 누름」: 등록 · 반영 성공은 × 없이 스스로 닫기(`closeAfterCommit`)를 시작한다. 닫는 동안 뒤판이 inert 라 × 자리 누름은 뒤 화면(`main.appmain`)에 닿는다. 두 입구 모두 이 누름을 넣은 채로 쟀다.

## 3. 관찰(판정 밖 · 후속 판단용)

1. **확대창 위로 등록 폼 일부가 그려진다** — 1440 L/D 에서 ⤢ 로 연 `.modal.pvx` 위에 ② 단계의 「기간」 칸(라벨 · 시작/종료)이 겹쳐 보인다. 하단 단추줄 `.reg-actions`(등록 취소 · 이전 · 다음)는 확대창 뒤판에 어두워지지 않는다(`3-preview-expand-1440-{light,dark}.png`). 원인과, 이번 변경 전부터 있었는지는 조사하지 않았다.
2. agent-browser 0.27 의 `set device` 가 지원하는 이름은 iPhone 15 · 16 · 16 Pro · 17 · iPad · iPad Pro · Pixel 9 · Galaxy S25 뿐이다. `iPad` 는 폭 820 이고 `(pointer: coarse)` 를 켜지 않았다. 768 터치를 재려면 §0 의 실행 인자가 필요하다.
3. 6-d 의 members · settings 768 터치 화면에서 GNB 「로그아웃」은 작은 높이로 보였다. 이 요소의 클래스와 높이는 재지 않았다.

## 4. 정리

- 세션 `fxe2` 를 `close` 했다(터치 인자 브라우저 포함 3회 띄우고 3회 닫음). `agent-browser session list` 결과는 「No active sessions」였다. `pgrep -af agent-browser` 는 시작 전 0건 · 종료 뒤 0건이었다.
- preview 서버(4291)는 `pkill -f 'vite preview --config audit.vite.config.ts'` 로 멈췄고, 4291 LISTEN 은 없다.
- 저장소 밖 임시물: 워크플로 작업 임시 폴더(1KB 더미 `design-audit.nc` · 원본 캡처 · preview 로그). 저장소에는 넣지 않았다.
- 이 폴더의 산출: `index.md` · `probe-init.js` · 프로브 기록 JSON 5개 · 스크린샷 PNG 34장.
