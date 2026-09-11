"""검토된 exact-target 계획만 적용하는 저장소 유지보수 CLI."""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import stat

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .storage_maintenance import parse_storage_reclaim_approval, run_storage_maintenance
from ..kernel.auth import Subject
from ..kernel.config import load_settings
from ..kernel.ids import Ulid
from ..kernel.s3 import S3Client


def _private_plan(path: str) -> str:
    plan = pathlib.Path(path)
    info = plan.lstat()
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
        raise RuntimeError("승인 계획은 일반 파일이어야 한다")
    if info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) != 0o600:
        raise RuntimeError("승인 계획은 실행자 소유 mode 0600이어야 한다")
    return plan.read_text(encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply-approved", action="store_true")
    parser.add_argument("--plan", required=True)
    parser.add_argument("--plan-sha256", required=True)
    parser.add_argument("--lab-id", required=True)
    parser.add_argument("--account-id", required=True)
    parser.add_argument("--environment", required=True)
    parser.add_argument("--expected-bucket", required=True)
    parser.add_argument("--expected-region", required=True)
    parser.add_argument("--expected-code-sha", required=True)
    parser.add_argument("--release-state", required=True)
    args = parser.parse_args(argv)
    if not args.apply_approved:
        raise RuntimeError("--apply-approved 없이는 삭제를 실행하지 않는다")
    if (len(args.expected_code_sha) != 40
            or any(char not in "0123456789abcdef" for char in args.expected_code_sha)
            or pathlib.Path(args.release_state).read_text(encoding="utf-8").strip()
            != args.expected_code_sha[:12]
            or args.environment != "dev"):
        raise RuntimeError("실행 코드 SHA 또는 환경이 승인 패킷과 다르다")

    settings = load_settings()
    if (settings.storage_mode != "s3" or settings.s3_bucket != args.expected_bucket
            or settings.s3_region != args.expected_region):
        raise RuntimeError("실행 S3 대상이 승인 패킷과 다르다")
    approval = parse_storage_reclaim_approval(
        _private_plan(args.plan), expected_lab_id=args.lab_id,
        expected_sha256=args.plan_sha256)
    subject = Subject(account_id=Ulid(args.account_id), lab_id=Ulid(args.lab_id))
    factory = sessionmaker(bind=create_engine(settings.database_url), expire_on_commit=False)
    report = run_storage_maintenance(
        factory, subject, s3=S3Client(bucket=settings.s3_bucket, region=settings.s3_region),
        mode="apply", approval=approval)
    print(json.dumps({
        "planSha256": report.plan_sha256,
        "reclaimedUploads": report.reclaimed_uploads,
        "reapedOpenTransfers": report.reaped_open_transfers,
        "prunedCompletedTransfers": report.pruned_completed_transfers,
        "preserved": report.preserved,
    }, ensure_ascii=False, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
