# ADR-0005: 훅·guard·역할 정의는 선언이며 OS 강제가 아니다

- 상태: accepted
- 날짜: 2026-09-17
- 대체함: 없음
- 대체됨: 없음

## 배경
이 하네스는 훅·guard 스크립트·역할 파일을 갖추고 있어 코드를 읽으면 전면 강제로 오독하기 쉽다.
실제 경계는 여섯 파일에 조각으로 적혀 있고 한 곳에도 결정으로 모여 있지 않다.
`scripts/harness/hooks/lifecycle_contract.py:3` 「This is a lifecycle evidence contract, not a sandbox or a signature authority.」
`docs/development/lifecycle-evidence.md:4` 「이 계약은 작업 증거 검증이다. OS 쓰기 차단이나 증거 서명을 제공하지 않는다.」
같은 문서 84행 「task 등록은 OS 접근 통제나 에이전트 신원 서명이 아니다.」
`docs/development/dual-agent.md:149-150` 「명시적 검사 호출 자체는 모든 명령·편집을 가로채지 않는다. 자동 적용 범위는 위의 등록된
Codex 이벤트·matcher다. 원격 브랜치 보호도 별도이며 이 변경이 설정하지 않는다.」
훅 자체에 킬스위치가 있다 — `docs/superpowers/specs/2026-09-06-harness-fable51-design.md:271` 「**킬스위치** — 모든 스크립트 첫 줄 `[ "${COLAB_HOOKS:-1}" = "0" ] && exit 0`.」
2026-09-15 실측도 범위를 한정해 적었다 — `docs/development/harness-transition-handoff.md:66-67` 「따라서 현재 앱·루트 사본의 정상 명령 허용과 두 보호 동작은 확인됐다. 모든 훅 이벤트,
별도 worktree·Windows CLI·Claude에서 같은 결과를 확인했다는 뜻은 아니다.」

## 결정
이 하네스는 OS 수준 강제를 주장하지 않는다. 기계가 실제로 강제하는 것은 게이트 종료코드와 작업 증거 계약뿐이다
([ADR-0004](0004-gate-verdict-three-states.md)).
훅은 등록된 이벤트·matcher 범위 안에서만 차단하며(차단은 exit 2만 유효 — 같은 spec 272행 「차단은 **exit 2** 만 유효(exit 1 은 통과).」),
명시 guard 호출·역할 쓰기 제한·task 등록은 규율 선언이다. 여기서 보고의 상한이 나온다.
`AGENTS.md:41` 「명시적 guard 호출은 자동 보안 경계가 아니다. 생략했으면 검사했다고 보고하지 않는다.」
역할 분리도 같은 성격이다 — `docs/development/dual-agent.md:88` 「researcher의 특정 폴더 제한과 gate-runner의 코드 무수정은 지침이며 OS 접근 제어는 아니다.」
「동일 체크아웃에는 쓰기 주체 하나」(`AGENTS.md:43`)는 잠금이 아니라 규칙이다. 실제 격리가 필요하면 `AGENTS.md:43` 「Codex와 Claude가 동시에 구현하면 각자 격리된 작업 사본을 쓴다.」를 따른다.
승인 근거: `docs/development/harness-transition-handoff.md:26` 「## 현재 운영 범위 — 2026-09-15 사용자 승인」, 같은 절 34-36행
「Codex의 정상 허용과 보호 편집 차단을 실제 훅으로 확인한다. 차단 확인은 제품 파일을
훼손하지 않는 격리된 시험 대상으로 한다. 확인 전에는 필요한 guard를 명시적으로 실행하며,
명시 guard 결과를 자동 훅 검증으로 주장하지 않는다.」
이 결정은 형식 판정과 승인의 분리([ADR-0003](0003-human-approval-machine-checks-form.md))를 도구 층에 적용한 것이다.

## 검토한 대안
- 훅으로 전면 강제 — 배제. v1의 13훅을 6으로 줄이며 이미 정리됐다. `docs/superpowers/specs/2026-09-06-harness-fable51-design.md:267` 「## C. 훅 설계 (13 → 6)」 · `:286` 「### 삭제한 훅과 대체 (advisor 지적 4·7·9·10·11 전면 수용)」. 문자열 가로채기 방식의 한계가 배제 근거로 남아 있다 — 같은 표 292행 「`git commit` 문자열 가로채기가 취약(v1 K-3 이 자인)」.
- 모든 응답 끝에 거는 `Stop` 훅 — 배제. 같은 표 293행 「**모든 세션의 모든 응답 끝**에 뜬다. 오케스트레이터 계획 턴마다 게이트 검사를 요구한다. `stop_hook_active` 우회는 매 턴 잔소리로 남는다」.
- 등록된 matcher를 강제 보장으로 간주 — 배제. 도구 간 입력 형태가 다르다. `docs/development/dual-agent.md:224-226` 「중요한 입력 차이: Codex에서 matcher를 `Edit|Write`로 써도 실제 `tool_name`은 `apply_patch`이고,
입력은 `tool_input.command`의 patch다. 기존 Claude `tool_input.file_path`와 같지 않으므로
기존 스크립트를 그대로 등록하면 파일 검사를 조용히 건너뛸 수 있다.」 같은 문서 228행 「이 도구 범위의 한계를 전체 셸·파일 접근의 강제 보장으로 확대해 보고하지 않는다.」
- 역할 제한을 OS 접근 제어로 승격 — 배제(별도 ADR로도 다루지 않는다). 역할 경계는 `.agents/roles/*.md`가 규범으로 이미 소유하고 있고, 여기로 옮기면 이중 정본이 된다. 이 ADR이 가져오는 것은 「그 경계가 OS 통제가 아니다」 한 줄뿐이다.

## 결과와 감수한 비용
- 얻는 것: 「무엇을 검증했다고 보고해도 되는가」의 상한이 정해진다. 명시적 guard 호출은 자동 보안 경계가 아니다 — 생략했으면 검사했다고 보고하지 않는다.
- 부담: 규율은 사람과 에이전트의 준수에 의존한다. 훅을 통과했다는 사실이 해당 명령·편집이 검사됐다는 뜻은 아니다.
- 「동일 체크아웃에는 쓰기 주체 하나」는 규칙이지 잠금이 아니다. 동시 쓰기를 막는 장치는 없고, 격리는 작업 사본을 실제로 나눠야 성립한다.
- 도구별 설정은 서로에게 자동 적용되지 않는다. [ADR-0001](0001-lane-worktree-base-ref-head.md)의 `.claude/settings.json` 변경이 Codex에 적용되지 않는 것이 같은 성격의 사례다.
- 훅은 `COLAB_HOOKS=0` 한 줄로 전부 무력화된다. 이 킬스위치의 존재 자체가 훅이 신뢰 경계가 아니라는 근거다.

## 재검토 조건
- 실제 OS 수준 강제(샌드박스 마운트·파일시스템 권한·서명 검증)가 도입되어 역할·guard 경계를 커널이 집행하게 될 때.
- 도구가 모든 셸·파일 접근을 가로채는 이벤트를 제공하고 `COLAB_HOOKS` 킬스위치를 제거하기로 할 때.
- `lifecycle_contract.py`가 증거 검증을 넘어 접근 통제나 신원 서명을 제공하게 될 때(docstring 3행이 바뀔 때).
- 체크아웃 단위의 쓰기 잠금이 실제로 구현되어 「쓰기 주체 하나」가 규칙에서 장치로 바뀔 때.

## 근거
- `AGENTS.md:41` · `:43`.
- `docs/development/dual-agent.md:88` · `:149-151` · `:224-228`.
- `scripts/harness/hooks/lifecycle_contract.py:1,3-4` — 1행 「Shared, fail-closed task evidence for Claude H6/H7 and the Codex adapter.」(계약 자체는 fail-closed이나 범위는 작업 증거다).
- `docs/development/lifecycle-evidence.md:4` · `:84`.
- `docs/development/harness-transition-handoff.md:26`(2026-09-15 사용자 승인) · `:34-36` · `:51-70`(최소 자동 훅 실측 — 54행 「수동 guard 호출을 자동 실행 근거로 사용하지 않았다.」).
- `docs/superpowers/specs/2026-09-06-harness-fable51-design.md:267,271-272,286,292-293`(§C 훅 13→6과 삭제 근거).
- 관련: [ADR-0001](0001-lane-worktree-base-ref-head.md) · [ADR-0003](0003-human-approval-machine-checks-form.md) · [ADR-0004](0004-gate-verdict-three-states.md).
