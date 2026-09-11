# TL-2 dev read-only observation — 2026-09-11

## Result

The deployed dev build `30f5adf67747` was observed after all four application containers were
healthy with restart count 0. The viz image ID was
`sha256:af13ab7dc206155acff92076716fa725c09fae6bcc2b52ddbc3dc0e1973168ff`.
The deployed `ownership.py` and `legacy_preview_observation.py` hashes matched the approved main
files before the observation ran.

At `2026-09-11T08:40:49.538900+00:00`, exact `previews/` contained **394 objects** grouped into
**174 preview bundles**. All 174 were modern; legacy bundles were **0**:

- sidecar absent: 0
- source ledger absent: 0
- source ledger present: 0
- unreachable by rebake: 0
- deleted: **0**

The existing four ownership grades were **live 116**, **upload-only 42**, **orphan 16**, and
**undecidable 0**. The 16 modern orphan bundles are separate from the historical 16 legacy bundles;
this observation did not delete or reclassify them. Exact keys and unsigned object size metadata are
sealed in `dev-20260911T083948Z/observation.json`.

The 394 objects were `.json` 174, `.pgw` 46, `.png` 110, and `.webp` 64. Map `.tif` objects were 0.
This replaces the earlier, mutable 333-object inventory with a timestamped current snapshot rather
than forcing the old number.

## Full-scope ledger input

The dev URL file existed as `root:root` mode 0600; its value was never printed or copied into an
artifact. A fresh read-only transaction observed `colab_backup` as non-superuser, BYPASSRLS true,
`pg_read_all_data` member true, and 31 FORCE-RLS tables. It counted and then dumped **d3_file 450**
and **d5_upload_file 595** IDs in sorted order. Counts matched dump line counts.

- d3 ID dump SHA-256: `a86cb8ace8a3773d212a37d961fe31c648dc2b3a59fcbef434aa7b33a50209df`
- d5 ID dump SHA-256: `4791bb0d02c777d636b345a62d20b514c08dc5aa45c965ead3e58d5755ef0f7a`

The temporary ID files were mode 0600, copied into the viz container for the one command, and removed
from the container immediately afterward. They are not retained in this report. No `SET ROLE
colab_app` was attempted.

## Historical comparison

The preserved local staging tree was independently classified with the same `ownership.legacy_tally`
implementation and a fresh read-only superuser ledger snapshot. It still produced the historical
oracle exactly: **19 legacy bundles = sidecar absent 14 + source ledger absent 2 + source ledger
present 3**, with **16 unreachable by rebake** and deletion 0. This comparison is stored separately in
`historical-staging/observation.json`; its 498 files and 304 total groups are local staging facts, not
dev S3 facts.

Therefore the old staging 19/16 set is reproduced, while current dev truth is legacy 0/unreachable 0.
The two environments are not treated as the same population.

This one-shot dev observation does not satisfy TL-2 completion definition item ⑤. That item still
requires a green staging deployment followed by one observed staging loop, and no approved decision
substitutes a dev one-shot for it. This evidence therefore cannot by itself mark TL-2 complete.

## Evidence hashes and safety

- dev observation JSON: `2527344b3217b61bdae3af2cd5a2b04683c6ed04ce8a521764ece7b7f20cff80`
- dev safe evidence text: `5b1a1190038d83f11921cf77963f8948da1c3e0a73ea8763a8060171bd9b5a47`
- historical comparison JSON: `c94c9b053c9cf179067283a93fd14e44c06b4578472fd4fc27a2102ec87b1af7`

S3 reads were limited to exact `previews/`; only JSON sidecars were downloaded. Database work used
read-only transactions. S3 delete, DB write, cron change, service restart, deployment, and external
notification were all **0** in this observation task.
