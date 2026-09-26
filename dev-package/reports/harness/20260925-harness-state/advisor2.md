VERDICT: ACCEPT-WITH-CHANGES

**1. Findings wrong / overstated / mis-tagged (spot-checked against code at develop @67a03a05)**
- R1-hooks-missed (spaced `-C` bypass, HIGH): CONFIRMED by code. `git-guard.sh:167` does unquoted `set -- $seg`, and the `-C` case does `shift 2`, so `-C "<home>/00` consumes only the first path fragment and `CoLAB/31` becomes `sub`; every rule is skipped. Branch is also judged from payload `$CWD` (line 143), not the `-C` target. The rc=0/rc=2 measurements are reader-run and plausible. This is the single most important defect and it has no `verify:` tag — all 11 "-missed" lines were never adversarially verified; report must label them "reader-verified, spot-checked" (this one) or "unverified" (the rest, e.g. `git pull --no-ff` gap).
- R1-2 / R5-7 (test-file-guard): CONFIRMED. `test-file-guard.sh:32` is `[ "${COLAB_FIX_LANE:-}" = "1" ] || exit 0`. Use the corrected wording: guard is off on Claude lanes; `begin --scope` + H7 is the only backstop, and it acts at handoff, not at edit time.
- R3-1 / R5-9 (merge-parent false red): CONFIRMED at `verify_evidence.py:57-58`. Use corrected severity medium (fail-closed noise, not a false green).
- R3-5 / R5-6 (`run.sh` drops extra args): CONFIRMED, `run.sh:9` `GATE="${1:-}"`. Use medium, not high — no tracked caller passes multiple gates.
- R3-3 (remote rules): CONFIRMED live — only ruleset 23379713 (product), develop has `required_status_checks: null`, `required_pull_request_reviews: null`. But repo docs disclose this as unapplied; report as "known, disclosed gap", not as drift.
- R2-1 / R5-governance-missed (measurement-lane says no mutex): CONFIRMED stale text at `measurement-lane.md:16-18`; `_lock.sh:80 gate_host_mutex_acquire` exists. Low severity — the "one gate lane at a time" policy still stands per ADR-0002 §37-40.
- R1-10 (H6/H7 ignore COLAB_HOOKS=0): CONFIRMED (0 hits in all three files), but likely intended (dual-agent.md:56). Report as README drift, not as a bug.
- Status-tag corrections to apply: R1-3 (css-edit-audit lost on Claude) rests on Claude Code docs quoted in the repo, not on a measurement — tag `documented`, not a code fact. R1-21 and R5-19 are single-session observations — say "observed once". R3-13 is `tested` (db-selftest), not `implemented`. R4-3's original sentence "lifecycle tests run only in agent-bridge.yml" is false (see §2). Several R-summaries still carry pre-correction severities (R3 summary calls H6 "biggest", R5-6 "high"); the report must use the post-verify severities.

**2. Measurement vs findings**
- No contradiction. The run supports R4-3's correction: local `gates/run.sh agent-bridge` ran 156 tests including `test_task_runtime` and `test_harness_lifecycle_contract` (green, 10 skipped). It confirms `harness-contract`/`adr-records` are `parallel`-declared, `agent-bridge` is `serial` and takes/releases the host mutex, and no gate-summary JSON is written unless `COLAB_GATE_REPORT_DIR`/`OUTDIR` is set.
- One new minor observation not in any finding: an unknown gate name (`harness`) acquires the host mutex before exiting 2 — exit 2 is outside the 0/1/78 contract (ties to R3-9).
- Important limit: the measurement ran without `COLAB_TASK_ID`, so the whole lifecycle/evidence path (R4, H6/H7, task binding) was never exercised live in this analysis. It is verified by unit tests only. The report must say this.

**3. Missing harness facts**
- Positive baseline is absent: on develop @67a03a05, harness-contract, agent-bridge check and 156 harness unit tests are green, hook registrations match, adapters have no body duplication. Lead with what works before the gap list (ELI7 reader needs the shape).
- No finding states plainly that most Claude-side controls are prose (role bodies, skills) and the mechanical ones are few: PreToolUse git/migration/decision guards (Edit/Write only, Bash-bypassable), H6/H7 SubagentStop, CI evidence chain. Ted should know the mechanical/prose split.
- Whether hooks fire at all for Workflow `agent()`-spawned agents (H6/H7, worktree-setup) is only an open question; it is the same class as R2-2 and should be named as an unknown.
- Time cost of `worktree-setup` per lane-worker spawn (4 venvs + npm ci, no timeout) is unmeasured; H10 re-trust is unverifiable from the repo.

**4. TOP 7 for Ted (ordered)**
1. In this repo (path with spaces), `git -C "<abs path>" …` — the form AGENTS.md tells agents to use — bypasses every git-guard rule; force push / `branch -D` on develop passed. (R1-hooks-missed; R1-4, R1-5)
2. The fix-lane test-edit guard never arms on Claude; only `begin --scope` + H7 catches test/gate edits, and only at handoff; skills still say the guard is on; Bash writes bypass all Edit/Write guards. (R1-2, R5-7, R1-7)
3. develop has no required status checks and no PR rule; red CI blocks nothing on develop; the ruleset proposal targets a `main` that no longer exists; `gates.required` and pr_contract are unenforced. (R3-3, R3-2, R4-2, R4-5)
4. Lane isolation is not guaranteed: a Workflow-spawned lane-worker committed in the parent worktree once, docs call isolation automatic, and the lane body never checks its checkout; whole-checkout handoff diffs make sibling writers block each other. (R2-2, R4-13, R4-missed)
5. Evidence lifecycle has no close/GC: 204 tasks, 153 MB, 74 orphans in `.git/colab-harness`; H6/H7 bind to whichever task the agent names, so a fresh `begin` can reset the baseline after edits. (R4-11, R4-12, R4-judges-missed)
6. Recurring false reds and exit-code drift: merge-parent check goes red whenever develop moves after PR open (workaround only in memory); `run.sh a b c` runs only `a`; 78/1 precedence differs across aggregators and unknown gate → exit 2. (R3-1/R5-9, R3-5/R5-6, R3-9)
7. Guidance drift that misleads every session: memory index lines (no mutex, 12/30 turns, "on hold", no worktree hook), measurement-lane role body "no mutex", README hook section, and sibling checkouts 32 (no fd fix) / 33 (no mutex) sharing the host lock path. (R5-1..4, R5-12, R5-governance-missed, R2-1, R1-12)

**5. Must NOT appear as fact**
- "/hooks re-trust was not done" or "researcher-task/ponytail hooks are inactive" — only unrecorded, unverifiable from repo (R1-19, R5-10, R2-10).
- "PostToolUse stdout is dropped on Claude" as measured — it is quoted docs, unmeasured (R1-3).
- "Researchers in one checkout block each other" — H4 itself marks it inference (R1-11, R4-13).
- "Workflow agent() ignores frontmatter isolation" as a mechanism — one observation, cause recorded only in user memory (R2-2).
- "H6/H7 ignoring COLAB_HOOKS=0 is a bug" — likely intended (R1-10).
- "git-guard matches `gh pr merge` anywhere in text" — refuted; segment-start only (R5-19).
- "33 CoLAB-v2 is in active use", Claude Code default hook timeout, matcher regex semantics, "harness upgrade on hold", "run.sh has no mutex" — all unverified or stale.
- Any `-missed` item other than the spaced `-C` bypass as "verified".