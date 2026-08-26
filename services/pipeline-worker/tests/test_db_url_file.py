"""원장 접속 URL 을 **파일 참조**로 받는 갈래 (`PLAN-SoT §9 〈121〉-㉯`).

`docker inspect` 의 환경변수 목록에 접속 문자열이 통째로 남는 것을 막는다. 값 대신
**경로만** 넘긴다 — core-api `tests/test_db_url_file.py` 와 같은 다섯 규칙이다.

⚠ 배포 단위는 서로 독립이라 판독기를 공유하지 않는다. 같은 규칙을 이 단위의 `kernel/`
안에 따로 둔다(`CLAUDE.md §3-1`).
"""
from __future__ import annotations

import pytest

from colab_pipeline.app import worker
from colab_pipeline.kernel.env_file import resolve_env_or_file

URL = "postgresql+psycopg://u:p@h:5432/colab_platform"
VAR = worker.ENV_DB
FILE_ENV = VAR + "_FILE"


def test_파일에서_읽는다_끝만_벗긴다(tmp_path):
    p = tmp_path / "pipeline.url"
    p.write_text(URL + "  \n", encoding="utf-8")
    assert resolve_env_or_file({FILE_ENV: str(p)}, VAR) == URL


def test_파일이_없으면_죽는다_경로만_적는다(tmp_path):
    missing = tmp_path / "nope.url"
    with pytest.raises(RuntimeError) as e:
        resolve_env_or_file({FILE_ENV: str(missing)}, VAR)
    assert str(missing) in str(e.value)


def test_파일이_비었으면_죽는다(tmp_path):
    p = tmp_path / "empty.url"
    p.write_text("   \n", encoding="utf-8")
    with pytest.raises(RuntimeError):
        resolve_env_or_file({FILE_ENV: str(p)}, VAR)


def test_둘_다_있으면_죽는다(tmp_path):
    p = tmp_path / "pipeline.url"
    p.write_text(URL, encoding="utf-8")
    with pytest.raises(RuntimeError) as e:
        resolve_env_or_file({VAR: URL, FILE_ENV: str(p)}, VAR)
    assert URL not in str(e.value)
    assert FILE_ENV in str(e.value)


def test_둘_다_없으면_None(tmp_path):
    assert resolve_env_or_file({}, VAR) is None


def test_읽기_실패에도_값이_새지_않는다(tmp_path):
    d = tmp_path / "dir.url"
    d.mkdir()
    with pytest.raises(RuntimeError) as e:
        resolve_env_or_file({FILE_ENV: str(d)}, VAR)
    assert URL not in str(e.value)
    assert str(d) in str(e.value)


def test_워커가_그_이름을_실제로_읽는다(monkeypatch, tmp_path):
    """읽는 쪽과 배선하는 쪽의 이름이 한 글자도 어긋나면 안 된다 — 워커가 `_FILE` 을 실제로 소비한다."""
    p = tmp_path / "pipeline.url"
    p.write_text(URL, encoding="utf-8")
    monkeypatch.delenv(VAR, raising=False)
    monkeypatch.setenv(FILE_ENV, str(p))
    monkeypatch.setenv(worker.ENV_UPLOAD_DIR, str(tmp_path))

    seen: list[str] = []

    def _fake_engine(url: str):
        seen.append(url)
        raise _Stop()

    class _Stop(Exception):
        pass

    monkeypatch.setattr(worker, "make_engine", _fake_engine)
    with pytest.raises(_Stop):
        worker.run_once()
    assert seen == [URL]


def test_워커는_둘_다_있으면_DB_에_붙기_전에_죽는다(monkeypatch, tmp_path):
    p = tmp_path / "pipeline.url"
    p.write_text(URL, encoding="utf-8")
    monkeypatch.setenv(VAR, URL)
    monkeypatch.setenv(FILE_ENV, str(p))
    monkeypatch.setenv(worker.ENV_UPLOAD_DIR, str(tmp_path))

    def _boom(url: str):  # pragma: no cover - 닿으면 안 되는 자리
        raise AssertionError("접속을 시도했다 — 갈린 출처로는 붙지 않아야 한다")

    monkeypatch.setattr(worker, "make_engine", _boom)
    with pytest.raises(RuntimeError) as e:
        worker.run_once()
    assert FILE_ENV in str(e.value)
