"""오라클 — 앱의 라우트 표 ↔ 계약(fe-core.yaml)을 diff 한다.

이 테스트가 오라클이다. 사람이 세지 않는다. 계약이 34 개면 앱도 34 개여야 하고,
경로·메서드가 한 글자라도 다르면 여기서 red 가 난다.
"""
from __future__ import annotations

import yaml
from conftest import CONTRACT

from colab_core.app.main import API_PREFIX, create_app
from colab_core.kernel.config import Settings

METHODS = {"get", "post", "put", "patch", "delete"}
SETTINGS = Settings(database_url="postgresql+psycopg://unused/unused", subjects_file=None)


def contract_operations() -> dict[str, tuple[str, str]]:
    doc = yaml.safe_load(CONTRACT.read_text(encoding="utf-8"))
    out: dict[str, tuple[str, str]] = {}
    for path, item in doc["paths"].items():
        for method, op in item.items():
            if method in METHODS:
                out[op["operationId"]] = (method.upper(), path)
    return out


def app_operations() -> dict[str, tuple[str, str]]:
    app = create_app(SETTINGS)
    out: dict[str, tuple[str, str]] = {}
    for route in app.routes:
        methods = getattr(route, "methods", None) or set()
        methods = {m for m in methods if m != "HEAD"}
        if not methods or not route.path.startswith(API_PREFIX):
            continue
        assert len(methods) == 1, f"라우트 하나에 메서드가 여럿이다: {route.path}"
        out[route.name] = (next(iter(methods)), route.path[len(API_PREFIX):])
    return out


def test_operation_count_is_34() -> None:
    assert len(contract_operations()) == 34, "계약의 오퍼레이션이 34 개가 아니다 — 발췌가 잘렸다."


def test_app_route_table_equals_contract() -> None:
    contract, app = contract_operations(), app_operations()
    assert set(app) - set(contract) == set(), "계약에 없는 라우트를 앱이 열었다."
    assert set(contract) - set(app) == set(), "계약에 있는 오퍼레이션을 앱이 등록하지 않았다."
    mismatched = {oid: (contract[oid], app[oid]) for oid in contract if contract[oid] != app[oid]}
    assert mismatched == {}, f"경로·메서드가 계약과 다르다: {mismatched}"


def test_no_duplicate_paths() -> None:
    app = create_app(SETTINGS)
    seen = set()
    for route in app.routes:
        for m in (getattr(route, "methods", None) or set()) - {"HEAD"}:
            key = (m, route.path)
            assert key not in seen, f"라우트가 중복 등록됐다: {key}"
            seen.add(key)
