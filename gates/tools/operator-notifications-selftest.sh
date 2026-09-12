#!/usr/bin/env bash
set -uo pipefail
ROOT="${REPO_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
python3 - "$ROOT" <<'PY'
import importlib.util, pathlib, sys, tomllib
root=pathlib.Path(sys.argv[1]);spec=importlib.util.spec_from_file_location('operator_gate',root/'gates/tools/operator_notifications.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
config=tomllib.loads((root/'gates/config/operator-notifications.toml').read_text())
passed={name for names in config['evidence'].values() for name in names}
assert m.check(config,passed)==0
assert m.check(config,set())==1
broken=dict(config,cases=config['cases'][:-1]);assert m.check(broken,passed)==78
broken=dict(config,evidence={});assert m.check(broken,passed)==78
removed=next(iter(config['evidence']['audit-success-rollback']));assert m.check(config,passed-{removed})==1
print('operator-notifications-selftest: missing case / mapping / actual execution rejected (3 negative classes)')
PY
