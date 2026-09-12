from __future__ import annotations

import contextlib
import datetime as dt
import fcntl
import hashlib
import json
import os
from pathlib import Path
import uuid

from .events import canonical, render, validate


class DeliveryUncertain(Exception):
    """The request may or may not have reached Slack."""


class EventConflict(ValueError):
    pass


class FileStore:
    def __init__(self, directory: Path):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        os.chmod(self.directory, 0o700)
        self.path = self.directory / "delivery.json"
        self.lock_path = self.directory / "delivery.lock"

    @contextlib.contextmanager
    def _locked(self):
        fd = os.open(self.lock_path, os.O_CREAT | os.O_RDWR, 0o600)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX)
            data = json.loads(self.path.read_text()) if self.path.exists() else {"schema": "colab.operator-store/1", "events": {}, "channels": {}}
            data.setdefault("channels", {})
            yield data
            temp = self.path.with_name(self.path.name + "." + uuid.uuid4().hex + ".tmp")
            out = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(out, "w") as stream:
                json.dump(data, stream, ensure_ascii=False, sort_keys=True); stream.flush(); os.fsync(stream.fileno())
            os.replace(temp, self.path)
            parent = os.open(self.directory, os.O_RDONLY | os.O_DIRECTORY); os.fsync(parent); os.close(parent)
        finally:
            os.close(fd)

    def put(self, record: dict) -> bool:
        record = validate(record)
        identity = {k: v for k, v in record.items() if k != "received_at"}
        digest = hashlib.sha256(canonical(identity)).hexdigest()
        with self._locked() as data:
            current = data["events"].get(record["event_id"])
            if current:
                if current["record_hash"] != digest: raise EventConflict("same event id has different content")
                return False
            data["events"][record["event_id"]] = {"record": record, "record_hash": digest, "state": "pending", "attempt": 0, "resolutions": []}
        return True

    def get(self, event_id: str) -> dict:
        with self._locked() as data: return json.loads(json.dumps(data["events"][event_id]))

    def claim(self, event_id: str, now: dt.datetime):
        with self._locked() as data:
            item = data["events"].get(event_id)
            if not item or item["state"] in {"sent", "held", "uncertain"}: return None
            if item["state"] == "sending":
                if dt.datetime.fromisoformat(item["lease_until"]) > now: return None
                if item["record"]["severity"] not in {"critical", "error"}:
                    item["state"] = "uncertain"; item["reason"] = "lease_expired"; item["unresolved_since"] = now.isoformat(); return None
                item["duplicate_warning"] = True
            if item.get("next_at") and dt.datetime.fromisoformat(item["next_at"]) > now: return None
            channel = item["record"]["channel"]
            payload=item["record"]["payload"]
            if payload.get("report_id") and int(payload.get("part",1))>1:
                for other in data["events"].values():
                    op=other["record"]["payload"]
                    if (op.get("report_id"),op.get("revision"))==(payload["report_id"],payload.get("revision")) and int(op.get("part",1))<int(payload["part"]) and other["state"]!="sent":return None
            channel_state=data["channels"].get(channel)
            if isinstance(channel_state,str): channel_state={"available_at":channel_state}
            if channel_state and dt.datetime.fromisoformat(channel_state["available_at"]) > now:
                return None
            item["state"] = "sending"; item["attempt"] += 1; item["claimed_at"] = now.isoformat()
            item["lease_until"] = (now + dt.timedelta(seconds=30)).isoformat()
            item["claim_token"] = uuid.uuid4().hex
            data["channels"][channel]={"token":item["claim_token"],"available_at":item["lease_until"],"next_send_at":(now+dt.timedelta(seconds=1)).isoformat()}
            return json.loads(json.dumps(item))

    def finish(self, event_id: str, state: str, next_at: dt.datetime | None, reason: str, *, rendered: str | None = None, claim_token: str | None = None):
        with self._locked() as data:
            item = data["events"][event_id]
            if claim_token is not None and item.get("claim_token") != claim_token: return
            owner_token=claim_token or item.get("claim_token")
            if item["state"] == "sent": return
            item["state"] = state; item["reason"] = reason
            item.pop("lease_until", None); item.pop("claim_token", None)
            item["next_at"] = next_at.isoformat() if next_at else None
            if rendered is not None:
                item["rendered"] = rendered
                item["body_hash"] = hashlib.sha256(rendered.encode()).hexdigest()
            channel=item["record"]["channel"];channel_state=data["channels"].get(channel)
            if isinstance(channel_state,dict) and channel_state.get("token")==owner_token:
                data["channels"][channel]={"available_at":channel_state["next_send_at"]}

    def mark_uncertain(self, event_id: str, *, duplicate_warning: bool, claim_token: str | None = None) -> None:
        with self._locked() as data:
            item = data["events"][event_id]
            if claim_token is not None and item.get("claim_token") != claim_token: return
            item["duplicate_warning"] = duplicate_warning

    def due(self, now: dt.datetime) -> list[str]:
        with self._locked() as data:
            rows=[v for v in data["events"].values() if
                          ((v["state"] in {"pending", "retry_wait"} and (not v.get("next_at") or dt.datetime.fromisoformat(v["next_at"]) <= now))
                           or (v["state"] == "sending" and dt.datetime.fromisoformat(v["lease_until"]) <= now))]
            rows.sort(key=lambda v:(v["record"]["payload"].get("report_date",""),int(v["record"]["payload"].get("revision",0)),int(v["record"]["payload"].get("part",0)),v["record"]["event_id"]))
            return [v["record"]["event_id"] for v in rows]

    def unresolved(self, now: dt.datetime) -> list[dict]:
        with self._locked() as data:return [json.loads(json.dumps(v)) for v in data["events"].values() if v["state"] in {"uncertain","held"}]

    def resolve(self, event_id: str, action: str, actor: str, now: dt.datetime):
        if action not in {"confirmed-sent", "retry"}: raise ValueError("unsupported resolution")
        with self._locked() as data:
            item = data["events"][event_id]
            if item["state"] not in {"uncertain", "held"}: raise ValueError("event does not require resolution")
            item["state"] = "sent" if action == "confirmed-sent" else "retry_wait"
            item["next_at"] = None
            if action == "retry": item["duplicate_warning"] = True
            item["resolutions"].append({"action": action, "actor": actor, "at": now.isoformat()})


def process(event_id: str, store: FileStore, sender, now: dt.datetime) -> str:
    claimed = store.claim(event_id, now)
    if claimed is None: return "not_due"
    record = claimed["record"]; text = render(record)
    if claimed.get("duplicate_warning"):
        text = "⚠ 중복 가능 — 이전 전송 결과가 불명확했습니다.\n" + text
    try:
        status, body, retry_after = sender(record["channel"], text)
    except DeliveryUncertain:
        state = "retry_wait" if record["severity"] in {"critical", "error"} else "uncertain"
        next_at = now + dt.timedelta(minutes=1) if state == "retry_wait" else None
        if state == "retry_wait":
            store.mark_uncertain(event_id, duplicate_warning=True, claim_token=claimed.get("claim_token"))
        store.finish(event_id, state, next_at, "delivery_unknown", rendered=text, claim_token=claimed.get("claim_token")); return state
    except Exception:
        delay = (60, 300, 900, 3600)[min(claimed["attempt"] - 1, 3)]
        store.finish(event_id, "retry_wait", now + dt.timedelta(seconds=delay), "transport_error", rendered=text, claim_token=claimed.get("claim_token")); return "retry_wait"
    if status == 200 and body == "ok":
        store.finish(event_id, "sent", None, "accepted", rendered=text, claim_token=claimed.get("claim_token")); return "sent"
    if status == 429 or 500 <= status < 600 or (status == 200 and body != "ok"):
        delay = (60, 300, 900, 3600)[min(claimed["attempt"] - 1, 3)]
        if retry_after: delay = max(delay, int(retry_after))
        store.finish(event_id, "retry_wait", now + dt.timedelta(seconds=delay), f"http_{status}", rendered=text, claim_token=claimed.get("claim_token")); return "retry_wait"
    store.finish(event_id, "held", None, f"http_{status}", rendered=text, claim_token=claimed.get("claim_token")); return "held"
