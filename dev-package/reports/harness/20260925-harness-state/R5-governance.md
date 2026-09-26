# R5-governance — decision history, backlog, stale branches, memory/doc drift
Repo: 31 CoLAB-v2 @ develop 67a03a05 (2026-09-25). Read-only analysis. Status axis: documented | implemented | tested | measured | draft.
Note: the H3 git-guard blocked writing this notes file because the heredoc text contained the literal gh-CLI PR-merge phrase — the guard matches command text, including heredoc payloads (observed 2026-09-25). Below, that command is written as "gh-pr-merge".

## 1. Dated timeline (harness)
| Date (KST unless noted) | Event | Delivered / evidence |
|---|---|---|
| 2026-09-06 | Fable 5.1 harness redesign spec `docs/superpowers/specs/2026-09-06-harness-fable51-design.md` ("판정은 전부 권고대로", §J) | 4 roles (advisor fable/high, lane-worker opus/high/worktree, researcher sonnet/medium/30 (:250), gate-runner haiku/low/20); hooks 13→6 (§C); gate summary contract (§D). Commits b7f36c9a (agents), 15bc4e06 (H1 bootstrap-diet, H2 worktree-setup), 16c42967 (H3 git-guard, H4 migration-guard, H5 decision-number-guard, work-items merge driver) |
| 2026-09-14 | 74d3e3ec | common rules/roles split out of tool adapters (.agents/ as source) |
| 2026-09-15 | fa963f90 develop integration of common harness + Ponytail; `harness-pr-centric.md` spec (e125dd55); ops scope approved: full transition & further upgrades on hold (`docs/development/harness-transition-handoff.md:26-49`, `R-HARNESS-PR-CENTRIC.md:4`) | handoff doc last touched here |
| 2026-09-17 | 22555957 `worktree.baseRef: head` committed (+ 4 issue intents, 2 ADRs); intents stop-hook & spec-WATCH written | `.claude/settings.json:3-4` |
| 2026-09-17/18 (merges UTC 09-17) | PR #115 superuser purge (#47) · #116 slot/lock limit failure → red 78 · #117 evidence contracts x3 (measurement-lane stop hook, spec inside WATCH, full-run invocation canon) · #118 host mutex merged only into sibling branch · #119 re-land mutex to develop | stop/WATCH intents approved 2026-09-18 "좋아 그렇게해"; 4c07f1ea stop hook generalized to role set; R-HARNESS-PR-CENTRIC last edit 7ad972ba (09-18) |
| 2026-09-24 | lane-hygiene intent approved ("전부 권고대로 할게") → PR #130 merged 15:19Z | R1 researcher-task hook (b6b0a2ff), F1 gate_mutex_spawn (b549d75d), F2 live_audit session close, role/instruction rules, ponytail-inject hook. Dropped: SubagentStop cleanup hook, handoff JSON contract change, advisor ① skip criteria |
| 2026-09-24 (23:03Z) | PR #131 agent-model-tiering (0e33ce02) | advisor fable/high/16, lane-worker opus/high/200, researcher opus/medium/50, measurement-lane sonnet/low/60, gate-runner haiku/low/20; Codex role mapping; bridge checks 5 roles. Outcome 8 (post-merge limit-hit re-measure) = follow-up |
| 2026-09-25 (UTC 09-24 23:20) | PR #140 external-harness-gap | ADR-0007 Intent-Ref + append-only approved intents; hook-registration check; adr-records gate; home abs-path check; always-on line cap 120; lane `--scope` handoff check; 7 deferred (dual-agent.md:267-277), 4 rejected; no new hooks |
| 2026-09-25 | PR #141 design-fix (product) surfaced harness residuals; PR #144 reset gate nonce log (03:26Z); PR #150 draft residuals intent (80aa95ac) | residuals H1–H15 unapproved |

## 2. Lane-hygiene reconciliation (memory "구현 보류" vs PR #130)
- Memory `design-system-program-state.md` ("하네스 고도화 — 구현 보류 (Ted 결정)"; branch `claude/harness-lane-hygiene` intent-only; f3846f32 "쓸지 버릴지는 그 검토 때") predates #130 and is now STALE.
- Implemented by #130: researcher-task hook `scripts/harness/hooks/researcher-task.sh` (registered `.claude/settings.json:29-33`, tests `scripts/tests/test_task_runtime.py:398+`); F1 `gates/tools/_lock.sh:136-146` `gate_mutex_spawn` used at `gates/run.sh:870`, `gates/tools/frontend-visual.sh:84` (selftest `gates/tools/gate-host-mutex-selftest.sh:294`); F2 `.agents/skills/design-review/scripts/live_audit.sh:14-20` EXIT trap + `frontend-visual.sh:82` idle timeout; advisor "도구 호출 8회 이하 뒤 판정" `.agents/roles/advisor.md:49`.
- Dropped by #130: SubagentStop cleanup hook; handoff JSON contract change (=> f3846f32 on `worktree-agent-abe5bbb8…` is rejected work); advisor ① skip criteria.
- Post-merge user steps: `/hooks` re-trust + researcher live smoke (agent_id Start/Stop) — no record (residual H10; `docs/development/lifecycle-evidence.md:42` still "not proven").

## 3. Intents & specs status
| Intent | Approval | Code status |
|---|---|---|
| 2026-09-17 measurement-lane-subagent-stop-hook | approved 09-18 | tested: settings.json:49-53 (lane-worker/measurement-lane → lane-gate-summary.sh); test_harness_lifecycle_contract.py:288 `test_measurement_lane_closes_with_a_red_row_on_both_harnesses` |
| 2026-09-17 spec-artifacts-outside-lifecycle-watch | approved 09-18 | tested: lifecycle_contract.py:26 WATCH incl. SPECS; test_harness_lifecycle_contract.py:229 `test_researcher_spec_output_is_blocked_and_named_as_unhanded_output` |
| 2026-09-24 harness-lane-hygiene (+S-HARNESS-LANE-HYGIENE) | approved 09-24 | implemented/tested (§2); smoke pending |
| 2026-09-24 agent-model-tiering | approved 09-24 | implemented: .claude/agents/*.md frontmatter; outcome 8 re-measure pending |
| 2026-09-25 external-harness-gap (+S-EXTERNAL-HARNESS-GAP) | approved 09-25 "권고댜로" | tested: test_harness_config.py:147,180; test_harness_record_gates.py:213-235; test_task_runtime.py:244-275 |
| 2026-09-25 reset-nonempty-gate | approved 09-25 | implemented in develop (dev-package/tools/dev-reseed/stages.sh reset_nonempty_gate); #144 nonce fix; post-merge ②③④ run per PR #144 body |
| 2026-09-25 harness-design-round-residuals | draft (미승인) | §4 |

## 4. Residuals H-items (draft; file has H1–H15, not H1–H14)
| H | One line | Current code |
|---|---|---|
| H1 | live_audit.sh slug `cut -c1-60` → probe files overwrite, frontend-visual under-counts | unresolved — live_audit.sh:29; counter frontend-visual.sh:108 |
| H2 | live_probe.js does not recurse into `@layer` | unresolved — live_probe.js:39 top-level cssRules |
| H3 | COLAB_FIX_LANE never reaches Claude lane hooks | unresolved — test-file-guard.sh:32; design-review SKILL.md:101,106 still claim it |
| H4 | shared-worktree researchers' handoffs rejected; SKILL §2-2 item 7 conflict | unresolved — lifecycle_contract.py:26 + whole-WATCH diff (:384-394) |
| H5 | begin accepts only runtime:artifacts vs role/skill telling repo paths | partial (R1 hook prints runtime cmd) |
| H6 | required-gates parent mismatch red(1) when develop moves; fix only in user memory | unresolved — verify_evidence.py:57-58; no repo doc |
| H7 | gates/run.sh silently drops extra args | unresolved — run.sh:9 `GATE="${1:-}"` |
| H8 | workflow advisor/measurement-lane StructuredOutput failure | partial (limits raised; no rule) |
| H9 | lane branch name collision `fixlane-work` | unresolved (instruction-side; grep 0 in repo) |
| H10 | #130 post-merge re-trust/smoke not recorded | unresolved — lifecycle-evidence.md:42 |
| H11 | capture-scene blind spots | unresolved |
| H12 | tsconfig.audit.json not in any gate | unresolved — grep 0 in gates/.github |
| H13 | visual diff gate promotion | pending Ted judgement |
| H14 | SKILL.md:101 fused sentence | unresolved — SKILL.md:101 |
| H15 | frontend-test load flake vs defect indistinguishable | unresolved |
| A39 | lock fd inheritance | resolved by #130 (b549d75d) |
None of H1–H15 is resolved by current code.

## 5. Branches
| Branch | Unique vs develop (git cherry) | Verdict |
|---|---|---|
| worktree-agent-a06b599e… (2fc95713, 09-17) | 0 (all "-") | stale, patch already in develop |
| worktree-agent-a20a6e57… (7 commits, 09-17: parallelism decls, ALL_GATES⊆parallelism.toml, 5-col gate row, ::gate-failure::, vitest 78, measurement-lane) | 0 (all "-") | stale, patch already in develop |
| worktree-agent-abe5bbb8… (f3846f32 handoff JSON evidence key, 09-24) | 1 unique | rejected by #130 (handoff contract change dropped) |
| integration/r-user-features-review-evidence (96e611d1, 09-15; also on origin) | 1 unique | product QA evidence, not harness |
| origin/worktree-ponytail-systemic (09-18) | 0 | #130 body asked to delete; still on origin |
| origin/claude/harness-lane-hygiene | — | deleted (as #130 asked) |
| origin/reseed-reset-gate | 62 commits not in develop | dev-reseed line; out of harness scope |
No open PRs.

## 6. MEMORY vs CODE drift table
| Memory file | Claim | Verdict | Code |
|---|---|---|---|
| subagent-turn-limits-truncate-results (+index) | advisor 12 turns, researcher 30 | STALE | .claude/agents/advisor.md:7 maxTurns 16; researcher.md:7 50 (0e33ce02, #131) |
| subagent-turn-limits… | lane-worker 200 | still-true | lane-worker.md:8 |
| subagent-turn-limits… | advisor "도구 호출 8회 이하" | still-true, codified | .agents/roles/advisor.md:49 |
| workflow-advisor-model-and-schema | advisor maxTurns 12 | STALE | advisor.md:7 = 16 |
| workflow-advisor-model-and-schema | host lock at /tmp/colab-v2-gate-host-mutex/host | still-true | gates/tools/_lock.sh:78 |
| workflow-advisor-model-and-schema | schema on advisor/measurement-lane fails | unverifiable (runtime) | — |
| gate-lanes-cannot-run-in-parallel (+index) | run.sh has no inter-process mutex | STALE | _lock.sh:80-121 gate_host_mutex_acquire; run.sh:870; gate-host-mutex-selftest.sh |
| gate-lanes… | pg slots host-global /tmp/colab-v2-gatepg-slots, default 4 | still-true | gates/tools/_pg.sh:75,79 |
| gate-lanes… | frontend-visual daemon inherits lock fd; root fix = future issue | STALE (fixed) | _lock.sh:136-146; frontend-visual.sh:84; run.sh:870 |
| gate-lanes… 09-18 correction | "훅은 없고" (no worktree hook) | STALE for lane-worker | settings.json:14-24 SubagentStart lane-worker → scripts/harness/hooks/worktree-setup.sh (venv :143, npm ci :188) since 15bc4e06 (09-06) |
| measurement-needs-provisioned-worktree | settings.json has no Worktree hook | partially stale | same; true only for measurement-lane / EnterWorktree / workflow agents (matcher lane-worker only) |
| worktree-baseref-must-match-working-branch (+index) | baseRef fresh → origin/main; switched to head 09-17 | still-true (current = head) | settings.json:4; committed 22555957 |
| issue-pr-workflow-shape | deleting main-checkout intent copies early reverts baseRef to fresh | STALE | head committed on develop (22555957) |
| issue-pr-workflow-shape | gh-pr-merge blocked by H3 git-guard | still-true (and matches heredoc text too) | scripts/harness/hooks/git-guard.sh:14,32,180 |
| issue-pr-workflow-shape | frontend-visual requires COLAB_VISUAL_URLS else 78 | still-true | gates/tools/frontend-visual.sh:49,57 |
| issue-pr-workflow-shape | gate evidence under git common dir colab-harness/<key>/<task> | still-true | scripts/harness/task_state.py:51 |
| issue-pr-workflow-shape | cleanup via `pkill -f agent-browser-linux-x64` | STALE/conflicting | contradicted by agent-browser-cleanup-by-session-name; F2 live_audit.sh:19-20 |
| lifecycle-guard-blocks-out-of-repo-edits | out-of-repo Edit/Write blocked by guards needing task_id | still-true | lifecycle_contract.py:503-532 (resolve_edit); migration-guard.sh:29, decision-number-guard.sh:35 call validate-input before path filter |
| lifecycle-guard… | guards path-scoped in-repo | still-true | decision-number-guard.sh:57; test-file-guard.sh:32 |
| lifecycle-handoff-shared-worktree-collision | handoff compares whole WATCH vs baseline; begin --artifact repo paths refused | still-true | lifecycle_contract.py:26,384-394; task_state.py:66-68 |
| never-write-into-running-lane-worktree | uncommitted-artifacts.sh blocks researcher on foreign files | still-true | settings.json:38-44 |
| workflow-lane-worker-runs-in-parent-worktree | workflow agent() ignores isolation frontmatter | unverifiable (runtime); frontmatter present | lane-worker.md:6 |
| required-gates-stale-pr-base | verify_evidence parent == event base/head | still-true | scripts/harness/verify_evidence.py:57-58 |
| design-system-program-state (+index) | harness upgrade on hold; lane-hygiene intent-only; H1–H14 | STALE | #130 merged; researcher-task.sh, _lock.sh:136-146; residuals file has H15 |
| prod-deploy-procedure | ship-gate requires local prod tag at sha, else exit 65 | still-true | infra/_lib/ship-gate.sh:47-53 |
| worktree-sandbox-rejects-compound-commands | Bash guard shape rejections | unverifiable (Claude Code runtime) | — |
| headroom / prefer-root-cause / verify-before-publishing / dev-deploy | not harness-code claims | n/a | — |

## 7. Legacy ledger
- No session hook auto-reads HANDOFF/work-items: bootstrap-diet.sh:89 explicitly forbids old §1 5-doc read.
- Still enforced/written by code: `work-item-consistency` in ALL_GATES (gates/run.sh:288), CI job (.github/workflows/ci.yml:596), merge driver installed by worktree-setup.sh:213-221 (.gitattributes:34), decision-number-guard PreToolUse on PLAN-SoT.md. Commits 7d662b9b/67ce0608 (09-24) and d5e224db (09-25) wrote work-items.yaml. Consistent with AGENTS.md ("legacy 항목을 실제로 변경할 때만 … 정합 유지").
- R-HARNESS-PR-CENTRIC Task 5 open boxes (:215-216) and "호환 종료 미완료" (:70,:226) — ledger transition not done (on hold).

## 8. Sibling-checkout lock risk
- 30/31/32 CoLAB-v2 share host mutex path `${TMPDIR:-/tmp}/colab-v2-gate-host-mutex/host` (_lock.sh:78). 30 (f0be4268) and 31 have gate_mutex_spawn; 32 (02d251d8) does not → 32's frontend-visual daemons can keep the shared host lock after its gate ends; 31's serial gates wait up to COLAB_GATE_MUTEX_WAIT=900 s then red(78). #140 body flagged "30·31"; the at-risk checkout is now 32.

## 9. Open questions
- Was the #130 researcher live smoke / `/hooks` re-trust done on this PC? No repo record.
- Has anyone re-measured limit-hit rates after #131 (outcome 8)?
- Should 32 CoLAB-v2 be updated or retired?
- Is origin/reseed-reset-gate superseded by reseed-reset-gate-develop?
