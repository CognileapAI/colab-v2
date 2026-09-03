"""로그인 시도 제한 (Ted 2026-08-26 필수 취급 조건 3 — 최소 보완).

## 무엇을 막는가

같은 식별자로 짧은 시간에 반복되는 실패. 사전 추측을 **느리게** 만든다.

## 한계를 감추지 않는다

**프로세스 안에서만 센다.** 워커가 여럿이면 그 수만큼 시도가 늘고, 프로세스가 재시작하면
셈이 0 이 된다. 즉 **분산 시행이 아니다.** 진짜 시행이 필요하면 공유 저장소가 있어야 하고,
그것은 저장처 신설이라 이 회차의 범위를 넘는다 (`PLAN-SoT §9 〈108〉-㉲`).

**IP 를 유일한 열쇠로 쓰지 않는다.** 프록시 뒤라 `X-Forwarded-For` 를 믿어야 하는데,
그것을 믿는 순간 헤더 하나로 제한을 우회할 수 있다. 그래서 **기본 식별자는 로그인이 겨냥한
자격**이고, 클라이언트 버킷은 그 **위에 얹는 두 번째 브레이크**다 (`kernel/authn.py`
`client_key` — 첫 홉이 사용자가 보낸 값이라는 한계를 그 자리에 적었다 · Ted 판정 대기).
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

    def _drop_expired(self, now: float) -> None:
        """창 밖으로 나간 버킷을 **통째로 버린다** — 이것이 dict 를 묶는 유일한 자리다.

        종전에는 삭제가 성공 로그인의 `clear()` 뿐이었다. 성공하지 않는 열쇠
        (무작위 `accountName`)는 **영원히 남았다.**
        """
        dead = [k for k, bucket in self._failures.items()
                if not bucket or now - bucket[-1] > self._window]
        for k in dead:
            del self._failures[k]

    def blocked(self, key: str, *, now: float | None = None) -> bool:
        """**쓰지 않는다** (`CODE-REVIEW-20260903` #5).

        이 함수는 **자격 검사 전에** 불린다. 종전에는 `setdefault` 로 항목을 만들어,
        무작위 `accountName`(최대 128자)을 실은 요청 하나하나가 프로세스 수명 동안 남는
        dict 항목이 됐다 — 삭제 경로는 성공 로그인의 `clear()` 뿐이었다.
        """
        bucket = self._failures.get(key)
        if not bucket:
            return False
        cutoff = (now or time.monotonic()) - self._window
        return sum(1 for at in bucket if at > cutoff) >= self._max

    def record_failure(self, key: str, *, now: float | None = None) -> None:
        now = now or time.monotonic()
        # **여기서만 항목이 는다.** 그러므로 여기서 만료된 것을 버린다 — 자라는 자리와
        # 줄어드는 자리를 같은 함수에 두면 둘이 갈라지지 않는다.
        self._drop_expired(now)
        self._prune(key, now).append(now)

    def clear(self, key: str) -> None:
        self._failures.pop(key, None)
