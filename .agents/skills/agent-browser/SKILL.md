---
name: agent-browser
description: CoLAB 웹 화면을 agent-browser CLI로 조작·검증하거나 사용자 여정 E2E를 수행할 때 사용한다. 시각 검사와 저장 동작 E2E를 구분한다.
---

# 브라우저 연결

공통 CLI 원본 `.claude/skills/agent-browser/SKILL.md`를 읽는다.
상대 리소스는 `.claude/skills/agent-browser/`를 기준으로 찾는다. 본문을 이곳에 복사하지 않는다.
Claude allowed-tools는 Codex 권한 설정이 아니다. 현재 셸에서 agent-browser의 존재·버전을 확인한다.

`docs/development/dual-agent.md`의 로컬 평가와 E2E 계약을 적용한다.
명시한 테스트 환경에서 UI 행동과 사전 기대 결과를 대조한다. 사용자 데이터 변경 권한을
스킬 사용 자체에서 추론하지 않는다. 자동 성공 문구·스크린샷만으로 저장 성공을 판정하지 않는다.
도구가 없으면 준비 실패로 보고하며 Playwright로 조용히 대체하지 않는다.

이 SKILL.md가 속한 저장소 루트를 먼저 확인한다. `AGENTS.md`, `docs/`, `.claude/` 등의 저장소 경로는 그 루트 기준이며, 현재 셸이 하위 폴더여도 기준을 바꾸지 않는다.
