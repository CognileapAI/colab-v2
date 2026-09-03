"""트리거 집행 — **받은 사건 하나를 재생성 한 회로 바꾼다** (`Y-1` · `〈253〉`).

여기에 무효화 **규칙**이 없다. 어느 산출물이 낡았는가는 `invalidation.plan` 이 이미
답하고(자동·수동이 함께 지나는 유일한 자리 · 완료 정의 ⓒ), 이 모듈이 더하는 것은
**「버스에서 집은 것을 언제 집행하고 언제 걷는가」** 하나다.

**순서** — 집는다 → 재생성한다 → **그 다음에** 걷는다(ack). 거꾸로 하면 실패한 알림이
사라지고 미리보기가 낡은 채 굳는다.

⭑ **⟨2026-09-03 · 코드리뷰 `CODE-REVIEW-20260903.md` #2⟩ 격리 단위가 「틱」에서
「봉투」로 내려왔다.** 종전 `list(port.poll())` 은 제너레이터 안에서 예외가 터지면
그 틱의 **전 봉투**를 잃었고(어긋난 봉투 하나가 멀쩡한 봉투들을 인질로 잡았다),
`regenerate` 도 `LookupError` 만 잡아 그 밖의 예외 한 건이 같은 틱의 나머지를 막았다.
독스트링은 「한 건이 실패해도 나머지를 멈추지 않는다」고 적혀 있었고 **코드가 그것을
안 지키고 있었다.**
"""
from __future__ import annotations

import logging

from ..ports.source import TargetNotFound

logger = logging.getLogger(__name__)


def _collect(port) -> list:
    """봉투를 모은다 — **집는 도중 터져도 이미 집은 것은 잃지 않는다.**

    ⚠ 이것은 이중 방어다. 어긋난 봉투 하나를 격리하고 계속 가는 것은 어댑터가 하고
    (`trigger_bus.SpoolTriggerPort.poll`), 여기서는 **어떤 Port 를 끼워도** 그 자리가
    틱 전체를 못 죽이게 한다 — `TriggerPort` 는 Protocol 이라 구현이 하나가 아니다.
    """
    events: list = []
    iterator = iter(port.poll())
    while True:
        try:
            events.append(next(iterator))
        except StopIteration:
            break
        except Exception:                        # noqa: BLE001 — 제너레이터가 죽었다
            # 죽은 제너레이터는 다시 못 돌린다. **이미 집은 것으로 이 틱을 돈다** —
            # 남은 봉투는 다음 바퀴가 집는다(at-least-once 의 소비자 쪽 짝).
            logger.warning("트리거 버스를 읽다 멈췄다 — 이 틱은 %d건으로 돈다",
                           len(events), exc_info=True)
            break
    return events


def drain(port, *, jobs, source) -> list:
    """버스에 쌓인 것을 한 바퀴 집행하고 **집행한 결과 목록**을 돌려준다.

    **그린 적 없는 대상 · 사라진 대상은 건너뛴다** — 앞은 `JobStore.regenerate` 가
    「무효화 범위를 지어내지 않는다」로 거절하는 자리(`LookupError`)이고, 뒤는 미리보기
    뒤에 대상 디렉터리가 없어져 `SourcePort.resolve` 가 거절하는 자리(`TargetNotFound`)다.
    **둘 다 다시 와도 같은 결론**이라 알림을 걷는다 — 할 일이 없다.

    ⭑ ⟨2026-09-03 · 레인 C 수용 검토 #3⟩ `TargetNotFound` 는 `LookupError` 가 **아니라**
    그냥 `Exception` 이라 아래 마지막 그물에 걸렸다. 그 갈래는 걷지 않으므로 사라진
    대상의 봉투를 **매 틱 다시 집어 영원히** 트레이스백만 찍었다. 「실패라서 다시 해
    본다」가 아니라 **결론이 이미 났는데 못 걷은 것**이라, 자리를 `LookupError` 옆으로 옮긴다.

    **한 건이 실패해도 나머지를 멈추지 않는다** — 실패한 건의 알림은 **걷지 않는다.**
    다음 바퀴가 다시 집는다(at-least-once 의 소비자 쪽 짝). 재생성이 시간 안에 안
    끝난 것도 여기 든다(`regenerate` 가 `TimeoutError` 로 끊는다) — 안 끝난 것은
    성공이 아니다.
    """
    done: list = []
    for event in _collect(port):
        try:
            outcome = jobs.regenerate(event, source=source)
        except (LookupError, TargetNotFound):
            logger.info("그린 적 없는 대상/사라진 대상이다 — 알림을 걷는다: %s",
                        event.target_id)
            port.ack(event)
            continue
        except Exception:                        # noqa: BLE001
            # **걷지 않는다** — 다음 바퀴가 다시 집는다. 여기서 ack 하면 실패한 재생성이
            # 조용히 사라지고 미리보기가 낡은 채 굳는다.
            logger.warning("재생성이 실패했다 — 알림을 걷지 않는다: %s",
                           event.target_id, exc_info=True)
            continue
        done.append(outcome)
        port.ack(event)
    return done
