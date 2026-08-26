#!/usr/bin/env python3
"""자격 파일에 비밀번호를 **해시로** 심거나 바꾼다 (`PLAN-SoT §9 〈108〉-㉯·㉱`).

이 스크립트가 **회전 수단**이다. 비밀번호를 바꾸는 자리가 없으면 회전이 불가능하고,
회전이 불가능하면 부트스트랩 자격을 영영 못 걷는다.

사용
    python3 ops/set-password.py --file <자격파일> --name colab \
        --account-id <ULID> --lab-id <ULID>
    # 비밀번호는 **표준입력**으로 받는다. tty 면 가려서 묻는다.

지키는 것
  · **비밀번호를 인자로 받지 않는다** — argv 는 `ps` 와 셸 히스토리에 남는다.
  · **평문을 어디에도 쓰지 않는다** — 파일에 들어가는 것은 `scrypt` 해시·소금·파라미터뿐.
  · **화면·로그에 값을 되비치지 않는다.**
  · 파일 권한 **0600**, 소유자는 실행한 사용자 (`〈93〉` 비밀 취급).
  · 기존 파일이 있으면 **읽어서 갱신**한다 — 다른 계정을 지우지 않는다.
  · 쓰기는 **같은 디렉터리의 임시 파일 → rename**. 도중에 죽어도 반쪽 파일이 남지 않는다.
"""
from __future__ import annotations

import argparse
import getpass
import json
import os
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from colab_core.kernel.ids import Ulid          # noqa: E402
from colab_core.kernel.password import hash_password  # noqa: E402


def read_password() -> str:
    if sys.stdin.isatty():
        first = getpass.getpass("새 비밀번호: ")
        again = getpass.getpass("한 번 더: ")
        if first != again:
            sys.exit("두 입력이 다르다. 아무것도 바꾸지 않았다.")
        return first
    return sys.stdin.readline().rstrip("\n")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--file", required=True, help="자격 파일 경로")
    ap.add_argument("--name", required=True, help="계정 이름 (로그인 입력의 accountName)")
    ap.add_argument("--account-id", help="ULID. 새 계정을 심을 때만 필요")
    ap.add_argument("--lab-id", help="ULID. 새 계정을 심을 때만 필요")
    args = ap.parse_args()

    path = pathlib.Path(args.file)
    table: dict = {}
    if path.exists():
        table = json.loads(path.read_text(encoding="utf-8"))

    existing = table.get(args.name)
    account_id = args.account_id or (existing or {}).get("accountId")
    lab_id = args.lab_id or (existing or {}).get("labId")
    if not account_id or not lab_id:
        sys.exit("새 계정에는 --account-id 와 --lab-id 가 필요하다.")
    for label, value in (("account-id", account_id), ("lab-id", lab_id)):
        if not Ulid.is_valid(value):
            sys.exit(f"{label} 가 정규 ID 가 아니다.")

    password = read_password()
    if not password:
        sys.exit("빈 비밀번호는 심지 않는다.")

    entry = {"accountId": account_id, "labId": lab_id}
    entry.update(hash_password(password).as_dict())
    table[args.name] = entry
    del password   # 메모리에 오래 들고 있지 않는다.

    tmp = path.with_name(path.name + ".tmp")
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        json.dump(table, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    os.replace(tmp, path)
    os.chmod(path, 0o600)

    # **값을 되비치지 않는다.** 무엇을 바꿨는지만 말한다.
    print(f"{path} — `{args.name}` 자격 갱신. 권한 0600. 이전 비밀번호는 즉시 무효다.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
