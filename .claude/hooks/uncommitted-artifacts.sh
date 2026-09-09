#!/usr/bin/env bash
# H6 shared task evidence. Missing/malformed evidence blocks; never auto-commit.
set -uo pipefail
command -v python3 >/dev/null 2>&1 || { echo 'H6: python3 missing; cannot verify task' >&2; exit 2; }
python3 "$(dirname "${BASH_SOURCE[0]}")/lifecycle_contract.py" stop --role researcher || exit 2
