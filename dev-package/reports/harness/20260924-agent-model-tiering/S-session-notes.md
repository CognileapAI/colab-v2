# S — 이 검토 세션(2026-09-24)의 직접 관측

출처: 이 세션의 서브에이전트 완료 알림(`usage`)과 최종 메시지 · 설정 파일 원문.

## 1. Claude 역할 설정 원문 (`.claude/agents/*.md` frontmatter)

| 역할 | model | effort | maxTurns | isolation | 도구 |
|---|---|---|---|---|---|
| researcher | sonnet | medium | 30 | — | Edit · NotebookEdit 금지 |
| lane-worker | opus | high | 200 | worktree | 전부 · skills 5개 |
| measurement-lane | sonnet | **(없음)** | 60 | — | Bash · Read |
| gate-runner | haiku | low | 20 | — | Bash · Read |
| advisor | fable | high | 12 | — | Edit · Write · NotebookEdit 금지 |

## 2. Claude Code 문서 조회 (claude-code-guide · https://code.claude.com/docs/en/sub-agents.md)

- `effort` 필드: 공개 문서에 없음. 빈 값일 때의 동작도 없음.
- `model`: `sonnet`·`opus`·`haiku` 또는 전체 모델 ID. 빈 값 동작은 문서에 없음.
- 이 세션의 Agent 도구 설명: 「each agent type's model, reasoning effort, and tools come from its definition」 · 스폰 때 넘긴 `model` 은 frontmatter 보다 우선한다.
- `maxTurns`: 「Max agentic turns before stopping」. 도달 시 동작·기본값은 문서에 없음. 실측: 도달하면 부분 결과로 끝나고 SendMessage 로 재개된다.
- `skills`: 스폰 시 선적재된다(문서 기재).

## 3. 이 세션의 역할 실행 관측

| 역할 · 모델 | 과제 | 도구 호출 | 결과 |
|---|---|---|---|
| researcher · sonnet | 역할별 transcript 통계(M1) | 33 | **30턴 절단 · 산출 0바이트**. 지시문에 「8번째 도구 호출 전 뼈대 쓰기」가 있었다. 재개 지시(첫 행동 = 파일 쓰기) 뒤 완료 |
| researcher · sonnet | Codex 사실(M2) | 38 | 산출 파일 완성 · **인계 거부**(read-only 판정: 같은 체크아웃에서 M1 이 임시 `tmp_*.py` 7개를 만들었다 지운 사이에 handoff) · 30턴 절단 |
| gate-runner · haiku(격리 워크트리) | develop 기준 게이트 1건 | 11 | 정상 |
| measurement-lane · sonnet | 전수 72게이트 `task` 1회 | 70 | **60턴 도달** · 인계는 완료 |
| lane-worker · opus ×2 | 레인 A·B 구현 | 63 · 57 | 정상 |
| advisor · (frontmatter) ×4 | ①·② 검토 | 7~9 | 정상 · 「도구 8회 이하」 문구 포함 |

- 관측 1: 숫자 규칙(8번째 호출 전 쓰기)을 지시문에 넣어도 Sonnet 조사자가 33회 호출까지 쓰지 않은 사례 1건. 앞선 Opus 사례(A2 af51a789)와 같은 행동이다.
- 관측 2: 같은 체크아웃의 조사자 둘은 서로의 임시 파일로 read-only 인계를 깨뜨린다. 조사자 병렬은 격리 워크트리이거나 임시 파일을 체크아웃 밖에 둬야 한다.
