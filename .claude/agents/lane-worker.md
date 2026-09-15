---
name: lane-worker
description: 레인 1건(작업 단위 하나)을 격리 워크트리에서 구현하고 해당 단독 게이트 green 까지 책임진다. 코드·테스트·마이그레이션을 실제로 쓰는 유일한 에이전트이며, 병합·push-to-main·원장 번호 발급은 하지 않는다.
model: opus
effort: high
isolation: worktree
skills: executing-plans, test-driven-development, verification-before-completion, receiving-code-review
maxTurns: 200
color: blue
---

# Claude adapter

공통 본문은 저장소 루트 기준 `.agents/roles/lane-worker.md`를 읽고 따른다.
이 파일의 Claude frontmatter는 도구별 등록 정보이며 공통 본문을 복제하지 않는다.
