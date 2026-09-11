#!/usr/bin/env python3
import importlib.util, json, stat, tempfile
from pathlib import Path
from unittest.mock import patch

root = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('alarm_runner', root/'infra/ops/alarm_runner.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)

class Response:
    def __init__(self, body=b'ok', status=200): self.body, self.status = body, status
    def read(self): return self.body
    def __enter__(self): return self
    def __exit__(self, *args): return False

def event():
    return {'schema':'colab.ops.v1','timestamp':'2026-09-11T00:00:00Z','level':'ERROR',
            'event':'alarm.raised','service':'ops-alarm','target':'acceptance-deploy-verification',
            'failure_count':3,'probe_stdout':'SECRET','url':'https://secret.invalid'}

sent=[]
def open_ok(req, timeout=0): sent.append((req.full_url, json.loads(req.data))); return Response()
with patch.object(m.urllib.request, 'urlopen', open_ok):
    m._notify('https://hooks.slack.com/services/T/B/X', event())
assert set(sent[-1][1]) == {'text'}
text=sent[-1][1]['text']
for value in ('acceptance-deploy-verification','alarm.raised','3','2026-09-11T00:00:00Z','시험'):
    assert value in text
assert 'SECRET' not in text and 'secret.invalid' not in text

sent.clear()
with patch.object(m.urllib.request, 'urlopen', open_ok):
    m._notify('https://hooks.slack.com.evil.invalid/hook', event())
assert sent[-1][1] == event()

with patch.object(m.urllib.request, 'urlopen', lambda *a, **k: Response(b'not ok', 200)):
    try: m._notify('https://hooks.slack.com/services/T/B/X', event())
    except RuntimeError: pass
    else: raise AssertionError('Slack 2xx body not-ok accepted')

with tempfile.TemporaryDirectory() as raw:
    d=Path(raw); state=d/'state.json'; hook=d/'hook'; hook.write_text('https://hooks.slack.com/services/T/B/X\n'); hook.chmod(stat.S_IRUSR|stat.S_IWUSR)
    responses=iter([Response(b'bad'), Response(b'ok')])
    with patch.object(m.urllib.request, 'urlopen', lambda *a, **k: next(responses)):
        rc1=m.main(['--state',str(state),'--target','health','--threshold','1','--webhook-file',str(hook),'--','/bin/false'])
        assert rc1 == 1 and not state.exists()
        rc2=m.main(['--state',str(state),'--target','health','--threshold','1','--webhook-file',str(hook),'--','/bin/false'])
        assert rc2 == 1 and json.loads(state.read_text())['targets']['health']['active'] is True
print('ops-alarm-notify-selftest green')
