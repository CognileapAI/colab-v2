#!/usr/bin/env python3
"""banned-import 게이트 (WU-D3) — 배포 단위별 import allow/deny.

강제하는 것: CLAUDE.md §3-4 "core-api 에 geo 라이브러리를 import 하지 않는다".
viz-render · pipeline-worker 는 허용된다 — 그래서 전역 금지가 아니라 **배포 단위별** deny 다.

금지 목록은 gates/config/boundaries.toml 에서만 정의된다. 이 파일은 목록을 갖지 않는다.

원칙 (CLAUDE.md §4):
  - 표준 라이브러리만 쓴다(ast). 도구 설치가 필요 없으니 "도구 부재로 skip"이 성립하지 않는다.
  - 파싱 실패는 red. 읽지 못한 파일을 통과로 세지 않는다.
  - 검사 대상 .py 가 0건이면 red. 코드가 없는 지금 이 게이트는 red 이고, 그게 정상이다.

환경변수 (selftest 전용)
  COLAB_SERVICES_DIR      배포 단위 루트 (기본: services/)
  COLAB_BOUNDARY_CONFIG   boundaries.toml 경로
"""
import ast
import os
import pathlib
import sys
import tomllib

REPO = pathlib.Path(__file__).resolve().parents[2]
SERVICES = pathlib.Path(os.environ.get("COLAB_SERVICES_DIR", REPO / "services"))
CONFIG = pathlib.Path(os.environ.get("COLAB_BOUNDARY_CONFIG", REPO / "gates/config/boundaries.toml"))

DYNAMIC_CALLS = {"import_module", "__import__"}


def red(msg: str) -> "None":
    print(f"::error::banned-import red — {msg}")
    raise SystemExit(1)


def top(name: str) -> str:
    return (name or "").split(".", 1)[0]


def scan(path: pathlib.Path, banned: set) -> list:
    """한 파일의 위반 목록. (line, 모듈, 형태)"""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (SyntaxError, UnicodeDecodeError) as e:
        red(f"파일을 파싱하지 못했다: {path} ({e}). 읽지 못한 것은 통과가 아니다.")
    hits = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                if top(a.name) in banned:
                    hits.append((node.lineno, a.name, "import"))
        elif isinstance(node, ast.ImportFrom):
            # `from . import x` (level>0) 는 패키지 내부다 — 금지 목록과 무관.
            if node.level == 0 and top(node.module or "") in banned:
                hits.append((node.lineno, node.module, "from-import"))
        elif isinstance(node, ast.Call):
            fn = node.func
            fname = fn.attr if isinstance(fn, ast.Attribute) else getattr(fn, "id", "")
            if fname in DYNAMIC_CALLS and node.args:
                a0 = node.args[0]
                if isinstance(a0, ast.Constant) and isinstance(a0.value, str) and top(a0.value) in banned:
                    hits.append((node.lineno, a0.value, "동적 import"))
    return hits


def main() -> int:
    if not CONFIG.is_file():
        red(f"설정이 없다: {CONFIG}")
    units = tomllib.load(CONFIG.open("rb"))["units"]

    total_files = 0
    violations = []
    lines = []
    for unit, spec in sorted(units.items()):
        src = SERVICES / spec["dir"] / "src"
        files = sorted(src.rglob("*.py")) if src.is_dir() else []
        total_files += len(files)
        banned = set(spec.get("banned", []))
        lines.append(f"  {unit:<16} .py {len(files):>4}건 · deny {len(banned)}개")
        if not banned:
            continue
        for f in files:
            for lineno, mod, kind in scan(f, banned):
                violations.append(f"{f.relative_to(REPO) if REPO in f.parents else f}:{lineno} "
                                  f"[{unit}] {kind} {mod}")

    print("# 배포 단위별 대상")
    print("\n".join(lines))

    if total_files == 0:
        red("검사할 .py 가 0건이다.\n"
            "   금지 import 가 하나도 없다는 판정은 '코드가 없다'와 구분되지 않는다.\n"
            "   P0 가 services/*/src 아래에 코드를 놓기 전까지 이 게이트는 red 다 (CLAUDE.md §4).")

    if violations:
        red("배포 단위에 금지된 import 가 있다:\n"
            + "\n".join(f"     - {v}" for v in violations)
            + "\n   래스터를 열어야 하는 일은 viz-render 또는 pipeline-worker 것이다 (DOMAINS.md §4).")

    print(f"banned-import green — .py {total_files}건, 금지 import 0.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
