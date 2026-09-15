---
name: executing-plans
description: Use when you have a written implementation plan to execute in a separate session with review checkpoints
---

# Executing Plans

## Overview

Load plan, review critically, execute all tasks, report when complete.

**Note:** Prefer delegation over inline execution — 위임 원칙(글로벌 `CLAUDE.md`) ＋ `lane-worker` 에이전트로 태스크당 새 레인을 띄우는 것이 이 레포의 기본값이다. 이 스킬은 레인을 띄우지 않고 이 세션에서 직접 실행할 때 쓴다.

## The Process

### Step 1: Load and Review Plan
1. Ensure an isolated workspace: `lane-worker` 는 `isolation: worktree`(자동)로 뜬다 — 이미 격리돼 있는지 확인만 한다
2. Read plan file
3. Review critically - identify any questions or concerns about the plan
4. If concerns: Raise them with your human partner before starting
5. If no concerns: Create todos for the plan items and proceed

### Step 2: Execute Tasks

For each task:
1. Mark as in_progress
2. Follow each step exactly (plan has bite-sized steps)
3. Run verifications as specified
4. Mark as completed

### Step 3: Complete Development

After all tasks complete and verified:
- **REQUIRED:** `colab-v2-work` §병합 규약 — 병합은 오케스트레이터가 ff 로 하고 〈N〉 은 그때 발급한다
- 레인은 브랜치 이름과 게이트 결과만 반환한다. 스스로 `main` 에 병합하지 않는다

## When to Stop and Ask for Help

**STOP executing immediately when:**
- Hit a blocker (missing dependency, test fails, instruction unclear)
- Plan has critical gaps preventing starting
- You don't understand an instruction
- Verification fails repeatedly

**Ask for clarification rather than guessing.**

## When to Revisit Earlier Steps

**Return to Review (Step 1) when:**
- Partner updates the plan based on your feedback
- Fundamental approach needs rethinking

**Don't force through blockers** - stop and ask.

## Remember
- Review plan critically first
- Follow plan steps exactly
- Don't skip verifications
- Reference skills when plan says to
- Stop when blocked, don't guess
- Never start implementation on main/master branch without explicit user consent

Before reporting, check each claim against this session's tool results.
