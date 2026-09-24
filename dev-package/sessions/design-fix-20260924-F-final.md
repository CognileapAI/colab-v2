# design-fix 20260924 · 잔여 정리 레인 F-final

- 기준: `18e1b295`(통합 브랜치 `worktree-design-review-apple-20260924`) · 브랜치 `worktree-wf_46f854b8-57a-1`
- 오라클: `dev-package/prd/specs/S-DESIGN-FIX-20260924.md` 「잔여 정리 레인 F-final」 1–5 ＋ 「통합 수정」 값 19 · 결함 원문 `dev-package/sessions/design-fix-20260924-acceptance.md`
- 파일 면: `frontend/src/components/upload/upload.css` · `frontend/src/components/preview/spring.ts` · `docs/design-system.md` · `frontend/test/design-fix-20260924-{L2,F-css,F-upload}.test.ts(x)`(시험 작성 단계만) · 새 시험 `frontend/test/design-fix-20260924-F-final.test.ts` · `dev-package/sessions/design-fix-20260924-F-preview.md`(항목 5 문구만) · 이 보고서
- lifecycle: `begin --role lane-worker` task `2fcfe9c7742449bc9ac17bbac8e47f24` · 선언 게이트 6(`frontend-typecheck` · `frontend-test` · `frontend-fixture-reach` · `frontend-design-lint` · `frontend-design-lint-selftest` · `frontend-visual`)
- 커밋: `7188cee2`(시험 작성) · `23de167f`(구현 · `frontend/test/**`·`gates/**`·`contracts/**` 0 — `git show --stat` 로 확인) · 이 보고서 커밋

## 1. 항목 → 전후 → 시험

| # | 항목 | 전 | 후 | 시험 |
|---|---|---|---|---|
| 1 | A21 · 값 19 | `.dr-nav button:active` · `.dr-useg button:active` = gray-100 — 다크 gray-100 = surface-hover(#2b3745)라 누름 = hover | 두 자리 = `var(--color-surface-pressed)`(`upload.css` `.dr-nav button:active` · `.dr-useg button:active`) | L2 「WU-A4 업로드 누름 피드백」 두 고정값 갱신 · F-css 「누름 ≠ hover」 표 두 자리 × 두 테마 추가 |
| 2 | 정본 판정 대기 정리 | ⑦ 판정 대기 17(A21) 행 · ⑤ 누름 줄 「⑦ 판정 대기 17 에 둔다」 · F-css 시험이 그 임시 상태를 고정 | 행·지시 삭제(값 19 는 Ted 확정) · ⑤ 예시에 업로드 달력 두 자리 추가 · F-css 두 번째 경우 삭제 · describe 제목에서 「남은 자리는 ⑦ 판정 대기」 제거 | F-final 「⑤ 누름 줄에 판정 대기 지시 없음」 · 「⑦ 에 A21 행 없음」 |
| 3 | `.btn-strong:hover` 비활성 제외 | `.btn-strong:hover` — 비활성 단추도 hover 에서 primary-700 | `.btn-strong:where(:not(:disabled)):hover`(값 무변 · 특이도 무변 · primitives `.btn-primary` 선례) · ③ 화면 편차 목록 선택자 갱신 | F-final 「`.btn-strong` hover 선택자는 모두 `:where()` 안에서 `:disabled` 제외」 · L2 #10 선택자 갱신 |
| 4 | FU-1 | 제목 「inert 를 남긴 채 모달이 남지 않는다」, 단언 = onClose 1회뿐 | 같은 경우에 closing 부재 · 배경 inert 부재 · 문서 `[inert]` 0 단언 ＋ UploadEntry 경우(같은 틱 언마운트 · `[inert]` 0) 추가 | F-upload A17 두 경우 |
| 5 | FP-3 · FP-2 | `spring.ts` 주석 「닫힌 식`x(t)」 · F-preview 보고서 A41 행이 effect 정리 `stopInertia()` 를 A41 조치로 적음 | 「닫힌 식 `x(t)」 · A41 행 = `remeasure` 가 담당 · effect 정리는 `clampView`·`stopInertia` 안정 참조라 언마운트 때만(정정 표지) | F-final 「닫힌 식 주석 공백」 |

항목 5 근거: `useZoomPan.ts` 의 `clampView` 의존 사슬 = `boxes` → `box` · `contentSize`(모두 `[]`), `stopInertia` = `[]` — 포인터 리스너 effect(`[clampView, stopInertia]`) 정리는 언마운트 때만 돈다.

## 2. RED 증거

시험 작성 커밋 `7188cee2` 시점(제품 = `18e1b295`) `npx vitest run` 4파일 → **9 실패 · 94 통과**. 전부 단언 실패(import 오류 0).

- L2 `.dr-nav button:active { background: var(--color-surface-pressed) }` · `.dr-useg …`: `expected false to be true`
- L2 #10: `규칙 부재: .btn-strong:where(:not(:disabled)):hover (plain)`
- F-css `.dr-nav button:active ≠ .dr-nav button:hover(dark)` · `.dr-useg …(dark)`: `expected '2b3745' not to be '2b3745'`
- F-final 3: `.btn-strong:hover: expected '.btn-strong:hover' to match /:where\(…:disabled…\)/` — 첫 작성본은 `@layer` 안을 읽지 못해 「0건」으로 실패(틀린 이유) → 파서를 `@layer`·`@media` 안으로 넣고 재확인
- F-final 2: `expected '- 누름 피드백 = …' not to contain '판정 대기'` · `expected [ Array(1) ] to deeply equal []`
- F-final 5: `expected '// 미리보기 끌기를 …' to contain '닫힌 식 \`x(t)'`
- FU-1(항목 4)은 제품이 이미 맞아 처음부터 green. 변이 확인 — `UploadModal.tsx` 0초 경로에 `setClosing(true)` 를 임시로 넣으면 `expected 'closing' not to be 'closing'` 로 실패 · 변이는 되돌림(커밋 안 됨).

구현 뒤 같은 4파일 → 103 통과 · 실패 0.

## 3. 게이트

`COLAB_TASK_ID=2fcfe9c7742449bc9ac17bbac8e47f24 COLAB_VISUAL_URLS='<4 URL>' bash gates/run.sh task`(저장소 루트 · 직렬).
`frontend-visual` 대상 = audit 빌드(`npm run audit:build` → `audit:preview --port 4193 --strictPort`) · 장면 upload(`audit-upload.html`) · primitives(`audit-design.html?scene=primitives&design=full`) × (라이트 · `theme=dark`) = URL 4. 픽스처 화면이다. 면제 선언 0.

- run `9c2cfece7dbe40bcb522bdcf3e307ec3`(구현 커밋 `23de167f` · 이 보고서 작성 전) — **green 6 / red(판정) 0 / red(준비) 0**, 종료코드 0.
  - typecheck 오류 0 · frontend-test 통과 1814 · 실패 0 · fixture-reach 도달 207 · 금지 0 · design-lint 파일 21 · 다크 누락 0(면제 6) · 색 리터럴 0 · 문서 표 갈림 0 · selftest 26건 기대대로(green 6 · red 14 · red(준비) 6) · visual 페이지 3 · 13px 미만 0 · 대비<4.5 0 · 스크린샷 6장.
  - visual 「페이지 3」 = primitives 라이트·다크 URL 이 `live_audit.sh` 60자 파일 이름 절단(A37)으로 같은 이름이 되어 덮인 결과. 마지막 run 은 `theme=dark` 를 질의 맨 앞에 두어 이름을 가른다.
- 이 보고서를 쓴 뒤 같은 선언 집합을 한 번 더 돌린다(보고서 파일도 hash 대상). 그 run 의 id·계수는 `handoff --mode complete` 의 `COLAB_HANDOFF` 줄에 있다.

## 4. 원한 결과 대조

- 미달: 없음(항목 1–5).
- 초과: ⑤ 누름 줄 예시에 업로드 달력 두 자리 추가 · ③ 화면 편차 목록의 `.btn-strong:hover` 선택자 표기 갱신 · F-css describe 제목에서 임시 상태 문구 제거 · FU-1 에 UploadEntry 경우 1건 추가. 모두 파일 면 안.
- 값: 새 hex · 새 토큰 이름 0. 쓴 값 = 값 19(`--color-surface-pressed`) · 기존 primary-700.

## 5. 남은 위험 · 후속

- 다크에서 `.dr-nav button` 테두리 `--color-border-strong`(#45566a) = 누름 면 `--color-surface-pressed`(#45566a) — 누르는 동안 테두리가 면과 같은 색이 된다(종전 ⑦ 17 행이 적었던 결과). 값 19 확정의 귀결이며 새 값을 넣지 않았다. 검사: 어느 게이트에도 걸리지 않는다(누름 상태 테두리 대비를 재는 검사 없음).
- 누름(`:active`) 상태는 정적 audit 장면에 없어 `frontend-visual` 이 재지 않는다 — 이 레인의 누름·비활성 hover 변경은 CSS 원문 계측(vitest)으로만 확인했다. 실제 브라우저 누름 검증 미실행.
- `frontend/src/components/preview/useZoomPan.ts` effect 정리 주석 「리스너를 새로 걸 때 멈춘다(A41)」 도 FP-2 와 같은 오기다(정리는 언마운트 때만). 파일 면 밖이라 고치지 않았다. 검사: 어느 게이트에도 걸리지 않는다.
- A37(`live_audit.sh` 60자 절단)은 하네스 후속(spec 「통합 수정」) 그대로 — 이 레인은 URL 질의 순서로 피했다.
