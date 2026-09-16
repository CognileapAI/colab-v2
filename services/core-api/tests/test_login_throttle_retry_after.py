"""429 가 **언제 풀리는지**를 말한다 (핫픽스 HF-B ①).

종전의 429 본문은 「잠시 뒤에 다시 시도한다」 한 줄이었다. 「잠시」가 몇 초인지는 서버만
알고 있었고, 화면은 그 값을 지어내거나 사람이 새로고침을 반복하는 수밖에 없었다 —
그 반복이 다시 실패로 세어지지는 않지만(막힌 요청은 `record_failure` 를 타지 않는다)
**사람은 그동안 자기 비밀번호를 계속 의심한다.**

여기서 재는 것 —
  ⓐ 429 응답에 `Retry-After` 헤더(정수 초)와 본문 `retryAfterSeconds` 가 **둘 다** 있다
  ⓑ 두 값이 같고, 창 길이를 넘지 않으며, 0 이 아니다
  ⓒ 401·201 에는 그 헤더가 붙지 않는다 — 막히지 않은 자리에 대기 시간을 말하지 않는다
  ⓓ `AttemptLimiter.retry_after` 는 **가장 먼저 창을 벗어나는 실패**를 기준으로 센다
"""
from __future__ import annotations

from conftest import TOKEN_RES

from colab_core.kernel.throttle import AttemptLimiter

SECRET = "test-session-secret-0123456789"
UNKNOWN = "심어-두지-않은-코드"


def _login(client, code: str):
    return client.post("/api/v1/sessions", json={"accessCode": code})


# ═══════════════════ ⓐ·ⓑ 응답이 대기 시간을 싣는다 ═══════════════════════════
def test_the_429_carries_both_a_header_and_a_body_field(p2_client) -> None:
    client = p2_client(session_secret=SECRET, login_max_failures=5)
    for _ in range(5):
        assert _login(client, UNKNOWN).status_code == 401
    blocked = _login(client, UNKNOWN)
    assert blocked.status_code == 429, blocked.text
    assert "Retry-After" in blocked.headers, \
        "429 가 언제 풀리는지 말하지 않는다 — 화면이 그 값을 지어내게 된다."
    body = blocked.json()
    assert "retryAfterSeconds" in body, "본문에 대기 시간이 없다."
    assert body["retryAfterSeconds"] == int(blocked.headers["Retry-After"]), \
        "헤더와 본문이 다른 수를 말한다."
    assert 0 < body["retryAfterSeconds"] <= 900, \
        f"대기 시간이 창(900초) 밖이다: {body['retryAfterSeconds']}"
    assert body["code"] == "TOO_MANY_ATTEMPTS"


def test_the_unblocked_answers_do_not_carry_a_wait(p2_client) -> None:
    """**넓히지 않았음을 함께 잰다** — 막히지 않은 응답은 대기 시간을 말하지 않는다."""
    client = p2_client(session_secret=SECRET, login_max_failures=5)
    denied = _login(client, UNKNOWN)
    assert denied.status_code == 401
    assert "Retry-After" not in denied.headers
    assert "retryAfterSeconds" not in denied.json()
    ok = _login(client, TOKEN_RES)
    assert ok.status_code == 201, ok.text
    assert "Retry-After" not in ok.headers


# ═══════════════════ ⓓ 제한기가 남은 초를 센다 ═══════════════════════════════
def test_retry_after_is_zero_while_the_bucket_is_not_blocked() -> None:
    limiter = AttemptLimiter(max_failures=3, window_seconds=900)
    assert limiter.retry_after("name:없는") == 0
    limiter.record_failure("name:하나", now=100.0)
    assert limiter.retry_after("name:하나", now=100.0) == 0, \
        "막히지도 않았는데 기다리라고 말한다."


def test_retry_after_counts_from_the_failure_that_leaves_the_window_first() -> None:
    """창을 벗어나는 **첫 실패**가 기준이다 — 마지막 실패를 기준으로 재면 과다 대기다."""
    limiter = AttemptLimiter(max_failures=3, window_seconds=900)
    limiter.record_failure("name:갑", now=100.0)
    limiter.record_failure("name:갑", now=200.0)
    limiter.record_failure("name:갑", now=300.0)
    assert limiter.blocked("name:갑", now=300.0) is True
    # 100.0 의 실패가 1000.0 에 창을 벗어난다 → 300.0 시점의 남은 초는 700.
    assert limiter.retry_after("name:갑", now=300.0) == 700


def test_retry_after_uses_the_max_th_newest_failure_when_there_are_extras() -> None:
    """실패가 한계보다 많으면 **`max` 번째로 새로운 실패**가 빠져야 풀린다."""
    limiter = AttemptLimiter(max_failures=3, window_seconds=900)
    for at in (100.0, 150.0, 200.0, 250.0):
        limiter.record_failure("name:을", now=at)
    # 살아 있는 넷 중 셋이 남으면 여전히 막힌다 — 150.0 이 빠져야 둘이 된다.
    assert limiter.retry_after("name:을", now=250.0) == 800


def test_retry_after_never_answers_zero_while_still_blocked() -> None:
    """**0 을 말하면 화면이 곧바로 다시 부른다** — 막혀 있는 동안은 최소 1 초다."""
    limiter = AttemptLimiter(max_failures=2, window_seconds=10)
    limiter.record_failure("name:병", now=100.0)
    limiter.record_failure("name:병", now=100.0)
    assert limiter.blocked("name:병", now=109.999) is True
    assert limiter.retry_after("name:병", now=109.999) >= 1


def test_the_window_length_is_readable() -> None:
    """버킷이 비었는데 막힌 경우의 대체값이 창 길이다 — 밖에서 읽을 수 있어야 한다."""
    assert AttemptLimiter(max_failures=5, window_seconds=900).window_seconds == 900
