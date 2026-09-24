#!/usr/bin/env python3
"""Validate the shared harness contract and its repository surface."""

import argparse
import os
from pathlib import Path
import re
import subprocess
import sys

from config import ContractError, check_always_on_lines, check_contract, check_home_paths, load_contract


ROOT = Path(__file__).resolve().parents[2]

# `gates/run.sh all` folds an undeclared gate into the solo list and prints a warning
# every single run (`gates/run.sh:716`, `:796-797`). A warning that is always there is
# not a signal. The declaration table is the thing under judgement here, so a gate that
# is missing from it is red(판정) — the same verdict the runner already implies but
# never enforces. Not being able to read either side is red(준비 · 78) instead: we
# failed to read the target, the target did not break the rule (ADR-0004).
ALL_GATES_RE = re.compile(r"^ALL_GATES=\(\n(.*?)^\)\s*$", re.MULTILINE | re.DOTALL)


def check_gate_parallelism(root: Path) -> tuple[list[str], str | None, int]:
    """Assert ALL_GATES ⊆ parallelism.toml.

    Returns (judgement errors, readiness reason, number of gates judged).

    The declaration table is parsed by `gates/tools/parallelism.py` — the same reader
    the runner uses (`gates/run.sh:683-697`). Keeping one reader is deliberate: a second
    parser here would eventually disagree with the runner about what is declared.
    """
    runner = root / "gates/run.sh"
    reader = root / "gates/tools/parallelism.py"
    manifest = Path(os.environ.get("COLAB_GATE_PARALLELISM_MANIFEST")
                    or root / "gates/config/parallelism.toml")
    try:
        match = ALL_GATES_RE.search(runner.read_text(encoding="utf-8"))
    except OSError as exc:
        return [], f"cannot read gate list: {exc}", 0
    if match is None:
        return [], f"ALL_GATES array not found in {runner.relative_to(root)}", 0
    listed = match.group(1).split()
    if not listed:
        return [], f"ALL_GATES is empty in {runner.relative_to(root)}", 0
    if not reader.is_file():
        return [], f"missing declaration reader: {reader.relative_to(root)}", 0
    try:
        result = subprocess.run([sys.executable, str(reader), str(manifest)],
                                capture_output=True, text=True)
    except OSError as exc:
        return [], f"cannot run declaration reader: {exc}", 0
    if result.returncode != 0:
        return [], f"declaration reader failed ({result.returncode}): {result.stderr.strip()}", 0
    declared, errors = {}, []
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        fields = line.split("\t")
        if fields[0] == "!PARSE":
            return [], "cannot read parallelism declarations: " + " ".join(fields[1:]), 0
        if fields[0] == "!BAD":
            errors.append("parallel-safety declaration is neither serial nor parallel: "
                          + " = ".join(fields[1:]))
            continue
        declared[fields[0]] = fields[1] if len(fields) > 1 else ""
    for name in listed:
        if name not in declared:
            errors.append(f"gate has no parallel-safety declaration: {name} "
                          "(declare it in gates/config/parallelism.toml with an evidence line)")
    for name in declared:
        if name not in listed:
            errors.append(f"parallel-safety declaration names a gate that does not exist: {name}")
    return errors, None, len(listed)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--contract", type=Path)
    args = parser.parse_args(argv)
    root = args.root.resolve()
    contract = args.contract or root / ".agents/harness.yaml"
    try:
        value = load_contract(contract)
    except ContractError as exc:
        print(f"::gate-readiness-failure:: harness-contract: {exc}", file=sys.stderr)
        return 78
    errors = check_contract(root, value)
    errors += check_always_on_lines(root, value)
    home_errors, home_readiness = check_home_paths(root, value)
    errors += home_errors
    parallelism_errors, readiness, judged_gates = check_gate_parallelism(root)
    readiness = readiness or home_readiness
    if readiness is not None:
        # We could not read the judgement target. Everything we *did* judge is still
        # printed, but the exit code says 준비, not 판정 (ADR-0004).
        for error in errors:
            print(f"red(판정): {error}", file=sys.stderr)
        print(f"::gate-readiness-failure:: harness-contract: {readiness}", file=sys.stderr)
        return 78
    errors += parallelism_errors
    if errors:
        for error in errors:
            print(f"red(판정): {error}", file=sys.stderr)
        return 1
    print(
        "green: shared harness contract; "
        f"required gates {len(value['gates']['required'])}, "
        f"adapters {len(value['adapters']['required_files'])}, "
        f"hook registrations {len(value['sources']['hook_registrations'])}, "
        f"always-on line budget {value['hygiene']['always_on_max_lines']}, "
        f"home-path roots {len(value['hygiene']['home_path_roots'])}, "
        f"parallel-safety declarations {judged_gates}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
