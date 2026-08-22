"""정규 ID 는 코드에서 한 곳에서만 정의된다 (CLAUDE.md §3-6)."""
from __future__ import annotations

import json
import pathlib

import pytest
from conftest import REPO

from colab_core.kernel.ids import Ulid


def test_pattern_matches_the_contract() -> None:
    """값 정본은 contracts/schemas/common.json 이다 — 코드가 그것과 다르면 드리프트다."""
    common = json.loads((REPO / "contracts/schemas/common.json").read_text(encoding="utf-8"))
    spec = common["$defs"]["Ulid"]
    from colab_core.kernel.ids import PATTERN
    assert PATTERN.pattern == spec["pattern"]
    assert spec["minLength"] == spec["maxLength"] == 26


def test_generate_is_valid_and_sortable() -> None:
    a = Ulid.generate(now_ms=1_700_000_000_000)
    b = Ulid.generate(now_ms=1_700_000_001_000)
    assert Ulid.is_valid(a) and len(a) == 26
    assert a < b, "시각 앞자리 정렬이 깨지면 커서 페이지가 어긋난다."


@pytest.mark.parametrize("bad", ["", "abc", "01ARZ3NDEKTSV4RRFFQ69G5FA", "01ARZ3NDEKTSV4RRFFQ69G5FAI"])
def test_rejects_non_canonical(bad: str) -> None:
    assert not Ulid.is_valid(bad)
    with pytest.raises(ValueError):
        Ulid(bad)


def test_db_domain_uses_the_same_pattern() -> None:
    sql = (REPO / "db/platform/schema.sql").read_text(encoding="utf-8")
    assert "^[0-9A-HJKMNP-TV-Z]{26}$" in sql
