# design-fix 20260924 · 통합 단계 기록

- 최종 트리: 브랜치 `worktree-design-review-apple-20260924` @ `407fbcab`(develop `7acd0fce` ＋ audit ＋ L1·L2·L3 ＋ F-css·F-upload·F-preview ＋ F-final ＋ F-int · 병합 충돌 0).
- 증거 폴더: `dev-package/reports/design-review/20260924/fix/`(이 커밋은 `dev-package/**` 만 바꾼다 — 게이트가 잰 제품 트리는 `407fbcab` 그대로).

## 게이트 (호스트 단독 · 1회)

- task `89f9c962114245dca4f46b3f2616a5de` · run `fd95a6a16eb94572a7b397d3ada64187` · commit `407fbcab` · tree `e8901156` — frontend-typecheck · frontend-test · frontend-fixture-reach · frontend-design-lint · frontend-design-lint-selftest · frontend-visual = **green 6 / red(판정) 0 / red(준비) 0**. 증거 = git common dir `colab-harness/3dd64333…/89f9c962…/fd95a6a1…/gate-summary.json`(오케스트레이터가 직접 읽음).
- frontend-visual: 17 장면 × (기본 · `theme=dark`) 34 URL, 전 행 13px 미만 0 · 대비 4.5 미만 0(`fix/visual-gate/index.md`). `theme=dark` 행이 audit 장면의 실제 다크 측정이다(audit 장면엔 매체 전환이 적용되지 않음 · A37). 60자 파일명 절단으로 다크 스크린샷 파일은 서로 덮였다 — 수치 행은 유효, 그림 증거는 1벌만 남음. 〔정정: 오케스트레이터가 한때 「중복이라 무해」로 설명했으나 틀렸다 · Fable advisor ③ 1〕
- `npm run build` 종료 0(기존 500kB 초과 청크 경고만) — `fix/build.log`.

## 캡처 대조 (`fix0924-base` @ e8fc4e13 대 `fix0924-final` @ 407fbcab)

- 202 캡처 · 바뀜 88(15 장면) · 불변 114 · 원인 불명 0. 원인 = 값 18 칩 테두리 · A12 · #11 · #12 `.btn-sm` · #7 자간 3곳 · #9 hover(캡처 절차상 포인터가 단추 위에 남음). 표 = `fix/capture-diff.md` · 대표 12벌 = `fix/capture/`.
- 캡처로 볼 수 없는 항목: #1 #2 #4 #10 #14 #16 #17 값 19 · 21 · WU-A1–A4(상태 장면 없음) · #8(16px 루트에선 픽셀 무변).

## 실브라우저 (agent-browser · audit 픽스처)

- pass 24 · fail 1 · not-run 2 — `fix/live/index.md`.
- fail a2: `.btn-primary`(·`.gnb-upload`·`.btn-strong`) 누름 = hover(primary-700 · 확정 값 10/14 의 귀결 · 값 19 범위 밖). 같은 부류: `.btn-danger`(`deletion.css`·`approval.css` · screens 층이 primitives 누름 규칙을 이겨 빨강 유지 — 회색으로 바뀌지는 않으나 누름 표시도 없다).
- not-run d5(등록 성공 뒤 닫는 중 재열기 = 새 ① — 등록 성공에 닿는 픽스처 없음 · jsdom 시험만) · h(값 21 dragover — 도구에 파일 끌기 없음).
- f/g(확대·이동·관성·동작 줄이기)는 `audit-selected-preview.html` 픽스처에서 쟀다(audit 빌드 장면엔 확대 요소 0).

## Fable advisor ③ (go/no-go)

- 두 명 모두 **go-with-conditions**. 조건 — ① 증거 폴더 커밋(이 커밋) ② PR 에 브라우저 미검증 d5 · h · 확대/이동 픽스처 한정 명시 ＋ dev 배포 뒤 실데이터 확인 3건 ③ visual-gate 서술 정정(위) ④ PR 에 사용자 노출 한계 명시: 641–1024px 터치 기기의 29px `.btn-sm` · 루트 글자≠16px 미검증 · 파란/빨간 채움 단추 누름 = hover · `@starting-style` 미지원 브라우저는 여는 전환 생략(기능 손실 없음) ⑤ 다른 채움 변형 grep → `.btn-danger` 2곳 확인(위).
- PR 본문(저장소 밖): `~/.claude/pr-bodies/PR-BODY-design-fix-20260924.md`.
- 〔추가 2026-09-25〕 위 「게이트」의 `fix/build.log` 는 `.gitignore:35`(`*.log`)에 걸려 develop 에 들어가지 않았다 — 같은 내용(바이트 동일)을 `dev-package/reports/design-review/20260924/fix/build-log.txt` 로 추가했다.
