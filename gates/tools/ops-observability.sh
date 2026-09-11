#!/usr/bin/env bash
set -euo pipefail
ROOT="${REPO_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
exec "$ROOT/gates/tools/ops_observability.py" \
  --residency "$ROOT/infra/ops/data-residency.toml" \
  --alarms "$ROOT/infra/ops/alarms.toml" \
  --compose "$ROOT/infra/dev/compose.yml" \
  --repo "$ROOT"
