#!/usr/bin/env python3
"""deploy_doctor의 24h S3 backup oracle만 재사용한다."""
from __future__ import annotations

import argparse
import importlib.util
import inspect
import sys
from pathlib import Path

READINESS = 78


def doctor_path(repo: Path) -> Path:
    return repo / "services/core-api/ops/deploy_doctor.py"


def self_check(repo: Path) -> int:
    try:
        doctor = load_doctor(repo)
    except (OSError, ImportError, TypeError):
        return READINESS
    try:
        ctx = doctor.parse_args(["--env", "dev", "--bucket", "colab-platform-data-dev"])
        rep = doctor.DeployReport()
    except (AttributeError, TypeError, SystemExit):
        return READINESS
    return 0 if ctx.env == "dev" and ctx.bucket == "colab-platform-data-dev" and rep is not None else READINESS


def load_doctor(repo: Path):
    path = doctor_path(repo)
    if not path.is_file():
        raise FileNotFoundError(path)
    ops = path.parent
    source = repo / "services/core-api/src"
    sys.path[:0] = [str(ops), str(source)]
    spec = importlib.util.spec_from_file_location("colab_deploy_doctor", path)
    if spec is None or spec.loader is None:
        raise ImportError("deploy_doctor spec")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    if list(inspect.signature(module.check_backups).parameters) != ["ctx", "rep"]:
        raise TypeError("check_backups signature")
    return module


def run(repo: Path) -> int:
    try:
        doctor = load_doctor(repo)
    except (OSError, ImportError, TypeError) as exc:
        print(f"::gate-readiness-failure::gate=backup-freshness|detail={type(exc).__name__}", file=sys.stderr)
        return READINESS
    ctx = doctor.parse_args(["--env", "dev", "--bucket", "colab-platform-data-dev"])
    rep = doctor.DeployReport()
    doctor.check_operator_credentials(ctx, rep)
    before = len(rep._marks)
    doctor.check_backups(ctx, rep)
    backup_marks = rep._marks[before:]
    if not backup_marks or doctor.BAD in backup_marks or doctor.SKIP in backup_marks:
        return 1
    print("backup-freshness green — deploy_doctor.check_backups 단독 oracle 통과")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args()
    return self_check(args.repo) if args.self_check else run(args.repo)


if __name__ == "__main__":
    raise SystemExit(main())
