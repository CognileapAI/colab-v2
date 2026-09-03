"""세션 서명 비밀값·viz 서비스 토큰도 **파일 참조**로 받는다 (`CODE-REVIEW-20260903` #15).

`_FILE` 간접참조는 DB URL 에만 걸려 있었다. 그래서 `compose.i2.yml` 이 **세션 서명 HMAC
키**와 **서비스 토큰**을 `docker inspect` 로 그대로 읽히는 컨테이너 env 로 넘겼다 —
DB 비밀번호가 작업 기록에 새어 `_FILE` 을 도입했던 **바로 그 경로**다.

더 나쁜 것은 조용한 실패였다: `COLAB_CORE_SESSION_SECRET_FILE` 을 설정하면 **오류 없이
무시**돼 signer 가 서지 않고 `POST /sessions` 가 500 `SESSION_UNAVAILABLE` 만 냈다.
무시된 변수 이름은 어디에도 나오지 않았다 — 배선은 있는데 아무도 안 읽는 상태다.

**뒤로 호환된다** — 생 env 만 있으면 지금과 같다. compose 는 이 회차에 바꾸지 않는다
(배포 변경이라 Ted go/no-go — 레인 기록 §유보).
"""
from __future__ import annotations

import pytest

from colab_core.kernel import config as cfg

URL = "postgresql+psycopg://u:p@h:5432/d"
SECRET = "세션-서명-비밀값-0123456789"
TOKEN = "viz-서비스-토큰-0123456789"


@pytest.fixture(autouse=True)
def _only_the_url(monkeypatch):
    """DB URL 만 세워 두고 나머지는 시험이 직접 정한다."""
    for name in (cfg.ENV_DATABASE_URL, cfg.ENV_SESSION_SECRET, cfg.ENV_VIZ_SERVICE_TOKEN):
        monkeypatch.delenv(name, raising=False)
        monkeypatch.delenv(name + cfg.FILE_SUFFIX, raising=False)
    monkeypatch.setenv(cfg.ENV_DATABASE_URL, URL)


def test_session_secret_is_read_from_the_file(monkeypatch, tmp_path):
    p = tmp_path / "session.secret"
    p.write_text(SECRET + "  \n\n", encoding="utf-8")
    monkeypatch.setenv(cfg.ENV_SESSION_SECRET + cfg.FILE_SUFFIX, str(p))
    assert cfg.load_settings().session_secret == SECRET


def test_viz_service_token_is_read_from_the_file(monkeypatch, tmp_path):
    p = tmp_path / "viz.token"
    p.write_text(TOKEN + "\n", encoding="utf-8")
    monkeypatch.setenv(cfg.ENV_VIZ_SERVICE_TOKEN + cfg.FILE_SUFFIX, str(p))
    assert cfg.load_settings().viz_service_token == TOKEN


def test_a_signed_session_actually_stands_when_the_secret_came_from_a_file(
        monkeypatch, tmp_path):
    """**설정을 읽는 것과 로그인이 서는 것은 다른 질문이다.**

    종전에는 `_FILE` 을 설정해도 `session_secret` 이 `None` 이라 signer 가 안 섰고,
    그 사실은 `POST /sessions` 의 500 으로만 드러났다.
    """
    p = tmp_path / "session.secret"
    p.write_text(SECRET, encoding="utf-8")
    monkeypatch.setenv(cfg.ENV_SESSION_SECRET + cfg.FILE_SUFFIX, str(p))
    settings = cfg.load_settings()
    assert settings.session_secret, "비밀값이 조용히 무시됐다 — 로그인이 500 만 낸다."

    from colab_core.kernel.session_token import SessionSigner
    signer = SessionSigner(settings.session_secret,
                           ttl_minutes=settings.session_ttl_minutes)
    assert signer.issue.__name__ == "issue"


@pytest.mark.parametrize("name", ["ENV_SESSION_SECRET", "ENV_VIZ_SERVICE_TOKEN"])
def test_both_sources_at_once_is_fatal_and_the_value_never_leaks(
        monkeypatch, tmp_path, name):
    """규칙 ③·⑤ 가 DB URL 과 **같다** — 두 출처가 갈리면 어느 것이 진실인지 아무도 모른다."""
    env = getattr(cfg, name)
    p = tmp_path / "secret"
    p.write_text(SECRET, encoding="utf-8")
    monkeypatch.setenv(env, SECRET)
    monkeypatch.setenv(env + cfg.FILE_SUFFIX, str(p))
    with pytest.raises(RuntimeError) as e:
        cfg.load_settings()
    assert SECRET not in str(e.value), "오류 메시지에 비밀값이 실렸다."
    assert env + cfg.FILE_SUFFIX in str(e.value)


@pytest.mark.parametrize("name", ["ENV_SESSION_SECRET", "ENV_VIZ_SERVICE_TOKEN"])
def test_a_missing_or_empty_file_is_fatal_not_a_silent_none(monkeypatch, tmp_path, name):
    """**조용한 폴백이 없다.** 종전에는 `_FILE` 이 오류 없이 무시됐다."""
    env = getattr(cfg, name)
    monkeypatch.setenv(env + cfg.FILE_SUFFIX, str(tmp_path / "없는파일"))
    with pytest.raises(RuntimeError):
        cfg.load_settings()

    empty = tmp_path / "empty"
    empty.write_text("\n  \n", encoding="utf-8")
    monkeypatch.setenv(env + cfg.FILE_SUFFIX, str(empty))
    with pytest.raises(RuntimeError):
        cfg.load_settings()


@pytest.mark.parametrize("name,attr", [("ENV_SESSION_SECRET", "session_secret"),
                                       ("ENV_VIZ_SERVICE_TOKEN", "viz_service_token")])
def test_the_plain_env_still_works_and_absence_is_still_none(monkeypatch, name, attr):
    """**뒤로 호환된다** — compose 를 안 바꿔도 지금과 같다(규칙 ④)."""
    env = getattr(cfg, name)
    monkeypatch.setenv(env, SECRET)
    assert getattr(cfg.load_settings(), attr) == SECRET
    monkeypatch.delenv(env)
    assert getattr(cfg.load_settings(), attr) is None
