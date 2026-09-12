---
name: slack-completion
description: Prepare one easy Korean Slack report after the user's entire development request is complete and all declared verification is green. Do not use for progress updates, individual lane completion, or an ordinary conversational stop.
---

# Slack completion report

This skill prepares the evidence-bound outbox item consumed by the deterministic Codex Stop hook. The hook does not invoke this skill or a model.

Use it only after the whole user-requested development scope is complete. A lane handoff alone is insufficient. Confirm that no review, activation, decision, test, or delivery work remains. If project hook trust or definition review is still pending, state that in the report and do not claim the notification feature itself is fully active.

Write a short Korean Markdown report next to the first gate-summary.json (for example dev-package/reports/<round>/<lane>/slack-eli5.md). The lifecycle verifier excludes that declared report directory from its source snapshot, so authoring the explanation after gates does not stale the gate evidence. Use these sections:

- 무엇을 바꿨나요?
- 사용할 때 무엇이 좋아지나요?
- 어떻게 확인했나요? Include actual checks and results.
- 남은 것이 있나요? Include activation or delivery limits.

Do not include secrets, internal decision numbers, or unexplained project shorthand. Then run:

    python3 scripts/slack_completion.py prepare \
      --report <report.md> \
      --evidence <task-id>:<gate-summary.json> \
      --whole-scope-complete

Add every independently required evidence item. The command reuses the lifecycle verifier and binds the artifact to the current Codex thread/session, checkout HEAD and working files, report hash, and evidence hashes. Never pass whole-scope-complete while anything is pending.

An ordinary Stop without this artifact sends nothing. Changed or stale inputs send nothing. Configure the webhook interactively with python3 scripts/slack_completion.py setup.

The sender does not retry an ambiguous timeout because Slack may already have accepted the message. It records an uncertain receipt for manual review instead of sending twice.
