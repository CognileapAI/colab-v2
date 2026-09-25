#!/usr/bin/env bash
# D5 owns platform tables; reuse the canonical disposable platform fixture.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
exec bash "$ROOT/services/core-api/tests/fixtures/setup-db.sh"
