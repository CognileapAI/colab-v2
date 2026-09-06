# 브리프: Fable 5.1 하네스 재설계 판정 보고서 (ELI5)

## 이 문서를 읽고 나면 사용자는 ___ 를 스스로 판단할 수 있다
→ 「7개 확정 항목 각각에서 ⓐ/ⓑ 중 무엇을 고를지, 그리고 그 선택이 매 세션에서 무슨 일을 바꾸는지」

## 독자
Ted(사용자). CoLAB v2 개발 총괄. Claude Code 를 매일 쓰는 숙련 사용자이며 오케스트레이터(메인 세션) + 서브에이전트 위임 구조로 일한다.
이미 아는 것: 서브에이전트·워크트리·advisor 게이트·HANDOFF 문서·메모리 파일·effort 라는 단어.
모르는 것(설명 대상): 각 플러그인/에이전트가 세션 시작 시 **어떻게 토큰과 시간을 먹는지**, effort 단계가 **실제로 무엇을 바꾸는지**, superpowers 가 왜 오케스트레이터 원칙과 충돌하는지, 자율 블록을 메인에 넣으면 무슨 일이 생기는지.
문체: 개조식·정성어 배제·단정적·근거 동반. 「굽는다」류 은유로 기술 용어를 대체하지 말 것(영어 원어 그대로 또는 사실 그대로). 비유는 허용하되 기술 용어 자체를 은유로 바꾸지 않는다.

## 배경 (실측, 2026-09-06)
- Claude Code 모델: claude-fable-5-1[1m]. settings.json: effortLevel 글로벌 low, fable-5-1 은 medium. autoCompactEnabled false.
- 글로벌 에이전트 13개: humanize-korean 계열 12개(전부 model: opus) + advisor 1개(fable). 코딩 에이전트 0.
- 글로벌 스킬 8개(apple-design, archify, explain-visually, graphify, humanize, humanize-korean, humanize-redo, travel-proposal). CoLAB 전용 0.
- 활성 플러그인 14개가 에이전트 13 + 스킬 39 주입. 합계 매 세션 후보 목록: 에이전트 26, 스킬 47.
  - superpowers 6.3.0: 스킬 14, 매 세션 using-superpowers SKILL.md 3,108 bytes 주입, 「1% 라도 해당하면 스킬 강제 호출」 규칙.
  - claude-mem 13.0.0: SessionStart 컨텍스트 주입 + UserPromptSubmit(매 프롬프트) + PostToolUse(매 도구 호출) 훅 → 매 도구 호출마다 별도 프로세스 실행.
  - understand-anything 2.7.7: 에이전트 9·스킬 8, 442MB(대부분 node_modules).
  - feature-dev(에이전트 3), codex(에이전트 1, 스킬 3, 커맨드 7), ralph-loop(커맨드 3), claude-md-management(스킬 1), frontend-design(스킬 1), eli5, context7, playwright, code-review, skill-creator, typescript-lsp, pyright-lsp.
- 프로젝트: 30 CoLAB-v2/CLAUDE.md 17,852 bytes/210줄. 30 CoLAB-v2/.claude/skills/colab-v2-work/SKILL.md 15,785 bytes/169줄 (유일한 개발 전용 자산). 그 외 프로젝트 .claude 에 agents/hooks/settings 없음.
- 메모리: 33파일 64KB. 「창 8-a 완료」「Ted 판정 2026-09-05」류 프로젝트 상태 항목이 섞여 있음(HANDOFF 몫).
- 안티패턴 스캔(서술 억제·안티포맷팅·승인 유도·전체 재작성 유도·테스트 강제): 0건. 문장은 깨끗하고 문제는 구조와 양.
- 제품 코드에 Anthropic API 호출 0. 하네스만 손대면 됨.

## Fable 5.1 프롬프팅 가이드 핵심 (Anthropic 공식 문서 요지, 수치·표현은 아래 그대로만 인용)
- effort: 기본 high. medium 은 「Fable 5 와 대략 동급을 더 싼 비용으로」. 능력 향상은 높은 단계에서 가장 큼. low 에서는 검색/조회 도구를 덜 부르고 기억으로 답하는 경향.
- 진행 업데이트: 5.1 은 긴 도구 호출 턴 중 사용자 대상 텍스트를 덜 씀. Claude Code 하네스가 이미 「시작 전 한 줄, 중간 업데이트, 마무리 요약」 지시를 주입하므로 CLAUDE.md 추가 불요.
- 도구 호출 배칭: 하네스가 매 턴 자동 주입. 불요.
- 문장 밀도/포맷: 5.1 은 볼드·헤더·리스트를 덜 씀. 안티포맷팅 규칙이 있으면 제거하고 「언제 리스트를 쓰라」는 긍정형 규칙으로.
- 태스크 완주: 「사용자가 지켜보고 있지 않다, 묻지 말고 끝까지」 블록은 자율 워크로드용. 이 블록은 모호한 요청에 질문을 덜 하게 만드는 트레이드오프가 있음 → human-in-the-loop 세션엔 부적합.
- 변경·테스트 범위: 「발견한 다른 버그는 고치지 말고 후속으로 보고, 테스트는 요청된 곳만」 블록을 넣으면 불필요 추가와 테스트 파일 커밋이 실질적으로 줄고 성공률 변화 없음.
- 부분 편집: 5.1 은 Fable 5 보다 전체 파일 재작성 경향. 한 줄 지시로 교정.
- 세이프가드 오탐: 「컴파일 되나」 대신 「버그 있나」. base64 도구 출력 제거.
- 서브에이전트: 리드가 기다리지 않게 하면 완료 시간 단축, 품질·비용 동일. Claude Code Agent 도구는 이미 백그라운드.
- compaction: 클라이언트 측 요약 시 보존 6항목 지시. 캐시 읽기가 싸져서 일찍 compact 할 이유가 줄어듦.

## 설계 후보 (이미 사용자에게 제시함)
- A안 최소 수정: 가이드 문장 5개 + effort high. 후보 73개·훅 오버헤드·충돌 그대로.
- B안 프로필 분리(추천): 글로벌 CLAUDE.md 는 사용자 불변 규칙만 2.5KB 이하. CoLAB 자산은 30 CoLAB-v2/.claude/ 로. 무관 에이전트·스킬은 원래 프로젝트로 이동. 플러그인은 개발용만.
  - 프로젝트 에이전트 4종: advisor(fable, high) · lane-worker(opus, 자율 블록 + 범위/테스트 블록) · researcher(sonnet, 검색 검증 + 인용 예시) · gate-runner(haiku, 전수 실행·판정 요약만).
  - 검증: 부트스트랩 바이트 전후, 후보 목록 수 전후, 같은 작업 1건 턴 수 비교.
- C안 전면 리셋: B 와 결과 같고 검증된 자산 재작성 비용만 추가.

## 확정 필요 7개 (문서의 본체. 각 항목마다: 지금 무슨 일이 벌어지고 있나 → ⓐ/ⓑ 를 고르면 다음 세션부터 무엇이 달라지나 → 되돌리는 비용 → 권고)
1. humanize·발표 계열 에이전트 12개 + 스킬 5개(apple-design·travel-proposal·explain-visually·humanize·humanize-korean·humanize-redo 중 개발 무관인 것). 매 세션 후보 목록에 올라 description 만으로 토큰 소비. ⓐ 각자 프로젝트 폴더 .claude/agents 로 이동(권고) ⓑ ~/.claude/agents-archive 보관 ⓒ 존치. ⓐ 는 humanize 본진 폴더 위치를 알려줘야 함. 되돌리기: 파일 이동이라 싸다.
2. claude-mem. 매 도구 호출마다 프로세스 1개 + 매 프롬프트 훅 + 세션 시작 주입. 대가로 「지난번에 어떻게 했지」 cross-session 검색. ⓐ 비활성화하고 메모리 파일 + HANDOFF 로 일원화(권고) ⓑ 존치. 판단 기준: 최근 한 달 mem-search 를 실제로 쓴 기억이 있으면 ⓑ. 되돌리기: settings 한 줄, 싸다(DB 는 남음).
3. superpowers. 매 세션 3KB 주입 + 「1% 라도 해당하면 스킬 강제」 → 메인 세션이 brainstorming·TDD 의식을 스스로 수행하게 되어 「메인 = 오케스트레이터, 실행은 위임」 원칙과 충돌. 부분 비활성화 불가. ⓐ 비활성화하고 필요한 절차(승인 게이트, verification-before-completion)만 colab-v2-work 에 흡수(권고) ⓑ 존치. 되돌리기: settings 한 줄, 싸다.
4. understand-anything · ralph-loop · claude-md-management · frontend-design · codex. 사용 이력 없으면 끔. ⓐ 전부 끄고 필요 시 재활성화(권고) ⓑ 남길 것 지정. 되돌리기: 싸다.
5. effort. 메인·advisor high 로 올리면 사고 토큰↑ 응답 느려짐 비용↑, 대신 판단 품질이 medium 대비 가장 크게 오르는 구간. ⓐ 메인 high, 레인 medium, 기계적 low(권고) ⓑ 전부 medium. 되돌리기: settings 한 줄. 주의: 에이전트별 effort 지정이 frontmatter 로 되는지는 실측 전(미확인 사실로 표기).
6. 메인 세션 성격. Ted 판정·advisor 게이트가 있는 human-in-the-loop. 「묻지 말고 끝까지」 자율 블록을 메인에 넣으면 게이트를 건너뛰고 진행하는 방향으로 기울고, 모호한 요청에 질문을 덜 함. ⓐ 메인은 그대로, 자율 블록은 레인 에이전트에만(권고) ⓑ 메인도 자율. 되돌리기: 텍스트 한 블록, 싸지만 사고 사고(게이트 무시) 는 되돌리기 비쌈.
7. 설계 문서 위치. ⓐ 30 CoLAB-v2/docs/superpowers/specs/2026-09-06-harness-fable51-design.md(권고, 레포 이력에 남음) ⓑ 40 COLAB-기획 하위 ⓒ ~/.claude/references/.

## 문서 구성 요구
- 상단: 한 문장 목적 + 현재 상태 지도(위 실측 표를 시각화. 후보 목록 73개 중 CoLAB 관련 몇 개인지 한눈에. 인라인 SVG 로 「세션 시작 시 무엇이 실리는가」 도식).
- 가이드 14항목 ↔ 이 하네스 대입표는 접어서(details) 제공.
- 본체: 7개 항목 카드. 각 카드에 ① 지금 벌어지는 일(ELI5) ② ⓐ/ⓑ 를 골랐을 때 다음 세션 장면 대비 ③ 되돌리는 비용 ④ 권고 + 이유. 필요하면 인출 연습 질문 1개(답은 접기).
- 하단: 권고안 요약표(7행: 항목·권고·되돌리기 비용·사용자 입력 필요 여부) + 채택 시 B안 목표 구조 도식(글로벌/프로젝트/플러그인 3층, 인라인 SVG).
- 비유는 각 항목당 최대 1개, 깨지는 지점 명시.
- 절대경로 금지. 경로는 `~/.claude/...` 또는 레포 상대경로 표기.
