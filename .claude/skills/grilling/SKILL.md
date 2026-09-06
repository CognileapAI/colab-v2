---
name: grilling
description: Grill the user relentlessly about a plan, decision, or idea. Use when the user wants to stress-test their thinking, or uses any 'grill' trigger phrases.
---

Interview the user relentlessly until you reach a shared understanding. Map this as a **design tree**: every decision branches into the decisions that hang off it.

Work the tree in **rounds**. The **frontier** is every decision whose prerequisites are already settled: the questions you can ask _now_ without guessing at answers you haven't heard yet. Ask the whole frontier in one round: number each question and give your recommended answer. Then wait for the user's answers before the next round.

Format a round like so:

```
❓ **Q1** - **<question title>**: <question body, might be multiple paragraphs, including multiple choices>

➡️ <your recommended answer>

---

❓ **Q2** - **<question title>**: <question body, might be multiple paragraphs, including multiple choices>

➡️ <your recommended answer>
```

Each round the user answers reshapes the tree: settled decisions push the frontier outward and unblock questions that depended on them. Recompute the frontier and ask the next round. A question whose answer depends on another question still open in this round belongs to a _later_ round, not this one.

Finding _facts_ is your job, never the user's. When a frontier question needs a fact from the environment (filesystem, tools, etc.), dispatch a sub-agent to find it; don't ask the user for anything you could look up yourself. Don't block on it: a running exploration is an unsettled prerequisite, so only the questions downstream of it wait for the sub-agent to report; ask the rest of the frontier now. The _decisions_ are the user's: put each to them and wait.

The session is done when the frontier is empty: every branch of the design tree visited, nothing left silently assumed. Do not act on it until the user confirms you have reached a shared understanding.

## CoLAB v2 운용 (vendored 개조)

- 사실 조회는 **`researcher` 서브에이전트**로 보낸다. 조회로 닫히는 것을 Ted 에게 묻지 않는다 —
  위 「finding facts is your job, never the user's」의 이 레포에서의 집행 방법이다.
- Ted 에게 가는 질문은 **한 라운드 단위로 묶어** 낸다. 한 건씩 왕복하지 않는다. 각 질문에 선택지를
  **ⓐ/ⓑ** 로 제시하고 권고 하나를 표시한다(원문의 recommended answer = Ted 의 ⓐ/ⓑ 문법).
- 질문문에 항목번호·WU 코드·내부 약어를 노출하지 않는다. 기능과 코드로 서술한다
  (`.claude/rules/colab-rules.md §5-2`·`§5-4`).

Before reporting, check each claim against this session's tool results.
