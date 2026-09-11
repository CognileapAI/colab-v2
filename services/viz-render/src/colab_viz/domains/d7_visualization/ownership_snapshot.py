"""D3/D5 소유자가 원자적으로 낸 전수 ID snapshot의 fail-closed 판독기."""
from __future__ import annotations

import hashlib
import json
import os
import stat
from datetime import datetime, timezone
from pathlib import Path

from ...kernel.ids import is_ulid
from .ownership import Ledger

SCHEMA = "colab-preview-ownership-snapshot/1"
MAX_BYTES = 64 * 1024 * 1024
_FIELDS = {"schema", "observed_at", "scope", "database_role", "role_evidence",
           "d3_file_ids", "d5_upload_file_ids", "counts", "content_sha256"}

class SnapshotNotReady(RuntimeError):
    pass


def _fail(message: str) -> SnapshotNotReady:
    return SnapshotNotReady(f"TL-2 원장 snapshot 준비 실패 — {message}")


def _load(path: Path, *, max_age_seconds: float, expected_owner_uid: int | None = None,
         expected_group_gid: int | None = None, now: datetime | None = None) -> Ledger:
    path = Path(path)
    owner_uid = os.getuid() if expected_owner_uid is None else expected_owner_uid
    group_gid = os.getgid() if expected_group_gid is None else expected_group_gid
    fd = None
    try:
        parent = path.parent.stat()
        if (parent.st_uid != owner_uid or parent.st_gid != group_gid
                or stat.S_IMODE(parent.st_mode) != 0o550):
            raise _fail("snapshot 디렉터리가 publisher 소유·consumer 그룹·mode 0550이 아니다")
        fd = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
        info = os.fstat(fd)
        if (not stat.S_ISREG(info.st_mode) or info.st_uid != owner_uid
                or info.st_gid != group_gid or stat.S_IMODE(info.st_mode) != 0o440):
            raise _fail("publisher 소유·consumer 그룹·mode 0440 일반 파일이 아니다")
        if info.st_size <= 0 or info.st_size > MAX_BYTES:
            raise _fail("파일 크기 범위를 벗어났다")
        chunks = []
        while True:
            chunk = os.read(fd, min(1 << 20, info.st_size + 1 - sum(map(len, chunks))))
            if not chunk: break
            chunks.append(chunk)
            if sum(map(len, chunks)) > info.st_size: raise _fail("읽는 동안 파일 크기가 바뀌었다")
        raw = b"".join(chunks)
        after = os.fstat(fd)
        identity = lambda value: (value.st_dev, value.st_ino, value.st_size, value.st_mode, value.st_uid, value.st_gid)
        if len(raw) != info.st_size or identity(after) != identity(info):
            raise _fail("읽는 동안 파일 identity가 바뀌었다")
        def unique(pairs):
            out = {}
            for key, value in pairs:
                if key in out: raise ValueError(f"duplicate JSON key: {key}")
                out[key] = value
            return out
        doc = json.loads(raw, object_pairs_hook=unique)
    except SnapshotNotReady:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise _fail(f"파일을 읽지 못했다 ({type(exc).__name__})") from None
    finally:
        if fd is not None: os.close(fd)
    if not isinstance(doc, dict) or set(doc) != _FIELDS:
        raise _fail("schema 필드 집합이 다르다")
    if doc["schema"] != SCHEMA or doc["scope"] != "all-tenants":
        raise _fail("schema 또는 전수 scope가 다르다")
    evidence = doc["role_evidence"]
    if (not isinstance(evidence, dict) or set(evidence) != {"superuser", "bypassrls", "read_all_data"}
            or any(type(evidence[key]) is not bool for key in evidence)
            or not evidence["read_all_data"]
            or not (evidence["superuser"] or evidence["bypassrls"])):
        raise _fail("전수 조회 권한 실측이 없다")
    d3, d5 = doc["d3_file_ids"], doc["d5_upload_file_ids"]
    if not isinstance(d3, list) or not isinstance(d5, list) or not d3 and not d5:
        raise _fail("ID 배열이 비었거나 형식이 다르다")
    if any(type(value) is not str or not is_ulid(value) for value in [*d3, *d5]):
        raise _fail("ULID 문자열이 아닌 ID가 있다")
    if len(set(d3)) != len(d3) or len(set(d5)) != len(d5):
        raise _fail("중복 ID가 있다")
    if doc["counts"] != {"d3_file": len(d3), "d5_upload_file": len(d5)}:
        raise _fail("선언 count와 ID 배열이 다르다")
    digest_doc = dict(doc); claimed = digest_doc.pop("content_sha256")
    canonical = json.dumps(digest_doc, sort_keys=True, separators=(",", ":")).encode()
    if not isinstance(claimed, str) or hashlib.sha256(canonical).hexdigest() != claimed:
        raise _fail("내용 hash가 다르다")
    try:
        observed = datetime.fromisoformat(doc["observed_at"])
        if observed.tzinfo is None: raise ValueError
    except (TypeError, ValueError):
        raise _fail("observed_at이 timezone timestamp가 아니다") from None
    current = now or datetime.now(timezone.utc)
    age = (current - observed.astimezone(timezone.utc)).total_seconds()
    if age < -300 or age > max_age_seconds:
        raise _fail("snapshot이 미래이거나 너무 오래됐다")
    return Ledger(frozenset(d3), frozenset(d5))


def load(path: Path, *, max_age_seconds: float, expected_owner_uid: int | None = None,
         expected_group_gid: int | None = None, now: datetime | None = None) -> Ledger:
    """모든 입력/형식 실패를 준비 실패 한 종류로 닫는다."""
    try:
        return _load(path, max_age_seconds=max_age_seconds, expected_owner_uid=expected_owner_uid,
                     expected_group_gid=expected_group_gid, now=now)
    except SnapshotNotReady:
        raise
    except Exception as exc:
        raise _fail(f"snapshot 형식이 올바르지 않다 ({type(exc).__name__})") from None
