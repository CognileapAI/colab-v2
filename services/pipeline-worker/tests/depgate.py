"""선언된 의존이 없을 때 **조용히 건너뛰지 않는다** (`CLAUDE.md §4` green-by-skip).

세 상태 —
  ① 선언돼 있고 import 된다        → 모듈을 돌려준다 (**검사한다**)
  ② 선언돼 있고 없는데 **명시 면제** → 건너뛰되 **건수를 세어 요약줄에 적는다**
  ③ 그 밖 전부(면제 없음 · 선언 없음) → **실패한다**

`pytest.importorskip` 을 쓰지 않는 이유 — 그것은 ②③ 을 가르지 않고 전부 skip 으로 만든다.
면제는 **이름으로만** 준다. 와일드카드·빈 값은 면제가 아니다(관대한 기본값 금지).
"""
from __future__ import annotations

import importlib
import os
import re
from functools import lru_cache
from pathlib import Path

import pytest

#: 면제를 선언하는 자리. 쉼표로 이름을 나열한다. 없거나 비면 면제 0 건이다.
EXEMPT_ENV = "COLAB_TEST_ALLOW_MISSING_DEPS"

#: 이름 → 면제로 건너뛴 건수. 요약줄이 이 값을 읽는다.
_EXEMPTED: dict[str, int] = {}

_REQ_FILES = ("requirements.in", "requirements-dev.in")
_NAME = re.compile(r"^\s*([A-Za-z0-9._-]+)")


def _import(name: str):
    """import 한 자리 — 시험이 여기를 막아 「없는 의존」을 재현한다."""
    return importlib.import_module(name)


@lru_cache(maxsize=1)
def declared_names() -> frozenset[str]:
    """이 단위가 **선언한** 의존 이름. 파일에서 읽는다 — 목록을 코드에 다시 적지 않는다."""
    root = Path(__file__).resolve().parent.parent
    names: set[str] = set()
    for fn in _REQ_FILES:
        p = root / fn
        if not p.is_file():
            continue
        for line in p.read_text("utf-8").splitlines():
            line = line.split("#", 1)[0].strip()
            if not line or line.startswith("-"):
                continue
            m = _NAME.match(line)
            if m:
                names.add(m.group(1).lower())
    return frozenset(names)


def _exempted(name: str) -> bool:
    raw = os.environ.get(EXEMPT_ENV) or ""
    wanted = {t.strip().lower() for t in raw.split(",") if t.strip()}
    return name.lower() in wanted  # `*` 는 이름이 아니므로 여기서 걸리지 않는다


def exempted_counts() -> dict[str, int]:
    return dict(_EXEMPTED)


def summary_line() -> str | None:
    """면제로 건너뛴 건수를 **드러내는** 한 줄. 0 건이면 줄이 없다."""
    if not _EXEMPTED:
        return None
    total = sum(_EXEMPTED.values())
    detail = " · ".join(f"{k}×{v}" for k, v in sorted(_EXEMPTED.items()))
    return f"면제로 건너뛴 의존 검사 {total}건 — {detail} (`{EXEMPT_ENV}`)"


def require_dep(name: str):
    """세 상태를 가르는 유일한 문."""
    if name.lower() not in declared_names():
        pytest.fail(
            f"`{name}` 은 이 단위가 **선언**한 의존이 아니다({' · '.join(_REQ_FILES)}) — "
            f"설치돼 있더라도 통과시키지 않는다"
        )
    try:
        return _import(name)
    except ImportError as exc:
        if _exempted(name):
            _EXEMPTED[name] = _EXEMPTED.get(name, 0) + 1
            pytest.skip(f"`{name}` 면제 — {EXEMPT_ENV} 에 이름이 있다 ({exc})")
        pytest.fail(
            f"선언된 의존 `{name}` 을 import 할 수 없다 ({exc}). "
            f"**skip 하지 않는다** — 면제하려면 {EXEMPT_ENV} 에 이름을 적어라"
        )
