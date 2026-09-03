"""발행에 실패하면 **다음 전달은 재전달이라고 말한다** (코드리뷰 20260903 부록).

봉투의 `delivery` 블록은 「재시도 여부·상한 판단을 소비자가 각자 하지 않는다」를 위해
있는데(`contracts/events/envelope.json#Delivery`), 실패한 발행에서 `attempt` 가 오르지
않아 재전달이 **영원히 `attempt: 1` · `redelivery: false`** 로 나갔다 — 첫 전달과 구분되지
않는 거짓말이고, 소비자가 봉투만 보고 재전달을 가릴 수 없었다.

⚠ **DLQ 는 이 회차 밖이다.** `maxAttempts`(기본 5)를 넘겨도 여기서 멈추지 않고 계속
재시도한다 — 계약의 「상한을 넘으면 DLQ 로 보낸다」는 아직 배선이 없다(작업항목 초안 #11).
여기서 고치는 것은 **숫자가 사실을 말하게 하는 것**뿐이다.
"""
from __future__ import annotations

import pytest
from colab_pipeline.d5.events import make_envelope, upload_ready_payload
from colab_pipeline.domains.d5_ingestion import relay_unpublished
from memory_ledger import MemoryLedger

_LAB = "01JQ0000000000000000000001"
_ACC = "01JQ0000000000000000000002"
_UPL = "01JQ0000000000000000000003"
_UP2 = "01JQ0000000000000000000004"


def _ledger_with(*upload_ids: str) -> MemoryLedger:
    ledger = MemoryLedger()
    for i, uid in enumerate(upload_ids):
        ledger.append_event(make_envelope(
            event_type="upload.ready", event_id=f"01JQ00000000000000000000E{i}",
            lab_id=_LAB, actor_account_id=_ACC, upload_id=uid,
            payload=upload_ready_payload(renderable=True, metadata_complete=False)))
    return ledger


class _Flaky:
    """첫 호출만 실패하는 발행자 — 브로커가 잠깐 안 받는 상황."""

    def __init__(self) -> None:
        self.seen: list[dict] = []
        self.failed = 0

    def __call__(self, env: dict) -> None:
        if self.failed == 0:
            self.failed += 1
            raise RuntimeError("발행 대상에 닿지 못했다")
        self.seen.append(env)


def test_발행에_실패하면_다음_전달이_재전달이라고_말한다():
    ledger = _ledger_with(_UPL)
    publish = _Flaky()

    assert relay_unpublished(ledger, publish=publish) == 0     # 첫 바퀴 — 못 보냈다
    assert relay_unpublished(ledger, publish=publish) == 1     # 다음 바퀴 — 보냈다

    env = publish.seen[0]
    assert env["delivery"]["attempt"] == 2, "재시도인데 첫 전달이라고 말한다"
    assert env["delivery"]["redelivery"] is True


def test_실패한_발행은_발행_표시를_남기지_않는다():
    """at-least-once — 못 보낸 것을 보냈다고 적으면 조용히 유실된다."""
    ledger = _ledger_with(_UPL)
    publish = _Flaky()
    relay_unpublished(ledger, publish=publish)
    assert len(ledger.unpublished()) == 1


def test_한_건의_발행_실패가_나머지를_막지_않는다():
    ledger = _ledger_with(_UPL, _UP2)
    publish = _Flaky()
    assert relay_unpublished(ledger, publish=publish) == 1
    assert [e["uploadId"] for e in publish.seen] == [_UP2]


def test_한_번에_나간_전달은_첫_전달_그대로다():
    ledger = _ledger_with(_UPL)
    sent: list[dict] = []
    assert relay_unpublished(ledger, publish=sent.append) == 1
    assert sent[0]["delivery"]["attempt"] == 1
    assert sent[0]["delivery"]["redelivery"] is False


def test_발행_실패가_틱을_죽이지_않는다():
    """예전에는 예외가 `_lab_pass` 까지 올라가 **그 바퀴의 처리·reaper 까지 롤백**했다."""
    ledger = _ledger_with(_UPL)

    def _always_fail(env):
        raise RuntimeError("브로커가 없다")

    assert relay_unpublished(ledger, publish=_always_fail) == 0
