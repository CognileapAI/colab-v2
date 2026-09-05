"""S3 커널 복제본 스모크 — `kernel/{sigv4,aws_credentials,s3}.py` 가 core-api 원본과 같은 바이트인가.

정본은 core-api 의 커널이고, 이 단위의 셋은 `contracts/codegen/manifest.toml` 에 등기된 복제본이다
(`generated-up-to-date` 게이트가 같은 것을 재생성해 대조한다). 이 시험은 게이트가 안 도는 자리
(단위 pytest)에서도 드리프트를 잡고, 복제본이 **이 단위 안에서** 성립하는지 — 형제 모듈이
core-api 가 아니라 이 단위의 kernel 로 묶이는지 — 를 본다.

DB·AWS·geo 라이브러리 불필요 — stdlib + 이 단위의 kernel 만 import 한다.
"""
from __future__ import annotations

import filecmp
import sys
import tomllib
from datetime import datetime, timezone
from pathlib import Path

from colab_viz.kernel import aws_credentials, s3, sigv4
from colab_viz.kernel.s3 import S3Client
from colab_viz.kernel.sigv4 import EMPTY_SHA256, Credentials, sign_headers

UNIT_PACKAGE = "colab_viz"
UNIT_DIR = "services/viz-render"
CORE_KERNEL = "services/core-api/src/colab_core/kernel"
MIRRORED = ("sigv4.py", "aws_credentials.py", "s3.py")


def _repo_root() -> Path:
    """등기부(`contracts/codegen/manifest.toml`)가 있는 조상 — 절대경로를 적지 않는다."""
    for parent in Path(__file__).resolve().parents:
        if (parent / "contracts" / "codegen" / "manifest.toml").is_file():
            return parent
    raise AssertionError("레포 루트를 찾지 못했다 (contracts/codegen/manifest.toml 기준)")


# ── 1. import 성립 — 형제 모듈이 이 단위의 kernel 로 묶인다 ─────────────────

def test_mirrored_kernel_imports_resolve_inside_this_unit():
    assert S3Client is s3.S3Client
    assert s3.__name__ == f"{UNIT_PACKAGE}.kernel.s3"
    # s3 → aws_credentials → sigv4 가 상대 import 라 core-api 가 아니라 **여기의** 모듈을 가리킨다
    assert s3.Credentials is sigv4.Credentials
    assert s3.load_credentials is aws_credentials.load_credentials
    assert aws_credentials.Credentials is sigv4.Credentials
    # 복제본이 core-api 패키지를 끌어오면 units-independent 위반이다 — 어떤 경로로도
    assert not [m for m in sys.modules if m.split(".", 1)[0] == "colab_core"]
    client = S3Client(bucket="b", region="ap-northeast-2",
                      creds=Credentials(access_key="AKIAEXAMPLE", secret_key="s"))
    assert client.host == "b.s3.ap-northeast-2.amazonaws.com"


# ── 2. 서명 벡터 — core `tests/test_sigv4.py` 의 알려진 정답과 같은 결과 ──────

def test_sigv4_known_answer_matches_core_oracle():
    """AWS 문서 "Signature Calculation: Examples" — 같은 입력에 같은 서명이어야 복제본이다."""
    creds = Credentials(access_key="AKIAIOSFODNN7EXAMPLE",
                        secret_key="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY")
    headers = sign_headers(method="GET", host="examplebucket.s3.amazonaws.com", key="test.txt",
                           region="us-east-1", creds=creds, query={}, payload=b"",
                           now=datetime(2013, 5, 24, 0, 0, 0, tzinfo=timezone.utc),
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


# ── 3. 바이트 동일 — 등기부가 가리키는 source 와 output 을 그대로 비교한다 ───

def test_mirrored_kernel_is_byte_identical_to_core_original():
    root = _repo_root()
    manifest = tomllib.loads((root / "contracts" / "codegen" / "manifest.toml").read_text("utf-8"))
    by_output = {e["output"]: e for e in manifest["output"]}
    imported = {
        "sigv4.py": sigv4, "aws_credentials.py": aws_credentials, "s3.py": s3,
    }
    for name in MIRRORED:
        out_rel = f"{UNIT_DIR}/src/{UNIT_PACKAGE}/kernel/{name}"
        entry = by_output.get(out_rel)
        assert entry is not None, f"등기부에 없다: {out_rel}"
        assert entry["source"] == f"{CORE_KERNEL}/{name}", entry
        assert (root / entry["source"]).is_file(), f"core 원본이 없다: {entry['source']}"
        # 시험이 import 한 모듈이 곧 등기된 그 파일이다 — 다른 자리의 같은 이름이 아니다
        assert Path(imported[name].__file__).resolve() == (root / out_rel).resolve()
        assert filecmp.cmp(root / entry["source"], root / entry["output"], shallow=False), (
            f"드리프트: {out_rel} ≠ {entry['source']} — core 원본을 고쳤으면 같은 커밋에 재생성한다"
        )
