---
name: colab-v2-work
description: CoLAB v2 구현·테스트·인계를 수행할 때 기존 프로젝트 절차를 Codex 도구로 연결한다. 일반 질문이나 다른 프로젝트에는 사용하지 않는다.
---

# CoLAB 작업 연결

먼저 `docs/development/dual-agent.md`를 읽고, 원본 `.claude/skills/colab-v2-work/SKILL.md`를 읽는다.
공통 내용은 원본에서만 편집한다. Claude 도구·격리·훅 문장은 연결 문서의 Codex 대응을 적용한다.
연결 문서는 제품 범위나 완료 조건을 바꾸지 않는다.

필요한 단계에서만 다음 원본을 읽는다:

- 요구사항 탐색: `.claude/skills/grill-me/SKILL.md`
- 승인된 요구사항을 사양으로: `.claude/skills/to-spec/SKILL.md`
- 계획·구현: `.claude/skills/writing-plans/SKILL.md`, `.claude/skills/executing-plans/SKILL.md`
- 회귀 테스트: `.claude/skills/test-driven-development/SKILL.md`
- 리뷰 수용·완료: `.claude/skills/receiving-code-review/SKILL.md`, `.claude/skills/verification-before-completion/SKILL.md`
- 디자인 검토를 요청받았을 때: `.claude/skills/design-review/SKILL.md`와 그 원본 상대 리소스

없는 플러그인을 요구하지 않는다. 현재 도구로 원본의 목적을 달성하고 실행하지 못한 검사는 명시한다.

이 SKILL.md가 속한 저장소 루트를 먼저 확인한다. `AGENTS.md`, `docs/`, `.claude/` 등의 저장소 경로는 그 루트 기준이며, 현재 셸이 하위 폴더여도 기준을 바꾸지 않는다.
