#!/usr/bin/env python3
"""IS4 import 직후 plan이 원격 값 변경 0인지 비밀을 출력하지 않고 판정한다."""
from __future__ import annotations

import json
import hashlib
import os
import stat
import sys
from pathlib import Path

TARGET = "cloudflare_zero_trust_tunnel_cloudflared_config.staging"
DECLARATIONS = ("versions.tf", "variables.tf", "tunnel.tf", "terraform.tfvars.example", ".terraform.lock.hcl")


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def private_file(path: Path) -> bool:
    try:
        info = path.lstat()
    except OSError:
        return False
    return stat.S_ISREG(info.st_mode) and not stat.S_ISLNK(info.st_mode) \
        and info.st_uid == os.getuid() and stat.S_IMODE(info.st_mode) == 0o600


def has_unknown(value: object) -> bool:
    if value is True:
        return True
    if isinstance(value, dict):
        return any(has_unknown(item) for item in value.values())
    if isinstance(value, list):
        return any(has_unknown(item) for item in value)
    return False


def verify_bundle(bundle: Path, expected_plan: str, source: Path,
                  expected_image: str, expected_version: str) -> int:
    try:
        info = bundle.lstat()
        if not stat.S_ISDIR(info.st_mode) or stat.S_ISLNK(info.st_mode) \
                or info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) != 0o700:
            raise ValueError("bundle 디렉터리가 owner 전용 0700이 아니다")
        if (bundle / "apply-attempted").exists():
            raise ValueError("이 plan은 이미 적용 시도되어 재사용할 수 없다")
        protected = ("manifest.json", "final.tfplan", "final-plan.json", "terraform.tfstate", *DECLARATIONS)
        if not all(private_file(bundle / name) for name in protected):
            raise ValueError("bundle 파일이 owner 전용 일반 파일 0600이 아니다")
        manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
        if (manifest.get("schema") != "colab-is4-recovery/1" or manifest.get("address") != TARGET
                or manifest.get("terraform_image") != expected_image
                or manifest.get("terraform_version") != expected_version):
            raise ValueError("manifest 계약 또는 resource address가 다르다")
        plan_hash = digest(bundle / "final.tfplan")
        if expected_plan != plan_hash or manifest.get("plan_sha256") != plan_hash:
            raise ValueError("승인 plan hash가 보존본과 다르다")
        if manifest.get("state_sha256") != digest(bundle / "terraform.tfstate"):
            raise ValueError("보존 state hash가 다르다")
        declared = manifest.get("declarations")
        if not isinstance(declared, dict) or set(declared) != set(DECLARATIONS):
            raise ValueError("선언 파일 목록이 다르다")
        for name in DECLARATIONS:
            if declared[name] != digest(bundle / name) or declared[name] != digest(source / name):
                raise ValueError("선언 파일 hash가 준비 시점과 다르다")
    except (OSError, ValueError, json.JSONDecodeError, KeyError):
        print("recovery-bundle red — 보존 bundle 검증 실패")
        return 1
    print(f"recovery-bundle green — address 1건 · plan sha256 {expected_plan}")
    return 0


def main(argv: list[str]) -> int:
    if len(argv) == 7 and argv[1] == "--verify-bundle":
        return verify_bundle(Path(argv[2]), argv[3], Path(argv[4]), argv[5], argv[6])
    if len(argv) != 2:
        print("recovery-plan red — plan JSON 경로 하나가 필요하다")
        return 1
    try:
        plan = json.loads(Path(argv[1]).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        print("recovery-plan red — plan JSON을 읽을 수 없다")
        return 1
    changes = plan.get("resource_changes")
    if plan.get("output_changes"):
        print("recovery-plan red — output 변경이 있다")
        return 1
    if not isinstance(changes, list) or len(changes) != 1:
        print("recovery-plan red — 판정할 resource는 정확히 1건이어야 한다")
        return 1
    item = changes[0]
    if (not isinstance(item, dict) or item.get("address") != TARGET
            or item.get("mode") != "managed"
            or item.get("type") != "cloudflare_zero_trust_tunnel_cloudflared_config"
            or item.get("deposed") not in (None, "")):
        print("recovery-plan red — 허용된 Cloudflare tunnel resource가 아니다")
        return 1
    change = item.get("change", {})
    actions = change.get("actions") if isinstance(change, dict) else None
    before, after = change.get("before"), change.get("after")
    if not isinstance(before, dict) or not isinstance(after, dict) \
            or has_unknown(change.get("after_unknown")) or change.get("replace_paths") not in (None, []):
        print("recovery-plan red — 값 누락, unknown 또는 replace path가 있다")
        return 1
    if actions == ["no-op"]:
        print("recovery-plan green — resource 1건 · no-op 1 · metadata-only 0")
        return 0
    # Full protected JSON에서만 비교한다. 값을 제거한 summary는 이 판정에 쓰지 않는다.
    if (actions == ["update"] and before == after
            and change.get("before_sensitive") != change.get("after_sensitive")):
        print("recovery-plan green — resource 1건 · no-op 0 · metadata-only 1")
        return 0
    print("recovery-plan red — add/delete/replace 또는 실제 원격 값 변경이 있다")
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
