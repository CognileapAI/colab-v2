"""로그인 시도 제한의 **버킷**과 **셈의 경계** (`CODE-REVIEW-20260903` #5).

종전에 접속 코드 로그인은 전부 상수 `"code:*"` **한 버킷**이었다. 결과 —
  · 누구든 5회 실패시키면 **15분간 모든 접속 코드 사용자가 429** 다 (전 연구실 정지).
  · 성공 1회가 **전원의 카운터**를 지운다 — 유효 코드 하나를 섞는 추측 공격은 늦춰지지 않는다.
그리고 `AttemptLimiter.blocked()` 가 `setdefault` 로 **쓰기**를 했다. `blocked()` 는
자격 검사 **전에** 불리므로, 무작위 `accountName`(최대 128자) 요청마다 dict 항목이 영구히
늘었다 — 삭제는 성공 로그인의 `clear()` 뿐이었다.

여기서 재는 것 —
  ⓐ 접속 코드 버킷이 **코드마다 다르고** 원문을 담지 않는다
  ⓑ 코드 A 를 두드려도 코드 B 는 막히지 않고, B 의 성공이 A 의 셈을 지우지 않는다
  ⓒ **클라이언트 버킷**이 코드를 갈아 가며 하는 열거를 센다 — 열쇠는 부른 쪽이 못 바꾸는
    **마지막 홉**이고, 길이 상한을 넘긴 홉도 버킷을 잃지 않는다(고정 버킷으로 접힌다)
  ⓓ `blocked()` 는 쓰지 않는다 · `record_failure` 는 만료 버킷을 버려 dict 를 묶는다
"""
from __future__ import annotations

from conftest import TOKEN_PROF, TOKEN_RES

from colab_core.kernel.authn import (CLIENT_OVERSIZE, CLIENT_PREFIX, LoginAttempt,
                                     client_key)
from colab_core.kernel.throttle import AttemptLimiter

SECRET = "test-session-secret-0123456789"
UNKNOWN = "심어-두지-않은-코드"


def _login(client, code: str, *, forwarded_for: str | None = None):
    headers = {} if forwarded_for is None else {"X-Forwarded-For": forwarded_for}
    return client.post("/api/v1/sessions", json={"accessCode": code}, headers=headers)


# ═══════════════════ ⓐ 버킷이 코드마다 다르고 원문을 안 담는다 ═════════════════
def test_the_access_code_bucket_is_per_code_and_never_carries_the_code() -> None:
    a = LoginAttempt(access_code="코드-가").key
    b = LoginAttempt(access_code="코드-나").key
    assert a != b, "접속 코드가 한 버킷에 접힌다 — 한 사람이 전원을 막는다."
    assert "코드-가" not in a, "시도 제한 열쇠에 접속 코드 원문이 실렸다."
    assert a.startswith("code:")
    assert LoginAttempt(access_code="코드-가").key == a, "같은 코드가 다른 버킷이 됐다."


def test_the_account_name_bucket_is_unchanged() -> None:
    """비밀번호 갈래는 그대로다 — **넓히지도 좁히지도 않았음**을 함께 잰다."""
    assert LoginAttempt(account_name="누구", password="x").key == "name:누구"


# ═══════════ ⓑ 한 코드의 실패가 다른 코드를 막지 않는다 ══════════════════════
def test_hammering_one_code_does_not_lock_out_another(p2_client) -> None:
    """**전 연구실 정지**가 이 시험이 막는 것이다."""
    client = p2_client(session_secret=SECRET, login_max_failures=3)
    for _ in range(4):
        _login(client, UNKNOWN)
    assert _login(client, UNKNOWN).status_code == 429, "자기 버킷은 막혀야 한다."
    ok = _login(client, TOKEN_RES)
    assert ok.status_code == 201, f"남의 실패가 정상 로그인을 막았다: {ok.text}"


def test_one_success_does_not_clear_everyone_elses_counter(p2_client) -> None:
    """성공 1회가 전원의 셈을 지우면 **유효 코드 하나를 섞는 추측 공격**이 안 늦춰진다."""
    client = p2_client(session_secret=SECRET, login_max_failures=3)
    for _ in range(3):
        _login(client, UNKNOWN)
    assert _login(client, TOKEN_RES).status_code == 201
    assert _login(client, UNKNOWN).status_code == 429, \
        "남의 성공이 추측 중인 버킷의 셈을 지웠다."


# ═════════════ ⓒ 클라이언트 버킷 — 코드를 갈아 가며 하는 열거 ═════════════════
def test_enumeration_across_many_codes_is_braked_per_client(p2_client) -> None:
    """코드마다 버킷을 가르면 **코드를 갈아 가며 하는 열거**는 브레이크가 없어진다.

    그래서 버킷이 둘이다 — **겨냥된 자격**과 **부른 클라이언트**. 하나만 두면 각각 뚫린다.
    """
    client = p2_client(session_secret=SECRET, login_max_failures=3)
    for i in range(3):
        assert _login(client, f"추측-{i}", forwarded_for="203.0.113.9").status_code == 401
    blocked = _login(client, TOKEN_RES, forwarded_for="203.0.113.9")
    assert blocked.status_code == 429, "코드를 갈아 가며 하는 열거가 그대로 통과했다."


def test_another_client_is_not_braked_by_its_neighbour(p2_client) -> None:
    """**한 사람이 전원을 막는 자리를 다시 만들지 않는다.**"""
    client = p2_client(session_secret=SECRET, login_max_failures=3)
    for i in range(4):
        _login(client, f"추측-{i}", forwarded_for="203.0.113.9")
    ok = _login(client, TOKEN_PROF, forwarded_for="198.51.100.7")
    assert ok.status_code == 201, f"옆 클라이언트의 실패가 나를 막았다: {ok.text}"


def test_the_client_key_reads_the_last_hop_not_the_first() -> None:
    """**마지막 홉**이 열쇠다 — 첫 홉은 부른 쪽이 지어낼 수 있는 값이다.

    `infra/staging/nginx.i2.conf:61` 은 `$proxy_add_x_forwarded_for` 를 쓴다 — 들어온 헤더
    **뒤에** `$remote_addr` 를 덧붙이는 변수라, 마지막 홉은 **nginx 가 실제로 본 주소**고
    부른 쪽이 못 바꾼다. 첫 홉을 읽으면 헤더 한 줄로 버킷을 무한히 갈 수 있어
    클라이언트 버킷이 브레이크 구실을 못 한다.
    """
    assert client_key("203.0.113.9, 10.0.0.1, 10.0.0.2") == "client:10.0.0.2"
    assert client_key("  203.0.113.9  ") == "client:203.0.113.9"
    assert client_key("2001:db8::1,198.51.100.7") == "client:198.51.100.7"
    assert client_key(None) is None
    assert client_key("") is None
    assert client_key(",") is None


def test_an_oversize_hop_falls_into_a_sentinel_bucket_not_into_nothing() -> None:
    """긴 홉은 **버킷을 잃는 것이 아니라 고정 버킷으로 접힌다.**

    종전에는 `None` 이었다 — 상한을 넘기기만 하면 클라이언트 버킷이 통째로 사라졌고,
    그것은 **제한을 끄는 스위치**였다. 길이 상한은 열쇠가 로그·dict 를 부풀리지 않게
    묶는 것이지 셈을 면제하는 것이 아니다.
    """
    assert client_key("x" * 400) == CLIENT_OVERSIZE
    assert client_key("203.0.113.9, " + "9" * 400) == CLIENT_OVERSIZE
    assert CLIENT_OVERSIZE.startswith(CLIENT_PREFIX), "자격 버킷과 이름 공간이 갈라져야 한다."


def test_rotating_the_first_hop_does_not_escape_the_client_bucket(p2_client) -> None:
    """**이 시험이 막는 것이 헤더를 돌리는 열거다.**

    첫 홉을 읽으면 요청마다 다른 값을 실어 버킷을 새로 만들 수 있다. 마지막 홉은
    nginx 가 덧붙인 값이라 부른 쪽이 못 바꾼다 — 셋을 실패하면 넷째가 막힌다.
    """
    client = p2_client(session_secret=SECRET, login_max_failures=3)
    for i in range(3):
        r = _login(client, f"추측-{i}", forwarded_for=f"10.9.9.{i}, 203.0.113.9")
        assert r.status_code == 401, r.text
    blocked = _login(client, TOKEN_RES, forwarded_for="10.9.9.99, 203.0.113.9")
    assert blocked.status_code == 429, "첫 홉을 갈아 끼워 클라이언트 버킷을 빠져나갔다."


def test_an_oversize_header_is_still_braked(p2_client) -> None:
    """긴 헤더로 **제한을 끄지 못한다** — 고정 버킷에서 그대로 센다."""
    client = p2_client(session_secret=SECRET, login_max_failures=3)
    long_hop = "9" * 300
    for i in range(3):
        assert _login(client, f"추측-{i}", forwarded_for=long_hop).status_code == 401
    blocked = _login(client, TOKEN_RES, forwarded_for=long_hop)
    assert blocked.status_code == 429, "긴 헤더가 클라이언트 버킷을 통째로 지웠다."


# ═══════════════ ⓓ blocked() 는 쓰지 않는다 · dict 가 묶인다 ══════════════════
def test_blocked_never_writes() -> None:
    """`blocked()` 는 **자격 검사 전에** 불린다 — 여기서 항목을 만들면 무작위 이름
    요청마다 dict 가 영구히 자란다. 삭제는 성공 로그인의 `clear()` 뿐이었다.
    """
    limiter = AttemptLimiter(max_failures=3, window_seconds=900)
    for i in range(1000):
        assert limiter.blocked(f"name:{i}") is False
    assert limiter._failures == {}, \
        f"blocked() 가 {len(limiter._failures)} 개 항목을 만들었다 — 이것이 메모리 누수다."


def test_record_failure_drops_buckets_that_left_the_window() -> None:
    """창 밖으로 나간 버킷은 **버린다** — 안 버리면 dict 는 단조 증가한다."""
    limiter = AttemptLimiter(max_failures=3, window_seconds=10)
    for i in range(50):
        limiter.record_failure(f"name:{i}", now=100.0)
    assert len(limiter._failures) == 50
    limiter.record_failure("name:새로운", now=1000.0)
    assert len(limiter._failures) == 1, \
        f"만료 버킷이 남았다: {len(limiter._failures)} 개."
    assert "name:새로운" in limiter._failures


def test_a_live_bucket_is_not_dropped_by_the_pruning() -> None:
    """**넓히지 않았음을 함께 잰다** — 창 안의 셈은 청소에 쓸려 나가지 않는다."""
    limiter = AttemptLimiter(max_failures=3, window_seconds=10)
    for _ in range(3):
        limiter.record_failure("name:살아있는", now=100.0)
    limiter.record_failure("name:다른", now=105.0)
    assert limiter.blocked("name:살아있는", now=105.0) is True
    assert limiter.blocked("name:살아있는", now=115.5) is False, "창이 지나도 계속 막았다."
