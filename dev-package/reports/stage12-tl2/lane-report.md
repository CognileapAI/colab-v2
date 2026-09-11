# TL-2 legacy preview observation lane

## Scope and safety

- Base: `205de119433119212212766cce9233644cdc786c`
- Scope: legacy preview observation classification in `ownership.py`, its gate output, and tests.
- Existing ownership verdict stays `판정 불가`; neither new observation subgrade enters
  `orphan_keys()` or `invalidation.reclaim_plan()`.
- Actual preview/S3 deletion: **0**. Deploy/apply: **0**. Ledger edits: **0**.

## TDD evidence

- RED: the three TL-2 tests failed with `AttributeError: ownership.legacy_tally` before the
  implementation existed (3 failed, 16 deselected).
- GREEN: `test_artifact_ownership.py` passes 20/20 after implementation.
- The 19-bundle oracle is fixed as 14 `사이드카 부재`, 2 `원천 원장 부재`, and 3
  `원천 원장 있음`; the first two form the 16 bundles unreachable by rebake.
- A separate fixture proves 333 modern PNG/WebP bundles and a `tile-*.tif` bundle do not enter
  the legacy population.
- A legacy sidecar without a source identifier fails closed instead of being guessed into a class.
- A physical JSON parse error or non-object JSON remains `판정 불가` for the old ownership contract,
  but TL-2 observation now preserves the parse-error state and stops readiness; it is never counted
  as `사이드카 부재`.

## Dev read-only command packet

The deployed-code command is `python -m colab_viz.domains.d7_visualization.legacy_preview_observation`.
Before it runs, an administrator read-only connection must dump the complete `d3_file.id` and
`d5_upload_file.id` sets inside `BEGIN READ ONLY`; repeat the same counts under the boundary role and
stop if the two scopes are equal or both administrator sets are empty. Pass only those two ID files,
the exact bucket/region, `--prefix previews`, and a new snapshot path to the command. Record the
container image/config ID and deployed build SHA first, then hash the resulting JSON snapshot.

The command lists only exact `previews/`, rejects nested/out-of-prefix/unknown objects, downloads only
JSON sidecars with List-size = HEAD-size and If-Match GET, closes every stream, and emits observation
time, current object/group counts, all legacy/rebake-unreachable key sets, unsigned object size metadata,
and `deleted: 0`. Duplicate pagination, missing/invalid metadata, malformed JSON, and empty ledgers are
readiness failures rather than zero counts. It has no delete client call and no DB connection.

## Observation boundary

- Historical reference set is `WINDOW-20260905-REBAKE-TARGETS.md`: 19 legacy bundles =
  sidecar absent 14 + old sidecar 5; among the old-sidecar five, ledger present 3 and absent 2.
- Current local-staging evidence in `20260911-stage12-failure-fix.md` still reports 19
  `판정 불가`, separately from 19 modern orphan bundles and 146 map tiles.
- The parent-provided current dev S3 inventory says map-tile `.tif` is 0 and other PNG/WebP
  objects total 333. Those 333 are not asserted to be the historical legacy 19; the code requires
  legacy sidecar/source evidence before counting them.
- A fresh deployed dev TL-2 count is pending deployment of this reviewed code. The current 333-object
  inventory is expected to change, so the snapshot timestamp and actual count are mandatory. This lane does not
  convert an undeployed classifier or the 333-format inventory into a production observation.

## Verification

- Declared task gates: `service-tests-viz-render`, `artifact-ownership-selftest`.
- Gate result is recorded in `gate-summary.json`.
