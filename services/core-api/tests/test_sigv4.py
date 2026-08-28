"""SigV4 서명기 오라클 — `kernel/sigv4.py` · `kernel/aws_credentials.py`.

정본은 AWS SigV4 규격 문서의 서명 예제다.
알려진 정답(known-answer) 벡터: AWS 문서 "Signature Calculation: Examples" —
자격증명 AKIAIOSFODNN7EXAMPLE, 버킷 examplebucket, us-east-1, 2013-05-24T00:00:00Z.
서명의 최종 검증은 실제 S3 왕복(ops/s3_smoke.py)이고, 여기는 규격 준수를 본다.

DB·AWS 불필요 — 순수 단위 테스트다.
"""
from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone

from colab_core.kernel.sigv4 import (
    EMPTY_SHA256,
    Credentials,
    canonical_request_for_headers,
    canonical_request_for_presign,
    presign,
    sign_headers,
    uri_encode,
)

# AWS 문서 예제의 고정 재료
AK = "AKIAIOSFODNN7EXAMPLE"
SK = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
HOST = "examplebucket.s3.amazonaws.com"
REGION = "us-east-1"
NOW = datetime(2013, 5, 24, 0, 0, 0, tzinfo=timezone.utc)
CREDS = Credentials(access_key=AK, secret_key=SK)


# ── 1. UriEncode 엣지 케이스 (§6 — quote 기본값과 규칙이 다르다) ────────────

def test_uri_encode_space_is_percent20():
    assert uri_encode("a b") == "a%20b"          # 절대 '+' 아님


def test_uri_encode_plus_is_encoded():
    assert uri_encode("a+b") == "a%2Bb"


def test_uri_encode_tilde_kept():
    assert uri_encode("~x-._") == "~x-._"        # unreserved 는 그대로


def test_uri_encode_hex_uppercase():
    assert uri_encode("\x1a") == "%1A"


def test_uri_encode_hangul_utf8_bytes():
    # 한글은 UTF-8 바이트별 대문자 %XX — 키에 원본 경로(한글·공백)가 들어간다
    assert uri_encode("한.csv") == "%ED%95%9C.csv"


def test_uri_encode_slash_kept_only_in_key():
    assert uri_encode("a/b", keep_slash=True) == "a/b"
    assert uri_encode("a/b") == "a%2Fb"


# ── 2·4. CanonicalRequest — 정렬·빈 줄까지 문서 예제와 바이트 일치 ──────────

def test_canonical_request_presign_matches_aws_doc():
    cr, _query = canonical_request_for_presign(
        method="GET", host=HOST, key="test.txt", region=REGION,
        creds=CREDS, query={}, expires=86400, now=NOW, service="s3",
    )
    assert cr == (
        "GET\n"
        "/test.txt\n"
        "X-Amz-Algorithm=AWS4-HMAC-SHA256"
        "&X-Amz-Credential=AKIAIOSFODNN7EXAMPLE%2F20130524%2Fus-east-1%2Fs3%2Faws4_request"
        "&X-Amz-Date=20130524T000000Z"
        "&X-Amz-Expires=86400"
        "&X-Amz-SignedHeaders=host\n"
        "host:examplebucket.s3.amazonaws.com\n"
        "\n"                                     # CanonicalHeaders 블록 뒤의 빈 줄 — 규격이다
        "host\n"
        "UNSIGNED-PAYLOAD"
    )


def test_canonical_request_headers_matches_aws_doc():
    cr, _headers = canonical_request_for_headers(
        method="GET", host=HOST, key="test.txt", region=REGION,
        creds=CREDS, query={}, payload=b"", now=NOW,
        headers={"Range": "bytes=0-9"}, service="s3",
    )
    assert cr == (
        "GET\n"
        "/test.txt\n"
        "\n"
        "host:examplebucket.s3.amazonaws.com\n"
        "range:bytes=0-9\n"
        f"x-amz-content-sha256:{EMPTY_SHA256}\n"
        "x-amz-date:20130524T000000Z\n"
        "\n"
        "host;range;x-amz-content-sha256;x-amz-date\n"
        f"{EMPTY_SHA256}"
    )


def test_query_sort_is_bytewise():
    # 'X'(0x58) < 'p'(0x70)·'u'(0x75) — X-Amz-* 가 partNumber·uploadId 앞
    cr, _q = canonical_request_for_presign(
        method="PUT", host=HOST, key="k", region=REGION, creds=CREDS,
        query={"uploadId": "abc123", "partNumber": "3"},
        expires=900, now=NOW, service="s3",
    )
    qline = cr.split("\n")[2]
    assert re.fullmatch(
        r"X-Amz-Algorithm=[^&]+&X-Amz-Credential=[^&]+&X-Amz-Date=[^&]+"
        r"&X-Amz-Expires=900&X-Amz-SignedHeaders=host&partNumber=3&uploadId=abc123",
        qline,
    ), qline


# ── 3. 빈 본문 SHA-256 상수 ────────────────────────────────────────────────

def test_empty_payload_sha256_constant():
    assert EMPTY_SHA256 == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"


# ── 5. 알려진 정답 서명 + 결정성 ────────────────────────────────────────────

def test_presign_known_answer_and_deterministic():
    url1 = presign(method="GET", host=HOST, key="test.txt", region=REGION,
                   creds=CREDS, query={}, expires=86400, now=NOW)
    url2 = presign(method="GET", host=HOST, key="test.txt", region=REGION,
                   creds=CREDS, query={}, expires=86400, now=NOW)
    assert url1 == url2                          # 같은 입력 → 같은 서명
    assert url1.startswith(f"https://{HOST}/test.txt?")
    sig = url1.rsplit("X-Amz-Signature=", 1)[1]
    assert sig == "aeeed9bbccd4d02ee5c0109b86d86835f995330da4c265957d157751f604d404"
    # 서명이 쿼리 맨 마지막에 덧붙는다
    assert url1.rsplit("&", 1)[1] == f"X-Amz-Signature={sig}"


def test_sign_headers_known_answer():
    headers = sign_headers(method="GET", host=HOST, key="test.txt", region=REGION,
                           creds=CREDS, query={}, payload=b"", now=NOW,
                           headers={"Range": "bytes=0-9"})
    auth = headers["Authorization"]
    assert auth.startswith(
        "AWS4-HMAC-SHA256 Credential=AKIAIOSFODNN7EXAMPLE/20130524/us-east-1/s3/aws4_request"
    )
    assert "SignedHeaders=host;range;x-amz-content-sha256;x-amz-date" in auth
    assert auth.endswith(
        "Signature=f0e8bdb87c964420e857bd35b5d6ed310bd44f0170aba48dd91039c6036bdb41"
    )
    assert headers["x-amz-date"] == "20130524T000000Z"
    assert headers["x-amz-content-sha256"] == EMPTY_SHA256
    assert headers["host"] == HOST


def test_session_token_is_signed_in_presign_query():
    creds = Credentials(access_key=AK, secret_key=SK, session_token="TOKEN123")
    url = presign(method="GET", host=HOST, key="k", region=REGION,
                  creds=creds, query={}, expires=900, now=NOW)
    assert "X-Amz-Security-Token=TOKEN123" in url
    # 토큰이 서명 앞(= CanonicalQueryString 안)에 있어야 한다 — 서명 대상이라는 뜻
    assert url.index("X-Amz-Security-Token=") < url.index("X-Amz-Signature=")


# ── 6. TTL 클램프 (§6 — 임시 자격증명 만료를 넘는 URL 은 배포 후에만 403) ──

def test_effective_ttl_clamp():
    from colab_core.kernel.aws_credentials import effective_ttl

    long_lived = Credentials(access_key=AK, secret_key=SK)
    assert effective_ttl(900, long_lived, NOW) == 900
    assert effective_ttl(999_999_999, long_lived, NOW) == 604800   # 프리사인 상한 7일

    expiring = Credentials(access_key=AK, secret_key=SK, session_token="t",
                           expires_at=NOW + timedelta(seconds=300))
    assert effective_ttl(900, expiring, NOW) == 240                # 만료 - 60초 여유
    nearly_dead = Credentials(access_key=AK, secret_key=SK, session_token="t",
                              expires_at=NOW + timedelta(seconds=30))
    assert effective_ttl(900, nearly_dead, NOW) == 60              # 바닥 60초


# ── 자격증명 공급자 — 환경변수 경로 ─────────────────────────────────────────

def test_env_credentials_provider(monkeypatch):
    from colab_core.kernel import aws_credentials

    monkeypatch.setenv("AWS_ACCESS_KEY_ID", AK)
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", SK)
    monkeypatch.delenv("AWS_SESSION_TOKEN", raising=False)
    aws_credentials.clear_cache()
    creds, source = aws_credentials.load_credentials()
    assert (creds.access_key, creds.secret_key) == (AK, SK)
    assert creds.session_token is None and creds.expires_at is None
    assert source == "env"
