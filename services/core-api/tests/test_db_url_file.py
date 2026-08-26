"""접속 URL 을 **파일 참조**로 받는 갈래 (`PLAN-SoT §9 〈121〉-㉯`).

`docker inspect` 의 환경변수 목록에 접속 문자열이 통째로 들어 있어 그 값이 작업 기록에
남았다. 그래서 값 대신 **경로만** 넘긴다 — `〈93〉`(주체 표) · `〈108〉-㉯`(자격 파일) 과
같은 방식이다.

규칙 다섯. ① `_FILE` 이 있으면 그 파일을 읽는다(끝의 공백·개행만 벗긴다)
② 없거나 못 읽거나 비었으면 **죽는다**(조용한 폴백 금지) ③ 둘 다 있으면 **죽는다**
④ 둘 다 없으면 지금과 같다 ⑤ **값을 메시지에 싣지 않는다**.
"""
from __future__ import annotations

import pytest

from colab_core.kernel import config as cfg

URL = "postgresql+psycopg://u:p@h:5432/d"
FILE_ENV = cfg.ENV_DATABASE_URL + "_FILE"


def _clean(monkeypatch) -> None:
    monkeypatch.delenv(cfg.ENV_DATABASE_URL, raising=False)
    monkeypatch.delenv(FILE_ENV, raising=False)


def test_파일에서_읽는다_끝만_벗긴다(monkeypatch, tmp_path):
    p = tmp_path / "core.url"
    p.write_text(URL + "  \n\n", encoding="utf-8")
    _clean(monkeypatch)
    monkeypatch.setenv(FILE_ENV, str(p))
    assert cfg.load_settings().database_url == URL


def test_파일이_없으면_죽는다_경로만_적는다(monkeypatch, tmp_path):
    missing = tmp_path / "nope.url"
    _clean(monkeypatch)
    monkeypatch.setenv(FILE_ENV, str(missing))
    with pytest.raises(RuntimeError) as e:
        cfg.load_settings()
    assert str(missing) in str(e.value)


def test_파일이_비었으면_죽는다(monkeypatch, tmp_path):
    p = tmp_path / "empty.url"
    p.write_text("\n  \n", encoding="utf-8")
    _clean(monkeypatch)
    monkeypatch.setenv(FILE_ENV, str(p))
    with pytest.raises(RuntimeError):
        cfg.load_settings()


def test_둘_다_있으면_죽는다(monkeypatch, tmp_path):
    p = tmp_path / "core.url"
    p.write_text(URL, encoding="utf-8")
    _clean(monkeypatch)
    monkeypatch.setenv(cfg.ENV_DATABASE_URL, URL)
    monkeypatch.setenv(FILE_ENV, str(p))
    with pytest.raises(RuntimeError) as e:
        cfg.load_settings()
    assert URL not in str(e.value)          # ⑤ 값을 메시지에 싣지 않는다
    assert FILE_ENV in str(e.value)


def test_둘_다_없으면_지금과_같다(monkeypatch):
    _clean(monkeypatch)
    with pytest.raises(RuntimeError):
        cfg.load_settings()


def test_환경변수만_있으면_지금과_같다(monkeypatch):
    _clean(monkeypatch)
    monkeypatch.setenv(cfg.ENV_DATABASE_URL, URL)
    assert cfg.load_settings().database_url == URL


def test_읽기_실패에도_값이_새지_않는다(monkeypatch, tmp_path):
    """디렉터리를 가리키게 해 OSError 를 낸다. 메시지에는 경로와 사유만 남는다."""
    d = tmp_path / "dir.url"
    d.mkdir()
    _clean(monkeypatch)
    monkeypatch.setenv(FILE_ENV, str(d))
    with pytest.raises(RuntimeError) as e:
        cfg.load_settings()
    assert URL not in str(e.value)
    assert str(d) in str(e.value)


def test_접미사는_정확히_FILE_이다(monkeypatch, tmp_path):
    """`_FILE` 이 아닌 이름은 아무 일도 하지 않는다 — 읽는 쪽과 배선하는 쪽의 이름이 어긋나면 안 된다."""
    p = tmp_path / "core.url"
    p.write_text(URL, encoding="utf-8")
    _clean(monkeypatch)
    monkeypatch.setenv(cfg.ENV_DATABASE_URL + "_PATH", str(p))
    with pytest.raises(RuntimeError):
        cfg.load_settings()
