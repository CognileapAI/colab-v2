"""ai-service 시험 공통 재료.

**DB 가 없으면 skip 이 아니라 fail 이다** — core-api `tests/conftest.py` 와 같은 규율이다
(`CLAUDE.md §4` · v1 CI 가 DB 없이 RLS 를 green-by-skip 한 실패를 반복하지 않는다).

환경변수 둘
  `COLAB_AI_TEST_PLATFORM_DB_URL`  D3 카탈로그 DB. **앱 롤**(NOBYPASSRLS·비소유자)로 붙는다.
                                   RLS 가 살아 있어야 cross-tenant 음성이 오라클이 된다.
  `COLAB_AI_TEST_DICT_DB_URL`      D9 사전 3종 DB (`db/ai` 체인).
"""
from __future__ import annotations

import os
import pathlib
import sys

import pytest

SRC = pathlib.Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

# core-api `tests/fixtures/seed.sql` 이 심는 값 — **여기서 새로 정하지 않는다.**
LAB_A = "0000000000000000000000000A"
LAB_B = "0000000000000000000000000B"
ACC_A_RES = "000000000000000000000000A1"
ACC_B_PROF = "00000000000000000000000BP1"
DS_A1 = "0000000000000000000000DSA1"   # 'A 강우 원자료' · 열림 · CSV · 변수 강우량
DS_A2 = "0000000000000000000000DSA2"   # 'A 강우 격자화' · **잠김** · NetCDF
DS_B1 = "0000000000000000000000DSB1"   # 다른 연구실 · 'B 토지피복 원자료'


def _require(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        pytest.fail(f"{name} 이 없다. DB 를 못 붙인 것은 통과가 아니다 (CLAUDE.md §4).")
    return value


@pytest.fixture(scope="session")
def platform_db_url() -> str:
    return _require("COLAB_AI_TEST_PLATFORM_DB_URL")


@pytest.fixture(scope="session")
def dict_db_url() -> str:
    return _require("COLAB_AI_TEST_DICT_DB_URL")


@pytest.fixture(scope="session")
def catalog(platform_db_url: str):
    from colab_ai.app.catalog_search import SqlCatalogSearch
    from colab_ai.kernel.db import make_engine
    return SqlCatalogSearch(make_engine(platform_db_url))


@pytest.fixture(scope="session")
def dictionaries(dict_db_url: str):
    from colab_ai.app.dictionaries import SqlDictionaries
    from colab_ai.kernel.db import make_engine
    return SqlDictionaries(make_engine(dict_db_url))
