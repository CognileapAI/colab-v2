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

## Observation boundary

- Historical reference set is `WINDOW-20260905-REBAKE-TARGETS.md`: 19 legacy bundles =
  sidecar absent 14 + old sidecar 5; among the old-sidecar five, ledger present 3 and absent 2.
- Current local-staging evidence in `20260911-stage12-failure-fix.md` still reports 19
  `판정 불가`, separately from 19 modern orphan bundles and 146 map tiles.
- The parent-provided current dev S3 inventory says map-tile `.tif` is 0 and other PNG/WebP
  objects total 333. Those 333 are not asserted to be the historical legacy 19; the code requires
  legacy sidecar/source evidence before counting them.
- A fresh deployed dev TL-2 count is pending deployment of this reviewed code. This lane does not
  convert an undeployed classifier or the 333-format inventory into a production observation.

## Verification

- Declared task gates: `service-tests-viz-render`, `artifact-ownership-selftest`.
- Gate result is recorded in `gate-summary.json`.
