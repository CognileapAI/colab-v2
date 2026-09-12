import json,pathlib,subprocess
ROOT=pathlib.Path(__file__).resolve().parents[5];OUT=pathlib.Path(__file__).resolve().parent
records=[]
def ab(*args,stdin=None):
 r=subprocess.run(['python3',str(ROOT/'scripts/agent-bridge.py'),'run-tool','browser','--','--session','consistency-check',*args],cwd=ROOT,text=True,input=stdin,capture_output=True,timeout=50)
 if r.returncode:raise RuntimeError(r.stdout+r.stderr)
 return r.stdout
def evaluate(js):return json.loads(ab('eval','--stdin','--json',stdin=js))['data']['result']
def evidence(name):
 p=evaluate((ROOT/'.claude/skills/design-review/scripts/live_probe.js').read_text());(OUT/(name+'.json')).write_text(json.dumps(p,ensure_ascii=False,indent=2));ab('screenshot',str(OUT/(name+'.png')));assert p['counts']['small']==0 and p['counts']['lowContrast']==0
ab('set','viewport','375','900')
ab('open','http://127.0.0.1:5178/audit-design.html?theme=dark&scene=catalog&design=calm')
ab('wait','--load','networkidle')
assert evaluate('document.querySelectorAll("tbody tr").length')==6
ab('click','th[data-col="주제"] button')
evidence('filter-open-dark-375')
ab('find','first','[role="menuitemcheckbox"]','click')
ab('wait','--fn','document.querySelectorAll("tbody tr").length === 3')
r=evaluate('({rows:document.querySelectorAll("tbody tr").length,count:document.querySelector(".hcnt").textContent,menu:document.querySelector("[role=menu]").getBoundingClientRect().toJSON(),viewport:innerWidth})');assert r['rows']==3 and r['menu']['left']>=0 and r['menu']['right']<=r['viewport'];records.append({'filter':r});evidence('filter-selected-dark-375')
ab('open','http://127.0.0.1:5178/audit-design.html?theme=dark&scene=projects&design=calm')
ab('find','role','button','click','--name','+ 새 프로젝트')
ab('find','role','button','click','--name','만들기')
assert '이름을 적어 주세요' in evaluate('document.querySelector("[role=alert]").textContent')
ab('press','Tab');assert evaluate('document.activeElement.getAttribute("aria-label")')=='창 닫기'
ab('press','Shift+Tab');assert evaluate('document.activeElement.textContent')=='만들기'
ab('find','role','button','click','--name','논문','--exact')
assert evaluate('[...document.querySelectorAll(".pj-seg button")].find(e=>e.textContent==="논문").getAttribute("aria-pressed")')=='true'
ab('find','label','연결 주소','fill','검토용 논문 번호')
r=evaluate('({value:document.activeElement.value,rect:document.activeElement.getBoundingClientRect().toJSON(),body:document.querySelector(".pj-modal-b").getBoundingClientRect().toJSON(),footer:document.querySelector(".pj-modal-f").getBoundingClientRect().toJSON(),viewport:innerHeight})');assert r['value']=='검토용 논문 번호' and r['rect']['bottom']<=r['body']['bottom']+1 and r['footer']['bottom']<=r['viewport'];records.append({'lastInputAndFooter':r});evidence('modal-validation-dark-375')
ab('press','Escape');r=evaluate('({dialogs:document.querySelectorAll("[role=dialog]").length,active:document.activeElement.textContent})');assert r=={'dialogs':0,'active':'+ 새 프로젝트'};records.append({'keyboard':'Tab/Shift+Tab cycle; type selection; Escape restore passed','restored':r})
ab('open','http://127.0.0.1:5178/design-preview.html')
ab('select','#scene','empty');ab('select','#theme','dark');ab('select','#width','375')
r=evaluate('({src:document.querySelector("iframe").getAttribute("src"),width:document.querySelector("iframe").style.width})');assert 'scene=empty' in r['src'] and 'theme=dark' in r['src'] and r['width']=='375px';records.append({'reviewControls':r})
ab('select','#design','before');assert evaluate('document.getElementById("theme").disabled') is True
(OUT/'interactions.json').write_text(json.dumps(records,ensure_ascii=False,indent=2));print(json.dumps(records,ensure_ascii=False))
