"""D9 사전 DB URL 을 **파일 참조**로 받는 갈래 (`PLAN-SoT §9 〈121〉-㉯`).

core-api `tests/test_db_url_file.py` 와 같은 다섯 규칙이다. 다른 것은 ④ 뿐 —
이 단위는 값이 없어도 **뜬다**(`CLAUDE.md §3`: AI 없이도 v2 는 완결된 제품이다).
그러나 **경로를 줬는데 못 읽는 것**은 다른 얘기다: 그것은 「없다」가 아니라 「배선이
틀렸다」이므로 조용히 넘기지 않는다.
"""
from __future__ import annotations

import pytest

from colab_ai.kernel.config import Settings

URL = "postgresql+psycopg://u:p@h:5432/colab_ai"
VAR = "COLAB_AI_DB_URL"
FILE_ENV = VAR + "_FILE"


def test_파일에서_읽는다_끝만_벗긴다(tmp_path):
    p = tmp_path / "ai.url"
    p.write_text(URL + " \n", encoding="utf-8")
    assert Settings.from_env({FILE_ENV: str(p)}).dict_db_url == URL


def test_파일이_없으면_죽는다_경로만_적는다(tmp_path):
    missing = tmp_path / "nope.url"
    with pytest.raises(RuntimeError) as e:
        Settings.from_env({FILE_ENV: str(missing)})
    assert str(missing) in str(e.value)


def test_파일이_비었으면_죽는다(tmp_path):
    p = tmp_path / "empty.url"
    p.write_text("\n", encoding="utf-8")
    with pytest.raises(RuntimeError):
        Settings.from_env({FILE_ENV: str(p)})


def test_둘_다_있으면_죽는다(tmp_path):
    p = tmp_path / "ai.url"
    p.write_text(URL, encoding="utf-8")
    with pytest.raises(RuntimeError) as e:
        Settings.from_env({VAR: URL, FILE_ENV: str(p)})
    assert URL not in str(e.value)
    assert FILE_ENV in str(e.value)


def test_둘_다_없으면_지금과_같다():
    assert Settings.from_env({}).dict_db_url is None


def test_환경변수만_있으면_지금과_같다():
    assert Settings.from_env({VAR: URL}).dict_db_url == URL


def test_읽기_실패에도_값이_새지_않는다(tmp_path):
    d = tmp_path / "dir.url"
    d.mkdir()
    with pytest.raises(RuntimeError) as e:
        Settings.from_env({FILE_ENV: str(d)})
    assert URL not in str(e.value)
    assert str(d) in str(e.value)
