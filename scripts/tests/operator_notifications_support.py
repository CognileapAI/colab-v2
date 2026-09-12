"""Black-box fixtures for operator notification command paths."""
from __future__ import annotations

import datetime as dt
import tempfile
from pathlib import Path


def run_case(name: str) -> dict:
    from infra.notifications.delivery import DeliveryUncertain, FileStore, process
    from infra.notifications.events import make_event

    now = dt.datetime(2026, 9, 12, tzinfo=dt.timezone.utc)
    temporary = tempfile.TemporaryDirectory()
    root = Path(temporary.name)
    store = FileStore(root)

    if name.startswith("report_") or name in {"digest_completeness", "long_digest"}:
        from infra.notifications.archive import Archive
        from infra.notifications.digest import build
        archive = Archive(root / "archive")
        manifest={"schema":"colab.operator-manifest/1","environment":"dev","usage":"live",
                  "coverage_started_at":"2026-09-01T00:00:00+00:00",
                  "test_exclusions":{"lab_ids":["test-lab"],"account_ids":["test-actor"],
                                     "effective_at":"2026-09-01T00:00:00+00:00"},
                  "sources":["d2","d3","d5","d6","d8"],
                  "collection":{"status":"complete","labs":[{"id":"live-lab","name":"live-lab"}],
                    "sources":[{"lab_id":"live-lab","source":s,"status":"complete","pending":0} for s in ("d2","d3","d5","d6","d8")],
                    "collected_at":"2026-09-12T00:00:00+00:00"}}
        if name == "report_then_old_timestamp_commit":
            first=build("2026-09-11",manifest,archive)
            from infra.notifications import jobs
            jobs.publish(first,manifest,archive,store)
            for index,event_id in enumerate(store.due(now)):
                process(event_id,store,lambda *args:(200,"ok",0),now+dt.timedelta(seconds=index*2))
            jobs.reconcile(archive,store)
            archive.accept({"source_id":"late-source","lab_id":"live-lab","actor_id":"actor",
                            "target_id":"dataset","action":"dataset.updated","before":{},"after":{"name":"new"},
                            "occurred_at":"2026-09-11T02:00:00+00:00"})
            second=build("2026-09-11",manifest,archive)
            messages=first+second
            return {"report_dates":[m["report_date"] for m in messages],"revisions":[m["revision"] for m in messages],
                    "messages":messages}
        if name == "digest_completeness":
            archive.accept({"source_id":"live","lab_id":"live-lab","actor_id":"actor","target_id":"d",
                            "action":"download.ticket_issued","before":None,"after":{},"occurred_at":"2026-09-11T02:00:00+00:00"})
            archive.accept({"source_id":"test","lab_id":"test-lab","actor_id":"test-actor","target_id":"d",
                            "action":"dataset.updated","before":{},"after":{},"occurred_at":"2026-09-11T03:00:00+00:00"})
            complete=build("2026-09-11",manifest,archive)[0]["text"]
            zero=build("2026-09-10",manifest,archive)[0]["text"]
            partial_manifest={**manifest,"collection":{**manifest["collection"],"status":"partial",
                "sources":[{**s,**({"status":"failed"} if s["source"]=="d3" else {})} for s in manifest["collection"]["sources"]]}}
            partial_archive=Archive(root/"partial-archive")
            partial_archive.accept({"source_id":"live","lab_id":"live-lab","actor_id":"actor","target_id":"d",
                            "action":"download.ticket_issued","before":None,"after":{},"occurred_at":"2026-09-11T02:00:00+00:00"})
            partial=build("2026-09-11",partial_manifest,partial_archive)[0]["text"]
            return {"complete":complete,"complete_zero":zero,"partial":partial,"test_actor":"test-actor"}
        for index in range(90):
            archive.accept({"source_id":f"source-{index:03}","lab_id":"live-lab","actor_id":"actor",
                            "target_id":f"target-{index}","action":"dataset.deleted","before":{"name":"<@U123>"+"가"*60},
                            "after":None,"occurred_at":"2026-09-11T03:00:00+00:00"})
        messages=build("2026-09-11",manifest,archive)
        return {"parts":len(messages),"lengths":[len(m["text"]) for m in messages],
                "raw_mentions":sum("<@" in m["text"] for m in messages)}

    def event(*, important=True, channel="development"):
        payload = ({"kind": "probe.failed", "target": "core"} if channel == "development" else
                   {"kind": "audit", "lab_id": "lab", "actor_id": "actor",
                    "target_id": "target", "action": "download", "before": None,
                    "after": {}, "source_id": "source"})
        return make_event(source="test", environment="dev", severity="critical" if important else "info",
                          channel=channel, occurred_at=now, payload=payload,
                          event_id="01KTEST0000000000000000000")

    if name == "important_timeout_then_restart":
        store.put(event())
        attempts = []
        def uncertain(channel, text):
            attempts.append({"event_id": event()["event_id"], "text": text})
            raise DeliveryUncertain()
        process(event()["event_id"], store, uncertain, now)
        store = FileStore(root)
        process(event()["event_id"], store, lambda c, t: (200, "ok", 0), now + dt.timedelta(minutes=1))
        attempts.append({"event_id": event()["event_id"], "text": store.get(event()["event_id"])["rendered"]})
        return {"activity_posts": [], "development_posts": attempts, "deployment_runs": 0}
    if name == "success_then_restart":
        store.put(event()); calls = []
        process(event()["event_id"], store, lambda c, t: (calls.append(t) or (200, "ok", 0)), now + dt.timedelta(seconds=1))
        process(event()["event_id"], FileStore(root), lambda c, t: (calls.append(t) or (200, "ok", 0)), now)
        return {"posts": len(calls), "state": store.get(event()["event_id"])["state"]}
    if name == "retry_responses":
        values = []
        record = event(); store.put(record)
        process(record["event_id"], store, lambda c, t: (429, "slow", 120), now)
        saved = store.get(record["event_id"]); values.append((saved["state"], int((dt.datetime.fromisoformat(saved["next_at"]) - now).total_seconds())))
        later = now + dt.timedelta(seconds=120)
        process(record["event_id"], store, lambda c, t: (503, "down", 0), later)
        saved = store.get(record["event_id"]); values.append((saved["state"], int((dt.datetime.fromisoformat(saved["next_at"]) - later).total_seconds())))
        return {"states": [x[0] for x in values], "retry_after_seconds": [x[1] for x in values]}
    if name == "permanent_rejection":
        store.put(event()); process(event()["event_id"], store, lambda c, t: (400, "bad", 0), now)
        return {"state": store.get(event()["event_id"])["state"]}
    if name == "general_timeout":
        record = event(important=False, channel="activity")
        store.put(record)
        process(record["event_id"], store, lambda c, t: (_ for _ in ()).throw(DeliveryUncertain()), now)
        before = store.get(record["event_id"])["state"]
        store.resolve(record["event_id"], "retry", "operator-1", now)
        saved = store.get(record["event_id"])
        return {"before": before, "after": saved["state"], "actor": saved["resolutions"][-1]["actor"]}
    if name == "invalid_records":
        from infra.notifications.events import EventError, validate
        bad_channel = event(); bad_channel["channel"] = "activity"; bad_channel["payload"]["kind"] = "probe.failed"
        secret = event(); secret["payload"]["webhook"] = "https://hooks.slack.com/services/secret"
        flags = []
        for value in (bad_channel, secret):
            try: validate(value)
            except EventError: flags.append(True)
        record = event(); record["event_id"] = record["event_id"][:-1] + "9"; store.put(record)
        process(record["event_id"], store, lambda c, t: (200, "OK", 0), now)
        return {"wrong_channel": flags[0], "secret": flags[1], "bad_body": store.get(record["event_id"])["state"]}
    if name == "competing_workers":
        store.put(event()); calls = []
        claimed = store.claim(event()["event_id"], now)
        process(event()["event_id"], FileStore(root), lambda c, t: (calls.append(t) or (200, "ok", 0)), now)
        store.finish(event()["event_id"], "retry_wait", now, "fixture-release")
        process(event()["event_id"], store, lambda c, t: (calls.append(t) or (200, "ok", 0)), now + dt.timedelta(seconds=1))
        return {"posts": len(calls), "claimed": bool(claimed)}
    if name == "st_verification_failed_then_delivery_retry":
        from infra.notifications.producers import release_result
        record=release_result("release-1","staging","verify",1,"sha-st",now)
        store.put(record);first=[];process(record["event_id"],store,lambda c,t:(first.append(t) or (503,"down",0)),now)
        later=now+dt.timedelta(minutes=1);second=[]
        process(record["event_id"],store,lambda c,t:(second.append(t) or (200,"ok",0)),later)
        return {"deploy_count":1,"success_messages":[],"failure_event_ids":[record["event_id"]],
                "expected_id":record["event_id"],"received":first+second}
    if name == "aws_issue_without_core_or_database":
        from infra.notifications.aws_events import normalize
        raw={"id":"event-1","account":"123","region":"us-east-1","source":"aws.health",
             "detail-type":"AWS Health Event","time":"2026-09-12T00:00:00+00:00",
             "detail":{"eventArn":"arn:aws:health:event/test","statusCode":"open","service":"RDS"}}
        records=normalize(raw,{"environment":"dev","aws":{"account_id":"123","region":"ap-northeast-2"}})
        return {"development_count":sum(r["channel"]=="development" for r in records),
                "activity_count":sum(r["channel"]=="activity" for r in records),"database_connections":0}
    raise KeyError(name)
