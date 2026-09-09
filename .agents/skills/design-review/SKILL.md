---
name: design-review
description: CoLAB v2 화면의 디자인 검토가 요청됐을 때 정적 계측과 실제 화면을 대조한다.
---

# Codex 연결

먼저 `AGENTS.md`와 `docs/development/dual-agent.md`를 읽고, `.claude/skills/design-review/SKILL.md`를 읽어 수행한다.
원본의 상대 링크와 스크립트는 원본 디렉터리를 기준으로 해석한다. 공통 본문은 복제하지 않는다.
Claude Skill 호출은 해당 원본 SKILL.md 읽기로, Read/Grep/Bash/Edit는 현재 Codex 도구로 대응한다.
원본이 요구하는 역할은 연결 문서의 위임·격리 규칙을 적용한다. 현재 사용 가능한 도구와 입력 방식을 쓰고, 존재하지 않는 플러그인을 호출하지 않는다.
사용자가 이미 제공한 답과 승인 범위를 유지한다. 원본의 제품 규칙·산출물·검증 조건은 유지하며 실제 실행하지 않은 훅이나 검사를 통과로 보고하지 않는다.

이 SKILL.md가 속한 저장소 루트를 먼저 확인한다. `AGENTS.md`, `docs/`, `.claude/` 등의 저장소 경로는 그 루트 기준이며, 현재 셸이 하위 폴더여도 기준을 바꾸지 않는다.
