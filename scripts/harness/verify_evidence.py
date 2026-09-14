#!/usr/bin/env python3
"""Create and verify SHA-bound CI and gate evidence."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys


class EvidenceError(ValueError):
    pass


class EvidenceReadinessError(EvidenceError):
    pass


ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / ".agents/ci-producers.json"


def sha(value: object, name: str) -> str:
    value = _required(value, name)
    if not re.fullmatch(r"[0-9a-f]{40}", value):
        raise EvidenceError(f"invalid {name}")
    return value


def _required(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise EvidenceReadinessError(f"missing {name}")
    return value


def event_shas(event_name: str, event: dict, checkout_sha: str) -> dict[str, str]:
    sha(checkout_sha, "checkout sha")
    if event_name == "pull_request":
        pull = event.get("pull_request") if isinstance(event, dict) else None
        pull = pull if isinstance(pull, dict) else {}
        base = pull.get("base") if isinstance(pull.get("base"), dict) else {}
        head = pull.get("head") if isinstance(pull.get("head"), dict) else {}
        result = {"base_sha": sha(base.get("sha"), "pull_request.base.sha"),
                  "head_sha": sha(head.get("sha"), "pull_request.head.sha"),
                  "merge_sha": sha(pull.get("merge_commit_sha"), "pull_request.merge_commit_sha")}
        if result["merge_sha"] != checkout_sha:
            raise EvidenceError("PR merge commit differs from checkout")
        return result
    if event_name == "push":
        result = {"before_sha": sha(event.get("before"), "push.before"),
                  "after_sha": sha(event.get("after"), "push.after")}
        if result["after_sha"] != checkout_sha:
            raise EvidenceError("push after differs from checkout")
        return result
    if event_name == "workflow_dispatch":
        return {"head_sha": checkout_sha}
    raise EvidenceReadinessError(f"unsupported event: {event_name}")


def build_ci_evidence(run_id: str, run_attempt: int, commit: str, tree: str,
                      shas: dict[str, str], jobs: list[dict]) -> dict:
    sha(commit, "commit")
    sha(tree, "tree")
    if type(run_attempt) is not int or run_attempt < 1:
        raise EvidenceReadinessError("invalid run attempt")
    if not jobs:
        raise EvidenceReadinessError("no CI jobs declared")
    names: set[str] = set()
    counts = {"green": 0, "red_judgment": 0, "red_readiness": 0,
              "not_applicable": 0}
    normalized = []
    for raw in jobs:
        if not isinstance(raw, dict):
            raise EvidenceReadinessError("CI job entry must be an object")
        name = _required(raw.get("name"), "CI job name")
        if name in names:
            raise EvidenceError(f"duplicate CI job: {name}")
        names.add(name)
        applicable = raw.get("applicable")
        if not isinstance(applicable, bool):
            raise EvidenceReadinessError(f"{name}: applicable must be boolean")
        result = _required(raw.get("result"), f"{name}.result")
        state = "not_applicable"
        if applicable and result == "success":
            state = raw.get("state", "red_readiness")
        elif applicable and result == "failure":
            state = "red_judgment"
        elif applicable:
            state = "red_readiness"
        elif not raw.get("reason") or result != "skipped":
            raise EvidenceReadinessError(f"{name}: non-applicable job needs skipped result and reason")
        if state not in counts:
            raise EvidenceError(f"{name}: invalid evidence state")
        counts[state] += 1
        normalized.append({"name": name, "applicable": applicable,
                           "result": result, "state": state,
                           "reason": raw.get("reason"), "checks": raw.get("checks", []),
                           "needs_result": raw.get("needs_result", result)})
    return {
        "schema": "colab-ci-evidence/1",
        "run_id": _required(run_id, "run id"),
        "run_attempt": run_attempt,
        "commit": _required(commit, "commit sha"),
        "tree": _required(tree, "tree sha"),
        "event_shas": shas,
        "counts": counts,
        "jobs": normalized,
    }


def verdict(evidence: dict) -> int:
    counts = evidence["counts"]
    if counts["red_judgment"]:
        return 1
    if counts["red_readiness"] or not counts["green"]:
        return 78
    return 0


def verify_gate_summary(summary: dict, commit: str, required_gates: list[str], tree: str | None = None) -> None:
    sha(commit, "gate commit")
    if summary.get("schema") != "colab-gate-summary/1":
        raise EvidenceError("invalid gate summary schema")
    if summary.get("commit") != commit:
        raise EvidenceError("gate summary commit differs")
    if tree is not None and summary.get("tree") != tree:
        raise EvidenceError("gate summary tree differs")
    counts = summary.get("counts")
    if not isinstance(counts, dict) or counts.get("red_판정") != 0 or counts.get("red_준비") != 0:
        raise EvidenceError("gate summary is not green")
    if any(type(counts.get(key)) is not int for key in ("green", "red_판정", "red_준비")) or counts.get("red_준비_입력미선언", 0) != 0:
        raise EvidenceError("invalid gate counts")
    gates = summary.get("gates")
    if not isinstance(gates, list) or any(not isinstance(row, dict) for row in gates):
        raise EvidenceError("gate summary has no gates")
    names = [item.get("name") for item in gates if isinstance(item, dict)]
    if not required_gates or len(names) != len(set(names)) or set(names) != set(required_gates):
        raise EvidenceError("required gate set is missing or duplicated")
    if type(counts.get("green")) is not int or counts["green"] != len(required_gates):
        raise EvidenceError("gate green count differs from rows")
    for row in gates:
        if row.get("status") != "green" or row.get("state") != "green" or type(row.get("exit")) is not int or row["exit"] != 0:
            raise EvidenceError("gate row is not green")


def load_registry() -> dict:
    value = json.loads(REGISTRY.read_text(encoding="utf-8"))
    if value.get("schema") != "colab-ci-producers/1" or not value.get("producers"):
        raise EvidenceReadinessError("missing CI producer registry")
    return value["producers"]


def collect_ci(run_id: str, run_attempt: int, commit: str, tree: str, registry: dict,
               needs: dict, filters: dict, artifact_root: Path) -> list[dict]:
    sha(commit, "CI commit")
    sha(tree, "CI tree")
    expected_jobs = {entry["job"] for entry in registry.values()} | {"changes"}
    if set(needs) != expected_jobs:
        raise EvidenceReadinessError("CI needs job set differs from registry")
    if needs["changes"].get("result") != "success":
        raise EvidenceReadinessError("path filter producer did not succeed")
    for key in {key for entry in registry.values() for key in entry["filters"]}:
        if filters.get(key) not in ("true", "false"):
            raise EvidenceReadinessError(f"missing or malformed path filter: {key}")
    files: dict[str, dict[str, Path]] = {}
    for summary in artifact_root.rglob("gate-summary.json"):
        if not (summary.parent / "evidence.json").is_file():
            raise EvidenceReadinessError("orphan gate summary without producer record")
    for path in artifact_root.rglob("evidence.json"):
        record = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(record, dict):
            raise EvidenceError("CI check evidence must be an object")
        producer, check = record.get("producer"), record.get("check")
        if producer not in registry or check not in registry[producer]["checks"]:
            raise EvidenceError("unknown CI evidence producer/check")
        if check in files.setdefault(producer, {}):
            raise EvidenceError("duplicate CI check evidence")
        files[producer][check] = path
    jobs = []
    for name, entry in registry.items():
        applicable = not entry["filters"] or any(filters[key] == "true" for key in entry["filters"])
        result = needs[entry["job"]].get("result")
        found = files.get(name, {})
        if not applicable:
            # Matrix rows execute only RUN=true check steps; the aggregate job may succeed.
            matrix = entry["job"] == "service-tests"
            if found or (not matrix and result != "skipped") or (matrix and result not in ("success", "failure", "cancelled", "skipped")):
                raise EvidenceError(f"{name}: N/A requires skipped checks and zero evidence")
            jobs.append({"name": name, "applicable": False, "result": "skipped", "state": "not_applicable",
                         "needs_result": result, "reason": "all registered path filters false; check steps skipped"})
            continue
        if set(found) != set(entry["checks"]):
            raise EvidenceReadinessError(f"{name}: missing required check evidence")
        for check, path in found.items():
            record = json.loads(path.read_text(encoding="utf-8"))
            spec = entry["checks"][check]
            for key, wanted in {"schema": "colab-ci-check/1", "run_id": run_id, "run_attempt": run_attempt,
                                "commit": commit, "tree": tree, "kind": spec["kind"], "command": spec["command"]}.items():
                if record.get(key) != wanted:
                    raise EvidenceError(f"{name}/{check}: different {key}")
            code = record.get("exit")
            if type(code) is not int:
                raise EvidenceReadinessError(f"{name}/{check}: missing exit code")
            if record.get("counts") != {"green": int(code == 0), "red_judgment": int(code not in (0, 78)), "red_readiness": int(code == 78)}:
                raise EvidenceError(f"{name}/{check}: inconsistent check counts")
            if code == 78:
                raise EvidenceReadinessError(f"{name}/{check}: preparation failed")
            if code != 0:
                raise EvidenceError(f"{name}/{check}: check failed ({code})")
            if spec["kind"] == "gate":
                summary_path = path.parent / "gate-summary.json"
                if not summary_path.is_file():
                    raise EvidenceReadinessError(f"{name}/{check}: missing gate summary")
                verify_gate_summary(json.loads(summary_path.read_text()), commit, spec["gates"], tree)
        jobs.append({"name": name, "applicable": True, "result": result,
                     "state": "green" if result == "success" else "red_readiness", "checks": sorted(found)})
    return jobs


def record_command(args: argparse.Namespace) -> int:
    registry = load_registry()
    if args.producer not in registry or args.check not in registry[args.producer]["checks"]:
        raise EvidenceError("undeclared producer/check")
    spec = registry[args.producer]["checks"][args.check]
    command = args.check_command
    if command and command[0] == "--":
        command = command[1:]
    if command != spec["command"]:
        raise EvidenceError("check command differs from registry")
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    tree = subprocess.check_output(["git", "rev-parse", "HEAD^{tree}"], text=True).strip()
    if commit != os.environ.get("GITHUB_SHA"):
        raise EvidenceError("producer checkout differs from GITHUB_SHA")
    folder = args.artifact_root / args.producer / args.check
    folder.mkdir(parents=True, exist_ok=False)
    env = dict(os.environ, COLAB_GATE_REPORT_DIR=str(folder.resolve()))
    try:
        code = subprocess.run(command, env=env).returncode
    except OSError:
        code = 78
    record = {"schema": "colab-ci-check/1", "producer": args.producer, "check": args.check,
              "run_id": _required(os.environ.get("GITHUB_RUN_ID"), "run id"),
              "run_attempt": int(_required(os.environ.get("GITHUB_RUN_ATTEMPT"), "run attempt")),
              "commit": commit, "tree": tree, "kind": spec["kind"], "command": command, "exit": code,
              "counts": {"green": int(code == 0), "red_judgment": int(code not in (0, 78)), "red_readiness": int(code == 78)}}
    (folder / "evidence.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    return code if code >= 0 else 1


def _markdown(evidence: dict) -> str:
    counts = evidence["counts"]
    return (
        "## Required gates evidence\n\n"
        f"- commit: `{evidence['commit']}`\n"
        f"- tree: `{evidence['tree']}`\n"
        f"- run: `{evidence['run_id']}` attempt `{evidence['run_attempt']}`\n"
        f"- counts: green {counts['green']} / red(judgment) {counts['red_judgment']} "
        f"/ red(readiness) {counts['red_readiness']} / N/A {counts['not_applicable']}\n"
    )


def ci_command(args: argparse.Namespace) -> int:
    try:
        event = json.loads(args.event_path.read_text(encoding="utf-8"))
        needs = json.loads(args.needs_json)
        filters = json.loads(args.filters_json)
        tree = subprocess.check_output(
            ["git", "rev-parse", "HEAD^{tree}"], text=True
        ).strip()
        if args.tree and args.tree != tree:
            raise EvidenceError("declared tree differs from checkout")
        args.tree = tree
        actual_commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
        if actual_commit != args.commit:
            raise EvidenceError("aggregator checkout differs from event SHA")
        shas = event_shas(args.event_name, event, args.commit)
        jobs = collect_ci(args.run_id, args.run_attempt, args.commit, tree, load_registry(), needs, filters, args.artifact_root)
        evidence = build_ci_evidence(
            args.run_id, args.run_attempt, args.commit, tree,
            shas, jobs,
        )
        args.output.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n",
                               encoding="utf-8")
        summary = _markdown(evidence)
        print(summary, end="")
        if args.summary:
            with args.summary.open("a", encoding="utf-8") as stream:
                stream.write(summary)
        return verdict(evidence)
    except EvidenceReadinessError as exc:
        print(f"::gate-readiness-failure:: required-gates: {exc}", file=sys.stderr)
        write_failed_ci(args, "red_readiness", str(exc))
        return 78
    except (EvidenceError, OSError, json.JSONDecodeError, subprocess.SubprocessError) as exc:
        print(f"red(판정): required-gates: {exc}", file=sys.stderr)
        write_failed_ci(args, "red_judgment", str(exc))
        return 1


def write_failed_ci(args: argparse.Namespace, state: str, error: str) -> None:
    # Count the failed aggregation validation, not unobserved product gate runs.
    counts = {"green": 0, "red_judgment": 0, "red_readiness": 0, "not_applicable": 0}
    counts[state] = 1
    evidence = {"schema": "colab-ci-evidence/1", "run_id": args.run_id, "run_attempt": args.run_attempt,
                "commit": args.commit, "tree": args.tree, "event_shas": {}, "counts": counts,
                "count_unit": "aggregation validation", "jobs": [], "errors": [error]}
    args.output.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.summary:
        with args.summary.open("a", encoding="utf-8") as stream:
            stream.write(_markdown(evidence) + f"\n- validation error: {error}\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    ci = sub.add_parser("ci")
    ci.add_argument("--event-name", required=True)
    ci.add_argument("--event-path", type=Path, required=True)
    ci.add_argument("--run-id", required=True)
    ci.add_argument("--run-attempt", type=int, required=True)
    ci.add_argument("--commit", required=True)
    ci.add_argument("--tree")
    ci.add_argument("--needs-json", required=True)
    ci.add_argument("--filters-json", required=True)
    ci.add_argument("--artifact-root", type=Path, required=True)
    ci.add_argument("--output", type=Path, required=True)
    ci.add_argument("--summary", type=Path)
    record = sub.add_parser("record")
    record.add_argument("--producer", required=True)
    record.add_argument("--check", required=True)
    record.add_argument("--artifact-root", type=Path, required=True)
    record.add_argument("check_command", nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    if args.command == "ci":
        return ci_command(args)
    try:
        return record_command(args)
    except (EvidenceError, OSError, ValueError) as exc:
        print(f"::gate-readiness-failure:: CI evidence: {exc}", file=sys.stderr)
        return 78


if __name__ == "__main__":
    raise SystemExit(main())
