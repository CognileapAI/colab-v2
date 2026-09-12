import json, pathlib, subprocess, concurrent.futures
ROOT=pathlib.Path(__file__).resolve().parents[5]
OUT=pathlib.Path(__file__).resolve().parent
OUT.joinpath('screens').mkdir(exist_ok=True)
def ab(session,*args,stdin=None):
    r=subprocess.run(['python3',str(ROOT/'scripts/agent-bridge.py'),'run-tool','browser','--','--session',session,*args],cwd=ROOT,input=stdin,text=True,capture_output=True,timeout=60)
    if r.returncode: raise RuntimeError(r.stderr+r.stdout)
    return r.stdout
probe=(ROOT/'.claude/skills/design-review/scripts/live_probe.js').read_text()
extra="""(() => ({theme:document.body.dataset.theme,bg:getComputedStyle(document.body).backgroundColor,font:getComputedStyle(document.body).fontFamily,fonts:[...document.fonts].filter(f=>f.status==='loaded').map(f=>f.family),width:innerWidth,scrollWidth:document.documentElement.scrollWidth,inputs:[...document.querySelectorAll('input,select,textarea')].map(e=>({size:getComputedStyle(e).fontSize,color:getComputedStyle(e).color,bg:getComputedStyle(e).backgroundColor})),dialog:(()=>{const e=document.querySelector('[role=dialog]');if(!e)return null;const r=e.getBoundingClientRect();return {left:r.left,right:r.right,bottom:r.bottom,scroll:e.scrollWidth,width:e.clientWidth}})() }))()"""
def capture(theme):
    session='consistency-'+theme
    results=[]
    for scene in ['catalog','lab','empty','project-dialog']:
        for width in [375,768,1440]:
            name=f'{scene}-{theme}-{width}'
            url=f'http://127.0.0.1:5178/audit-design.html?theme={theme}&scene={scene}&design=calm'
            ab(session,'set','viewport',str(width),'900')
            ab(session,'open',url)
            ab(session,'wait','--load','networkidle')
            ab(session,'eval','document.fonts.ready.then(() => true)')
            shot=['screenshot',str(OUT/'screens'/f'{name}.png')]
            if scene!='project-dialog':shot.append('--full')
            ab(session,*shot)
            v=json.loads(ab(session,'eval','--stdin','--json',stdin=probe))['data']['result']
            x=json.loads(ab(session,'eval','--stdin','--json',stdin=extra))['data']['result']
            errors=ab(session,'errors')
            result={'name':name,'visual':v,'layout':x,'errors':errors,'screenshot':f'screens/{name}.png'}
            (OUT/'screens'/f'{name}.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
            results.append(result)
            print(name,v['counts']['small'],v['counts']['lowContrast'],x['scrollWidth'],flush=True)
    return results
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
    results=sum(list(pool.map(capture,['light','dark'])),[])
(OUT/'scenes.json').write_text(json.dumps(results,ensure_ascii=False,indent=2))
assert len(results)==24
assert all(r['visual']['counts']['small']==0 and r['visual']['counts']['lowContrast']==0 and r['layout']['scrollWidth']<=r['layout']['width'] for r in results)
assert all(r['layout']['theme'] in ['light','dark'] and r['layout']['fonts'] for r in results)
print('24 scenes passed')
