"""트리거 집행 — **받은 사건 하나를 재생성 한 회로 바꾼다** (`Y-1` · `〈253〉`).

여기에 무효화 **규칙**이 없다. 어느 산출물이 낡았는가는 `invalidation.plan` 이 이미
답하고(자동·수동이 함께 지나는 유일한 자리 · 완료 정의 ⓒ), 이 모듈이 더하는 것은
**「버스에서 집은 것을 언제 집행하고 언제 걷는가」** 하나다.

**순서** — 집는다 → 재생성한다 → **그 다음에** 걷는다(ack). 거꾸로 하면 실패한 알림이
사라지고 미리보기가 낡은 채 굳는다.
"""
from __future__ import annotations


def drain(port, *, jobs, source) -> list:
    """버스에 쌓인 것을 한 바퀴 집행하고 **집행한 결과 목록**을 돌려준다.

    **그린 적 없는 대상은 건너뛴다** — `JobStore.regenerate` 가 「무효화 범위를 지어내지
    않는다」로 거절하는 자리다. 이 인스턴스가 한 번도 그리지 않은 대상에는 낡은 산출물이
    없으므로 **할 일이 없고**, 그때도 알림은 걷는다(다시 와도 같은 결론이다).

    **한 건이 실패해도 나머지를 멈추지 않는다** — 실패한 건의 알림은 **걷지 않는다.**
    다음 바퀴가 다시 집는다(at-least-once 의 소비자 쪽 짝).
    """
    done: list = []
    for event in list(port.poll()):
        try:
            outcome = jobs.regenerate(event, source=source)
        except LookupError:
            port.ack(event)
            continue
        done.append(outcome)
        port.ack(event)
    return done
