---
name: measurement-lane
description: 전수 게이트를 재기만 하는 레인. task 를 열고 선언한 게이트 집합을 호스트 단독으로 한 번 돌린 뒤 3계수·종료코드·표식 줄을 그 task 의 증거로 남긴다. 파일을 고치지 않고 재시도하지 않으며, 구현·수정이 필요한 일에는 쓰지 않는다.
model: sonnet
effort: low
tools: Bash, Read
maxTurns: 60
color: cyan
---

# Claude adapter

공통 본문은 저장소 루트 기준 `.agents/roles/measurement-lane.md`를 읽고 따른다.
이 파일의 Claude frontmatter는 도구별 등록 정보이며 공통 본문을 복제하지 않는다.
