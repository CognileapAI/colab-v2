#!/usr/bin/env bash
set -uo pipefail
ROOT="${REPO_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
ready() {
  printf '::gate-readiness-failure::gate=product-reseed-selftest|waited_for=%s|limit=-|elapsed=-|detail=필수 시험 환경 부재\n' "$1"
  exit 78
}
PY="$ROOT/services/core-api/.venv/bin/python"
[ -x "$PY" ] && "$PY" -c 'import pytest' >/dev/null 2>&1 || ready pytest
command -v node >/dev/null 2>&1 || ready node
(cd "$ROOT/frontend" && node -e "require('jsdom')") >/dev/null 2>&1 || ready jsdom
FILES=(
  "$ROOT/dev-package/tools/product-reseed/test_reseed.py"
  "$ROOT/dev-package/tools/dev-seed/tests/test_runner_project_index.py"
  "$ROOT/dev-package/tools/dev-seed/tests/test_runner_plan_mapping.py"
  "$ROOT/services/core-api/tests/test_reset_product_environment.py"
  "$ROOT/infra/prod/tests/test_maintenance.py"
)
for file in "${FILES[@]}"; do [ -f "$file" ] || { echo '::error::필수 시험 파일 부재'; exit 1; }; done
RESULT="$(mktemp)"
trap 'rm -f "$RESULT"' EXIT
# This gate exercises command boundaries with external DB/AWS dependencies replaced.
# The service-wide autouse real-DB fixture belongs to service-tests-core-api.
"$PY" -m pytest --noconftest -q "${FILES[@]}" --junitxml="$RESULT"
rc=$?
[ "$rc" -eq 0 ] || exit 1
"$PY" - "$RESULT" <<'PY'
import sys
import xml.etree.ElementTree as ET
cases = ET.parse(sys.argv[1]).findall('.//testcase')
names = {case.attrib['name'].split('[')[0] for case in cases}
required = {
    'test_ordinary_run_cannot_initialize_absent_record',
    'test_first_run_succeeds_and_duplicate_never_resets',
    'test_reset_failure_keeps_maintenance_and_refuses_automatic_retry',
    'test_failed_mutating_stage_cannot_be_blindly_resumed',
    'test_child_keeps_lock_if_parent_is_killed',
    'test_provision_before_merge_binds_real_candidate_only_when_run',
    'test_manual_resume_checks_partial_stage_and_never_repeats_reset',
    'test_corrupt_record_is_not_treated_as_ready',
    'test_project_identity_comes_from_exact_name_and_row_id',
    'test_duplicate_project_names_are_not_silently_collapsed',
    'test_maintenance_not_confirmed_causes_zero_deletes',
    'test_both_database_schemas_checked_before_first_drop',
    'test_changed_s3_inventory_blocks_database_drop',
    'test_partial_database_reset_cannot_be_automatically_repeated',
    'test_cli_provision_is_explicit_and_cannot_replace_existing_state',
    'test_missing_file_backup_blocks_reset',
    'test_same_key_changed_source_blocks_all_deletes',
    'test_verify_completed_never_starts_ready_or_failed_execution',
    'test_stage_inherits_outer_release_lock_and_reseed_lock',
    'test_enter_blocks_default_api_and_previews_and_preserves_original',
    'test_status_rejects_interrupted_enter_without_mutating_cloudfront',
    'test_leave_restores_exact_original_after_readback_verification',
    'test_entering_requires_explicit_resume_and_can_recover_active_remote',
    'test_unexpected_cache_behavior_is_rejected_as_public_bypass',
    'test_leave_state_write_failure_reenters_maintenance_and_records_active',
    'test_sigkill_after_restore_can_be_resumed_to_maintenance',
    'test_aws_subprocess_inherits_local_and_controller_lock_fds',
    'test_controller_reset_maintenance_chain_preserves_lock_after_parent_death',
}
bad = any(case.find(tag) is not None for case in cases for tag in ('skipped','failure','error'))
missing = required - names
if not cases or missing or bad:
    print('::error::필수 시나리오 누락·미실행·실패:', sorted(missing))
    sys.exit(1)
print(f'product-reseed-selftest — 필수 {len(required)}/{len(required)} · 실제 실행 {len(cases)} · 실패 0 · skip 0')
PY
