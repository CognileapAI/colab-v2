# R4-judges-evidence — judge scripts and lifecycle/evidence model (final)

Repo: develop @ 67a03a05 (read-only analysis, 2026-09-25). Paths repo-relative.

## 1. What harness-contract (scripts/harness/check.py) verifies
Entry: gates/run.sh:312-313 -> python3 scripts/harness/check.py. CI: .github/workflows/agent-bridge.yml:57-62 (separate workflow, path-filtered; NOT in ci.yml required-gates bundle, ci.yml:848).
1. load_contract/validate_contract (config.py:55-122): JSON parse; schema colab-harness/1; TOP_LEVEL keys (schema, project, commands, gates, evidence, sources, adapters, paths, publication, hygiene); default_branch==develop, deployment_branch==product; gates.required non-empty unique; states == {0,1,78}; relative paths; hook_registrations {event,matcher}; hygiene ints/lists. Failure -> 78.
   NOT validated: adr_gate, pr_contract, agreement_snapshot, transition sections (config.py:13-24) — read raw by each judge.
2. check_contract (config.py:125-206): product source + exact CLAUDE.md adapter text; each rule/role source non-empty + exact .claude adapter body; Codex role toml name + developer_instructions contains path; each hook_names entry: scripts/harness/hooks/<n> exists, .claude/hooks/<n> is exactly one exec line; lifecycle_contract.py exists; _check_hook_wiring (config.py:209-240) each hook registered in .claude/settings.json under declared event+matcher, and no undeclared registrations; adapters.required_files exist; paths.required exist; retired_roots absent.
3. check_always_on_lines (config.py:243-268): AGENTS.md, CLAUDE.md, .claude/rules/*.md <= 120 lines.
4. check_home_paths (config.py:271-323): no /home/<u>/, /Users/<u>/, /mnt/x/Users/<u>/, X:\Users\<u>\ in git-listed files under AGENTS.md CLAUDE.md .agents .claude .codex docs; allow /home/user/; zero scanned -> 78.
5. check_gate_parallelism (check.py:25-75): ALL_GATES in gates/run.sh == declared set in gates/config/parallelism.toml (both directions) via gates/tools/parallelism.py; bad values red.
Readiness 78 still prints judged errors first (check.py:96-106).
NOT checked: gates.required (only counted in the green line, check.py:113), commands.*, publication.*, evidence.task_runtime vs task_state.py, codex_only_skills.
Tests: scripts/tests/test_harness_config.py (15 tests) e.g. :147 test_declared_hook_must_be_registered_under_its_event_and_matcher, :180, :204, :230, :269. check_gate_parallelism itself only stubbed (:240) — no fixture test of an undeclared gate.

## 2. pr_contract (scripts/harness/pr_contract.py)
Required sections = evidence.required_pr_sections (harness.yaml:38: 목적 범위 계획 결정 검증 남은 제약) + pr_contract.required_sections ([] harness.yaml:112) (pr_contract.py:13-17).
validate (pr_contract.py:31-97): visible() strips HTML comments/fences; Head-SHA exactly once, 40 hex, == --head; Plan-Ref present, no <..>/TODO/TBD; each section heading `## X` exactly once, non-empty, no placeholder; `검증 상태:` in {미검증, 부분 검증, 검증됨}; mode complete requires 검증됨; 검증됨/complete require CI evidence JSON (schema colab-ci-evidence/1, head match via event_shas.head_sha/after_sha/commit), Evidence-Ref + CI-Ref, counts/jobs coherent, green>0 no red, and --artifact-root bundle recomputed by verify_evidence.verify_ci_bundle. CLI: Evidence-SHA256 line must equal sha256 of --evidence file (:113-116).
Intent-Ref is NOT a PR-body field; it is a commit trailer judged by scripts/harness/intent_ref.py (gate intent-ref, CI job ci.yml:665-679, PR only, base..head).
Wiring: pr_contract is a local CLI only — no gate case, no CI step (git grep: only docs/reports/tests/publish.sh). Test: scripts/tests/test_pr_contract.py:101 test_pr_draft_and_completion_require_explicit_sha_and_evidence, :32 test_verified_claim_consumes_registry_bundle_in_both_modes.
Practice: merged PR #140 #144 #159 #160 bodies all have the 6 sections, Plan-Ref, Head-SHA, 검증 상태: 부분 검증, Evidence-Ref 없음/로컬 — complete mode never used.
Template: .github/pull_request_template.md:1-37 matches the contract.

## 3. ADRs (scripts/harness/adr_gate.py)
Root docs/decisions (harness.yaml:103-107); 9 records 0001-0009 + README + _template. Checks (adr_gate.py:154-288): NNNN-slug.md in root; `# ADR-NNNN:` title; single 상태/날짜/대체함/대체됨 fields; status in proposed/accepted/superseded; valid date; 6 sections 배경/결정/검토한 대안/결과와 감수한 비용/재검토 조건/근거 non-placeholder; 대체함/대체됨 = 없음 or matching link, reciprocal, no cycles; superseded needs 대체됨; proposed cannot supersede; accepted/superseded history not deleted/reverted vs --base. --all with 0 records -> exit 1.
Gate adr-records gates/run.sh:318-322 (base ${COLAB_ADR_BASE:-HEAD}); CI ci.yml:591-595 with COLAB_ADR_BASE = PR base sha, wrapped in verify_evidence record (planning-gates producer, ci-producers.json:282-289).
Tests: test_harness_record_gates.py:61, :86 test_zero_adr_records_is_red_not_a_silent_pass, :96 test_deleting_an_accepted_adr_is_red_against_the_pr_base, :113; test_pr_contract.py:83.
Locally base=HEAD -> committed deletions of accepted ADRs invisible outside CI (documented run.sh:321).

## 4. intent_ref
intent_ref.py:418-499. (1) if fork..head touches services/ frontend/src/ contracts/ db/ scripts/ gates/ .agents/ .claude/ .codex/ (:354-355) at least one commit must carry a valid Intent-Ref trailer naming an existing intent at head. (2) intents approved at base OR fork (메타 line has 승인 and not 미승인) are append-only (ordered-subsequence of raw lines). Tests test_harness_record_gates.py:197-365 incl. :365 frozen 62-intent classification table. CI job not wrapped by verify_evidence record (ci.yml:679) but in ci-required needs (ci.yml:848,859). infra/, .github/, docs/, dev-package/ out of subject scope (consistent with ADR-0007:13).

## 5. Task runtime lifecycle (scripts/harness/hooks/lifecycle_contract.py + task_state.py)
Shim: .claude/hooks/lifecycle_contract.py:1-6 runpy -> scripts/harness/hooks/lifecycle_contract.py. CLI via scripts/agent-bridge.py:364 (lifecycle), :376 (verify-report).
Storage (task_state.py:19-63): <git-common-dir>/colab-harness/<checkout_id=sha256(toplevel\0private-gitdir)[:32]>/<task_id>/task.json; per run <task_id>/<run_id>/{gate-summary.json, logs/N.log, artifacts/...}; confined() rejects symlinks/.. /non-canonical (:33-46). Legacy colab-task/1 in <private-gitdir>/colab-lifecycle/<task>.json (lifecycle_contract.py:165-172).
Roles: TASK_ROLES researcher + GATE_ROLES (lane-worker, measurement-lane) (lifecycle_contract.py:48-49; task_state.py:12). measurement-lane may close with red rows (:55, :335).
begin (:210-284): role check; scope only for gate roles; scope -> refuse unmerged index, record started_index=write-tree; colab-task/2: task_id/run_id uuid, baseline=snapshot(root) (sha256 of every tracked+untracked non-ignored file), started_identity commit/tree; lane requires explicit gates; researcher no gates; artifacts must be runtime:artifacts/<name>.
gate-start/run-gates (:432-500): new run_id per run, rebind paths, run each declared gate once (no all/task), rows with exit->state (78 or readiness line -> red_준비), report with task_evidence before/after (file snapshot hash + commit/tree); before!=after -> 78.
handoff (:601-609): builds COLAB_HANDOFF JSON {task_id, mode, summary, artifacts{path:sha}, run_id} and self-runs stop(); prints marker. Nothing persisted — no closed state.
stop (:350-429) = H6 (uncommitted-artifacts.sh, researcher) / H7 (lane-gate-summary.sh, lane-worker|measurement-lane): exactly one COLAB_HANDOFF line; run_id matches; artifacts hash match; role/agent_id; summary non-empty; researcher read-only/draft-return: no file changed anywhere in checkout + HEAD unchanged; artifacts: changes subset of declared artifacts within WATCH; lanes: mode complete, scope check, verify_task_report (report schema, counts, required gates, no red unless measuring, commit/tree == HEAD, before==after==now).
Scope (:81-97, :403-427): changed = snapshot diff ∪ diff started..HEAD ∪ diff --cached started_index; defaults dev-package/reports/** + lifecycle-evidence.md; message names two exits. Tests test_task_runtime.py:244-368 (10 scope tests).
No close/GC command exists (subcommands :542-569).
Tests: test_task_runtime.py (31 tests), test_harness_lifecycle_contract.py (29 tests) — e.g. :151 test_actual_summary_producer_binds_task_and_rejects_changed_during_gate, :165 test_new_gate_run_invalidates_old_success_even_if_producer_fails, :288 test_measurement_lane_closes_with_a_red_row_on_both_harnesses, :397 test_agent_identity_mismatch_blocks.
BUT gates/run.sh:315-316 harness-contract-selftest runs only test_harness_config, test_harness_evidence, test_pr_contract, test_harness_work_state, test_harness_record_gates — lifecycle tests run only via agent-bridge.yml unittest discover (agent-bridge.yml:63-64).

## 6. Runtime census (read-only, measured 2026-09-25)
.git/colab-harness: 42 checkout keys, 204 task.json, 153 MB (task.json total 144 MB — every task.json >500 KB because baseline stores a hash per repo file; logs 5.1 MB). Roles: researcher 112, lane-worker 82, measurement-lane 10. Scoped tasks: 2 (both 2026-09-25, design-fix-followups-grill). 74 tasks point to checkouts that no longer exist (removed .claude/.codex worktrees, /tmp dirs) = orphans; 130 in main checkout. 12 gate-role tasks have no gate-summary.json in current run. Legacy .git/colab-lifecycle: 2 entries. Tasks by mtime day: 09-15 69, 09-16 71, 09-17 17, 09-18 15, 09-24 11, 09-25 21. Most recent: 2026-09-25 17:45 measurement-lane (design-fix-followups-grill, GONE). Open vs closed is not determinable (handoff persists nothing).
Local branches left: worktree-agent-abe5bbb87a35cd7b6 (f3846f32), worktree-agent-a06b599e273033d13, worktree-agent-a20a6e576f57347f9, integration/r-user-features-review-evidence; git worktree list = main only.

## 7. f3846f32 (branch worktree-agent-abe5bbb87a35cd7b6, parent 12225b9b in develop)
Stat: docs/development/lifecycle-evidence.md +10, scripts/harness/hooks/lifecycle_contract.py +28/-4, scripts/tests/test_task_runtime.py +44.
Change: new handoff_evidence()/handoff_record(); for gate roles in mode complete the COLAB_HANDOFF JSON gains evidence={gate_summary: absolute report path, sha256, task_id, run_id}; stop() compares it only if present (optional key).
Coverage today: NOT in current code (lifecycle_contract.py:601-609 has no evidence key). Approved spec S-HARNESS-LANE-HYGIENE-20260924.md:12 says handoff JSON contract unchanged and :47-48 lists "handoff JSON `evidence` 키" as 범위 밖; the approved ② was realised as a checklist rule .agents/skills/colab-v2-work/SKILL.md:40 (advisor ② prompt carries gate-summary absolute path + 3 counts). Partial machine substitute: `lifecycle gate-snapshot --task` prints report path (lifecycle_contract.py:322-324, :582-583). Legacy merge-tree vs develop: 1 textual conflict in lifecycle-evidence.md (scope paragraph inserted at same place); code/tests merge cleanly. Worktree removed; branch remains. Classification: draft, unapproved, outside approved scope.

## 8. Other judges
- verify_evidence.py: record (CI producers; command must equal registry; commit==GITHUB_SHA) and ci (aggregate; recompute from bundle). ci_command maps OSError/JSONDecodeError/SubprocessError to red_judgment exit 1 (:362-365); record_command maps EvidenceError (judgement-type mismatches) to 78 (:404-408) — inverted vs ADR-0004. verify_ci_bundle validates content, not provenance (:246-251).
- work_state.py: local validator for colab-work-state/1; new mode via COLAB_WORK_STATE_MODE=work-state in work-item-consistency; transition-complete requires transition.mode=='retired' (:253) vs harness.yaml:126 legacy-compatibility; hard-coded PRs {35,38} (:282). Tests test_harness_work_state.py (13), :181.
- release_evidence.py: enforced by infra/dev/ship.sh:12-18 (78 without env), infra/prod/ship.sh:16, scripts/deploy_release.py:38-47. Tests test_harness_release_evidence.py (16). Docs drift: release-evidence.md:43,45 and docs/development/github-ruleset.json:2,6 still say main.
- agreement_snapshot.py: local CLI; --check returns 1 on unreadable snapshot (no 78) (:157-180, :238-241); used nowhere but docs/decisions/README.md and tests.
- run_unittest.py: collected=0 / import failure / not all executed -> 78 (:261-289); used by CI planning-regression (ci.yml:608).

## Findings summary: see StructuredOutput R4-1..R4-17.
## Open questions
- Is the agent-bridge.yml "compatibility" job a required status check in the live ruleset? (harness-contract + lifecycle unit tests only run there.)
- Should orphaned colab-harness tasks (74) be GC'd, and who owns that? No doc covers retention.
- Is f3846f32 to be dropped (spec says out of scope) or re-proposed via a new intent?
