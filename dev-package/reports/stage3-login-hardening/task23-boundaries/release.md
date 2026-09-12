# Task 2/3 session boundary follow-up

## Result

The server-side session boundary follow-up is complete. No staging service or staging database was contacted, restarted, or changed.

The added integration coverage proves:

- a session is accepted immediately before its fixed 12-hour expiry and rejected at the exact expiry;
- password change rechecks the clock after waiting for the credential lock and rejects an expired session;
- authentication rejects a signed session whose lab no longer matches the account's current lab;
- concurrent initial-password change and current-session revocation cannot leave either the old or rotated token usable;
- a revoked browser session cannot mint a new download ticket.

The API already commits password change and returns the rotated session from the same database transaction, without a post-commit lookup. Loss of the HTTP response after commit is therefore a client recovery concern and does not create a second backend state transition.

## Verification

- Focused boundary tests: 8 passed.
- Final declared `service-tests-core-api` gate: 1,111 collected and executed, 1,111 passed, 0 skipped, 6 deselected, 0 failed, 0 errors (167.83 seconds).
- Gate summary: 1 green, 0 judgment failures, 0 readiness failures.
- `git diff --check`: passed.

This follow-up does not change the prior Task 2/3 eleven-gate result or reclassify its accepted `contract-breaking` exact-oneof judgment failure. That result remains 10 green, 1 accepted judgment failure, and 0 readiness failures, with its acceptance recorded in `dev-package/reports/stage3-login-hardening/task1/contract-acceptance.md`.

## Environment handoff

The disposable, tmpfs-backed schema database container `colab_task23_schema_2901792` remains available for the parent lane. It publishes no host port. When no longer needed, remove it with `docker rm -f colab_task23_schema_2901792`.

Server source is frozen after this report.
