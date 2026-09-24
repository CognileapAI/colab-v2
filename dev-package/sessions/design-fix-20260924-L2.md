# design-fix 20260924 · L2 업로드 — 레인 보고서

- spec: `dev-package/prd/specs/S-DESIGN-FIX-20260924.md` §1 · §3 · §4 「L2」 · §5 · 「확정 값」 1 · 2 · 3 · 7 · 17 · #10
- 기준: `e8fc4e13` (브랜치 `worktree-design-review-apple-20260924`) — `git merge --ff-only e8fc4e13` 결과 이미 같은 HEAD
- 레인 브랜치: `worktree-agent-abbf1561508ff5c53`
- lifecycle task: `32e822fa377b4f23b5daf376f5f1b192` (lane-worker · 선언 게이트 5종: frontend-typecheck · frontend-test · frontend-fixture-reach · frontend-design-lint · frontend-visual)
- 준비(3-0): `frontend/` 에서 `npm ci` 종료 0

## 1. 항목별 before → after

| # | before | after | 파일 | 커밋 |
|---|---|---|---|---|
| 10 | `.btn-strong:hover { background: var(--color-gray-50) }` — 다크 글자 대비 1.05/1.10:1 | `background: var(--color-primary-700)` — on-primary 대비 L 5.46 · D 10.12(시험이 토큰에서 다시 계산) | `upload.css` | `4667f4ef` |
| WU-A4 | 업로드 화면 `:active` 0 | `.btn-strong:active` primary-700 · `.dr-nav button:active` gray-100 · `.dr-cal-d:active` primary-200 · `.dr-useg button:active` gray-100(`.on` 규칙 앞 — `.on` 은 누르는 중에도 primary-600) · `.dr-field:active` 테두리 primary-600 (값 17) | `upload.css` | `e232181b` |
| 2 | `.dr-pop` 전환 없음 · 기준점 없음(즉시 나타남) | `transform-origin: top left` · `transition: opacity var(--ease), transform var(--ease)` · `@starting-style { opacity: 0; transform: scale(0.96) }` · 640px 이하 바닥 시트 `transform-origin: bottom center` (값 3). 닫기는 즉시 · TSX 0 | `upload.css` | `75213efb` |
| 4 | 드롭 영역이 끌기 중 반응 없음 | `FileDropCard` 라벨이 dragenter/dragleave 깊이를 세어 `is-dragover` 부여 · 깊이 0(바깥)·drop 에서 해제 · dragOver `preventDefault` ＋ `stopPropagation` 유지 · CSS `.dropzone.is-dragover` · `.up-empty .dropzone.is-dragover` = 테두리 primary-600 · 바탕 primary-50 (값 7) · 분석 장면 규칙이 같은 특이도로 뒤에 서 그대로 이김 | `FileDropCard.tsx` · `upload.css` | `84101e72` |
| 1 | `@keyframes up-rise`(0.46s ease · opacity 0.4 → 1) · 닫기는 즉시 언마운트 · `props.onClose` 직접 호출 7곳 | `transition: transform 0.3s cubic-bezier(0.2, 0, 0, 1), opacity 0.3s …` ＋ `@starting-style`(translateY(3%) · opacity 0) ＋ `[data-state="closing"]` 같은 끝 모양 (값 1). 닫기 요청 함수 `beginClose` 하나 → 계산된 전환 시간 0 이면 같은 틱에 `finishClose` · 아니면 `data-state="closing"` → 모달 자신의 `transitionend` 또는 타이머(전환 시간 ＋ 50ms) → `finishClose` → `props.onClose`(파일 안 1곳). 닫는 중 Esc · 배경 누름 무시. 값 2: 닫는 중 배경 `pointer-events: none` · 부모 2곳이 「열림」(`open`)·「그려 둠」(`rendered`)을 따로 들고 닫는 중 단추 → `open` 복귀 → 모달이 closing 해제(입력 유지). 완전히 닫힌 뒤 다시 열면 언마운트 리셋으로 처음 장면(PRD-13) | `upload.css` · `UploadModal.tsx` · `UploadEntry.tsx` · `GridAttachEntry.tsx` | `0bae1c4d` |

- `UploadModal` 공개 인터페이스 증가: 선택 prop 2개 `open?` · `onCloseStart?`(주지 않으면 종전과 같이 열림으로 본다). `onClose` 의 뜻 = 「전환이 끝난 뒤 1회」.

## 2. 수용 기준 대조 (spec §4 「L2」)

| 단언 | 시험(`frontend/test/design-fix-20260924-L2.test.tsx`) | 결과 |
|---|---|---|
| #1 F6 — `props.onClose` 직접 호출 0 · discard 포함 모든 닫기 경로가 닫기 요청 함수 하나 | `advisor ① F6` 묶음 2건(주석 제거 원문에서 `props.onClose` 1곳 · `discard: beginClose`) | green |
| #1 CSS — `up-rise` 0 · transition(값 1) · `@starting-style` 시작 모양 · closing 끝 모양 · 닫는 중 배경 `pointer-events: none` | `#1 CSS` 5건 | green |
| #1 동작 — 0.3s 스텁: closing 잔존 → transitionend 뒤 언마운트(onClose 1회) · transitionend 없이 350ms 에 onClose · 여는 도중 닫기 → 곧바로 closing · 전환 0 이면 같은 틱 언마운트 | `#1 동작` 8건(＋ 자식 transitionend 버블 무시 · 닫는 중 Esc/배경 무시) | green |
| #1 값 2 — 닫는 중 업로드 단추 → closing 해제 · 입력 유지 · onClose 0회 · 완전히 닫힌 뒤 다시 열면 처음 | `#1 값 2` 2건 | green |
| 기존 닫기 시험 수정 없이 green — `prd34-close-copy-20260907`(감시 `:352` 포함) · `register-steps-20260907`(PRD-13 ⑥) | 전체 vitest | green · 두 파일 diff 0 |
| #2 — `.dr-pop` transform-origin · 전환 var(--ease) · `@starting-style` · 640px 이하 bottom center | `#2` 3건 | green |
| #4 — dragEnter 부여 · 자식 짝 유지 · 바깥 dragLeave 해제 · drop 뒤 해제 · dragOver preventDefault ＋ stopPropagation · CSS 두 블록 값 7 | `#4 CSS` 3건 ＋ `#4 동작` 4건 | green |
| #10 — `.btn-strong:hover` primary-700 · on-primary 대비 두 테마 ≥ 4.5 | `#10` 2건 | green |
| WU-A4 — 5개 선택자 `:active`(값 17) | `WU-A4` 6건(＋ `.on` 순서) | green |

- RED 확인(시험 작성 커밋 `8ae40b65` 시점): 35건 중 31 실패 · 4 통과(회귀 고정 — #10 대비 · 전환 0 즉시 닫기 2 · dragOver 버블 차단). 실패 사유 예: `규칙 부재: .modal.modal-takeover (starting-style)` · `expected [ 'props.onClose', …(6) ] to have a length of 1 but got 7` · `expected "vi.fn()" to be called +0 times, but got 1 times`.

## 3. 시험 수

| 시점 | Test Files | Tests |
|---|---|---|
| before(`e8fc4e13` · `npx vitest run`) | 130 passed | 1613 passed |
| after(`0bae1c4d` · `npx vitest run`) | 131 passed | 1648 passed(＋35 = 새 파일) |

- 시험 작성 커밋 `8ae40b65` 이후 `frontend/test/**` 변경 0(`git diff 8ae40b65 -- frontend/test` 빈 출력).

## 4. 게이트 3계수

### 4-1. 단독 실행(task 비결합 · 커밋 `0bae1c4d` · 저장소 루트 `bash gates/run.sh <게이트>` 하나씩)

| 게이트 | 시작(UTC) | green / red(판정) / red(준비) | 근거 |
|---|---|---|---|
| frontend-design-lint | 2026-09-24T15:40:49Z | 1 / 0 / 0 | `dev-package/reports/design-fix-20260924/L2/design-lint/gate-summary.json`(무시 대상 · 커밋 안 함) · 요약줄 「색 리터럴 0(면제 1) · 인라인 0(변수 대입 7) · 문서 표 갈림 0」 |
| frontend-typecheck | 2026-09-24T15:40:57Z | 1 / 0 / 0 | `…/L2/typecheck/gate-summary.json` |
| frontend-fixture-reach | 2026-09-24T15:41:16Z | 1 / 0 / 0 | `…/L2/fixture-reach/gate-summary.json` |
| frontend-test | 2026-09-24T15:54:00Z | 1 / 0 / 0 | `…/L2/test/gate-summary.json` · Test Files 131 · Tests 1648 passed |
| frontend-visual | — | 0 / 0 / 1 | red(준비 · 78) — 호스트 뮤텍스 900초 대기 초과(다른 저장소 사본 `32 CoLAB-v2` · `30 CoLAB-v2` 세션의 serial 게이트가 잡고 있었다). 판정되지 않았다. summary JSON 없음 |

- frontend-visual 입력: audit 빌드(`frontend/` 의 audit:build 종료 0) → 이 레인의 audit:preview(포트 4187) · `COLAB_VISUAL_URLS` = `/audit-design.html?design=full&scene=` ＋ `upload` · `upload-classify` · `upload-metadata` · `upload-link`(spec §5 L2 목록). 4187 은 먼저 다른 레인(`agent-a6ad039bf930a5172`)이 쓰고 있어 풀린 뒤 띄웠다.

### 4-2. task 결합 실행(최종 증거)

- `COLAB_TASK_ID=32e822fa377b4f23b5daf376f5f1b192 bash gates/run.sh task` — 선언 5종을 순차 1회. 결과 3계수와 run_id 는 레인 최종 메시지의 `COLAB_HANDOFF` 줄에 있다(이 보고서 커밋 뒤에 돌리므로 여기 적지 않는다 — 적으면 실행 전후 파일 hash 가 갈린다).

## 5. 하지 않은 것

- 실화면 증거(§4 「실화면 증거」 #1 · #2 · #4 · #10 · WU-A4)는 통합 단계 몫이다(advisor ① F3) — 이 레인은 찍지 않았다. #4 는 agent-browser 가 OS 파일 끌기를 만들 수 없으면 미실행으로 넘어간다(spec 표).
- 캡처 대조(`visual:capture` `fix0924-L2` 대 `fix0924-base`) 미실행 — 기준 캡처 `fix0924-base` 는 spec §3 순서 3 에서 오케스트레이터가 찍는 것이고 이 레인 워크트리에 없다.
- `docs/design-system.md` ③ 화면 편차 목록의 `.btn-strong:hover` 갱신은 L1 몫(spec §3) — 손대지 않았다.
- `.btn-strong:active` 와 `:hover` 가 같은 값(primary-700)이다 — 값 17 확정대로 두었다(파란 채움 선례 `.btn-primary:active` 와 같음).
- 배경(어두운 막 `.mb-takeover`)의 열기·닫기 전환은 넣지 않았다 — 값 1 은 모달 본체만 말한다. 닫기 끝에 막이 한 번에 사라진다(아래 부수 변화).
- `test-file-guard` 훅: 이 세션의 Claude 프로세스 환경에 `COLAB_FIX_LANE` 이 없어(`echo` 로 unset 확인) 구현 단계에서 훅이 무장되지 않았다. 대신 구현 단계에서 시험 파일을 쓰지 않았고 그 사실을 위 diff 로 확인했다.

## 6. 부수 변화

- 닫기 동작이 0.3초 늦어진다(전환 시간이 있을 때). 그 동안 모달은 DOM 에 남고 `data-state="closing"` 이다 — 이 속성을 읽는 기존 코드·시험은 없다.
- 등록·반영 성공 뒤 닫기도 같은 전환을 탄다(`beginClose(); navigate(…)`). 성공 직후 0.3초 안에 업로드 단추를 다시 누르면 방금 끝난 모달이 되돌아온다(값 2 의 일반 규칙). 확인 필요 여부는 advisor ③ 입력.
- 닫기 전환 중 `.modal-takeover` 에 transform 이 걸려 안쪽 `position: fixed` 요소(`.reg-actions` · 640px 이하 `.dr-pop`)의 기준이 0.3초 동안 모달이 된다. 쉬는 상태(transform 없음)에서는 종전과 같다.
- 막(overlay)은 전환하지 않아 닫기 끝에 한 번에 사라진다 · 열기 때도 막은 즉시 선다(종전과 같음).
- 간격·치수 변화 0 — 이 레인의 CSS 변경은 색·전환·기준점만이다.
