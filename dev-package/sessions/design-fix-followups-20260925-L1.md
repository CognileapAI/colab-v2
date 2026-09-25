# design-fix 후속 20260925 — L1 (CSS · 문서)

spec: `dev-package/prd/specs/S-DESIGN-FIX-FOLLOWUPS-20260925.md` 부록 A(L1 행) · 부록 B · 부록 C(L1) · 부록 E(L1) · 부록 F
intent: `dev-package/intent/2026-09-25-design-fix-followups.md` 설계트리 Q1a–Q1f · Q3a · Q3c · Q5 · Q8b
기준: 브랜치 `worktree-design-fix-followups-grill` 커밋 `610a76e8`(ff-only 확인).

## 상태
- RED · GREEN · 커밋 완료. 이 파일은 게이트 실행 **전에** 확정했다 — lifecycle 증거(task_evidence)는 작업 파일 전체 hash 와 HEAD 를 담아, 게이트 뒤에 이 파일을 고치거나 커밋하면 인계가 차단된다(B0 선례). 게이트 3계수 · `frontend-visual` 판정 페이지 수는 인계 요약(`COLAB_HANDOFF`)과 이 task 의 gate-summary(Git common runtime · task `a4a559d512024a5c9d45c056b4554db0`)에 있다.
- 실행 사본: 오케스트레이터가 이 레인을 통합 워크트리(`.claude/worktrees/design-fix-followups-grill` · 브랜치 `worktree-design-fix-followups-grill`)를 cwd 로 띄웠다. 별도 레인 브랜치는 없고 커밋은 통합 브랜치에 바로 쌓였다(워크트리 신설은 하네스가 「cwd 고정 서브에이전트」로 거절). 첫 줄 ff-only 병합 = 「Already up to date」 · HEAD `610a76e8` 일치.
- lifecycle task `a4a559d512024a5c9d45c056b4554db0` · 필수 게이트 6(`frontend-typecheck` · `frontend-test` · `frontend-fixture-reach` · `frontend-design-lint` · `frontend-design-lint-selftest` · `frontend-visual`) · 범위 14 경로(부록 B L1 소유 파일 ＋ 이 보고).
- 커밋: `fdda698d`(시험 · RED) · `d14d7bfc`(제품 · 정본) · 이 보고 커밋.

## RED
- 새 시험 `frontend/test/design-fix-followups-20260925-L1.test.ts` ＋ 기존 `frontend/test/design-fix-20260924-L1.test.ts` 잠금 3곳(`.btn-primary:active` → 800 · `.btn-sm` 매체 조건 · `.gnb-upload:active` → 800) 수정 뒤 구현 전 실행: 23 실패 · 59 통과(2 파일).
- 인용: `AssertionError: 선택자 블록 수: .btn:disabled : expected +0 to be 1 // Object.is equality`.
- 첫 단언 = 대상 개수(L1 비활성 선택자 4 · 파란 채움 누름 2). 선택자 블록을 못 찾으면 블록 수 단언으로 실패한다.

## GREEN — V 별 결과
구현 뒤 L1 시험 ＋ 감시 시험(`design-fix-20260924-{L1,F-css,F-final}` · `auth` · `dashboard` · `lineage-unknown-20260907`) 7 파일: 195 통과 · 0 실패. 새 시험 단독 27 통과.

| V | 변경(file:line) | 단언 결과 |
|---|---|---|
| V1 Q1a · Q1b | `frontend/src/shell/primitives.css:41` `.btn:disabled { opacity: 0.5; cursor: not-allowed; }` · hover 비활성 제외 원문 불변(`:32` · `:36`) | 통과 — 블록 1 · 두 값 · `!important` 0 |
| V1 Q1c | `frontend/src/auth/login.css:89`–`92` 회색 채움 · `cursor: default` 제거 → 두 값 | 통과 |
| V1 Q1d | `frontend/src/components/detail/deletion.css` `.detail-page .btn-danger:disabled` 삭제(지운 값 = 새 프리미티브 규칙과 같음) | 통과 — `:disabled` 0 |
| V1 Q1e | `frontend/src/components/dashboard/dashboard.css:66` `.dash-section-label:disabled` · `:323` `.titem button:disabled` · `frontend/src/components/preview/preview.css:350` `.pv-zoom button:disabled` · `frontend/src/components/project/project.css:375` `.pj-x:disabled` | 통과 — 4 선택자 두 값 |
| V2 Q3a | `frontend/src/shell/primitives.css:37` `.btn-primary:active` · `frontend/src/shell/shell.css:249` `.gnb-upload:active` = `var(--color-primary-800)` · 주석 `primitives.css:28`–`29` | 통과 — on-primary 대 primary-800 라이트 7.56 · 다크 12.56 · hover 대 누름 라이트 1.38 · 다크 1.24 |
| V3 Q3c | `frontend/src/shell/tokens.css:199`–`203` `@media (pointer: coarse) { :root { --control-height: 44px } }`(640px 블록 뒤) · 머리 주석 `:6`–`7` · `frontend/src/shell/primitives.css:46` `@media (max-width: 640px), (pointer: coarse)` · 주석 `:42`–`43` | 통과 — coarse 블록 1 · 선언 1 · 기본 40px · 640 블록 불변 |
| V8 Q1f · Q1d · Q3a · Q5 | `docs/design-system.md:173` btn 행 · `:240` 편차 칸 · `:280` 합격선 · `:281` 누름 줄 · `:282` 비활성 줄 · `:312` ⑦-17 행 · 생성 표(토큰 · 프리미티브 표지 안) · `.agents/skills/design-review/SKILL.md:17` | 통과 — `design-docs.mjs --check` 「문서 표 갈림 0」 |
| V9 Q8b | `frontend/src/components/lineage/lineage.css` `.lin-unknown-why` 규칙 삭제 · `:166`–`167` 주석에서 클래스 이름 제거 | 통과 — 0 |

- 사전 확인(증거 아님): `gates/tools/frontend-design-lint.sh` 직접 실행 green — 토큰 파일의 `@media (pointer: coarse)` 블록을 받아들였다(spec 위험 3 해소). 증거는 아래 게이트 실행.
- 생성 표 재생성 결과(`node frontend/scripts/design-docs.mjs`): 토큰 표 `--control-height` 매체 칸에 `(pointer: coarse): 44px` · `.btn` 규칙 3 → 4 · `primitives.css` 규칙 36 → 37 · 선언 123 → 125 · `.btn-sm` 매체 조건 · 입력 sha256 2개 갱신.
- `--control-height` 사용처(spec 위험 11): `var(--control-height)` 17줄 · 9 파일 — `project.css` 5 · `primitives.css` 3 · `preview.css` 2 · `login.css` 2 · `dashboard.css` · `search.css` · `catalog.css` · `shell.css` · `upload.css` 각 1. 조사의 18줄은 `tokens.css` 정의 줄을 더한 수로 보인다(정의 줄 = 기본 · 640 · 이번 coarse).
- 화면 층이 `.btn` 계열에 cursor · opacity 를 정하는 규칙(프리미티브 비활성 규칙을 이기는 자리): 주석을 걷고 전 CSS 를 훑어 1건 — `frontend/src/components/detail/detail.css` `.detail-page label.btn { cursor: pointer }`. `label` 은 `:disabled` 가 되지 않아 영향 0.

## 게이트
- 실행 = 저장소 루트에서 `COLAB_TASK_ID=a4a559d512024a5c9d45c056b4554db0 COLAB_VISUAL_URLS=<62 URL> bash gates/run.sh task` 1회 · audit 빌드(`npm --prefix frontend run audit:build`) ＋ `audit:preview -- --port 4291 --strictPort`. 62 URL = 디자인 30장면 × 라이트/다크 ＋ `audit-upload.html` × 라이트/다크(B0 보고 목록).
- 지시문과 다른 점: `COLAB_GATE_REPORT_DIR` 를 주지 않았다. `gates/run.sh:46`–`49` 가 task 실행에서 이 값이 현재 run 의 runtime 보고 경로와 다르면 exit 78(「explicit report directory differs from current task run」)로 멈추고, run 경로는 `gate-start` 가 새 run_id 로 매번 새로 정한다(`scripts/harness/hooks/lifecycle_contract.py:434`–`438`) — 미리 맞출 수 없다. gate-summary 는 runtime 보고 폴더(Git common dir)에 선다.
- 3계수 · 판정 페이지 수 = 인계 요약 참조(위 상태 절 사유).

## 하지 않은 것
- L2 몫(`upload.css` · TSX · 픽스처 · `scenes.json`) 0.
- 실브라우저 computed 측정(부록 D) — E 단계 몫.
- 캡처(`visual:capture`) — E 단계 몫(`fixfu0925-final`).
- 초과분: 시험 2건 추가 — 주석 문장이 새 값과 맞는지(spec 위험 9 · `primitives.css` 「primary 는 primary-700 유지」 0 · `tokens.css` 구조 문장에 coarse 분기). 부록 C 표 밖이다.

## 후속
- ⑦-17 빨간 삭제 단추 hover · 누름 없음 — 오늘 렌더 = 기본 = hover = 누름 · 선택지 = 새 빨간 단계 토큰 · 전역 `.btn-danger` · 출처 = intent Q3b · Q5. 정본 `docs/design-system.md:312` 에 적었다. 자리 = 다음 design-review §0 「이월 · 판정 대기」.
- 우려 1(768 터치 넘침): 이 레인은 실측하지 않았다(E 부록 D 6 · dev 768 터치 Q7b). 넘침은 E 또는 dev 확인에서 화면 · 폭 · 스크린샷으로 기록한다.
- 이 레인이 통합 워크트리에서 돌아 별도 레인 브랜치가 없다 — 오케스트레이터의 「레인 브랜치 병합」 단계는 이 레인에 대해 할 일이 없다. 스폰 격리 설정은 하네스 쪽 확인 항목이다.
- 지시문의 `COLAB_GATE_REPORT_DIR=dev-package/reports/<회차>/<레인>` 규약(lane-worker 역할 문서 「게이트」 절)은 `colab-task/2` task 실행과 맞지 않는다(위 게이트 절). 이 불일치는 어느 게이트에도 걸리지 않고 실행 시 78 로만 드러난다 — 역할 문서 · 지시문 서식 정정은 하네스 쪽 항목이다.
