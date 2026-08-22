#!/usr/bin/env python3
"""migration-single-head 게이트 (WU-D3) — alembic head 분기 검출.

강제하는 것
  CLAUDE.md §3-3  D9·D10 저장소는 D1~D8 과 마이그레이션 체인이 분리된다 (db/ai vs db/platform)
  db/README.md    single-head 강제 — **두 체인 각각**

판정 방식: 마이그레이션 파일의 `revision` / `down_revision` 모듈 수준 대입을 `ast` 로 읽어
그래프를 직접 만든다. alembic 을 설치해 `ScriptDirectory.get_heads()` 를 부르지 않는다. 이유 셋.
  1. **DB 접속 없이 판정 가능해야 한다.** v1 CI 가 DB 없이 돌아 green-by-skip 한 실패를 반복하지 않으려면
     이 게이트만은 인프라가 없어도 항상 실제 판정을 내야 한다. head 분기는 파일만으로 결정되는 사실이다.
  2. alembic 의 head 계산은 마이그레이션 모듈을 **import 해서 실행한다.** 게이트가 검사 대상 코드를
     실행하면, 검사 대상이 게이트를 좌우할 수 있다(env.py 의 side effect·DB 접속 시도).
  3. `ast` 는 표준 라이브러리다 — `banned-import.py` 와 같은 판단이다. 도구를 하나 덜 핀할수록
     게이트가 조용히 바뀔 경로가 하나 줄어든다.
  대가: alembic 만 아는 것(`branch_labels` 로 의도적으로 연 분기, `depends_on` 크로스 체인)은
  이 게이트가 alembic 과 다르게 볼 수 있다. §8 한계에 적었다.

`version_table` 중복 검사는 **하지 않는다.** 이미 `ai-no-lineage-write` ⑪ 이 그 조건을 본다.
역할 분담: 이 게이트 = 한 체인 안의 그래프 형태(head 개수·고아·순환), ai-no-lineage-write = 두 체인의 격리.

원칙 (CLAUDE.md §4): 대상 0건은 red. "분기가 없다"와 "마이그레이션이 없다"는 다른 사실이다.

환경변수 (selftest 전용 — 평시엔 건드리지 않는다)
  COLAB_DB_DIR   db 루트 (기본: db/)
"""
from __future__ import annotations

import ast
import os
import pathlib
import sys

CHAINS = ("platform", "ai")
REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
DB_DIR = pathlib.Path(os.environ.get("COLAB_DB_DIR") or (REPO_ROOT / "db"))

errors: list[str] = []


def rel(p: pathlib.Path) -> str:
    try:
        return str(p.relative_to(REPO_ROOT))
    except ValueError:
        return str(p)


def literal(node: ast.AST):
    try:
        return ast.literal_eval(node)
    except Exception:
        return _UNKNOWN


class _Unknown:
    def __repr__(self) -> str:  # pragma: no cover
        return "<동적>"


_UNKNOWN = _Unknown()


def read_revision(path: pathlib.Path) -> dict | None:
    """모듈 수준 대입에서 revision/down_revision 을 뽑는다. 실행하지 않는다."""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"), filename=str(path))
    except SyntaxError as e:
        errors.append(f"{rel(path)} — 파싱 불가({e}). 읽지 못한 파일을 통과로 세지 않는다.")
        return None
    found: dict = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id in ("revision", "down_revision"):
                found[target.id] = literal(node.value)
    return found


def normalize_down(value) -> list[str] | None:
    """down_revision 은 str | None | tuple/list(머지 리비전)."""
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, (tuple, list)) and all(isinstance(v, str) for v in value):
        return list(value)
    return None  # 판정 불가


def check_chain(chain: str) -> None:
    root = DB_DIR / chain
    tag = f"db/{chain}"
    if not root.is_dir():
        errors.append(f"{tag} — 체인 디렉터리가 없다. 체인은 두 개다 (db/README.md).")
        return

    ini = root / "alembic.ini"
    if not ini.is_file():
        errors.append(f"{tag}/alembic.ini 가 없다. 체인이 alembic 체인임을 선언하는 자리다.")

    versions = root / "versions"
    files = sorted(versions.glob("*.py")) if versions.is_dir() else []
    files = [f for f in files if f.name != "__init__.py"]
    if not files:
        errors.append(
            f"{tag}/versions/*.py 가 0건이다. 대상 0건은 통과가 아니다 — "
            f"'head 가 하나다'와 '마이그레이션이 없다'는 다른 사실이다 (CLAUDE.md §4)."
        )
        return

    revs: dict[str, pathlib.Path] = {}
    downs: dict[str, list[str]] = {}
    for f in files:
        meta = read_revision(f)
        if meta is None:
            continue
        if "revision" not in meta:
            errors.append(f"{rel(f)} — `revision` 대입이 없다. alembic 마이그레이션이 아니거나 동적이다.")
            continue
        rev = meta["revision"]
        if not isinstance(rev, str):
            errors.append(f"{rel(f)} — `revision` 이 리터럴 문자열이 아니다. 정적으로 판정할 수 없다.")
            continue
        if rev in revs:
            errors.append(f"{tag} — revision '{rev}' 중복: {rel(revs[rev])} · {rel(f)}")
            continue
        revs[rev] = f
        if "down_revision" not in meta:
            errors.append(f"{rel(f)} — `down_revision` 대입이 없다. 초기 리비전이면 `None` 을 명시한다.")
            continue
        down = normalize_down(meta["down_revision"])
        if down is None:
            errors.append(f"{rel(f)} — `down_revision` 을 정적으로 읽을 수 없다.")
            continue
        downs[rev] = down

    if not revs:
        errors.append(f"{tag} — 읽어낸 리비전이 0건이다.")
        return

    # 고아 참조 — 다른 체인의 리비전을 가리키는 경우도 여기서 잡힌다 (체인은 서로를 모른다).
    for rev, parents in downs.items():
        for p in parents:
            if p not in revs:
                errors.append(
                    f"{tag} — 리비전 '{rev}'({rel(revs[rev])})의 down_revision '{p}' 가 이 체인에 없다. "
                    f"체인을 넘는 참조라면 §3-3 위반이다."
                )

    # 순환
    state: dict[str, int] = {}

    def visit(node: str, stack: list[str]) -> None:
        if state.get(node) == 2:
            return
        if state.get(node) == 1:
            cycle = " → ".join(stack[stack.index(node):] + [node])
            errors.append(f"{tag} — 리비전 순환: {cycle}")
            return
        state[node] = 1
        for p in downs.get(node, []):
            if p in revs:
                visit(p, stack + [node])
        state[node] = 2

    for rev in revs:
        visit(rev, [])

    # head = 아무도 자기를 down_revision 으로 가리키지 않는 리비전
    referenced = {p for parents in downs.values() for p in parents}
    heads = sorted(r for r in revs if r not in referenced)
    if len(heads) == 0:
        errors.append(f"{tag} — head 가 0개다(전부 순환). 적용 순서를 정할 수 없다.")
    elif len(heads) > 1:
        detail = "\n".join(f"     - {h}  ({rel(revs[h])})" for h in heads)
        errors.append(
            f"{tag} — head 가 {len(heads)}개다. single-head 를 강제한다 (db/README.md).\n{detail}\n"
            f"     → 머지 리비전을 하나 만들어 합친다: alembic -c {tag}/alembic.ini merge heads"
        )
    else:
        print(f"# {tag}: 리비전 {len(revs)}건 · head 1개 ({heads[0]})")


def main() -> int:
    print(f"# db 루트 = {rel(DB_DIR)} · 체인 = {', '.join(CHAINS)}")
    for chain in CHAINS:
        check_chain(chain)
    if errors:
        print("::error::migration-single-head red —")
        for e in errors:
            print(f"   - {e}")
        print(
            "   두 체인(db/platform · db/ai)은 각각 head 가 하나여야 한다 (CLAUDE.md §3-3).\n"
            "   두 체인이 같은 version_table 을 쓰는지는 ai-no-lineage-write ⑪ 이 본다 — 여기서 중복 구현하지 않는다."
        )
        return 1
    print("migration-single-head green — 두 체인 모두 head 1개.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
