#!/usr/bin/env bash
# ai-no-lineage-write 게이트 실행기 — 판정 로직은 ai_no_lineage_write.py.
# YAML 파서(PyYAML)가 필요해 gates/.venv 를 쓴다. 설치 실패는 skip 이 아니라 red.
set -uo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
# shellcheck source=/dev/null
. "$(dirname "${BASH_SOURCE[0]}")/_venv.sh"
ensure_gate_venv ai-no-lineage-write || exit 1
exec "$GATE_PY" "$REPO_ROOT/gates/tools/ai_no_lineage_write.py"
