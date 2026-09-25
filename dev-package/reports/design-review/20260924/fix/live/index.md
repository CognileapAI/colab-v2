# design-fix 20260924 · 실화면 상호작용 계측(live)

정적 캡처가 못 보이는 상태(누름 유지 · hover · 전환 · 끌기 관성 · 동작 줄이기)를 실브라우저로 잰 결과다. 판정은 아래 계산값·프레임 기록·스크린샷 근거에 따른다. not-run 은 통과로 세지 않는다.

## 0. 조건

- 트리: 브랜치 `worktree-design-review-apple-20260924` @ `407fbcab` (계획 워크트리 · 추적 파일 무변경).
- 대상: **audit 빌드 픽스처 장면**(모의 응답 · 서버 호출 차단). `frontend/` 에서 `npm run audit:build` → `npm run audit:preview -- --port 4291 --strictPort`. 주소 `/audit-design.html?design=full&scene=<장면>` · `/audit-upload.html`. staging·dev 환경 접속 0.
  - 예외 1건(f·g 의 끌기): audit 빌드의 `preview`·`preview-done`·`detail` 장면에는 확대·이동 요소가 없다(`[data-zoom-scale]` 0개 실측). 그래서 저장소의 로컬 픽스처 `frontend/audit-selected-preview.html?tiles=1`(`DatasetPreviewSection` · 모의 응답)을 `npx vite --config audit.vite.config.ts --port 4292` **개발 서버**로 띄워 쟀다. 개발 모드 React이며, audit 빌드 입력에 없는 진입점이다.
- 도구: agent-browser 0.27.0 (headless Chrome). 계산 스타일 = `agent-browser get styles`. 시각 기록 = 읽기 전용 init script `probe-init.js`(이 폴더) — `<html>` 의 `data-probe-*` 속성에만 기록하고 `get attr html …` 로 읽었다. `eval` 은 쓰지 않았다.
- 테마: 다크 = `theme=dark` 쿼리(`<html data-theme="dark">`). 뷰포트 1440×900(e·f 일부 375×812).
- 누름 계측: `mouse down` 을 유지한 채 400ms 뒤(전환 0.14s 종료 뒤) 측정. 요소 밖으로 옮긴 뒤 놓아 click 이 나지 않게 했다.
- 명암비는 WCAG 상대 휘도식으로 계산했다(반투명 hover 는 흰 바탕 합성값).

## 1. 판정 요약

| # | 점검 | 결과 | 근거 |
|---|---|---|---|
| a1 | `.btn` 쉼·hover·누름 (L·D) | pass | §2 표 · `a-btn-{rest,hover,press}-{light,dark}.png` |
| a2 | `.btn-primary` 누름 ≠ hover | **fail** | 두 테마에서 누름 = hover(1.00:1). 확정 값 10·14(primary-700 두 자리) 그대로이며 값 19 범위 밖. F-css 보고에 「파란 채움 누름 = hover」로 이미 적힌 잔여 · `a-btn-primary-{hover,press}-*.png` |
| a3 | 카탈로그 행 `.tbl tr.clk` | pass | 다크 hover #2b3745 → 누름 #45566a(1.61:1) · `a-row-*.png` |
| a4 | 상단 메뉴 링크 | pass | 다크 1.61:1 · `a-nav-{hover,press}-*.png` |
| a5 | 현재 탭(`.is-active`) 누름 | pass | hover 는 무변화(흰 면 유지). 누름은 L #e8ecf2 · D #45566a · `a-nav-current-*.png` |
| a6 | 업로드 달력 `.dr-nav button` | pass | 다크 1.61:1. 누르는 동안 다크 테두리(#45566a)와 누름 면(#45566a)이 같은 색이 된다. F-final 보고에 적힌 귀결이다 · `a-drnav-*.png` |
| a7 | `.dr-useg button` | pass | 다크 1.61:1 · `a-druseg-*.png` |
| a8 | `.dr-cal-d` | pass | L #e2eeff → #bad7ff · D #284769 → #315779(각 1.26:1) · `a-drcald-*.png` |
| b1 | 비활성 `.btn-primary` hover | pass | L #1369e9 · D #92c2ff 에서 hover 해도 무변화 · `b-btn-primary-disabled-hover-*.png` |
| b2 | 비활성 `.btn-strong` hover | pass | 대상은 픽스처 503 뒤 비활성인 `reg-open`. L #1369e9 · D #92c2ff 에서 무변화 · `b-btn-strong-disabled-{rest,hover}-*.png` |
| c1 | `.chip--off` 윤곽 (라이트) | pass | 테두리 = border-strong #dfe3e8 1px(값 18이 되돌려지지 않음). 1px 링이 식별되지만 약하다: 페이지 대비 1.23:1 · `c-chip-off-primitives-light@2x.png` |
| c2 | 검색 화면 칩 윤곽 (라이트) | pass | `.search-page .chip` 테두리 = #dfe3e8 1px solid(A12 반영) · `c-search-chip-light-zoom4x.png` |
| d1 | 업로드 모달 여는 전환 | pass | 약 300ms 동안 opacity 0→1 · translateY 12.2→0px |
| d2 | × 닫기 전환(즉시 아님) | pass | `closing` 뒤 약 311ms 동안 opacity 1→0 · translateY 0→12.2px. 이어서 언마운트(+312ms). 배경 관찰은 §4-1 |
| d3 | 닫는 도중 다시 열면 입력 유지(값 2) | pass | 닫기 시작 +26ms · +271ms 두 경우 모두 언마운트 없이 되돌아왔다. 고른 파일 `design-audit.nc` 1건 유지 · `d-upload-reopen-*.png` |
| d4 | (보조) 완전히 닫힌 뒤 다시 열면 새 모달 | pass | 파일 0건 |
| d5 | 등록 확정 뒤 닫는 도중 다시 열면 새 ① | **not-run** | 픽스처에서 등록 성공에 닿을 수 없다(아래 §3-d) |
| e1 | `.dr-pop` 이 기간 칸에서 열림 (1440) | pass | 칸 왼쪽 정렬 · 칸 아래. starting-style opacity 0 · scale .96 → 1 · `e-dr-pop-open-1440-{light,dark}.png` |
| e2 | 375px 바닥 시트 | pass (다크만) | position fixed · 좌우·아래 12px · 높이 80dvh · 기준점 아래 가운데 · `e-dr-pop-sheet-375-open-dark.png` |
| f1 | 확대 | pass (키보드) | 「확대」에 초점을 두고 Enter를 눌러 0.698 → 1.396 → 1.615(한계)로 확대. 휠은 도구가 지도에 전달하지 못했다(§4-5) |
| f2 | 6px 끌기 = 안 움직임 | pass | translate x −97.5 그대로(임계 10px · `useZoomPan.ts:31`) |
| f3 | 20px 끌기 = 따라옴 | pass | −97.5 → −77.5(누른 자리부터 전량 +20) · 천천히 놓으면 관성 0 |
| f4 | 빠른 끌기·놓기 → 미끄러짐 프레임 | pass | 0 / 98 / 298 / 598ms 에 −145.0 / −74.6 / −6.8 / 0.0 |
| f5 | 경계에서 넘치지 않고 섬 | pass | 경계 0. 모든 프레임이 ≤ 0이고 단조 증가하며 498ms 에 0 도달, 1515ms 까지 0 |
| g1 | 동작 줄이기: 모달 즉시 | pass | 전환 none. × 직후 언마운트되고 다시 열면 첫 프레임부터 opacity 1 · none |
| g2 | 동작 줄이기: 관성 없음 | pass | 같은 빠르기(약 820px/s)로 놓아도 −50px 에 정지 · 1515ms 까지 불변 |
| h | 드롭 영역 dragover(값 21) | **not-run** | 지원되는 파일 끌기 방법이 없다(§3-h) |

소계: pass 24 · fail 1(a2) · not-run 2(d5 · h).

## 2. 누름·hover 계산값 (`get styles` background-color)

| 요소 | L 쉼 | L hover | L 누름 | D 쉼 | D hover | D 누름 | D hover:누름 |
|---|---|---|---|---|---|---|---|
| `.btn` (primitives) | #ffffff | #f9fafb | #e8ecf2 | #1a222c | #202b37 | #2b3745 | 1.19:1 |
| `.btn-primary` | #1369e9 | #0f62e0 | #0f62e0 | #92c2ff | #add2ff | #add2ff | **1.00:1** |
| 카탈로그 행 td | 투명 | rgba(105,112,119,.08) | #e8ecf2 | 투명 | #2b3745 | #45566a | 1.61:1 |
| 메뉴 링크 「연구실」 | 투명 | rgba(105,112,119,.08) | #e8ecf2 | 투명 | #2b3745 | #45566a | 1.61:1 |
| 현재 탭 「데이터셋」 | #ffffff | #ffffff | #e8ecf2 | #1a222c | #1a222c | #45566a | 2.13:1(쉼 대비) |
| `.dr-nav button` | #ffffff | rgba(105,112,119,.08) | #e8ecf2 | #1a222c | #2b3745 | #45566a | 1.61:1 |
| `.dr-useg button`(「월」) | #ffffff | rgba(105,112,119,.08) | #e8ecf2 | #1a222c | #2b3745 | #45566a | 1.61:1 |
| `.dr-cal-d`(「1」) | 투명 | #e2eeff | #bad7ff | 투명 | #284769 | #315779 | 1.26:1 |

- 라이트 hover:누름 = `.btn` 1.13:1 · 행(합성 #f3f4f4) 1.08:1 · `.dr-cal-d` 1.26:1.
- 장면: `primitives` · `catalog`(audit-design) · `audit-upload.html` ② 메타데이터 단계의 기간 팝오버.

## 3. 항목별 근거

### c. 칩 윤곽
- `primitives` `.chip--off`: 라이트 바탕 #e8ecf2 · 테두리 #dfe3e8 1px solid · 글자 #565c63 · 페이지 #f9fafb. 다크 바탕 #2b3745 · 테두리 #45566a · 페이지 #11161d(링 대 페이지 2.41:1).
- `search` `.search-page .chip`(5개): 라이트 바탕 #e8ecf2 · 테두리 #dfe3e8 1px solid · 글자 #434950.
- 링 명암비(라이트): 대 페이지 #f9fafb 1.23:1 · 대 흰 카드 1.29:1 · 대 칩 채움 1.09:1. 종전 링 #e8ecf2 는 페이지 대비 1.13:1 이었다. 확대 크롭에서 링이 보이지만 약하다.

### d. 업로드 모달 (`scene=catalog` → GNB 「업로드」)
- 이 진입은 API 소스 모달이다. 픽스처 fetch 가 503 을 주므로 파일을 고르면 「로그인 상태를 다시 확인해 주세요」가 뜬다(`d-upload-picked-light.png`). 「입력」은 고른 파일 카드 1건으로 확인했다.
- 프레임 기록 발췌: `d-g-probe-modal-log.json`.
  - 여는 전환: +2ms opacity 0.00 · 12.2px → +99ms 0.73 · 3.3px → +265ms 1.00 · 0.05px → +316ms none.
  - × 닫기(파일 없음): `closing` → +61ms 0.59 → +144ms 0.16 → +311ms 0.00 → +312ms 언마운트. 중간 캡처 `d-upload-closing-mid-light.png`.
  - 닫는 도중 다시 열기: +26ms(opacity 0.96에서 되돌아옴 → 다음 프레임 1.00) · +271ms(0.00에서 되돌아옴 → 약 300ms에 걸쳐 1.00). 두 경우 모두 unmount 기록이 없다. 800ms 뒤 `.filecard` 1 · `data-state` 없음 · `inert` 없음. 캡처 `d-upload-closing-150ms-light.png`(거의 투명) → `d-upload-reopen-150ms-kept-light.png`(파일 유지).
- d5 not-run 사유: 등록 성공(`closeAfterCommit`)이 필요하다. audit-design 진입은 API 소스(503)이고, `audit-upload.tsx` 는 `register` 가 던지며 `onClose` 가 빈 함수라 다시 열 부모가 없다. `GridAttachEntry` 반영 성공도 픽스처 장면에 없다. 대체 근거는 기존 시험 「F-int 1 UploadEntry / GridAttachEntry」(jsdom)뿐이며 실화면 근거는 아니다.

### e. 기간 팝오버 (`audit-upload.html` → 파일 고르기 → 등록 → 분류 3칸 → 다음)
- 1440: 클릭 직후 opacity 0 · `matrix(0.96…)` → 400ms 뒤 opacity 1 · none. 칸 x 612.6 · y 459.2 · h 54.5, 팝오버 x 612.6 · y 549.8 · 576×465(position absolute).
- 375(다크): position fixed · x 12 · y 150.4 · 351×649.6(아래 끝 800 = 812 − 12) · transform-origin 175.5px 649.594px(아래 가운데) · opacity 0 → 1. Esc 로 팝오버만 닫히고 모달은 남는다(`.dr-pop` 0 · `.modal-takeover` 1).
- 라이트 375 시트는 찍지 않았다.

### f·g. 끌기·관성 (`audit-selected-preview.html?tiles=1` · 375×812 · 지도 뷰포트 317×231)
- 확대 한계 1.615(= 512 / 317). 한계 배율에서 이동 범위는 translate x −195 … 0.
- 빠른 끌기: (60,560)에서 누르고 약 66ms 동안 +50px 끈 뒤 곧바로 놓았다. 놓는 속도 약 760px/s이고, 투영 목표가 경계 0으로 잘린다(145px 앞).

| 놓은 뒤 ms | 15 | 32 | 98 | 198 | 298 | 398 | 482 | 498 | 598 | 1515 |
|---|---|---|---|---|---|---|---|---|---|---|
| translate x (px) | −145.0 | −132.5 | −74.6 | −24.3 | −6.8 | −1.8 | −0.6 | 0.0 | 0.0 | 0.0 |

- 첫 프레임 속도 약 735px/s(놓는 속도와 이어짐). 최대값 0 = 경계로 넘침 0. 원본 기록은 `f-g-probe-pan-log.json` 이다(속도 인계·동작 줄이기 두 번의 놓기 포함).
- g2: `set media light reduced-motion` 에서 (200,560)부터 −50px 을 약 61ms 에 끌어 놓았다. 15–1515ms 모든 프레임이 −50.
- 스크린샷(`f-drag-*`, `f-glide-a/e`, `g-rm-fling-*`)은 조작 시점 기록일 뿐이다. 이 픽스처는 지도 타일이 그려지지 않아 움직임이 그림으로 보이지 않는다. 판정은 프레임 기록으로 했다.

### h. 드롭 영역 not-run 사유
- agent-browser 0.27 CLI 에는 파일(DataTransfer Files)을 끌어 오는 명령이 없다. `drag` 는 끌 수 있는 요소가 필요한데 모달 안에는 그런 요소가 없다. 합성 DragEvent 는 `eval`(금지)이나 조작형 init script 가 필요해 읽기 전용 원칙 밖이다.

## 4. 관찰(판정 밖 · 후속 판단용)

1. 모달이 닫히는 약 300ms 동안 **뒤판 어둡힘은 그대로이고**, 언마운트 순간 한 번에 사라진다(`d-upload-closing-mid-light.png` · `-closing-150ms-` vs `d-upload-closed-light.png`). 뒤판 계산값은 재지 않았고 스크린샷 관찰이다.
2. 비활성 `.btn-strong`(`reg-open`)의 계산값은 cursor pointer · opacity 1 이다. hover 는 막혔지만 모양은 활성과 같다.
3. 1440×900 에서 `.dr-pop`(아래 끝 1014.8px)이 뷰포트 아래로 넘친다. 아래쪽은 모달 발판에 가려 스크롤해야 보인다(`e-dr-pop-open-1440-light.png`).
4. `audit-selected-preview` 픽스처 한정 관찰:
   - 처음 연 직후에는 「확대」·휠이 무반응이다. 창 크기가 바뀐 뒤에야 한계가 잡혔다(`maxScale` 1 → 1.615). 픽스처 `mapGeometry` 가 즉시 응답하는 타이밍 탓으로 보이며 제품 재현은 확인하지 않았다.
   - 375 에서는 HUD 문구가 확대 단추를 덮는다(스타일 없는 픽스처 페이지).
5. 도구 한계: `agent-browser mouse wheel` 이벤트의 target 이 `main.detail-page` 였다(프로브 기록). 그래서 휠 확대는 재지 못했다.
6. 파일을 골랐으나 픽스처 503 으로 실패한 상태에서 × 를 누르면 확인 없이 바로 닫혔다(`hasHumanInput` 판정 결과). 판정은 하지 않았다.

## 5. 정리·산출

- 브라우저 세션 `fixlive` · `fixprobe` · `fixpan` 을 모두 `close` 했다. preview 서버(4291)와 vite 개발 서버(4292)도 종료했다. 확인 결과: `pgrep -af "agent-browser|vite|chrom"` 0건, `agent-browser session list` 「No active sessions」, 4291·4292 LISTEN 없음.
- 저장소 밖 임시물: `/tmp/fixlive/`(batch JSON · 1KB 더미 `.nc`), `/tmp/fixlive-out`(이 폴더를 가리키는 공백 없는 심볼릭 링크). batch JSON 은 lifecycle guard 가 저장소 밖 Write 를 막아 Bash heredoc 으로 썼다.
- 이 폴더의 산출: `index.md` · `probe-init.js` · `d-g-probe-modal-log.json` · `f-g-probe-pan-log.json` · 스크린샷 PNG. 모두 미커밋이며 커밋은 오케스트레이터가 한다.
