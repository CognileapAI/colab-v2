# 레인 C 보고 — 버그 1·9·2 (프로젝트 화면 뿌리 스타일 · 연구실 설정 gap)

- 브랜치 `worktree-agent-a5f384032f2d1b8da` · 워크트리 `.claude/worktrees/agent-a5f384032f2d1b8da`
- 커밋 `61ef95b` (버그 1·9) · `d3bf37e` (버그 2). 워크트리 클린.
- 진행: Sonnet 이 CSS·시험 초안 작성 → Fable(메인 세션)이 검토·수정·검증·커밋.

## 근본 원인 (확정)
- 1·9: 이 레포엔 공용 PageShell 이 없고 화면 뿌리 클래스가 자기 여백을 적는 관례인데 `project.css` 에 `.project-page`·`.project-detail` 뿌리 규칙이 0건. 되돌아가기 줄은 `detail.css` 가 `.detail-page` 로만 스코프해 프로젝트 상세엔 닿지 않았다.
- 2: `shell.css` `.gnb-settings` 만 `gap` 누락 (형제 6~7px).

## 변경
| 파일 | 내용 |
|---|---|
| `frontend/src/components/project/project.css` | +70: 뿌리 여백·최대폭(카탈로그·상세와 같은 값), h1, backrow/backlink(detail.css 복제, 토큰은 project.css 관례 `--line`·`--fg-muted`·`--surface`), 상세 카드 `background`·`box-shadow` |
| `frontend/src/shell/shell.css` | +1: `gap: 6px` |
| `frontend/vite.config.ts` | `test.css.include` 에 `project.css`·`shell.css` 추가, `(\?raw)?` 허용 |
| `frontend/test/project.test.tsx` | +2건: 목록 뿌리 padding>0·max-width(계산값), 상세 뿌리 padding>0 + 카드 규칙 원문에 `background: var(--surface`·`box-shadow` |
| `frontend/test/shell.test.tsx` | +1건: `.gnb-settings` 규칙 원문 `gap ≥ 6px` |

## Sonnet 초안에서 고친 것
- 카드 배경·gap 을 `getComputedStyle` 로 재던 단언 2건이 CSS 적용 후에도 실패 — jsdom 은 `var()` 배경을 `rgba(0,0,0,0)` 으로, `gap` 을 빈 문자열로 낸다. 규칙 원문(`?raw`)으로 교체.
- `?raw` 가 vitest css 스텁에 걸려 빈 문자열 → `css.include` 정규식에 `(\?raw)?` 추가.
- `node:fs` 우회는 배제 — `e01-apply-points.test.ts:14` 선례(tsc·이미지 빌드 깨져 2026-09-02 main 배포 불가).
- 시험 제목 「계산값」→「선언값」.

## 증거
- RED (CSS 되돌린 상태): 3 failed / 52 passed — 정확히 신규 3건.
- GREEN: 36 파일 573/573 통과 (include 확장으로 흔들린 기존 시험 0건). `npm run typecheck` 오류 0.

## 등록만 (수정 안 함)
- `LabPage` 뿌리 규칙 부재(recon-C 곁가지) — 같은 무늬, 이번 범위 밖.
