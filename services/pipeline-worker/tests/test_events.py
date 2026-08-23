"""이벤트 7종 — 봉투·멱등 키·발행자 규칙. 계약(`contracts/events/**`)이 오라클이다.

계약은 **동결**이다. 이 시험은 계약을 고치지 않고, 우리가 만든 봉투가 계약을 통과하는지만 본다.
"""
from __future__ import annotations

import json

import pytest

from colab_pipeline.d5.events import (
    EVENT_TYPES,
    SOURCE_BY_TYPE,
    WorkerCannotEmitError,
    idempotency_key,
    make_envelope,
)

_LAB = "01JQ0000000000000000000001"
_ACC = "01JQ0000000000000000000002"
_UPL = "01JQ0000000000000000000003"
_EV = "01JQ00000000000000000000E1"


def test_seven_types_in_canonical_order():
    assert EVENT_TYPES == (
        "upload.accepted",
        "file.format-detected",
        "file.header-parsed",
        "file.crs-normalized",
        "preview.cog-built",
        "upload.ready",
        "upload.failed",
    )


def test_idempotency_key_is_deterministic_and_matches_the_contract_pattern():
    a = idempotency_key("file.format-detected", _UPL)
    b = idempotency_key("file.format-detected", _UPL)
    assert a == b == f"file.format-detected:{_UPL}"
    import re
    assert re.fullmatch(r"[a-z][a-z0-9-]*\.[a-z][a-z0-9-]*:[0-9A-HJKMNP-TV-Z]{26}", a)


def test_only_core_api_sources_upload_accepted():
    assert SOURCE_BY_TYPE["upload.accepted"] == "core-api"
    for t in EVENT_TYPES[1:]:
        assert SOURCE_BY_TYPE[t] == "pipeline-worker"


def test_worker_refuses_to_emit_upload_accepted():
    """`upload.accepted` 는 core-api 가 내는 **유일한** 이벤트다 — 봉투가 const 로 못박았다."""
    with pytest.raises(WorkerCannotEmitError):
        make_envelope(
            event_type="upload.accepted", event_id=_EV, lab_id=_LAB,
            actor_account_id=_ACC, upload_id=_UPL, payload={"files": []},
        )


def test_envelope_carries_delivery_and_stable_identities():
    env = make_envelope(
        event_type="upload.ready", event_id=_EV, lab_id=_LAB, actor_account_id=_ACC,
        upload_id=_UPL, payload={"renderable": True, "metadataComplete": True},
    )
    assert env["type"] == "upload.ready"
    assert env["source"] == "pipeline-worker"
    assert env["schemaVersion"] == "1.0"
    assert env["idempotencyKey"] == f"upload.ready:{_UPL}"
    d = env["delivery"]
    assert d["attempt"] == 1 and d["redelivery"] is False and d["maxAttempts"] == 5
    assert d["firstPublishedAt"] == d["publishedAt"]


def test_redelivery_keeps_event_id_and_first_published_at():
    first = make_envelope(
        event_type="upload.ready", event_id=_EV, lab_id=_LAB, actor_account_id=_ACC,
        upload_id=_UPL, payload={"renderable": True, "metadataComplete": True},
    )
    again = make_envelope(
        event_type="upload.ready", event_id=_EV, lab_id=_LAB, actor_account_id=_ACC,
        upload_id=_UPL, payload={"renderable": True, "metadataComplete": True},
        attempt=2, occurred_at=first["occurredAt"],
        first_published_at=first["delivery"]["firstPublishedAt"],
    )
    assert again["eventId"] == first["eventId"]
    assert again["occurredAt"] == first["occurredAt"]
    assert again["delivery"]["firstPublishedAt"] == first["delivery"]["firstPublishedAt"]
    assert again["delivery"]["redelivery"] is True
    assert again["idempotencyKey"] == first["idempotencyKey"]   # 작업의 정체성은 하나다


def test_every_emitted_envelope_validates_against_the_frozen_contract(event_validator):
    """7종 전부를 계약 스키마로 검증한다 — 우리가 만든 것이 계약을 통과하는가."""
    from colab_pipeline.d5.events import sample_payloads
    for t, payload in sample_payloads(_UPL).items():
        env = make_envelope(
            event_type=t, event_id=_EV, lab_id=_LAB, actor_account_id=_ACC,
            upload_id=_UPL, payload=payload, allow_core_api_source=True,
        )
        errors = event_validator(env)
        assert not errors, (t, errors, json.dumps(env, ensure_ascii=False)[:400])
