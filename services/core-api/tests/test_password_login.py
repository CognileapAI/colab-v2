"""비밀번호 로그인 · 해시 저장 · 회전 · 시도 제한 (`PLAN-SoT §9 〈108〉` · Ted 2026-08-26).

**red 를 먼저 봤다** — `kernel/credentials.py`·`kernel/password.py` 가 없던 시점에 이 파일은
모듈 해석 실패로 red 였고, 계약이 `accessCode` 를 필수로 두고 있어 비밀번호 본문은 400 이었다.

⚠ **평문 비밀번호를 시험에도 실제 값으로 적지 않는다.** 아래 값은 시험 전용이며 배포된 값이
아니다 — 배포 값은 이 레포 어디에도 없다 (`〈93〉` 비밀 취급).
"""
from __future__ import annotations

import json
import subprocess
import sys

import pytest
from conftest import ACC_A_RES, LAB_A, TOKEN_RES, auth

from colab_core.kernel.credentials import CredentialStore
from colab_core.kernel.password import hash_password, verify_password

SECRET = "test-session-secret-0123456789"
NAME = "시험계정"
GOOD = "시험용-비밀번호-1"
BAD = "시험용-비밀번호-2"


@pytest.fixture()
def credentials_file(tmp_path):
    """자격 파일 한 벌. **평문 칸이 없다** — 해시·소금·파라미터뿐이다."""
    entry = {"accountId": ACC_A_RES, "labId": LAB_A}
    entry.update(hash_password(GOOD, n=1024).as_dict())   # 시험에서는 n 을 낮춰 빨리 돈다
    path = tmp_path / "credentials.json"
    path.write_text(json.dumps({NAME: entry}, ensure_ascii=False), encoding="utf-8")
    return str(path)


@pytest.fixture()
def client(p2_client, credentials_file):
    return p2_client(session_secret=SECRET, credentials_file=credentials_file)


def _login(client, **body):
    return client.post("/api/v1/sessions", json=body)


# ── 발급 ────────────────────────────────────────────────────────────────────────

def test_정_비밀번호는_201_이다(client) -> None:
    res = _login(client, accountName=NAME, password=GOOD)
    assert res.status_code == 201, res.text
    assert res.json()["token"]


def test_발급된_세션으로_me_가_열린다(client) -> None:
    token = _login(client, accountName=NAME, password=GOOD).json()["token"]
    res = client.get("/api/v1/me", headers=auth(token))
    assert res.status_code == 200
    assert res.json()["accountId"] == ACC_A_RES


def test_오_비밀번호는_401_이다(client) -> None:
    res = _login(client, accountName=NAME, password=BAD)
    assert res.status_code == 401
    assert res.json()["code"] == "UNAUTHORIZED"


def test_없는_계정도_같은_401_이다(client) -> None:
    """**계정 존재 여부를 노출하지 않는다** — 응답 본문이 오 비밀번호와 같아야 한다."""
    missing = _login(client, accountName="없는계정", password=GOOD)
    wrong = _login(client, accountName=NAME, password=BAD)
    assert missing.status_code == wrong.status_code == 401
    assert missing.json() == wrong.json()


def test_응답에_비밀번호가_되비치지_않는다(client) -> None:
    for res in (_login(client, accountName=NAME, password=BAD),
                _login(client, accountName=NAME, password=GOOD)):
        assert GOOD not in res.text and BAD not in res.text


def test_두_형태를_섞으면_400_이다(client) -> None:
    res = _login(client, accountName=NAME, password=GOOD, accessCode=TOKEN_RES)
    assert res.status_code == 400


def test_빈_본문은_400_이다(client) -> None:
    assert client.post("/api/v1/sessions", json={}).status_code == 400


def test_접속_코드_경로가_그대로_돈다(client) -> None:
    """비밀번호 수단을 더해도 기존 경로가 끊기지 않는다 (`〈107〉-㉱`)."""
    assert _login(client, accessCode=TOKEN_RES).status_code == 201


# ── 저장 ────────────────────────────────────────────────────────────────────────

def test_자격_파일에_평문이_없다(credentials_file) -> None:
    raw = open(credentials_file, encoding="utf-8").read()
    assert GOOD not in raw
    entry = json.loads(raw)[NAME]
    assert entry["kdf"] == "scrypt"
    assert set(entry) == {"accountId", "labId", "kdf", "salt", "hash", "n", "r", "p"}


def test_같은_비밀번호도_해시가_매번_다르다() -> None:
    """소금이 매번 다르다 — 같은 해시가 두 번 나오면 소금이 없는 것이다."""
    assert hash_password(GOOD, n=1024).digest != hash_password(GOOD, n=1024).digest


def test_모르는_KDF_는_거부한다() -> None:
    """「모르니까 통과」를 만들지 않는다 (fail-closed)."""
    stored = hash_password(GOOD, n=1024)
    assert verify_password(GOOD, dataclass_replace(stored, kdf="평문")) is False


def dataclass_replace(obj, **kw):
    import dataclasses
    return dataclasses.replace(obj, **kw)


def test_없는_자격_파일은_뜨지_않는다(tmp_path) -> None:
    """경로 오타가 「비밀번호 로그인이 조용히 사라진 배포」가 되지 않게 한다."""
    with pytest.raises(RuntimeError):
        CredentialStore.from_file(str(tmp_path / "없다.json"))


# ── 회전 ────────────────────────────────────────────────────────────────────────

def test_회전하면_구_비밀번호가_401_이다(p2_client, credentials_file) -> None:
    """부트스트랩 자격을 걷는 수단이 실제로 있는지 본다 (Ted 조건 2)."""
    assert _login(p2_client(session_secret=SECRET, credentials_file=credentials_file),
                  accountName=NAME, password=GOOD).status_code == 201

    ops = __import__("pathlib").Path(__file__).resolve().parents[1] / "ops" / "set-password.py"
    done = subprocess.run([sys.executable, str(ops), "--file", credentials_file,
                           "--name", NAME],
                          input=BAD + "\n", capture_output=True, text=True)
    assert done.returncode == 0, done.stderr
    # 스크립트가 값을 되비치지 않는다.
    assert BAD not in done.stdout and BAD not in done.stderr

    rotated = p2_client(session_secret=SECRET, credentials_file=credentials_file)
    assert _login(rotated, accountName=NAME, password=GOOD).status_code == 401
    assert _login(rotated, accountName=NAME, password=BAD).status_code == 201


def test_회전_후_파일_권한이_0600_이다(credentials_file) -> None:
    import os
    import pathlib
    ops = pathlib.Path(__file__).resolve().parents[1] / "ops" / "set-password.py"
    subprocess.run([sys.executable, str(ops), "--file", credentials_file, "--name", NAME],
                   input=BAD + "\n", capture_output=True, text=True, check=True)
    assert os.stat(credentials_file).st_mode & 0o777 == 0o600


# ── 시도 제한 ───────────────────────────────────────────────────────────────────

def test_실패가_쌓이면_429_다(p2_client, credentials_file) -> None:
    client = p2_client(session_secret=SECRET, credentials_file=credentials_file,
                       login_max_failures=3)
    for _ in range(3):
        assert _login(client, accountName=NAME, password=BAD).status_code == 401
    res = _login(client, accountName=NAME, password=BAD)
    assert res.status_code == 429
    assert res.json()["code"] == "TOO_MANY_ATTEMPTS"


def test_막힌_동안은_정_비밀번호도_429_다(p2_client, credentials_file) -> None:
    """막힌 것과 틀린 것을 가른다 — 429 와 401 을 한 코드로 합치지 않는다."""
    client = p2_client(session_secret=SECRET, credentials_file=credentials_file,
                       login_max_failures=2)
    for _ in range(2):
        _login(client, accountName=NAME, password=BAD)
    assert _login(client, accountName=NAME, password=GOOD).status_code == 429


def test_성공하면_셈이_지워진다(p2_client, credentials_file) -> None:
    client = p2_client(session_secret=SECRET, credentials_file=credentials_file,
                       login_max_failures=3)
    _login(client, accountName=NAME, password=BAD)
    _login(client, accountName=NAME, password=BAD)
    assert _login(client, accountName=NAME, password=GOOD).status_code == 201
    assert _login(client, accountName=NAME, password=BAD).status_code == 401
