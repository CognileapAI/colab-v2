from __future__ import annotations

import copy
import datetime as dt
import hashlib
import json
import re

SCHEMA = "colab.operator-event/1"
CHANNELS = {"development", "activity"}
ENVIRONMENTS = {"dev", "staging"}
DEVELOPMENT_KINDS = {"deploy.succeeded", "deploy.failed", "deploy.verification_failed",
                     "probe.failed", "probe.recovered", "probe.unobservable",
                     "aws.health.issue", "aws.health.closed", "aws.health.scheduled", "aws.alarm"}
ACTIVITY_KINDS = {"audit", "activity.digest"}
SECRET_KEYS = {"secret", "token", "password", "webhook", "authorization", "cookie"}
ID = re.compile(r"[A-Za-z0-9._:-]{8,160}")


class EventError(ValueError):
    pass


def _iso(value: dt.datetime | str) -> str:
    if isinstance(value, dt.datetime):
        if value.tzinfo is None:
            raise EventError("timezone-aware timestamp required")
        value = value.astimezone(dt.timezone.utc).isoformat()
    try:
        parsed = dt.datetime.fromisoformat(value)
    except (TypeError, ValueError):
        raise EventError("invalid timestamp") from None
    if parsed.tzinfo is None:
        raise EventError("timezone-aware timestamp required")
    return parsed.astimezone(dt.timezone.utc).isoformat()


def canonical(value: dict) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()


def validate(record: dict) -> dict:
    if not isinstance(record, dict) or record.get("schema") != SCHEMA:
        raise EventError("operator event schema required")
    required = {"event_id", "source", "environment", "occurred_at", "received_at", "severity", "channel", "payload"}
    if required - record.keys() or not ID.fullmatch(str(record.get("event_id", ""))):
        raise EventError("required event fields missing")
    if record["environment"] not in ENVIRONMENTS or record["channel"] not in CHANNELS:
        raise EventError("unknown environment or channel")
    payload = record["payload"]
    if not isinstance(payload, dict) or not isinstance(payload.get("kind"), str):
        raise EventError("payload kind required")
    allowed = DEVELOPMENT_KINDS if record["channel"] == "development" else ACTIVITY_KINDS
    if payload["kind"] not in allowed:
        raise EventError("event kind is not allowed on channel")
    def inspect(value):
        if isinstance(value, dict):
            for key, item in value.items():
                if str(key).lower() in SECRET_KEYS:
                    raise EventError("secret-bearing field rejected")
                inspect(item)
        elif isinstance(value, list):
            for item in value: inspect(item)
        elif isinstance(value, str) and "hooks.slack.com/services/" in value:
            raise EventError("secret-bearing value rejected")
    inspect(payload)
    result = copy.deepcopy(record)
    result["occurred_at"] = _iso(result["occurred_at"])
    result["received_at"] = _iso(result["received_at"])
    return result


def make_event(*, source: str, environment: str, severity: str, channel: str,
               occurred_at: dt.datetime, payload: dict, event_id: str | None = None) -> dict:
    received = dt.datetime.now(dt.timezone.utc)
    if event_id is None:
        basis = canonical({"source": source, "environment": environment, "at": _iso(occurred_at), "payload": payload})
        event_id = hashlib.sha256(basis).hexdigest()
    return validate({"schema": SCHEMA, "event_id": event_id, "source": source,
                     "environment": environment, "occurred_at": _iso(occurred_at),
                     "received_at": _iso(received), "severity": severity,
                     "channel": channel, "payload": payload})


def escape(value: object) -> str:
    return str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def render(record: dict) -> str:
    record = validate(record); p = record["payload"]
    if p["kind"] == "activity.digest":
        text = str(p["text"])
        if len(text) > 3000: raise EventError("rendered digest exceeds Slack text limit")
        return text
    status = p["kind"].replace(".", " / ")
    target = escape(p.get("target", p.get("release_id", p.get("service", "-"))))
    text = f"[{record['severity'].upper()}] {record['environment']} · {status}\n대상: {target}\n발생: {record['occurred_at']}\nID: {record['event_id']}"
    if p.get("status") is not None: text += "\n상태: " + escape(p["status"])
    if p.get("scheduled_at") is not None: text += "\n예정: " + escape(p["scheduled_at"])
    if len(text) > 3000: raise EventError("rendered event exceeds Slack text limit")
    return text
