#!/usr/bin/env python3
"""Validate the shared harness contract and its repository surface."""

import argparse
import datetime as dt
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


# Eval freshness (spec S-HARNESS-E0-EVAL-GATE-20260926 §4.5). The runner does not pin a model, so
# the model/CLI under test changes without any repository diff (`eval/harness/README.md`). A time-based
# signal asks for a re-measurement. 30 days ≈ one ≈32 USD run a month; a warning, never an exit change.
EVAL_MAX_DAYS = 30
EVAL_RUN_ID_RE = re.compile(r"^\d{8}-\d{6}$")


def newest_eval_result(root: Path) -> tuple[str, "dt.datetime"] | None:
    """Newest `eval/harness/results/<YYYYMMDD-HHMMSS>/` directory, or None when there is none."""
    results = root / "eval/harness/results"
    if not results.is_dir():
        return None
    newest = None
    for entry in results.iterdir():
        if not entry.is_dir() or not EVAL_RUN_ID_RE.match(entry.name):
            continue
        try:
            stamp = dt.datetime.strptime(entry.name, "%Y%m%d-%H%M%S")
        except ValueError:
            continue
        if newest is None or stamp > newest[1]:
            newest = (entry.name, stamp)
    return newest


def eval_age_days(stamp: "dt.datetime", now: "dt.datetime | None" = None) -> int:
    """Whole days since a run id's stamp, never negative.

    Run ids carry the recording machine's local clock (`date +%Y%m%d-%H%M%S` in the runner), so a
    runner in an earlier timezone (CI is UTC; results are recorded in KST) that reads a same-day
    result sees a stamp in its own future. That is "0 days old", not "-1d" (E0 PR #176 CI red)."""
    return max(0, ((now or dt.datetime.now()) - stamp).days)


def check_eval_freshness(root: Path, now: "dt.datetime | None" = None,
                         max_days: int = EVAL_MAX_DAYS) -> tuple[str | None, str | None]:
    """Return (warning, readiness). No parseable result id = readiness (the target was not read)."""
    newest = newest_eval_result(root)
    if newest is None:
        return None, "no eval/harness/results/<YYYYMMDD-HHMMSS>/ result directory to judge freshness"
    run_id, stamp = newest
    age = (now or dt.datetime.now()) - stamp
    if age > dt.timedelta(days=max_days):
        return f"warning: harness-eval newest result {run_id} is {age.days} days old (>{max_days})", None
    return None, None


# Rate-measuring eval tasks (15라운드 판정 H18-rate). A `mode`=rate task leaves the regression set, so two
# warnings keep the marker from turning into an escape hatch (exit unchanged — signals, not verdicts):
# the task must be listed in the README rate table, and a rate stuck at 0/2 for three rounds is reported.
RATE_ROUNDS = 3
RATE_ROW_RE = re.compile(r"^\| (H\d\d-[^ |]+) \| rate ([0-2])/2 \|", re.MULTILINE)


def check_rate_tasks(root: Path) -> list[str]:
    harness = root / "eval/harness"
    try:
        rate = sorted(p.parent.name for p in harness.glob("H[0-9][0-9]-*/mode")
                      if p.read_text(encoding="utf-8", errors="replace").rstrip("\n") == "rate")
        readme = (harness / "README.md").read_text(encoding="utf-8") if (harness / "README.md").is_file() else ""
        runs = sorted(d for d in (harness / "results").glob("*/summary.md") if EVAL_RUN_ID_RE.match(d.parent.name))
        seen: dict[str, list[str]] = {name: [] for name in rate}
        for summary in reversed(runs):
            rows = dict(RATE_ROW_RE.findall(summary.read_text(encoding="utf-8", errors="replace")))
            for name in rate:
                if name in rows and len(seen[name]) < RATE_ROUNDS:
                    seen[name].append(rows[name])
    except OSError as exc:
        return [f"warning: eval mode=rate tasks could not be read: {exc}"]
    warnings = [f"warning: eval task {name} is mode=rate but missing from the eval/harness/README.md rate table"
                for name in rate if f"| `{name}` |" not in readme]
    warnings += [f"warning: eval task {name} (mode=rate) was rate 0/2 in the last {RATE_ROUNDS} rounds"
                 for name, got in seen.items() if got == ["0"] * RATE_ROUNDS]
    return warnings


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
    home_stats: dict = {}
    home_errors, home_readiness = check_home_paths(root, value, home_stats)
    errors += home_errors
    parallelism_errors, readiness, judged_gates = check_gate_parallelism(root)
    # Judged parallel-safety errors are printed even when another check could not read
    # its target (advisor review 2026-09-25): a readiness exit must not hide judgements.
    errors += parallelism_errors
    freshness_warning, freshness_readiness = check_eval_freshness(root)
    readiness = readiness or home_readiness or freshness_readiness
    if readiness is not None:
        # We could not read the judgement target. Everything we *did* judge is still
        # printed, but the exit code says 준비, not 판정 (ADR-0004).
        for error in errors:
            print(f"red(판정): {error}", file=sys.stderr)
        print(f"::gate-readiness-failure:: harness-contract: {readiness}", file=sys.stderr)
        return 78
    if errors:
        for error in errors:
            print(f"red(판정): {error}", file=sys.stderr)
        return 1
    if freshness_warning:
        print(freshness_warning)
    for warning in check_rate_tasks(root):
        print(warning)
    newest_id, newest_stamp = newest_eval_result(root)
    print(
        "green: shared harness contract; "
        f"required gates {len(value['gates']['required'])}, "
        f"adapters {len(value['adapters']['required_files'])}, "
        f"hook registrations {len(value['sources']['hook_registrations'])}, "
        f"always-on line budget {value['hygiene']['always_on_max_lines']}, "
        f"home-path roots {len(value['hygiene']['home_path_roots'])} "
        f"(scanned {home_stats.get('scanned', 0)}, skipped {home_stats.get('skipped', 0)} binary/non-UTF-8/symlink), "
        f"parallel-safety declarations {judged_gates}, "
        f"harness-eval newest {newest_id} ({eval_age_days(newest_stamp)}d)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
