#!/usr/bin/env python3
"""게이트의 **병렬 안전성 선언**을 읽어 `<이름>\t<모드>` 로 뱉는다.

정본 = `gates/config/parallelism.toml`. 실행기(`gates/run.sh all`)가 이것을 읽고 지킨다.

왜 실행기 안의 이름 목록이 아닌가: `gates/README.md` 는 이미 「`db-selftest` 는 병렬로
돌리지 않는다」고 선언해 두었는데 **실행기가 그 선언을 읽지 않았다.** 선언과 집행이 갈리면
선언은 산문일 뿐이다. 다른 정본들(`db-boundaries.toml`·`rls-allowlist.toml`)과 같은 배치로
표를 게이트 곁에 두고, 실행기는 표를 읽기만 한다.

출력 (한 줄 하나 · 탭 구분)
    <게이트 이름>\t<serial|parallel>      선언된 것
    !PARSE\t<사유>                        표를 읽지 못했다 → 호출자가 **전부 단독**으로 돈다
    !BAD\t<이름>\t<값>                    serial·parallel 이 아닌 값 → 호출자가 **단독**으로 돈다

⚠ **여기서 기본값을 만들지 않는다.** 「선언이 없다」를 「병렬 안전」으로 바꾸는 자리가 있으면
그것이 곧 green-by-skip 의 병렬판이다 (`CLAUDE.md §4`). 미선언은 **미선언 그대로** 넘긴다.
"""
from __future__ import annotations

import pathlib
import sys
import tomllib

VALID = ("serial", "parallel")


def main() -> int:
    if len(sys.argv) != 2:
        print("!PARSE\t인자가 하나여야 한다 (선언표 경로)")
        return 0
    path = pathlib.Path(sys.argv[1])
    try:
        table = tomllib.loads(path.read_text(encoding="utf-8"))
    except Exception as e:                                    # noqa: BLE001
        print(f"!PARSE\t{type(e).__name__}: {e}")
        return 0
    gates = table.get("gates")
    if not isinstance(gates, dict):
        print("!PARSE\t[gates] 표가 없다")
        return 0
    for name, mode in gates.items():
        if isinstance(mode, str) and mode in VALID:
            print(f"{name}\t{mode}")
        else:
            print(f"!BAD\t{name}\t{mode}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
