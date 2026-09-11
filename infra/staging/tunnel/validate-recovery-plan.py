#!/usr/bin/env python3
"""IS4 import 직후 plan이 원격 값 변경 0인지 비밀을 출력하지 않고 판정한다."""
from __future__ import annotations

import json
import sys
from pathlib import Path


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("recovery-plan red — plan JSON 경로 하나가 필요하다")
        return 1
    try:
        plan = json.loads(Path(argv[1]).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        print("recovery-plan red — plan JSON을 읽을 수 없다")
        return 1
    changes = plan.get("resource_changes")
    if not isinstance(changes, list) or not changes:
        print("recovery-plan red — 판정할 resource가 0건이다")
        return 1
    no_op = metadata = 0
    for item in changes:
        change = item.get("change", {}) if isinstance(item, dict) else {}
        actions = change.get("actions")
        if actions == ["no-op"]:
            no_op += 1
            continue
        # import 직후 provider sensitivity 메타만 정착하는 경우 값 before/after는 같다.
        if (actions == ["update"] and change.get("before") == change.get("after")
                and change.get("before_sensitive") != change.get("after_sensitive")):
            metadata += 1
            continue
        print("recovery-plan red — add/delete/replace 또는 실제 원격 값 변경이 있다")
        return 1
    print(f"recovery-plan green — resource {len(changes)}건 · no-op {no_op} · metadata-only {metadata}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
