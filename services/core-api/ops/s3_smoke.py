"""`s3_smoke` — 멀티파트 전 과정 실전 왕복 (dev-package/S3.md §2).

doctor 가 "설정이 맞는가"를 본다면, smoke 는 "업로드 기계가 실제로 도는가"를 본다.
서명·클라이언트 코드를 고쳤으면 이 스크립트로 실전 재검증한다.

    (services/core-api 에서)
    .venv/bin/python ops/s3_smoke.py [--bucket 이름] [--region ap-northeast-2]

실패 해석: 403 SignatureDoesNotMatch = SigV4 정규화 버그 ·
400 MalformedXML = Complete 본문 문제 · 404 NoSuchUpload = uploadId 전달 문제.
"""
from __future__ import annotations

import argparse
import os
import sys
import time
import urllib.request
from datetime import datetime, timezone

from colab_core.kernel.aws_credentials import load_credentials
from colab_core.kernel.s3 import S3Client, S3Error
from colab_core.kernel.sigv4 import presign

MIN_PART = 5 * 1024 * 1024  # 마지막이 아닌 파트의 S3 최소 크기


def _put_presigned(url: str, payload: bytes) -> int:
    req = urllib.request.Request(url, method="PUT", data=payload)
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.status


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="멀티파트 실전 왕복 (dev-package/S3.md §2)")
    parser.add_argument("--bucket", default=os.environ.get("COLAB_S3_BUCKET"))
    parser.add_argument("--region", default=os.environ.get("COLAB_S3_REGION", "ap-northeast-2"))
    args = parser.parse_args(argv)
    if not args.bucket:
        print("--bucket 또는 COLAB_S3_BUCKET 이 필요하다 (dev-package/S3.md §1)")
        return 1

    creds, _source = load_credentials()
    c = S3Client(bucket=args.bucket, region=args.region, creds=creds)
    stamp = int(time.time())
    keys: list[str] = []
    failed = False

    def step(label: str, fn):
        nonlocal failed
        if failed:
            print(f"  ─ {label} (건너뜀)")
            return
        t0 = time.monotonic()
        try:
            detail = fn() or ""
            print(f"  ✓ {label} ({time.monotonic() - t0:.2f}s) {detail}")
        except (S3Error, OSError, AssertionError) as e:
            failed = True
            print(f"  ✗ {label} — {e}")

    def presigned_put(key: str, payload: bytes) -> None:
        url = presign(method="PUT", host=c.host, key=key, region=args.region,
                      creds=creds, query={}, expires=900, now=datetime.now(timezone.utc))
        status = _put_presigned(url, payload)
        assert status == 200, f"PUT {status}"

    def assert_size(key: str, expected: int) -> str:
        size, _etag = c.head_object(key)
        assert size == expected, f"크기 기대 {expected}, 실제 {size}"
        return f"{size}B"

    # 1·2. 프리사인드 단일 PUT + HeadObject
    key_a = f"_smoke/{stamp}/plain.bin"
    keys.append(key_a)
    step("프리사인드 PUT (ASCII 키)", lambda: presigned_put(key_a, b"x" * 1024))
    step("HeadObject 크기 확인", lambda: assert_size(key_a, 1024))

    # 3. 한글·공백 키 — UriEncode 검증
    key_b = f"_smoke/{stamp}/한글 폴더/데이터 1.bin"
    keys.append(key_b)
    step("프리사인드 PUT (한글·공백 키)", lambda: presigned_put(key_b, b"y" * 2048))
    step("HeadObject (한글 키)", lambda: assert_size(key_b, 2048))

    # 4. 멀티파트 전 과정: create → 파트 2개 → list → complete → head
    key_c = f"_smoke/{stamp}/multi.bin"
    keys.append(key_c)
    part1, part2 = b"a" * MIN_PART, b"b" * 1024
    state: dict[str, str] = {}

    def mp_create():
        state["upload_id"] = c.create_multipart_upload(key_c, "application/octet-stream")
        return state["upload_id"][:12] + "…"

    def mp_put_parts():
        for n, payload in ((1, part1), (2, part2)):
            url = presign(method="PUT", host=c.host, key=key_c, region=args.region,
                          creds=creds, query={"partNumber": str(n), "uploadId": state["upload_id"]},
                          expires=900, now=datetime.now(timezone.utc))
            status = _put_presigned(url, payload)
            assert status == 200, f"파트 {n} PUT {status}"
        return "5MiB + 1KiB"

    def mp_complete():
        parts = c.list_parts(key_c, state["upload_id"])
        assert [p.number for p in parts] == [1, 2], f"파트 목록 {parts}"
        assert parts[0].size == MIN_PART and parts[1].size == 1024
        c.complete_multipart_upload(key_c, state["upload_id"], parts)
        size, _etag = c.head_object(key_c)
        assert size == MIN_PART + 1024, f"조립 후 크기 {size}"
        return f"{size}B"

    step("CreateMultipartUpload", mp_create)
    step("파트 2개 프리사인드 PUT", mp_put_parts)
    step("ListParts → Complete → Head", mp_complete)

    # 5. Abort — 중단하면 진행 중 목록에서 사라져야 한다
    key_d = f"_smoke/{stamp}/aborted.bin"

    def mp_abort():
        upload_id = c.create_multipart_upload(key_d)
        url = presign(method="PUT", host=c.host, key=key_d, region=args.region,
                      creds=creds, query={"partNumber": "1", "uploadId": upload_id},
                      expires=900, now=datetime.now(timezone.utc))
        assert _put_presigned(url, b"z" * 1024) == 200
        c.abort_multipart_upload(key_d, upload_id)
        remaining = [u for _k, u in c.list_multipart_uploads(prefix=key_d)]
        assert upload_id not in remaining, "Abort 후에도 목록에 남아 있다"
        return "소멸 확인"

    step("Create → 파트 1 → Abort → 소멸", mp_abort)

    # 6. 뒷정리 — 성공 여부와 무관하게 시도한다
    try:
        c.delete_objects(keys)
        listed = list(c.list_objects(f"_smoke/{stamp}/"))
        if listed:
            print(f"  ✗ 뒷정리 — 남은 객체 {len(listed)}개: 손으로 지울 것 (_smoke/{stamp}/)")
            failed = True
        else:
            print("  ✓ DeleteObjects 뒷정리 (남은 객체 0)")
    except S3Error as e:
        print(f"  ✗ 뒷정리 실패 — {e} · _smoke/{stamp}/ 를 손으로 지울 것")
        failed = True

    print(f"\n  {'실패 — 위 ✗ 를 해결하기 전에는 다음 지점으로 가지 않는다' if failed else '통과 — 멀티파트 전 과정이 실전에서 돈다 '}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
