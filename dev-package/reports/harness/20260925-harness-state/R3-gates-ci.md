# R3-gates-ci — gate runner and CI (final)

Repo: develop @ 67a03a05. Read-only. No gates/tests run. Remote state read via `gh api` GET (2026-09-25).

## 1. Required gates (.agents/harness.yaml:18-31) -> run.sh case -> CI

| gate | run.sh case | CI job (ci.yml) | path filter | producer in .agents/ci-producers.json |
|---|---|---|---|---|
| rls-effect | run.sh:536 | schema-gates ci.yml:416 | db, core-api (ci.yml:396) | schema-gates |
| migration-single-head | run.sh:508 | schema-gates ci.yml:410 | db, core-api | schema-gates |
| contract-lint | run.sh:378 | contract-gates ci.yml:244 | contracts (contracts/**, gates/**) | contract-gates |
| event-lint | run.sh:387 | contract-gates ci.yml:256 | contracts | contract-gates |
| generated-up-to-date | run.sh:771 | contract-gates ci.yml:266 | contracts | contract-gates |
| import-boundary | run.sh:481 | boundary-gates ci.yml:374 | core-api/ai/viz/pw/infra/contracts | boundary-gates |
| service-tests-core-api | run.sh:668 | service-tests matrix ci.yml:548 | RUN expr ci.yml:491 | service-tests-core-api (filters core-api, contracts) |
| frontend-test | run.sh:417 | frontend-gates ci.yml:319 | frontend, contracts | frontend-gates |
| seed-plan-drift | run.sh:346 | planning-gates ci.yml:605 (COLAB_SEED_PLAN_NO_FILES=1 exempt) | dev-package | planning-gates |
| adr-records | run.sh:318 | planning-gates ci.yml:595 | dev-package | planning-gates |
| agent-bridge | run.sh:308 (6 unittest files) | NONE via run.sh. agent-bridge.yml:50,64 runs `agent-bridge.py check` + `unittest discover -s scripts/tests` | agent-bridge.yml:4-34 (PR only) | none |
| harness-contract | run.sh:312 | agent-bridge.yml:62 (plain bash, no evidence record) | agent-bridge.yml paths (PR only) | none |

- `gates.required` is only shape-checked (scripts/harness/config.py:71-73) and counted in text (scripts/harness/check.py:113). Nothing enforces that the 12 ran (CI or task mode). Task mode runs task['gates'] (lifecycle_contract.py:468-479).
- All 12 are in ALL_GATES (run.sh:284-305); ALL_GATES=76 = 59 parallel + 17 serial in parallelism.toml.

## 2. Exit semantics
- harness.yaml:32 states 0/1/78; config.py:74-75 asserts that map.
- run.sh single gate: child exit passed through (run.sh:248). gate_state_of: 0 green, 111|78|marker readiness, else judgment (run.sh:103-108).
- `all`: rc=1 for ANY non-zero incl. readiness-only (run.sh:900,969) -> never 78.
- `selftest` aggregate: judgment precedence then 78 (run.sh:743-744).
- lifecycle run_gates: readiness precedence (78 if any red_준비 even with red_판정) (lifecycle_contract.py:500) + 78 if files changed (498-499).
- verify_evidence.verdict: judgment precedence (verify_evidence.py:137-143). EvidenceError -> 1, EvidenceReadinessError -> 78 (357-366).
- usage / unknown gate -> exit 2 (run.sh:971-977) -> counted as red_판정 everywhere.

## 3. Host mutex (gates/tools/_lock.sh)
- Path `${TMPDIR:-/tmp}/colab-v2-gate-host-mutex/host` (_lock.sh:78). Only for `serial` (or undeclared) gates (run.sh:163-182; all: run.sh:850-872 per gate).
- flock -n, then flock -w COLAB_GATE_MUTEX_WAIT (default 900, non-numeric -> 900) with ::gate-waiting:: lines (_lock.sh:104-117).
- flock missing / mkdir fail / open fail / timeout -> readiness marker + 78 (_lock.sh:89-124). No exemption variable.
- COLAB_GATE_MUTEX_HELD=1 exempts children; CHILD=1 does not (run.sh:152-155, 175). gate_mutex_spawn closes fd for daemon-spawning children (_lock.sh:143-146; frontend-visual.sh:84; run.sh:869-870).
- Tested: gates/tools/gate-host-mutex-selftest.sh cases ⓐ-ⓕ (L23-25, 109-134).
- Separate install lock gate_lock_fd: fixed fd 9, `flock 9` unbounded wait (_lock.sh:28-46), used by _venv.sh:21, contract-lint.sh:31, event-lint.sh:46.
- Host: TMPDIR unset in Claude env -> /tmp/colab-v2-gate-host-mutex exists.

## 4. Postgres slots (gates/tools/_pg.sh)
- COLAB_PG_MAX_CONCURRENT default 4, COLAB_PG_SLOT_WAIT 900, dir COLAB_PG_SLOT_DIR or ${TMPDIR:-/tmp}/colab-v2-gatepg-slots (_pg.sh:72-79). Polls slots every 1s (92-110). Exhausted -> readiness marker + 78 (103-107). flock missing/mkdir/open fail -> 78 (82-99).
- pg_start: docker missing / pull fail / run fail / ready timeout (COLAB_PG_READY_TIMEOUT 60) -> 78 (175-215). No published ports, tmpfs PGDATA, `trap pg_cleanup EXIT INT TERM` (193).
- BUG: that trap replaces caller traps -> service-tests.sh:81-82 SVC_CLEAN (rm -rf $TMP) lost -> 329 /tmp/service-tests-* dirs on host (19 with ai-worker-db/ URL files).

## 5. Gate summary colab-gate-summary/1
- Writer A: gates/tools/gate_summary_json.py (called by run.sh:97-101) from single-gate wrapper (run.sh:205-249, only when COLAB_GATE_REPORT_DIR or COLAB_GATE_OUTDIR set) and `all` (run.sh:959-967). Output = $COLAB_GATE_REPORT_DIR/gate-summary.json (+ $COLAB_GATE_OUTDIR/gate-summary.json). Fields: schema, tree, commit, started, finished, parallelism, counts{green,red_판정,red_준비,red_준비_입력미선언}, gates[{name,status,state,exit,readiness,failures}], targets. With COLAB_TASK_ID: requires declared task report among outputs and adds task_evidence (gate_summary_json.py:118-133). Emission failure never changes verdict (run.sh:97-101).
- Writer B: lifecycle_contract.py run_gates (484-497): 3 counts, no started/finished/parallelism, task_evidence, tree/commit only for colab-task/2.
- Consumers: verify_evidence.verify_gate_summary (146-170), lifecycle validate_report (287-316), lane-gate-summary hook (H7).
- CI: verify_evidence.py record sets COLAB_GATE_REPORT_DIR=<artifact>/<producer>/<check> (280-308), so every gate step emits a summary.

## 6. Task mode
- `gates/run.sh task`: requires COLAB_TASK_ID else 78; exec lifecycle_contract.py run-gates (run.sh:29-33).
- COLAB_TASK_ID set & not CHILD: gate-start (78 on failure) (run.sh:37-42). colab-task/2 returns report path -> explicit COLAB_GATE_REPORT_DIR must match (78) -> exec run-bound-gate --gate "$GATE" (run.sh:43-53); requires task gates == [GATE] else ValueError -> 78 (lifecycle_contract.py:588-592, 613). `all`/`task` inside task rejected (468-469).
- colab-task/1 (legacy): gate-start rotates run_id and archives previous report on every call (lifecycle_contract.py:442-452), then normal path.
- COLAB_TASK_ID unset: normal path (mutex -> optional wrapper -> env file -> case).
- Children: lifecycle passes COLAB_TASK_ID + CHILD=1 (471) -> no rebinding, no wrapper, but host mutex still taken (run.sh:163).

## 7. Resource needs (by grep of gates/tools)
- DB (_pg.sh): rls-effect, rls-coverage, schema-diff/ci-schema-diff, service-tests (core-api/ai-service/pipeline-worker), stage2-markers, render-latency, e2e-format-coverage, operator-notifications, db-selftest, preview-tile-slot-selftest, autometa-loss-selftest, artifact-ownership-selftest.
- node/node_modules: contract-lint, contract-breaking, event-lint, frontend-typecheck/test/fixture-reach/design-lint (+selftests), product-reseed-selftest; frontend-visual needs agent-browser + chrome.
- gates/.venv (gates/requirements.txt: import-linter, PyYAML, alembic, SQLAlchemy, psycopg): import-boundary, ai-no-lineage-write, ci-schema-diff.
- service venvs: service-tests*, migration-drift, schema-diff, render-latency, e2e-format-coverage, operator-notifications, stage2-markers, product-release/reseed-selftest, ops-schedule-selftest.
- All non-CI runs need ~/.colab-v2-test.env else 78 (run.sh:264-281).

## 8. Draft residuals (dev-package/intent/2026-09-25-harness-design-round-residuals.md, DRAFT) — still true?
- (a) H7 extra args dropped: TRUE. run.sh:9; task path run.sh:52 forwards only $GATE; `all` reads only `$2 == -j` (run.sh:795). No in-repo multi-arg callers found.
- (b) H6 stale merge-parent: TRUE. verify_evidence.py:56-58 + EvidenceError -> exit 1 (362-365); behavior locked by scripts/tests/test_harness_evidence.py:164-178; recurred in #160 (commit 791f7c7c). Workaround not in repo docs (grep: 0 hits).
- (c) H1/A37 overwrite: TRUE. live_audit.sh:29 `cut -c1-60`, :35 writes $SLUG.probe.json; frontend-visual.sh:108-112 counts files, never compares with URL count.
- (d) H2 live_probe @layer: TRUE. live_probe.js:38-44 top-level cssRules only. Metric columns (activeRules etc.) are not used by frontend-visual verdict -> affects design-review reports only.
- Extra: live_probe.js:56 caps small/lowContrast at 80 rows; frontend-visual.sh:126-129 filters the capped rows -> silent pass if first 80 are allowlisted.

## 9. Remote rules (gh api, 2026-09-25)
- rulesets: only `product-promotion-policy` (id 23379713) on refs/heads/product: deletion, non_fast_forward, PR (merge only, thread resolution), required checks product-promotion, product-safety, ci-required (strict).
- develop protection exists but has NO required_status_checks and NO required PR reviews (only no force-push / no deletion).
- main: 404 Branch not found. docs/development/github-ruleset.json proposes main + `required-gates` -> obsolete target; docs say "원격 미적용" (harness-transition-handoff.md:191, release-evidence.md:45).
- PR #160 checks: all SUCCESS except harness-eval SKIPPED; agent-bridge compatibility not triggered.

## 10. Other
- Latent bug: ai-service-only or pipeline-worker-only PR -> core-api matrix leg RUN=true (ci.yml:491) records producer service-tests-core-api evidence while registry filters are core-api/contracts -> verify_evidence.py:207-214 EvidenceError -> required-gates exit 1. Introduced 9adaf4db (2026-09-18); no such PR merged since (all 3 ai-touching merges also touched core-api paths).
- README CI table drift (gates/README.md:232-246) vs ci.yml; misplaced/stale comment blocks in ci.yml (167-171, 268-276, 418-420, 452-464, 550-556, 611-619, 638-650, 702-703).
- Memory drift: ~/.claude/projects/.../memory/gate-lanes-cannot-run-in-parallel.md says run.sh has no inter-process mutex; host mutex exists since 2026-09-18.

## Open questions
- Does Codex (or any sandbox) set TMPDIR differently? If yes, host mutex and pg slots split silently (_lock.sh:63-66,78; _pg.sh:75).
- Is develop intentionally ungated (user-managed merges) or is the ruleset proposal meant to be retargeted to develop?
- Should agent-bridge/harness-contract be registered producers in ci-producers.json so required-gates sees them?
