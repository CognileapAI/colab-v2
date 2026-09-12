"""Read-only screenshots and computed-style measurements of the current browser page."""
import argparse, json, subprocess, pathlib, datetime
ROOT=pathlib.Path(__file__).resolve().parents[4]
OUT=pathlib.Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('name');p.add_argument('--url');p.add_argument('--width',type=int,default=1440);p.add_argument('--height',type=int,default=1000);p.add_argument('--dark',action='store_true');p.add_argument('--session',default='design-20260912');a=p.parse_args()
def ab(*args,stdin=None):
    r=subprocess.run(['python3',str(ROOT/'scripts/agent-bridge.py'),'run-tool','browser','--','--session',a.session,*args],input=stdin,text=True,capture_output=True,cwd=ROOT,timeout=50)
    if r.returncode: raise RuntimeError(f'{args[0]} failed: {r.stderr[:240]} {r.stdout[:240]}')
    return r.stdout
ab('set','viewport',str(a.width),str(a.height));ab('set','media','dark' if a.dark else 'light')
if a.url: ab('open',a.url)
try: ab('wait','--load','networkidle')
except RuntimeError: pass
folder=OUT/'live';folder.mkdir(exist_ok=True)
prefix=folder/a.name
ab('screenshot',str(prefix)+'.png','--full')
for kind,script in [('visual',ROOT/'.claude/skills/design-review/scripts/live_probe.js'),('layout',OUT/'layout_probe.js')]:
    result=ab('eval','--stdin','--json',stdin=script.read_text())
    pathlib.Path(str(prefix)+f'.{kind}.json').write_text(result)
snapshot=ab('snapshot','-i');pathlib.Path(str(prefix)+'.snapshot.txt').write_text(snapshot)
d=json.loads(pathlib.Path(str(prefix)+'.layout.json').read_text())['data']['result']
v=json.loads(pathlib.Path(str(prefix)+'.visual.json').read_text())['data']['result']
record={'name':a.name,'time':datetime.datetime.now(datetime.timezone.utc).isoformat(),'url':d['url'],'viewport':d['viewport'],'screen':d.get('screen'),'document':d['document'],'counts':v['counts'],'screenshot':str(prefix.relative_to(ROOT))+'.png'}
with (OUT/'live-manifest.jsonl').open('a') as f:f.write(json.dumps(record,ensure_ascii=False)+'\n')
print(json.dumps(record,ensure_ascii=False))
