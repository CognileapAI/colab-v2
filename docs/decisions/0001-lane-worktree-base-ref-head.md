# ADR-0001: 레인 워크트리는 현재 브랜치(head)에서 갈라진다

- 상태: accepted
- 날짜: 2026-09-17
- 대체함: 없음
- 대체됨: 없음

## 배경
`.claude/settings.json`의 `worktree.baseRef`가 `fresh`였다. `fresh`는 워크트리를 `origin/<기본 브랜치>` = `main`에서 만든다.
이 저장소의 실작업 브랜치는 `develop`이고, 2026-09-17 기준 `develop`이 `main`보다 56커밋 앞서 있었다.
이 상태로 lane-worker를 띄우면 방금 `develop`에 들어간 파일(`RegisterArea.tsx`·`UploadModal.tsx` — develop 전용 커밋 6705675d)과
그 시험(`lv0-source-20260907.test.tsx`)의 옛 판 위에서 재현·수정·검증이 전부 성립한다. 실패가 드러나지 않고 병합 시점에야 어긋난다.

## 결정
`worktree.baseRef`를 `head`로 한다. 레인 워크트리는 스폰 시점의 현재 브랜치에서 갈라진다.
`head`는 고정 기준이 아니라 세션 상태에 의존하므로, 레인을 띄우기 전에 `git branch --show-current`로 기준 브랜치를 확인한다.
승인 근거: 2026-09-17 대화, Ted "권고대로 ㄱㄱ" (advisor 계획 검토 권고 ②에 대한 승인).

## 검토한 대안
- `fresh` 유지 + 레인마다 `git worktree add -b <브랜치> develop` 수동 생성 — 공유 설정 무변경. 배제: 매 레인마다 같은 실수를 할 여지를 남기고, 설정이 실제 작업 흐름과 어긋난 채 남는다.
- `baseRef`를 `develop` 문자열로 고정 — Claude Code 워크트리 설정은 `fresh`(origin/기본 브랜치)와 `head`(현재 로컬 HEAD) 두 값만 정의한다. 브랜치 이름 직접 지정은 없다. 배제.

## 결과와 감수한 비용
- 얻는 것: 레인이 실작업 브랜치의 최신 트리 위에서 시작한다.
- 부담: 다른 브랜치에서 레인을 띄우면 그 브랜치를 물려받는다. 스폰 전 브랜치 확인이 절차에 추가된다.
- `.claude/settings.json`은 공유 설정이라 이후 모든 Claude 레인에 적용된다. Codex에는 자동 적용되지 않는다(AGENTS.md).

## 재검토 조건
- `main`이 `develop`을 따라잡아 두 브랜치 운용이 하나로 합쳐질 때.
- 기본 브랜치 운용이 바뀌거나 `baseRef`가 브랜치 이름을 직접 받게 될 때.

## 근거
- `.claude/settings.json` `worktree.baseRef` (이 결정으로 `fresh` → `head`).
- Claude Code `EnterWorktree` 도구 문서: "`fresh` (default) branches from origin/<default-branch>; `head` branches from your current local HEAD".
- `git rev-list --count develop ^main` = 56 · `git show --name-only 6705675d`에 `RegisterArea.tsx`·`UploadModal.tsx` 포함 (2026-09-17 실측).
- 적용 확인: 이 결정 직후 띄운 레인 워크트리 `.claude/worktrees/agent-*`가 `develop` tip(1e4dbd66) 위에서 생성됨.
- 관련: [ADR-0002](0002-gate-running-lanes-run-alone.md).
