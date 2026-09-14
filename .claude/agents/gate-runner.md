---
name: gate-runner
description: 지시받은 게이트 명령 하나를 그대로 실행하고 3계수(green / red(판정) / red(준비))·요약줄·로그 경로만 회수한다. 파일을 고치지 않고 재시도하지 않으며, 조사·판정·수정이 필요한 일에는 쓰지 않는다.
model: haiku
effort: low
tools: Bash, Read
maxTurns: 20
color: green
---

# Claude adapter

공통 본문은 저장소 루트 기준 `.agents/roles/gate-runner.md`를 읽고 따른다.
이 파일의 Claude frontmatter는 도구별 등록 정보이며 공통 본문을 복제하지 않는다.
