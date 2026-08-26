"""로그인 시도 제한 (Ted 2026-08-26 필수 취급 조건 3 — 최소 보완).

## 무엇을 막는가

같은 식별자로 짧은 시간에 반복되는 실패. 사전 추측을 **느리게** 만든다.

## 한계를 감추지 않는다

**프로세스 안에서만 센다.** 워커가 여럿이면 그 수만큼 시도가 늘고, 프로세스가 재시작하면
셈이 0 이 된다. 즉 **분산 시행이 아니다.** 진짜 시행이 필요하면 공유 저장소가 있어야 하고,
그것은 저장처 신설이라 이 회차의 범위를 넘는다 (`PLAN-SoT §9 〈108〉-㉲`).

**IP 로 세지 않는다.** 프록시 뒤라 `X-Forwarded-For` 를 믿어야 하는데, 그것을 믿는 순간
헤더 하나로 제한을 우회할 수 있다. 식별자는 **로그인이 겨냥한 계정**이다.
"""
from __future__ import annotations

import time
from collections import deque


class AttemptLimiter:
    """식별자별 실패 횟수를 창(window) 안에서 센다. 성공하면 그 식별자의 셈을 지운다."""

    def __init__(self, *, max_failures: int, window_seconds: int) -> None:
        if max_failures <= 0 or window_seconds <= 0:
            raise ValueError("시도 제한 값은 1 이상이어야 한다.")
        self._max = max_failures
        self._window = window_seconds
        self._failures: dict[str, deque[float]] = {}

    def _prune(self, key: str, now: float) -> deque[float]:
        bucket = self._failures.setdefault(key, deque())
        while bucket and now - bucket[0] > self._window:
            bucket.popleft()
        return bucket

    def blocked(self, key: str, *, now: float | None = None) -> bool:
        return len(self._prune(key, now or time.monotonic())) >= self._max

    def record_failure(self, key: str, *, now: float | None = None) -> None:
        now = now or time.monotonic()
        self._prune(key, now).append(now)

    def clear(self, key: str) -> None:
        self._failures.pop(key, None)
