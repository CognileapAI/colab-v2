# R1-hooks — Claude Code hooks (FINAL)

Repo: develop @ 67a03a05. Read-only static analysis; no hooks/gates executed deliberately.
One live observation: git-guard blocked my own notes-writing heredoc (see R1-21).
All .claude/hooks/*.sh are 3-line adapters that exec scripts/harness/hooks/<same>.sh.
Real logic lives in scripts/harness/hooks/*.sh (shared with Codex via scripts/agent-bridge.py).
.claude/hooks/lifecycle_contract.py is a runpy shim to scripts/harness/hooks/lifecycle_contract.py (R4 owns internals).

## settings
- .claude/settings.json:2 effortLevel "high"; :3-5 worktree.baseRef "head" (user-approved 2026-09-17 per memory).
- No permissions key, no timeout on any hook (Codex .codex/hooks.json sets 25-580s).
- .claude/settings.local.json:1-5 env only: COLAB_TEST_ENV_FILE=~/.colab-v2-test-31.env. No hooks, no COLAB_HOOKS.
- .agents/harness.yaml:49-62 hook_names + hook_registrations == settings.json exactly (11 hooks, same event+matcher).
  Tested: scripts/tests/test_harness_config.py:147 test_declared_hook_must_be_registered_under_its_event_and_matcher;
  adapters: scripts/tests/test_harness_source_layout.py:58 test_hook_judges_are_shared_and_claude_files_are_adapters.

## Hook table (event/matcher; decision; python3 missing; kill switch; tests)
- bootstrap-diet: SessionStart startup|clear; plain stdout to context, exit 0 always; open; COLAB_HOOKS L2; test_harness_config.py:19, test_harness_lifecycle_contract.py:401
- worktree-setup: SubagentStart lane-worker; npm ci + 4 service venvs + gates venv + merge driver, exit 0 always; open; L2; registration test only
- researcher-task: SubagentStart researcher; runs agent-bridge lifecycle begin --role researcher, prints ids, exit 0 always; open; L2; test_task_runtime.py:456-558
- uncommitted-artifacts (H6): SubagentStop researcher; lifecycle_contract.py stop --role researcher, exit 2 blocks stop; CLOSED; NO kill switch; test_harness_lifecycle_contract.py:55,229,252, test_task_runtime.py:468
- lane-gate-summary (H7): SubagentStop lane-worker|measurement-lane; lifecycle_contract.py stop --role lane-worker --role measurement-lane; CLOSED; NO kill switch; test_harness_lifecycle_contract.py:48,288,292,306,313
- git-guard: PreToolUse Bash; validate-input --field command then segment parse, exit 2 + stderr; CLOSED at L82 (L90 dead); L2; test_agent_bridge.py:478-507, test_harness_lifecycle_contract.py:319,328
- migration-guard: PreToolUse Edit|Write; validate-input --field file_path, blocks db/{platform,ai}/versions/*.py already in origin/develop, exit 2 if origin/develop ref missing; CLOSED; L2; test_agent_bridge.py:514
- decision-number-guard: PreToolUse Edit|Write; validate-input, PLAN-SoT section 9 new row numbers must be origin/main max+1; CLOSED; L2; test_harness_lifecycle_contract.py:366,381
- test-file-guard: PreToolUse Edit|Write; armed only if COLAB_FIX_LANE=1 (L32), blocks frontend/test, services/*/tests, gates, contracts; CLOSED when armed; L2 + COLAB_ALLOW_TEST_EDIT; test_harness_lifecycle_contract.py:394, test_agent_bridge.py:509,537
- css-edit-audit: PostToolUse Edit|Write; css_audit.py row for frontend/src/*.css as PLAIN stdout, exit 0; open; L2; only bridge test with mocked subprocess test_agent_bridge.py:157
- ponytail-inject: PostToolUse Edit|Write; JSON additionalContext once per session+agent per 60 min on code roots; open; L2; test_agent_bridge.py:183

## Findings
R1-1 strength/tested low — registry parity harness.yaml:49-62 == settings.json:7-100; adapters are thin shims; tested (above).
R1-2 gap/implemented HIGH — test-file-guard inert on Claude: gated on process env COLAB_FIX_LANE (test-file-guard.sh:32); nothing sets it per Claude lane (only Codex pass-through scripts/agent-bridge.py:278, scripts/dev.ps1:102). Observed: dev-package/prd/specs/S-DESIGN-FIX-20260924.md:394; residual H3 (draft) residuals.md:38,68-73. Docs still claim it works: .agents/skills/design-review/SKILL.md:101,106; docs/development/dual-agent.md:60.
R1-3 gap/implemented MED — css-edit-audit prints plain stdout on PostToolUse (css-edit-audit.sh:74); repo's own quoted docs (bootstrap-diet.sh:24-26, worktree-setup.sh:41-42) say only SessionStart/SubagentStart plain stdout reaches context. Header claim css-edit-audit.sh:21 wrong. ponytail-inject uses JSON additionalContext (ponytail-inject.sh:76). Codex bridge wraps plain text (scripts/agent-bridge.py:354) so Codex gets it, Claude does not. Claude route untested.
R1-4 risk/implemented MED — git-guard evaluates the branch of the payload cwd (git-guard.sh:143) and skips the -C path only to locate the subcommand (L191-199). A non-ff merge aimed via -C at a develop checkout, or a cd-then-merge chain, issued from a feature-branch cwd passes. No test.
R1-5 risk/implemented MED — git-guard exact-argv gaps: gh pr merge caught only as the literal argv (L181-184); gh -R o/r form and gh api pulls/N/merge pass; it also applies to the main thread, not only agents; force detection uses exact tokens (L207) so bundled -fu passes rule 2; subagent push of HEAD while on develop passes (L213-243). No gh test anywhere in scripts/tests. Wrapped forms acknowledged (L74-76).
R1-6 strength/tested low — protected set main|master|develop|product (L145,156), product push/merge block (L223-225,247), remote delete (L226-228), branch -D (L261-272), reseed ACK (L134-137); tested test_agent_bridge.py:483,487; test_harness_lifecycle_contract.py:328.
R1-7 risk/implemented MED — Edit|Write guards are matcher-bound (settings.json:69); Bash writes (sed -i, cat redirect, python) bypass migration/decision/test-file guards; git-guard only parses git/gh (L181,188). Memory lifecycle-guard-blocks-out-of-repo-edits.md tells agents to use Bash heredoc. README.md:115-119 calls hooks friction, not a boundary.
R1-8 strength/tested low — out-of-repo Edit/Write block confirmed: migration-guard.sh:29 and decision-number-guard.sh:35 always call validate-input; lifecycle_contract.py:514-530 resolve_edit/inside (L126-127) raises unless a colab-task/2 task with matching agent_id; tested test_task_runtime.py:66. The block surfaces from hooks named for migrations/decisions (confusing).
R1-9 drift/implemented low — fail-closed on python3 (git-guard.sh:82, migration-guard.sh:28, decision-number-guard.sh:34, test-file-guard.sh:38) contradicts retained headers (git-guard.sh:71-72, migration-guard.sh:21, decision-number-guard.sh:27, test-file-guard.sh:27); later exit-0 fallbacks are dead code (git-guard.sh:90, migration-guard.sh:32, decision-number-guard.sh:38, test-file-guard.sh:42). Supersession noted in-file (git-guard.sh:3-4).
R1-10 drift/implemented MED — README.md:89 says every hook's first line honors COLAB_HOOKS=0, but uncommitted-artifacts.sh:1-5 and lane-gate-summary.sh:1-5 have no such check (lifecycle_contract.py has none either). With COLAB_HOOKS=0, H6/H7 still block stops.
R1-11 risk/implemented MED — researcher-task.sh always exits 0 even when begin fails (L50-53); H6 then blocks every stop until maxTurns (.claude/agents/researcher.md maxTurns 50). Shared-checkout researchers reject each other's handoffs (residual H4 draft residuals.md:39,76-81).
R1-12 drift/implemented MED — README hook section stale: 7 hooks (README.md:61) vs 11; migration-guard origin/main (README.md:70; also migration-guard.sh:5-12 header) vs code origin/develop (migration-guard.sh:72-78); git-guard main/master only (README.md:69) vs develop|product (git-guard.sh:145); H6/H7 described as untracked-file scan and reports gate-summary.json (README.md:72-73) vs lifecycle task runtime (uncommitted-artifacts.sh:5, lane-gate-summary.sh:5); README.md:57 latest R-*.md only vs bootstrap-diet.sh:75-86.
R1-13 drift/implemented low — decision-number-guard baseline origin/main (decision-number-guard.sh:66-68) while migration-guard moved to origin/develop (migration-guard.sh:72); PLAN-SoT legacy per AGENTS.md, so low impact.
R1-14 drift/implemented MED — memory measurement-needs-provisioned-worktree.md says no worktree hook exists and the earlier "npm ci + venv" claim was wrong; code worktree-setup.sh:141-210 does provision 4 service venvs + npm ci + gates venv, but only on SubagentStart lane-worker (settings.json:19-27). Not for EnterWorktree (no WorktreeCreate), measurement-lane, gate-runner, researcher. colab-rules.md:69 "enforced by hook" is true only for lane-worker. No behavioral test.
R1-15 risk/implemented MED — worktree-setup acts on payload cwd (L65-67) and deletes any venv lacking its stamp (L117, L151-152). Lane-workers running in the parent checkout (memory workflow-lane-worker-runs-in-parent-worktree.md) or parallel spawns into one cwd delete/rebuild manually built venvs concurrently, with no lock, possibly during a gate. No explicit timeout in settings.json.
R1-16 drift/implemented low — baseRef head (settings.json:3-5) vs stale text worktree-setup.sh:248-256 (fresh = origin/main, P-E branch) and colab-rules.md:67 (origin/<default>); worktree-setup checks only ~/.colab-v2-test.env (L247) while gates/run.sh:264 honors COLAB_TEST_ENV_FILE set by settings.local.json:3.
R1-17 risk/implemented low — reseed ACK regex (git-guard.sh:134) misses quoted or indirect assignment (export with quoted NAME=, read, printf -v, Write to env file); acknowledged not a boundary (L130-133).
R1-18 drift/documented low — compound-command rejection (memory worktree-sandbox-rejects-compound-commands.md) is not repo code: settings.json has no permissions; git-guard segments on and-and/or-or/semicolon/pipe (L149) and denies only enumerated forms. Likely Claude Code built-in worktree path check; not testable/tunable in repo. BUT see R1-21: git-guard itself does reject heredoc bodies that contain a git merge/push after a separator.
R1-19 pending/documented MED — /hooks re-trust after #130 for SubagentStart researcher and PostToolUse ponytail, plus the researcher live smoke, not recorded (docs/development/dual-agent.md:87-89; residual H10 draft residuals.md:45,121-126).
R1-20 risk/implemented low — hook commands resolve via CLAUDE_PROJECT_DIR (settings.json:13..96) = main checkout, not the worktree (worktree-setup.sh:32-38); lane edits to scripts/harness/hooks are judged by the main checkout's copy.
R1-21 risk/measured MED — git-guard false positive on data text: newlines become segment separators (git-guard.sh:106) and the splitter cuts on and-and/semicolon/pipe inside heredoc or quoted text (L149), so a heredoc line containing an and-and followed by a git merge invocation was judged as a real non-ff merge on develop and blocked (this session, 2026-09-25, while writing this notes file; stderr "차단(H3 git-guard) — 현재 브랜치가 develop 인 상태의 git merge(--ff-only 없음)"). Explains part of the memory-reported heredoc rejections; wastes turns when agents write docs/PR bodies mentioning git commands. No test for quoted/heredoc data.

## Known-context verdicts
- git-guard blocks gh pr merge for agents: PARTIAL — literal form blocked for everyone incl. main thread; gh -R and gh api pass; untested.
- worktree guard rejects compound commands: mixed — no repo hook rejects by shape, but git-guard misreads heredoc/quoted text as commands (R1-21).
- lifecycle guard blocks Edit/Write outside repo: CONFIRMED via validate-input in migration-guard/decision-number-guard.
- worktree-setup does not provision venvs/npm: REFUTED for lane-worker spawns; TRUE for EnterWorktree, measurement-lane, other agent types.

## Open questions
- SubagentStart payload cwd for an isolation-worktree lane-worker: new worktree root or parent?
- Claude Code default hook timeout (none set) vs npm ci + 4 venv installs in worktree-setup.
- /hooks re-trust state on this PC for researcher-task and ponytail-inject (H10).
- Current Claude Code behavior for PostToolUse plain stdout (confirms R1-3).
- Is H6/H7 ignoring COLAB_HOOKS=0 intentional? Not documented.
- Matcher semantics for hyphenated agent names (lane-worker) — exact vs regex substring.
