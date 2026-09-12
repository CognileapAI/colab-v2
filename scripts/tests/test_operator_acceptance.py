import datetime as dt
from pathlib import Path
import tempfile
import unittest
from infra.notifications.archive import Archive
from infra.notifications.digest import build
from infra.notifications.jobs import run

MANIFEST = {"schema":"colab.operator-manifest/1","environment":"dev","usage":"live",
 "channels":{"development":"development-secret-ref","activity":"activity-secret-ref"},
 "coverage_started_at":"2026-09-08T00:00:00+09:00",
 "test_exclusions":{"lab_ids":[],"account_ids":[],"effective_at":"2026-09-08T00:00:00+09:00"},
 "sources":["d2","d3","d5","d6","d8"],"probes":["service"],"lab_ids":["lab-live"]}

def row(source, occurred, target, before=None):
 return {"source_id":source,"lab_id":"lab-live","actor_id":"actor-live","target_id":target,
         "action":"dataset.deleted","occurred_at":occurred,"before":before,"after":None}

class DigestAcceptance(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
  self.archive=Archive(Path(self.tmp.name))
 def test_kst_half_open_day(self):
  self.archive.accept(row("source-before","2026-09-11T14:59:59+00:00","outside-before"))
  self.archive.accept(row("source-start","2026-09-11T15:00:00+00:00","included-at-start"))
  self.archive.accept(row("source-last","2026-09-12T14:59:59+00:00","included-at-end"))
  self.archive.accept(row("source-after","2026-09-12T15:00:00+00:00","outside-after"))
  body="\n".join(p["text"] for p in build("2026-09-12",MANIFEST,self.archive))
  self.assertIn("included-at-start",body);self.assertIn("included-at-end",body)
  self.assertNotIn("outside-before",body);self.assertNotIn("outside-after",body)
 def test_long_audit_detail_is_not_truncated(self):
  self.archive.accept(row("source-long","2026-09-12T02:00:00+00:00","long-target",{"label":"Q"*6500+"TAIL_SENTINEL"}))
  parts=build("2026-09-12",MANIFEST,self.archive)
  self.assertTrue(parts)
  self.assertTrue(all(len(p["text"])<=3000 for p in parts))
  body="\n".join(p["text"] for p in parts)
  self.assertEqual(body.count("Q"),6500)
  self.assertIn("TAIL_SENTINEL",body)
  self.assertEqual([p["part"] for p in parts],list(range(1,len(parts)+1)))
  self.assertTrue(all(p["total"]==len(parts) for p in parts))
 def test_catchup_includes_empty_missing_dates(self):
  parts=run(dt.datetime(2026,9,12,0,0,tzinfo=dt.timezone.utc),MANIFEST,self.archive)
  self.assertEqual(sorted(set(p["report_date"] for p in parts)),["2026-09-08","2026-09-09","2026-09-10","2026-09-11"])
 def test_first_partial_day_is_labeled(self):
  manifest=dict(MANIFEST,coverage_started_at="2026-09-12T12:00:00+09:00")
  parts=build("2026-09-12",manifest,self.archive)
  self.assertIn("수집 시작", "\n".join(p["text"] for p in parts))



"""Independent behavioral checks of the approved delivery decisions."""
import datetime as dt
from pathlib import Path
import tempfile
import unittest
from infra.notifications.events import make_event
from infra.notifications.delivery import FileStore, process, DeliveryUncertain

NOW = dt.datetime(2026, 9, 12, tzinfo=dt.timezone.utc)

def event(severity="info", suffix="one"):
    return make_event(source="deploy", environment="dev", severity=severity,
                      channel="development", occurred_at=NOW,
                      event_id="release-acceptance-" + suffix,
                      payload={"kind": "deploy.failed" if severity == "error" else "deploy.succeeded",
                               "release_id": "acceptance-release"})

class DeliveryAcceptance(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.store = FileStore(Path(self.tmp.name))

    def test_source_replay_ignores_new_receipt_timestamp(self):
        first = event()
        self.store.put(first)
        replay = dict(first, received_at=(NOW + dt.timedelta(hours=2)).isoformat())
        self.assertFalse(self.store.put(replay))
        self.assertEqual(self.store.get(first["event_id"])["state"], "pending")

    def test_manual_retry_labels_general_uncertainty(self):
        record = event(); self.store.put(record)
        def timeout(channel, text):
            raise DeliveryUncertain()
        self.assertEqual(process(record["event_id"], self.store, timeout, NOW), "uncertain")
        self.store.resolve(record["event_id"], "retry", "operator-acceptance", NOW)
        received = []
        def sender(channel, text):
            received.append(text); return 200, "ok", None
        self.assertEqual(process(record["event_id"], self.store, sender, NOW + dt.timedelta(minutes=2)), "sent")
        self.assertIn("중복 가능", received[0])

    def test_known_server_failure_does_not_claim_unknown_receipt(self):
        record = event("error"); self.store.put(record)
        process(record["event_id"], self.store, lambda c,t:(503,"unavailable",None), NOW)
        received = []
        def sender(channel, text):
            received.append(text); return 200, "ok", None
        process(record["event_id"], self.store, sender, NOW + dt.timedelta(minutes=2))
        self.assertEqual(len(received), 1)
        self.assertNotIn("전송 결과가 불명확", received[0])

    def test_transient_transport_failures_backoff_after_first_attempt(self):
        record = event(); self.store.put(record)
        def failed_connect(channel, text):
            raise ConnectionRefusedError()
        process(record["event_id"], self.store, failed_connect, NOW)
        later = NOW + dt.timedelta(minutes=1)
        process(record["event_id"], self.store, failed_connect, later)
        actual = dt.datetime.fromisoformat(self.store.get(record["event_id"])["next_at"])
        self.assertGreaterEqual(actual, later + dt.timedelta(minutes=5))

if __name__ == "__main__":
    unittest.main(verbosity=2)
