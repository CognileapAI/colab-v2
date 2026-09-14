#!/usr/bin/env python3
"""Create and verify SHA-bound CI and gate evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys


class EvidenceError(ValueError):
    pass


class EvidenceReadinessError(EvidenceError):
    pass


def _required(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise EvidenceReadinessError(f"missing {name}")
    return value


def event_shas(event_name: str, event: dict, checkout_sha: str) -> dict[str, str]:
    if event_name == "pull_request":
        pull = event.get("pull_request") if isinstance(event, dict) else None
        pull = pull if isinstance(pull, dict) else {}
        base = pull.get("base") if isinstance(pull.get("base"), dict) else {}
        head = pull.get("head") if isinstance(pull.get("head"), dict) else {}
        return {
            "base_sha": _required(base.get("sha"), "pull_request.base.sha"),
            "head_sha": _required(head.get("sha"), "pull_request.head.sha"),
            "merge_sha": _required(checkout_sha, "merge checkout sha"),
        }
    if event_name == "push":
        return {
            "before_sha": _required(event.get("before"), "push.before"),
            "after_sha": _required(event.get("after"), "push.after"),
        }
    if event_name == "workflow_dispatch":
        return {"head_sha": _required(checkout_sha, "workflow dispatch sha")}
    raise EvidenceReadinessError(f"unsupported event: {event_name}")


def build_ci_evidence(run_id: str, run_attempt: int, commit: str, tree: str,
                      shas: dict[str, str], jobs: list[dict]) -> dict:
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
            state = "green"
        elif applicable and result == "failure":
            state = "red_judgment"
        elif applicable:
            state = "red_readiness"
        elif not raw.get("reason"):
            raise EvidenceReadinessError(f"{name}: non-applicable job needs a reason")
        counts[state] += 1
        normalized.append({"name": name, "applicable": applicable,
                           "result": result, "state": state,
                           "reason": raw.get("reason")})
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


def verify_gate_summary(summary: dict, commit: str, required_gates: list[str]) -> None:
    if summary.get("schema") != "colab-gate-summary/1":
        raise EvidenceError("invalid gate summary schema")
    if summary.get("commit") != commit:
        raise EvidenceError("gate summary commit differs")
    counts = summary.get("counts")
    if not isinstance(counts, dict) or counts.get("red_판정") != 0 or counts.get("red_준비") != 0:
        raise EvidenceError("gate summary is not green")
    gates = summary.get("gates")
    if not isinstance(gates, list):
        raise EvidenceError("gate summary has no gates")
    names = [item.get("name") for item in gates if isinstance(item, dict)]
    if len(names) != len(set(names)) or any(name not in names for name in required_gates):
        raise EvidenceError("required gate set is missing or duplicated")


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
        jobs = json.loads(args.jobs_json)
        tree = args.tree or subprocess.check_output(
            ["git", "rev-parse", "HEAD^{tree}"], text=True
        ).strip()
        evidence = build_ci_evidence(
            args.run_id, args.run_attempt, args.commit, tree,
            event_shas(args.event_name, event, args.commit), jobs,
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
        return 78
    except (EvidenceError, OSError, json.JSONDecodeError, subprocess.SubprocessError) as exc:
        print(f"red(판정): required-gates: {exc}", file=sys.stderr)
        return 1


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
    ci.add_argument("--jobs-json", required=True)
    ci.add_argument("--output", type=Path, required=True)
    ci.add_argument("--summary", type=Path)
    args = parser.parse_args(argv)
    return ci_command(args)


if __name__ == "__main__":
    raise SystemExit(main())
