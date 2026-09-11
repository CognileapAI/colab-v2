"""D3/D5 전수 ID를 한 read-only snapshot으로 원자 발행한다."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import create_engine, text

from ..domains import d3_catalog, d5_ingestion
from sqlalchemy.orm import sessionmaker


SCHEMA = "colab-preview-ownership-snapshot/1"
_OBSERVED_AT = text("SELECT clock_timestamp()")
_ROLE = text("""SELECT current_user, rolsuper, rolbypassrls,
  pg_has_role(current_user, 'pg_read_all_data', 'member')
FROM pg_roles WHERE rolname = current_user""")


def collect(session) -> dict:
    session.execute(text("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY"))
    snapshot_started_at = session.execute(_OBSERVED_AT).scalar_one()
    role, superuser, bypassrls, read_all = session.execute(_ROLE).one()
    if not read_all or not (superuser or bypassrls):
        raise RuntimeError("전수 snapshot 권한이 아니다")
    d3, d3_count = d3_catalog.all_file_ids_for_ownership_snapshot(session)
    d5, d5_count = d5_ingestion.UploadLedgerAdapter(session).all_file_ids_for_ownership_snapshot()
    if d3_count != len(d3) or d5_count != len(d5):
        raise RuntimeError("원장 count와 ID dump 길이가 다르다")
    payload = {
        "schema": SCHEMA,
        "observed_at": snapshot_started_at.isoformat(),
        "scope": "all-tenants",
        "database_role": str(role),
        "role_evidence": {"superuser": bool(superuser), "bypassrls": bool(bypassrls),
                          "read_all_data": bool(read_all)},
        "d3_file_ids": d3, "d5_upload_file_ids": d5,
        "counts": {"d3_file": len(d3), "d5_upload_file": len(d5)},
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    payload["content_sha256"] = hashlib.sha256(canonical).hexdigest()
    return payload


def atomic_write(path: Path, payload: dict, *, owner_uid: int | None = None,
                 group_gid: int | None = None) -> None:
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    data = (json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n").encode()
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        if owner_uid is not None or group_gid is not None:
            os.fchown(fd, -1 if owner_uid is None else owner_uid,
                      -1 if group_gid is None else group_gid)
        os.fchmod(fd, 0o440)
        with os.fdopen(fd, "wb") as stream:
            fd = None
            stream.write(data); stream.flush(); os.fsync(stream.fileno())
        os.replace(tmp, path)
    finally:
        if fd is not None: os.close(fd)
        if tmp.exists(): tmp.unlink()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="TL-2 전수 소유권 snapshot read-only publisher")
    parser.add_argument("--output", required=True)
    parser.add_argument("--database-url-file", required=True)
    parser.add_argument("--output-owner-uid", required=True, type=int)
    parser.add_argument("--output-group-gid", required=True, type=int)
    args = parser.parse_args(argv)
    secret = Path(args.database_url_file)
    info = secret.lstat()
    import stat
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode) or stat.S_IMODE(info.st_mode) != 0o600:
        raise RuntimeError("DB URL 파일은 일반 파일 mode 0600이어야 한다")
    database_url = secret.read_text(encoding="utf-8").strip()
    if not database_url:
        raise RuntimeError("DB URL 파일이 비었다")
    factory = sessionmaker(bind=create_engine(database_url), expire_on_commit=False)
    with factory() as session, session.begin():
        payload = collect(session)
    if args.output_owner_uid < 0 or args.output_group_gid < 0:
        raise RuntimeError("output owner uid/gid는 0 이상이어야 한다")
    atomic_write(Path(args.output), payload, owner_uid=args.output_owner_uid,
                 group_gid=args.output_group_gid)
    print(json.dumps({"schema": SCHEMA, "observed_at": payload["observed_at"],
                      "counts": payload["counts"], "content_sha256": payload["content_sha256"]},
                     sort_keys=True), flush=True)
    return 0

if __name__ == "__main__": raise SystemExit(main())
