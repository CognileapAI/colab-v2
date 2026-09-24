# ADR-0004: 게이트 판정은 세 상태다 — green · red(판정) · red(준비)

- 상태: accepted
- 날짜: 2026-09-17
- 대체함: 없음
- 대체됨: 없음

## 배경
v1 CI가 DB 없이 돌아 RLS 테스트를 green-by-skip 했다. `gates/README.md:117` 「"전부 green"과 "전부 무력"은 구분되지 않는다. v1 CI는 DB 없이 돌아 RLS 테스트를 **green-by-skip** 했다.」
같은 사고가 `gates/run.sh:4-5` 머리에 원칙으로 박혀 있다 — 「원칙: 미구현 게이트는 red다. 조용히 green이 되는 게이트는 게이트가 아니며,
v1에서 CI가 DB 없이 돌아 RLS 테스트를 green-by-skip 했던 실패를 반복하지 않는다.」
같은 계열의 두 번째 사고는 셀프테스트 쪽이었다. `gates/README.md:124-126` 「⭑ **⟨2026-09-03 · 코드리뷰 #6⟩ 준비 실패(종료코드 78)를 「기대한 red」로 세지 않는다.**
자체 `expect()` 를 가진 셀프테스트 12개 중 **10개가 78 을 그냥 red 로 접고 있었다.**」 그 결과는 `gates/README.md:128-129` 「**판정된 적이 없는데 출력은 「red OK」라고 말한다** — 검사기가 아무것도 검사하지 않은 채 통과를 / 보고하는 모양이다.」
종료코드 값은 `AGENTS.md:45` · `docs/development/dual-agent.md:127` · `.agents/harness.yaml:30`에 한 줄씩 적혀 있으나, 왜 셋인지와 미선언 입력을 왜 통과로 접지 않는지는 결정으로 승격된 적이 없다.

## 결정
게이트 판정은 셋뿐이다 — `green`(exit 0) · `red_판정`(exit 1) · `red_준비`(exit 78). `SKIP`을 만들지 않는다.
`gates/run.sh:18-19` 「⚠ 상태는 `green` / `red_판정` / `red_준비` **셋뿐이다. `SKIP` 을 만들지 않는다** — 이 레포는
대상 0건을 red 로 못박았고, SKIP 은 green-by-skip 통로를 다시 여는 것이다(`CLAUDE.md §4`).」
같은 결정의 나머지 두 면을 여기에 함께 둔다.
- 입력의 세 상태 — `AGENTS.md:46` 「선언하면 검사하고, 명시적 면제는 건수·사유를 드러내며, 아무 선언도 없으면 준비 실패로 처리한다.」 미선언은 green이 될 수 없다. 면제는 조용히 넘어가지 못하고 건수·사유를 출력해야 한다.
- 요약 JSON 3계수 — 사람이 읽는 요약줄과 같은 변수로 기계가 읽는 한 벌을 낸다. `gates/run.sh:12-14` 「왜 있나: 3상태 요약은 **사람이 읽는 텍스트로만** 있었고, 레인 종료 검사(H7)와 전수 재실행 / 갈음(트리 해시 대조)은 그 텍스트를 사람이 옮겨 적은 값에 기대고 있었다. 옮겨 적는 자리는 / 언젠가 틀린다.」 계수는 다시 세지 않는다 — `gates/README.md:102` 「**계수를 다시 세는 자리를 만들지 않았다** — 배출기(`gates/tools/gate_summary_json.py`)는 직렬화만 한다.」
병합 진입 조건은 두 red가 모두 0이다 — `gates/README.md:112` 「⚠ **병합 진입 조건은 `red_판정 == 0` 과 `red_준비 == 0` 둘 다**다(준비 red 도 red 다).」
승인 근거: `docs/superpowers/specs/2026-09-06-harness-fable51-design.md:410` 「## J. 확정 판정 (Ted 2026-09-06 — 「판정은 전부 권고대로」)」. 같은 절 412행이 재개봉을 막는다 — 「**재개봉 금지.** 아래 11건은 확정 사실이며 후속 세션에서 선택지로 되돌리지 않는다.」
승인과 검사의 관계는 [ADR-0003](0003-human-approval-machine-checks-form.md)을 따른다 — green은 형식 판정이며 승인이 아니다.

## 검토한 대안
- v1의 4상태 요약 계약 — 배제. `docs/superpowers/specs/2026-09-06-harness-fable51-design.md:299` 「## D. 게이트 요약 계약 (v1 의 4상태 폐기 — advisor 지적 3 수용)」. 새 계수 개념을 만들지 않은 이유는 같은 문서 313행 — 「`counts` 는 run.sh 가 이미 세는 `n_green` / `n_red_judge` / `n_red_ready` / `n_undeclared_input` 을 그대로 쓴다. 새 계수 개념(`targets`) 없음 → v1 K-4(53게이트가 targets 를 낼 수 있는가) **소멸**.」
- `SKIP` 상태 신설(대상 0건·환경 부재를 통과로 표기) — 배제. `docs/superpowers/specs/2026-09-06-harness-fable51-design.md:312` 「`state` 값은 **`green` / `red_판정` / `red_준비` 3개뿐**. `SKIP` 은 만들지 않는다 — 이 레포는 대상 0건을 red 로 못박았고, SKIP 은 green-by-skip 통로를 다시 여는 것이다.」
- 준비 실패 78을 판정 red 1로 접기 — 배제. `docs/development/dual-agent.md:128` 「준비 실패는 건너뛴 성공이나 일반 판정 실패로 바꾸지 않는다. 실제 반환 코드와 상태를 함께 보고한다.」
- 게이트 로직을 고쳐 요약을 맞추기 — 배제. `gates/run.sh:16-17` 「⚠ **게이트 로직은 한 줄도 바뀌지 않는다.** 검사·판정·종료코드는 그대로이고, 요약이 이미 센 / 계수를 직렬화할 뿐이다」.

## 결과와 감수한 비용
- 얻는 것: 「돌지 못했다」와 「돌아서 틀렸다」가 갈린다. 두 red 모두 병합을 막으므로 준비 실패가 통과 통로가 되지 않는다.
- 부담: 환경이 없는 체크아웃에서 게이트가 78로 자주 멈춘다. 완화 수단은 범위 축소·재시도가 아니라 환경 준비다.
- 셀프테스트 쪽 기대 어휘는 판정 축과 별도로 네 갈래를 쓴다(`green`·`red`·`ready`·`미선언`, `gates/README.md:131-138`). 갈래를 넷으로 둔 이유는 `gates/README.md:140-141` 「`ready` 와 `미선언` 을 가르는 이유 — **미선언은 간헐이 아니다.** 매번 같은 답을 내므로 「판정 못 함」으로 / 접지 않고 그 자리에서 판정한다.」 판정 축은 여전히 하나이고 실행기 요약은 `red(준비)`로 접어 적는다(`gates/README.md:143`). ⚠ 게이트 상태 3개와 셀프테스트 기대 갈래 4개는 같은 축이 아니다.
- 정본은 하나다 — `gates/README.md:122` 「### 셀프테스트의 판정 갈래 — 정본은 `gates/tools/_expect.sh` 하나」. 게이트마다 자기 판정 코드를 다시 쓰면 위 10/12 사고가 재발한다.

## 재검토 조건
- 세 상태로 표현되지 않는 판정 결과가 실제로 나타날 때(예: 부분 판정을 기록해야 하는 게이트 신설). 그때도 `SKIP` 은 후보가 아니다.
- `colab-gate-summary/1` 스키마가 `/2`로 올라가 `counts` 키 집합이 바뀔 때(`.agents/harness.yaml:31` `report_schema`).
- 병합 진입 조건에서 `red_준비 == 0` 이 빠질 때 — 이 ADR의 전제가 무너진다.
- `.agents/harness.yaml:30` `"states": {"green": 0, "red_judgment": 1, "red_readiness": 78}` 의 값이 바뀔 때.

## 근거
- `gates/run.sh:4-5`(green-by-skip 금지 원칙) · `:11-19`(요약 JSON 스키마 `colab-gate-summary/1` 주석).
- `gates/README.md:99-102,112,117,122,124-129,131-143`.
- `docs/superpowers/specs/2026-09-06-harness-fable51-design.md:299-316`(§D) · `:410-412`(§J 확정 판정 — 승인 문장).
- `AGENTS.md:45-46` · `docs/development/dual-agent.md:127-128`. (2026-09-25 줄 번호 갱신)
- `.agents/harness.yaml:30`(`states`) · `:31`(`report_schema`) · `:37`(`required_counts`). (2026-09-25 키 추가로 줄 번호 갱신)
- 관련: [ADR-0003](0003-human-approval-machine-checks-form.md) · [ADR-0005](0005-harness-controls-are-declarative.md).
