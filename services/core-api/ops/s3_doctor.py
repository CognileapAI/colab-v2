"""`s3_doctor` — AWS 콘솔 작업(버킷·정책·CORS·라이프사이클)의 기계적 검증 도구 (dev-package/S3.md §2).

AWS CLI 를 쓰지 않기로 했으므로 이 스크립트가 유일한 검증 수단이다.
`kernel/sigv4.py` 의 헤더 인증으로 STS·S3 에 직접 묻는다.

    (services/core-api 에서)
    .venv/bin/python ops/s3_doctor.py [--bucket 이름] [--region ap-northeast-2]
                                      [--origin http://localhost:5173]

설계 규칙:
- 각 항목은 ✓ / ✗ / ─(해당 없음·건너뜀). ✗ 는 기대값과 실제값을 나란히 찍는다
- 앞 항목이 실패하면 뒤 항목은 ─ 로 건너뛴다 — 에러 열 개가 쏟아지면 원인이 묻힌다
- 마지막 줄에 다음 할 일과 dev-package/S3.md 절 번호를 찍는다
- 왕복 테스트가 남긴 객체는 반드시 지우고 끝낸다
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

from colab_core.kernel.aws_credentials import load_credentials
from colab_core.kernel.sigv4 import Credentials, sign_headers

OK, BAD, SKIP = "✓", "✗", "─"


class Report:
    def __init__(self) -> None:
        self.passed = 0
        self.failed = 0

    def line(self, status: str, label: str, detail: str = "") -> None:
        if status == OK:
            self.passed += 1
        elif status == BAD:
            self.failed += 1
        print(f"    {status} {label:<14}{detail}")

    def section(self, title: str) -> None:
        print(f"  {title}")


def _request(url: str, *, method: str, headers: dict[str, str],
             payload: bytes = b"") -> tuple[int, bytes]:
    req = urllib.request.Request(url, method=method, headers=headers,
                                 data=payload if payload else None)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


def _s3_call(*, method: str, bucket: str, region: str, creds: Credentials,
             key: str = "", query: dict[str, str] | None = None,
             payload: bytes = b"") -> tuple[int, bytes]:
    host = f"{bucket}.s3.{region}.amazonaws.com"
    now = datetime.now(timezone.utc)
    headers = sign_headers(method=method, host=host, key=key, region=region,
                           creds=creds, query=query or {}, payload=payload, now=now)
    from colab_core.kernel.sigv4 import uri_encode  # 키 인코딩 규칙을 서명과 공유
    path = "/" + uri_encode(key, keep_slash=True)
    qs = "&".join(f"{k}={v}" if v else f"{k}=" for k, v in sorted((query or {}).items()))
    url = f"https://{host}{path}" + (f"?{qs}" if qs else "")
    return _request(url, method=method, headers=headers, payload=payload)


def _error_code(body: bytes) -> str:
    try:
        node = ET.fromstring(body.decode("utf-8", "replace")).find(".//{*}Code")
        if node is None:  # 일부 에러는 Error 가 루트다
            node = ET.fromstring(body.decode("utf-8", "replace")).find("{*}Code")
        return node.text or "" if node is not None else ""
    except ET.ParseError:
        return ""


def check_credentials(rep: Report, region: str) -> Credentials | None:
    rep.section("자격증명")
    try:
        creds, source = load_credentials()
    except RuntimeError as e:
        rep.line(BAD, "출처", str(e))
        return None
    rep.line(OK, "출처", source + (" (AWS_ACCESS_KEY_ID)" if source == "env" else ""))
    host = f"sts.{region}.amazonaws.com"
    now = datetime.now(timezone.utc)
    query = {"Action": "GetCallerIdentity", "Version": "2011-06-15"}
    headers = sign_headers(method="GET", host=host, key="", region=region,
                           creds=creds, query=query, now=now, service="sts")
    status, body = _request(
        f"https://{host}/?Action=GetCallerIdentity&Version=2011-06-15",
        method="GET", headers=headers,
    )
    if status != 200:
        rep.line(BAD, "유효", f"STS {status} — {_error_code(body) or body[:120]!r}")
        return None
    arn = ET.fromstring(body).find(".//{*}Arn")
    rep.line(OK, "유효", arn.text if arn is not None else "(Arn 파싱 실패)")
    if creds.expires_at is None:
        rep.line(SKIP, "만료", "없음 (장기 자격증명)")
    else:
        rep.line(OK, "만료", creds.expires_at.isoformat())
    return creds


def check_bucket(rep: Report, bucket: str, region: str, origin: str,
                 creds: Credentials) -> bool:
    """설정 항목을 검사한다. 존재 확인이 실패하면 나머지는 ─."""
    rep.section(f"버킷  {bucket}")
    status, body = _s3_call(method="HEAD", bucket=bucket, region=region, creds=creds)
    if status != 200:
        rep.line(BAD, "존재", f"HeadBucket {status}")
        for label in ("리전", "버저닝", "기본 암호화", "CORS", "버킷 정책", "라이프사이클"):
            rep.line(SKIP, label, "존재 확인 실패로 건너뜀")
        return False
    rep.line(OK, "존재")

    def diag(label: str, query: dict[str, str], render) -> None:
        s, b = _s3_call(method="GET", bucket=bucket, region=region, creds=creds, query=query)
        if s == 403:
            rep.line(SKIP, label, "권한 없음 (prod 정책은 진단 제외가 정상 — dev-package/S3.md §1)")
        else:
            render(s, b)

    def r_location(s: int, b: bytes) -> None:
        if s != 200:
            rep.line(BAD, "리전", f"GetBucketLocation {s}")
            return
        node = ET.fromstring(b)
        actual = (node.text or "").strip() or "us-east-1"  # 빈 값 = us-east-1 특례
        rep.line(OK if actual == region else BAD, "리전",
                 actual if actual == region else f"기대 {region}, 실제 {actual}")

    def r_versioning(s: int, b: bytes) -> None:
        node = ET.fromstring(b).find("{*}Status") if s == 200 else None
        actual = node.text if node is not None and node.text else "미설정"
        rep.line(OK if actual == "Enabled" else BAD, "버저닝",
                 actual if actual == "Enabled" else f"기대 Enabled, 실제 {actual}")

    def r_encryption(s: int, b: bytes) -> None:
        if s != 200:
            rep.line(BAD, "기본 암호화", f"기대 SSE 구성, 실제 없음 ({_error_code(b) or s})")
            return
        algo = ET.fromstring(b).find(".//{*}SSEAlgorithm")
        bucket_key = ET.fromstring(b).find(".//{*}BucketKeyEnabled")
        detail = (algo.text if algo is not None else "?") + (
            " (Bucket Key on)" if bucket_key is not None and bucket_key.text == "true" else ""
        )
        rep.line(OK if algo is not None else BAD, "기본 암호화", detail)

    def r_cors(s: int, b: bytes) -> None:
        if s != 200:
            rep.line(BAD, "CORS", f"AllowedOrigins 에 {origin} 없음 — 현재: 구성 자체가 없음")
            return
        origins = [n.text for n in ET.fromstring(b).findall(".//{*}AllowedOrigin")]
        ok = origin in origins
        rep.line(OK if ok else BAD, "CORS",
                 f"오리진 {origins}" if ok else f"AllowedOrigins 에 {origin} 없음 — 현재: {origins}")

    def r_policy(s: int, b: bytes) -> None:
        if s != 200:
            rep.line(BAD, "버킷 정책", "기대 DenyInsecureTransport, 실제 정책 없음")
            return
        try:
            stmts = json.loads(b).get("Statement", [])
        except json.JSONDecodeError:
            stmts = []
        ok = any(
            st.get("Effect") == "Deny"
            and str(st.get("Condition", {}).get("Bool", {})
                    .get("aws:SecureTransport", "")).lower() == "false"
            for st in stmts
        )
        rep.line(OK if ok else BAD, "버킷 정책",
                 "DenyInsecureTransport 있음" if ok else "TLS 강제(Deny) 문이 없음")

    def r_lifecycle(s: int, b: bytes) -> None:
        if s != 200:
            rep.line(BAD, "라이프사이클", "AbortIncompleteMultipartUpload 규칙 없음 (구성 없음)")
            return
        ok = any(
            r.find("{*}AbortIncompleteMultipartUpload") is not None
            and (r.find("{*}Status") is not None and r.find("{*}Status").text == "Enabled")
            for r in ET.fromstring(b).findall(".//{*}Rule")
        )
        rep.line(OK if ok else BAD, "라이프사이클",
                 "Abort 규칙 있음" if ok else "AbortIncompleteMultipartUpload 규칙 없음")

    diag("리전", {"location": ""}, r_location)
    diag("버저닝", {"versioning": ""}, r_versioning)
    diag("기본 암호화", {"encryption": ""}, r_encryption)
    diag("CORS", {"cors": ""}, r_cors)
    diag("버킷 정책", {"policy": ""}, r_policy)
    diag("라이프사이클", {"lifecycle": ""}, r_lifecycle)
    return True


def check_roundtrip(rep: Report, bucket: str, region: str, creds: Credentials) -> None:
    rep.section("왕복 테스트")
    key = f"_doctor/probe-{int(time.time())}"
    body = b"s3_doctor probe"
    t0 = time.monotonic()
    try:
        for method, payload, expect in (("PUT", body, 200), ("HEAD", b"", 200),
                                        ("GET", b"", 200)):
            s, resp = _s3_call(method=method, bucket=bucket, region=region,
                               creds=creds, key=key, payload=payload)
            if s != expect:
                rep.line(BAD, "PUT/HEAD/GET",
                         f"{method} {s} — {_error_code(resp) or resp[:120]!r}")
                return
        rep.line(OK, "PUT/HEAD/GET", f"성공 ({time.monotonic() - t0:.2f}s)")
    finally:
        s, _resp = _s3_call(method="DELETE", bucket=bucket, region=region,
                            creds=creds, key=key)
        if s not in (200, 204):
            rep.line(BAD, "정리", f"probe 객체 삭제 실패 ({s}) — 손으로 지울 것: {key}")
    rep.line(SKIP, "멀티파트", "전 과정 검증은 s3_smoke 몫")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="S3 설정 진단 (dev-package/S3.md §2)")
    parser.add_argument("--bucket", default=os.environ.get("COLAB_S3_BUCKET"),
                        help="검사할 버킷 (기본: 환경변수 COLAB_S3_BUCKET)")
    parser.add_argument("--region", default=os.environ.get("COLAB_S3_REGION", "ap-northeast-2"))
    parser.add_argument("--origin", default=os.environ.get("COLAB_S3_ORIGIN", "http://localhost:5173"),
                        help="CORS 에 있어야 할 오리진")
    args = parser.parse_args(argv)

    print()
    rep = Report()
    creds = check_credentials(rep, args.region)
    if creds is None:
        print(f"\n  {rep.passed}/{rep.passed + rep.failed} 통과 · 다음: 자격증명 설정 (dev-package/S3.md §1)")
        return 1
    if not args.bucket:
        rep.section("버킷")
        rep.line(SKIP, "(미지정)", "--bucket 또는 COLAB_S3_BUCKET 을 주면 검사한다 (dev-package/S3.md §1)")
    else:
        if check_bucket(rep, args.bucket, args.region, args.origin, creds):
            check_roundtrip(rep, args.bucket, args.region, creds)
    total = rep.passed + rep.failed
    print(f"\n  {rep.passed}/{total} 통과", end="")
    print(" · 고치는 법: dev-package/S3.md §1 (CORS·정책·라이프사이클)" if rep.failed else "")
    return 0 if rep.failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
