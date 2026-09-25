# design-fix 후속 20260925 — L2 (업로드 · upload.css · TSX · 픽스처)

spec: `dev-package/prd/specs/S-DESIGN-FIX-FOLLOWUPS-20260925.md` 부록 A(L2 행) · 부록 B · 부록 C(L2) · 부록 D 7–8 · 부록 E(L2) · 부록 G
intent: `dev-package/intent/2026-09-25-design-fix-followups.md` 설계트리 Q1e · Q2a · Q2b · Q2d · Q2f · Q3a · Q4 · Q7c · Q8a(＋0개 줄) · Q8b · Q8e
기준: 브랜치 `worktree-design-fix-followups-grill` 커밋 `6e3ae9d3`(L1 커밋 포함 · 진입 대조 일치 · 미추적은 `dev-package/reports/design-fix-followups-20260925/` 하나).

## 상태
- RED · GREEN · 커밋 완료. 이 파일은 게이트 실행 **전에** 확정했다 — lifecycle 증거가 작업 파일 hash 와 HEAD 를 담아 게이트 뒤 수정 · 커밋은 인계를 막는다(L1 선례). 게이트 3계수 · `frontend-visual` 판정 페이지 수는 인계 요약(`COLAB_HANDOFF`)과 이 task 의 gate-summary(Git common runtime · task `3f614cf2bdf34933b529a1375fc82d25`)에 있다.
- 실행 사본: 통합 워크트리(`.claude/worktrees/design-fix-followups-grill`)에서 돌았다. 별도 레인 브랜치 없음 · 커밋은 통합 브랜치에 쌓였다.
- lifecycle task `3f614cf2bdf34933b529a1375fc82d25` · 필수 게이트 5(`frontend-typecheck` · `frontend-test` · `frontend-fixture-reach` · `frontend-design-lint` · `frontend-visual`) · 범위 13 경로(부록 B L2 소유 파일 ＋ 이 보고 · `RegisterArea.tsx` 는 선언만, 변경 0).
- 커밋: `c9e6ae0c`(시험 · RED) · `ab9ec0b2`(제품 · 픽스처) · 이 보고 커밋.

## RED
- 새 시험 `frontend/test/design-fix-followups-20260925-L2.test.tsx` ＋ 기존 시험 3곳 수정 뒤 구현 전 실행(4 파일): 19 실패 · 68 통과.
- 인용: `AssertionError: 선택자 블록 수: .thumbrow .th-slot:disabled : expected +0 to be 1 // Object.is equality`.
- 첫 단언 = 대상 개수(비활성 선택자 2 · 파란 채움 누름 1 · 팔레트 경우 6). 선택자 블록을 못 찾으면 블록 수 단언으로 실패한다.
- 기존 시험 수정: `frontend/test/design-fix-20260924-L2.test.tsx:227`(`.btn-strong:active` → primary-800) · `frontend/test/design-fix-20260924-F-ci.test.tsx:124`–`134`(0개 = 안내 없음 · `UNAVAILABLE` · 「다시 시도」 있음) · `frontend/test/design-fix-20260924-F-preview.test.tsx:342`(제목 「16ms 간격으로 11 · 1 · 1px」 · 단언 불변).

## GREEN — V 별 결과
구현 뒤 L2 시험 4 파일 ＋ 감시 시험(`upload-transfer` · `design-fix-20260924-F-int` · `register-steps-20260907` · `close-guard-20260905`) 8 파일: 155 통과 · 0 실패. `npm run typecheck` · `npm run audit:build`(`tsconfig.audit.json` 포함) 통과.

| V | 변경(file:line) | 단언 결과 |
|---|---|---|
| V1 Q1e | `frontend/src/components/upload/upload.css:435` `.thumbrow .th-slot:disabled` · `:215` `.regsteps button:disabled` = opacity 0.5 · cursor not-allowed · `:434` 격자 칸 hover = `.thumbrow .th-slot:where(:not(:disabled)):hover` | 통과 — 2 선택자 두 값 · hover 선택자 1 · `.btn-strong` 규칙에 cursor · opacity 0 |
| V2 Q3a | `upload.css:329` `.btn-strong:active` = `var(--color-primary-800)` · 주석 `:327`–`328` | 통과 |
| V4 Q2a | `upload.css:317` `.confirm-back .modal` · `:577` `.modal.pvx` = `box-shadow: none` ＋ `border: 1px solid var(--color-border-strong)` | 통과 — `primitives.css` `.modal` 그림자 `var(--shadow-sm)` 불변 |
| V5 Q2b | `upload.css:19` 뒤판 `transition: background-color 0.3s cubic-bezier(0.2, 0, 0, 1)` · `:35` `@starting-style` 뒤판 `background-color: transparent` · `:39` closing 규칙에 `background-color: transparent`(`pointer-events: none` 유지) | 통과 — 본체 transition 원문 불변 · JS 변경 0 |
| V6 Q2d | `frontend/src/components/upload/PeriodCalendarPopover.tsx:97`–`100` 마운트 1회 `rootRef.current?.scrollIntoView?.({ block: 'nearest' })` · `:131` ref · `upload.css:513` `.dr-pop` `scroll-margin-bottom: 88px`(등록 본문 아래 여백 값 재사용 · 우려 2 ⓐ) | 통과 — 기간 칸 누름 → 1회 · 대상 = 팝오버 루트 · smooth 아님 · 팝오버 안 조작 뒤 추가 0 · API 없는 jsdom 예외 0 |
| V7 Q2f · Q8a | `frontend/src/components/upload/PreviewPanel.tsx:524` 안내 조건 `length > 0 && length !== 3` · `:166` 0개 → `setError(UNAVAILABLE)` · `:98` 회차 상태 · `:178` 효과 deps · `:601`–`613` 「다시 시도」(`btn btn-sm` · 표시 = `error && palettes?.length === 0` · 누르면 오류 해제 ＋ 재조회) | 통과 — 0 · 1 · 2 · 3 · 4 · 실패→재시도(조회 2회 · 3개 성공 뒤 오류 0 · 그리기 활성) · 0개 재시도 · 그리기 실패 오류에 「다시 시도」 0 |
| V9 Q8b · Q8e | F-preview 제목(위 RED 절) · `frontend/src/components/upload/UploadModal.tsx:12`–`14` 머리 주석 「새 부모는 `useUploadModalPresence` … 필수」 | 통과 |
| V10 Q4 | `frontend/audit-upload.tsx:44`–`55` `?register=ok` 분기(등록 · 반영 성공 모의 · 계보 모의) · `:60` 실제 부모 `UploadEntry` ＋ `GridAttachEntry` · 질의 없으면 기존 `UploadModal`(등록 실패 · 빈 닫기) 그대로 · `frontend/scripts/visual-baseline/scenes.json:893` 장면 `upload-register-ok`(첫 동작 = 업로드 단추 누름 → 모달 대기) ＋ notes 1줄 | 통과 — typecheck · audit 빌드 · 기존 업로드 4장면 질의 `{}` 불변 · F-int 1 두 시험 수정 없이 green |
| V10 Q7c | `frontend/audit-design.tsx:234`–`236` `?mismatch=1` 일 때만 catalog 첫 행 `processingLevelMismatch: true`(우려 3 ⓐ) · 질의 없으면 `undefined` → 기본 `FIXTURE_ROWS` | 기본 장면 불변(질의 기반) · 계측은 E |

- 실브라우저 확인(증거 보강 · E 측정 대체 아님): audit 빌드 `http://127.0.0.1:4291/audit-upload.html?register=ok` 를 agent-browser 로 열어 두 입구 단추(「업로드」 · 「기준 격자 추가」)를 보고 「업로드」 누름 → `[data-testid=upload-backdrop]` computed `transition-property: background-color` · `transition-duration: 0.3s` · `transition-timing-function: cubic-bezier(0.2, 0, 0, 1)` · `background-color: rgba(15, 20, 28, 0.45)`(열린 뒤). 세션 종료.
- 우려 3 ⓐ 나머지 4 상태(계정 관리 모달 층 · 열 메뉴 자간 · 다크 「필수」 · 닫는 중 `inert`)는 자료 추가 없이 기존 장면 ＋ 조작(누름)으로 열린다 — 계정 관리(`scene=account-admin` 기존 fetch 모의) · 열 메뉴(`scene=catalog` 열 머리 누름) · 다크 「필수」(`audit-upload.html?theme=dark` 등록 열기) · 닫는 중(`audit-upload.html` × 누름). 1회 계측은 E(부록 D 8).

## 게이트
- 실행 = 저장소 루트에서 `COLAB_TASK_ID=3f614cf2bdf34933b529a1375fc82d25 COLAB_VISUAL_URLS=<4 URL> bash gates/run.sh task` 1회 · `COLAB_GATE_REPORT_DIR` 없음(spec 부록 E) · audit 빌드 ＋ `audit:preview -- --port 4291 --strictPort`.
- 4 URL = `audit-upload.html` · `audit-upload.html?theme=dark` · `audit-upload.html?register=ok` · `audit-upload.html?register=ok&theme=dark`(부록 E L2 열). 등록 성공 장면의 첫 화면 = 두 입구 단추 화면이다(모달은 동작 뒤라 캡처 대조 · 부록 D 가 본다).
- 3계수 · 판정 페이지 수 = 인계 요약 참조(위 상태 절 사유).

## 하지 않은 것
- L1 파일 0 · `RegisterArea.tsx` 변경 0(스크롤 호출은 팝오버 마운트에 두었다).
- 실브라우저 computed 전수 측정(부록 D 1–8) · 캡처(`visual:capture` · `fixfu0925-final`) · 캡처 대조 — E 단계 몫.
- 768 터치 넘침(우려 1) 실측 — E · dev 확인 몫.
- 초과분: 시험 4건 — `.btn-strong` 규칙 cursor · opacity 0(부록 C V1 에 있음) 외에 ⑴ 0개에서 「다시 시도」 재조회 ⑵ 「다시 시도」 클래스 = `btn btn-sm` ⑶ 픽스처 기본 동작 원문 불변 ⑷ `scenes.json` 기존 업로드 4장면 질의 불변. 부록 C 표 밖이다(위험 8 대응 · 우려 4 ⓐ 확인). `scenes.json` notes 1줄.
- 「다시 시도」 누름 때 `palettes` 를 `null`(조회 중)로 되돌린다 — 재조회 동안 단추 · 오류가 사라지고 결과로 다시 선다. 판정 문구(「오류 해제 ＋ 재조회」) 밖의 세부다.

## 후속
- `.dr-pop` 여는 순간 `@starting-style` `scale(0.96)` 상태의 박스로 스크롤 양이 정해진다(spec 위험 6). 여백 88px 대 고정 단추줄(12 ＋ 40 ＋ 12 ＋ 1px ≈ 65px) 차이 약 23px 이 그 오차를 덮는지는 E 가 1440×900 에서 팝오버 아래 끝 대 `.reg-actions` 위 끝으로 잰다. 640px 이하 하단 시트(`position: fixed`)에서 스크롤 호출의 영향도 E 375 대조 항목이다.
- 등록 성공 장면의 캡처 동작은 모달 열기까지다. 「등록 → 0.3초 안 닫기 → 다시 열기」는 입력 동작 수가 많아 캡처 동작(agent-browser 호출 단위)으로는 0.3초 창을 맞추지 못한다 — E 부록 D 7 에서 측정 도구로 한 번 잰다. 영구 장면 여부는 하네스 intent H11.
