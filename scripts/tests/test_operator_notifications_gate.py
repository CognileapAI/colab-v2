import datetime as dt, json, threading, tempfile, unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from infra.notifications.delivery import FileStore, process
from infra.notifications.events import make_event
from infra.notifications.http_sender import HttpSender

class Handler(BaseHTTPRequestHandler):
    posts = []
    def do_POST(self):
        body = self.rfile.read(int(self.headers["Content-Length"])); self.posts.append((self.path, json.loads(body)))
        self.send_response(200); self.end_headers(); self.wfile.write(b"ok")
    def log_message(self, *args): pass

class GateTests(unittest.TestCase):
    def test_two_channels_reach_distinct_loopback_receivers(self):
        Handler.posts = []; server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        try:
            base = f"http://127.0.0.1:{server.server_port}"
            sender = HttpSender({"development": base + "/dev", "activity": base + "/activity"}, local_only=True)
            with tempfile.TemporaryDirectory() as tmp:
                store = FileStore(Path(tmp)); now = dt.datetime(2026, 9, 12, tzinfo=dt.timezone.utc)
                records = [
                    make_event(source="gate", environment="dev", severity="critical", channel="development", occurred_at=now, event_id="gate:development:1", payload={"kind":"probe.failed","target":"core"}),
                    make_event(source="gate", environment="dev", severity="info", channel="activity", occurred_at=now, event_id="gate:activity:1", payload={"kind":"activity.digest","text":"CoLAB 일일 보고 · 활동 없음"}),
                ]
                for record in records:
                    store.put(record); self.assertEqual(process(record["event_id"], store, sender, now), "sent")
            self.assertEqual([path for path, _ in Handler.posts], ["/dev", "/activity"])
        finally:
            server.shutdown(); server.server_close()
