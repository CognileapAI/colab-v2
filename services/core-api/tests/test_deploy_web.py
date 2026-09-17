"""`ops/deploy_web.py` — 순서(assets 먼저 · index.html 마지막) · 타입 · 캐시 두 갈래 · 모르는 확장자 거부.

실 S3 호출 없음 — `put_object` 를 기록하는 스텁. 모듈은 `ops/` 에 있어 경로로 읽는다(`test_deploy_doctor.py` 와 같다).
"""
from __future__ import annotations

import importlib.util
import pathlib
import sys

import pytest

OPS = pathlib.Path(__file__).resolve().parents[1] / "ops" / "deploy_web.py"


def load():
    spec = importlib.util.spec_from_file_location("deploy_web", OPS)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules["deploy_web"] = mod   # `@dataclass` 가 `sys.modules[__module__]` 를 본다 — 등록 뒤 실행
    spec.loader.exec_module(mod)
    return mod


class StubClient:
    def __init__(self) -> None:
        self.puts: list[tuple[str, bytes, str, str | None]] = []

    def put_object(self, key, payload, content_type="application/octet-stream", cache_control=None):
        self.puts.append((key, payload, content_type, cache_control))
        return '"etag"'


def _dist(tmp_path: pathlib.Path) -> pathlib.Path:
    d = tmp_path / "dist"
    (d / "assets").mkdir(parents=True)
    (d / "index.html").write_text("<html>", encoding="utf-8")
    (d / "assets" / "index-abc123.js").write_text("console.log(1)", encoding="utf-8")
    (d / "assets" / "index-abc123.css").write_text("body{}", encoding="utf-8")
    (d / "favicon.ico").write_bytes(b"\x00\x00\x01\x00")
    return d


def test_순서는_assets_먼저_index_html_마지막이고_타입과_캐시가_갈린다(tmp_path):
    dw = load()
    items = dw.plan(_dist(tmp_path))
    keys = [u.key for u in items]
    assert keys[0].startswith("assets/") and keys[1].startswith("assets/")
    assert keys[-1] == "index.html"
    by = {u.key: u for u in items}
    assert by["assets/index-abc123.js"].content_type.startswith("text/javascript")
    assert by["assets/index-abc123.js"].cache_control == dw.IMMUTABLE
    assert by["index.html"].content_type.startswith("text/html")
    assert by["index.html"].cache_control == dw.NO_CACHE
    assert by["favicon.ico"].cache_control == dw.NO_CACHE


def test_sync_는_계획_순서대로_put_object_에_헤더를_싣는다(tmp_path):
    dw = load()
    items = dw.plan(_dist(tmp_path))
    client = StubClient()
    total = dw.sync(items, client)
    assert [p[0] for p in client.puts] == [u.key for u in items]
    assert client.puts[-1][0] == "index.html" and client.puts[-1][3] == dw.NO_CACHE
    assert all(p[3] == dw.IMMUTABLE for p in client.puts if p[0].startswith("assets/"))
    assert total == sum(len(p[1]) for p in client.puts) > 0


def test_모르는_확장자는_거부하고_아무것도_올리지_않는다(tmp_path):
    dw = load()
    d = _dist(tmp_path)
    (d / "weird.bmp").write_bytes(b"BM")
    with pytest.raises(SystemExit) as e:
        dw.plan(d)
    assert "weird.bmp" in str(e.value)


def test_index_html_이_없으면_빌드부터_하라고_멈춘다(tmp_path):
    dw = load()
    d = tmp_path / "empty"
    d.mkdir()
    with pytest.raises(SystemExit):
        dw.plan(d)


def test_dry_run_은_올리지_않는다(tmp_path, capsys):
    dw = load()
    assert dw.main(["--dist", str(_dist(tmp_path)), "--bucket", "b", "--dry-run"]) == 0
    assert "올리지 않았다" in capsys.readouterr().out


@pytest.fixture
def deploy_credentials(tmp_path, monkeypatch):
    from colab_core.kernel import s3

    for name in ("AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_SESSION_TOKEN", "AWS_PROFILE"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("COLAB_DEPLOY_MANAGED", "1")
    credentials_file = tmp_path / "credentials"
    monkeypatch.setenv("AWS_SHARED_CREDENTIALS_FILE", str(credentials_file))
    captured = []

    def client(**kwargs):
        captured.append(kwargs.get("creds"))
        return StubClient()

    monkeypatch.setattr(s3, "S3Client", client)
    args = ["--dist", str(_dist(tmp_path)), "--bucket", "b"]
    return credentials_file, captured, args


@pytest.mark.parametrize("token", ["", "aws_session_token=session%token\n"])
def test_explicit_profile_credentials_reach_s3_client(deploy_credentials, monkeypatch, token):
    file, captured, args = deploy_credentials
    file.write_text("[deploy]\naws_access_key_id=profile-key\naws_secret_access_key=secret%value\n" + token)
    monkeypatch.setenv("AWS_PROFILE", "deploy")
    assert load().main(args) == 0
    assert captured[0].access_key == "profile-key"
    assert captured[0].secret_key == "secret%value"
    assert captured[0].session_token == ("session%token" if token else None)


def test_complete_environment_credentials_take_priority(deploy_credentials, monkeypatch):
    _, captured, args = deploy_credentials
    monkeypatch.setenv("AWS_PROFILE", "missing")
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "environment-key")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "environment-secret")
    monkeypatch.setenv("AWS_SESSION_TOKEN", "environment-token")
    assert load().main(args) == 0
    assert captured[0].access_key == "environment-key"
    assert captured[0].session_token == "environment-token"


def test_unset_profile_preserves_existing_provider_chain(deploy_credentials):
    _, captured, args = deploy_credentials
    assert load().main(args) == 0
    assert captured == [None]


@pytest.mark.parametrize("content", [
    None, "[other]\naws_access_key_id=secret-marker\n", "malformed secret-marker",
    "[DEFAULT]\naws_secret_access_key=secret-marker\n[deploy]\naws_access_key_id=key\n",
    "[deploy]\nrole_arn=secret-marker\nsource_profile=base\n",
    "[deploy]\nsso_session=secret-marker\n",
])
def test_explicit_profile_failure_never_falls_back_or_leaks(deploy_credentials, monkeypatch, capsys, content):
    file, captured, args = deploy_credentials
    if content is not None:
        file.write_text(content)
    monkeypatch.setenv("AWS_PROFILE", "deploy")
    assert load().main(args) == 78
    assert captured == []
    err = capsys.readouterr().err
    assert "AWS_PROFILE" in err
    assert "secret-marker" not in err
    assert str(file) not in err


def test_default_credentials_path_and_dry_run(deploy_credentials, monkeypatch, tmp_path):
    _, captured, args = deploy_credentials
    monkeypatch.delenv("AWS_SHARED_CREDENTIALS_FILE")
    monkeypatch.setenv("AWS_PROFILE", "deploy")
    monkeypatch.setattr(pathlib.Path, "home", classmethod(lambda cls: tmp_path))
    # A missing explicit profile would fail a real deployment; dry-run never reads it.
    assert load().main(args + ["--dry-run"]) == 0
    assert captured == []
    (tmp_path / ".aws").mkdir()
    (tmp_path / ".aws" / "credentials").write_text(
        "[deploy]\naws_access_key_id=home-key\naws_secret_access_key=home-secret\n"
    )
    assert load().main(args) == 0
    assert captured[0].access_key == "home-key"
