#!/usr/bin/env bash
set -uo pipefail
ROOT="${REPO_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
GATE=product-release-selftest
ready() { printf '::gate-readiness-failure::gate=%s|waited_for=%s|limit=-|elapsed=-|detail=%s\n' "$GATE" "$1" "$2"; exit 78; }

PY=""
for candidate in "$ROOT/services/core-api/.venv/bin/python" "$ROOT/gates/.venv/bin/python"; do
  if [ -x "$candidate" ] && "$candidate" -c 'import pytest' >/dev/null 2>&1; then PY="$candidate"; break; fi
done
[ -n "$PY" ] || ready 'pytest python' 'cause=실행기부재 pytest를 가진 프로젝트 venv가 없다'

FILES=("$ROOT/scripts/product_release.py" "$ROOT/scripts/deploy_release.py" "$ROOT/scripts/tests/test_product_release.py" "$ROOT/scripts/tests/test_deploy_release.py")
FILES+=("$ROOT/scripts/tests/test_product_promotion.py")
for file in "${FILES[@]}"; do [ -f "$file" ] || { echo "::error::$GATE red(판정) — 판정 재료 부재: ${file#"$ROOT/"}" >&2; exit 1; }; done

required=(
  test_select_release_accepts_allowed_human_same_repo_develop_merge
  test_select_release_rejects_ineligible_events
  test_api_response_must_match_original_event
  test_merge_parents_and_manifest_digest_bind_release
  test_check_cli_has_no_state_or_deploy_side_effects
  test_duplicate_is_skipped_and_stale_or_unrelated_candidate_is_rejected
  test_deploy_template_is_bound_to_actual_merge_without_mutating_source
  test_reseed_template_only_binds_candidate_and_requires_null_placeholder
  test_notification_off_is_explicit_and_never_calls_sender
  test_candidate_sha_is_passed_to_each_managed_child
  test_artifact_changed_refuses_before_deploy
  test_promotion_check_rejects_wrong_source_before_merge
  test_wrong_checkout_cannot_validate_pinned_release
  test_check_rejects_invalid_deployment_template
  test_notification_off_failure_does_not_queue_operator_message
  test_approval_binds_manifest_and_all_required_success_checks
  test_approval_rejects_missing_failed_or_wrong_source_checks
  test_absent_release_record_never_auto_starts
  test_explicit_provision_is_private_and_binds_one_initial_pr
  test_authorization_rechecks_promotion_binding_and_requires_human_resume
  test_promotion_run_selection_requires_exact_workflow_pr_head_and_success
  test_initial_reseed_is_only_for_provisioned_pr_and_never_for_later_release
  test_manifest_binding_reads_exact_head_blob_and_merge_file
  test_failed_deploy_can_only_resume_explicitly_and_reverifies
  test_resume_never_repeats_passed_or_uncertain_mutation_without_check
  test_release_record_is_only_candidate_order_source_and_missing_is_rejected
  test_artifact_redirect_only_allows_unsigned_github_blob_download
  test_check_suite_sha_parents_bind_exact_pr_base_and_head
  test_premerge_check_sha_can_differ_from_actual_human_merge
  test_wrong_promotion_workflow_policy_digest_blocks_release
  test_failed_resume_check_can_be_retried_without_repeating_mutation
  test_resume_between_completed_commands_does_not_repeat_completed_work
)
result="$(mktemp)"
trap 'rm -f "$result"' EXIT
"$PY" -m pytest -q "${FILES[@]:2}" --junitxml="$result"
rc=$?
[ "$rc" -eq 0 ] || exit 1
"$PY" - "$result" "${required[@]}" <<'PY'
import sys
import xml.etree.ElementTree as ET
cases = ET.parse(sys.argv[1]).findall('.//testcase')
names = {case.attrib['name'].split('[')[0] for case in cases}
missing = set(sys.argv[2:]) - names
bad = any(case.find(tag) is not None for case in cases for tag in ('skipped', 'failure', 'error'))
if not cases or missing or bad:
    print('::error::필수 시나리오 누락·미실행·실패:', sorted(missing))
    sys.exit(1)
print(f'product-release-selftest — 필수 {len(sys.argv)-2} · 실제 실행 {len(cases)} · 실패 0 · skip 0')
PY
