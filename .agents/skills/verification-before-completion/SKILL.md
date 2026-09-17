---
name: verification-before-completion
description: Use when about to claim work is complete, fixed, or passing, before committing or creating PRs - requires running verification commands and confirming output before making any success claims; evidence before assertions always
---

# Verification Before Completion

## Overview

**Core principle:** Evidence before claims, always.

**Violating the letter of this rule is violating the spirit of this rule.**

## The Iron Law

```
NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE
```

If you haven't run the verification command in this message, you cannot claim it passes.

## The Gate Function

```
BEFORE claiming any status or expressing satisfaction:

1. IDENTIFY: What command proves this claim?
2. RUN: Execute the FULL command (fresh, complete)
3. READ: Full output, check exit code, count failures
4. VERIFY: Does output confirm the claim?
   - If NO: State actual status with evidence
   - If YES: State claim WITH evidence
5. ONLY THEN: Make the claim

Skip any step = lying, not verifying
```

## 브라우저 검증의 환경·계정 선택 (CoLAB)

검증하려는 동작과 현재 사용자 승인 범위를 기준으로 환경·계정·방법을 선택한다.

- CLI·DB 등 비시각 변경은 관련 실행 시험을 사용한다. UI 변경은 [agent-browser](../agent-browser/SKILL.md)로 실제 조작을 확인한다.
- 공개 화면이나 로컬에서 충분히 확인할 수 있는 동작에는 dev 로그인이나 관리자 계정을 요구하지 않는다. 배포 후 확인이 요청됐으면 로컬 결과로 대신하지 않는다.
- 인증이 필요한 화면은 해당 역할을 가진 승인된 테스트 계정을 선택한다. 일반 사용자 권한 검증을 관리자 계정으로 대신하지 않는다.
- dev의 무소속 관리자 화면 또는 전체 연구실 읽기 검증에는 기존 `test_admin@colab.invalid`을 사용할 수 있다. 선택한 경우 `python3 scripts/dev-browser-check.py`로 실제 로그인부터 확인한다. [설정과 도구 사용법](../../../docs/development/dual-agent.md#dev-브라우저-로그인-확인-도구)을 필요한 때 읽는다.
- 이 계정은 연구실 소속 쓰기 검증에 적합하지 않다. 다른 역할·환경에는 해당 시나리오에 맞는 계정과 인증 방법을 사용한다. 검증을 위해 계정 생성·권한 확대·배포 권한을 임의로 추정하지 않는다.
- 필요한 인증이 실패하면 그 인증에 의존하는 시나리오는 미실행으로 기록한다. 독립적인 검증은 계속할 수 있다. 로그인 도구 성공 자체를 기능 검증 성공으로 보고하지 않는다.

선택한 환경·버전·역할과 실제 조작 결과를 근거로 남긴다. 저장 동작은 조회·새로고침 후 지속성을 확인한다.

## intent 대조 (CoLAB v2 개조)

완료를 주장하기 전에 **연결된 `dev-package/intent/<날짜>-<주제>.md` 의 `## 원한 결과 (proposed outcome)`
항목을 한 줄씩 대조**하고 아래 둘을 열거한다. 대조 없이 「완료」를 말하지 않는다.

- **미달** — proposed outcome 에 있는데 이번 산출물이 채우지 못한 항목. 각 항목에 무엇이 막는지 한 줄.
- **초과** — proposed outcome 에 없는데 만들어진 항목. 범위 확대이므로 근거를 밝히거나 되돌린다
  (CLAUDE.md §5 「범위 늘리기」).

둘 다 0건이어야 「intent 충족」이다. 0건이 아니면 그 목록을 그대로 보고에 싣는다 —
advisor 게이트 ② 가 같은 목록을 요구한다.

## Common Failures

| Claim | Requires | Not Sufficient |
|-------|----------|----------------|
| Tests pass | Test command output: 0 failures | Previous run, "should pass" |
| Linter clean | Linter output: 0 errors | Partial check, extrapolation |
| Build succeeds | Build command: exit 0 | Linter passing, logs look good |
| Bug fixed | Test original symptom: passes | Code changed, assumed fixed |
| Regression test works | Red-green cycle verified | Test passes once |
| Agent completed | VCS diff shows changes | Agent reports "success" |
| Requirements met | Line-by-line checklist | Tests passing |

## Red Flags - STOP

- Using "should", "probably", "seems to"
- Expressing satisfaction before verification ("Great!", "Perfect!", "Done!", etc.)
- About to commit/push/PR without verification
- Trusting agent success reports
- Relying on partial verification
- Thinking "just this once"
- Tired and wanting work over
- **ANY wording implying success without having run verification**

## Rationalization Prevention

| Excuse | Reality |
|--------|---------|
| "Should work now" | RUN the verification |
| "I'm confident" | Confidence ≠ evidence |
| "Just this once" | No exceptions |
| "Linter passed" | Linter ≠ compiler |
| "Agent said success" | Verify independently |
| "I'm tired" | Exhaustion ≠ excuse |
| "Partial check is enough" | Partial proves nothing |
| "Different words so rule doesn't apply" | Spirit over letter |

## Key Patterns

**Tests:**
```
✅ [Run test command] [See: 34/34 pass] "All tests pass"
❌ "Should pass now" / "Looks correct"
```

**Regression tests (TDD Red-Green):**
```
✅ Write → Run (pass) → Revert fix → Run (MUST FAIL) → Restore → Run (pass)
❌ "I've written a regression test" (without red-green verification)
```

**Build:**
```
✅ [Run build] [See: exit 0] "Build passes"
❌ "Linter passed" (linter doesn't check compilation)
```

**Requirements:**
```
✅ Re-read plan → Create checklist → Verify each → Report gaps or completion
❌ "Tests pass, phase complete"
```

**Agent delegation:**
```
✅ Agent reports success → Check VCS diff → Verify changes → Report actual state
❌ Trust agent report
```

## When To Apply

**ALWAYS before:**
- ANY variation of success/completion claims
- ANY expression of satisfaction
- ANY positive statement about work state
- Committing, PR creation, task completion
- Moving to next task
- Delegating to agents

**Rule applies to** exact phrases, paraphrases, synonyms, implications — ANY communication suggesting completion/correctness.

Before reporting, check each claim against this session's tool results.
