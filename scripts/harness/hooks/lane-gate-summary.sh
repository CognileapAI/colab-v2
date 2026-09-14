#!/usr/bin/env bash
# H7 shared task evidence. Use only the declared task report, never mtime lookup.
set -uo pipefail
command -v python3 >/dev/null 2>&1 || { echo 'H7: python3 missing; cannot verify task' >&2; exit 2; }
python3 "$(dirname "${BASH_SOURCE[0]}")/lifecycle_contract.py" stop --role lane-worker || exit 2
