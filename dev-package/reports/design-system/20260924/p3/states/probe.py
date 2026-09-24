"""Scratch P3 probe: sites the 196 captures do not reach. Builds the same DOM shape against the
before-build CSS (old inline styles) and the after-build CSS (new variables/classes) in agent-browser
and compares computed values in light and dark."""
import json, pathlib, re, sys, subprocess, time
sys.path.insert(0, str(pathlib.Path('scripts/visual-baseline').resolve()))
import capture as C

OLD = {
  'tile': '<div class="pv-mosaic" style="position:relative;width:300px;height:300px"><img id="t" class="pv-tile-piece" alt="" style="position:absolute;left:10px;top:20px;width:30px;height:40px"></div>',
  'uplayers': '<div class="pv-layers" id="t" data-zoom-scale="2" style="transform:translate(5px, 6px) scale(2);transform-origin:0 0;width:100px;height:80px"></div>',
  'plainlayers': '<div class="pv-layers" id="t" style="width:100px;height:80px"></div>',
  'dslayers': '<div class="pv-viewport" style="width:300px;height:225px;overflow:hidden"><div class="pv-layers" id="t" data-zoom-scale="1.5" data-zoom-max-scale="8" data-zoom-base-scale="1" style="transform:translate(-40px, -12.5px) scale(1.5);transform-origin:0 0"></div></div>',
  'dereq': '<div class="detail-page"><div class="dt-edit"><span class="de-req" id="t">필수</span></div></div>',
  'vswon': '<div class="search-page"><button class="vfilter on"><span class="vsw" id="t"></span></button></div>',
  'reg': '<div class="card-b"><div id="t" style="margin-top:16px">x</div></div>',
  'relbar': '<div class="search-page"><div class="relbar"><span id="t" style="width:42%"></span></div></div>',
  'bar': '<span class="dash-bar-track" style="display:block;width:200px"><span id="t" class="dash-bar-fill" style="width:25%"></span></span>',
  'swatch': '<span class="pv-swatch" id="t" style="background:#21918c"></span>',
}
NEW = {
  'tile': '<div class="pv-mosaic" style="position:relative;width:300px;height:300px"><img id="t" class="pv-tile-piece" alt="" style="--pv-piece-left:10px;--pv-piece-top:20px;--pv-piece-w:30px;--pv-piece-h:40px"></div>',
  'uplayers': '<div class="pv-layers" id="t" data-zoom-scale="2" style="--pv-layers-transform:translate(5px, 6px) scale(2);width:100px;height:80px"></div>',
  'plainlayers': OLD['plainlayers'],
  'dslayers': '<div class="pv-viewport" style="width:300px;height:225px;overflow:hidden"><div class="pv-layers" id="t" data-zoom-scale="1.5" data-zoom-max-scale="8" data-zoom-base-scale="1" style="--pv-layers-transform:translate(-40px, -12.5px) scale(1.5)"></div></div>',
  'dereq': OLD['dereq'],
  'vswon': OLD['vswon'],
  'reg': '<div class="card-b"><div id="t" class="reg-source-block">x</div></div>',
  'relbar': '<div class="search-page"><div class="relbar"><span id="t" style="--hit-relbar-w:42%"></span></div></div>',
  'bar': '<span class="dash-bar-track" style="display:block;width:200px"><span id="t" class="dash-bar-fill" style="--dash-bar-w:25%"></span></span>',
  'swatch': '<span class="pv-swatch" id="t" style="--pv-swatch-bg:#21918c"></span>',
}
PROPS = ['position', 'left', 'top', 'width', 'height', 'transform', 'transform-origin', 'margin-top', 'color', 'background-color']

def run(dist, markup, session):
    port = C.free_port()
    srv = subprocess.Popen([sys.executable, '-m', 'http.server', str(port), '--bind', '127.0.0.1', '--directory', str(dist)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1.5)
    try:
        return _run(dist, markup, session, port)
    finally:
        srv.terminate()

def _run(dist, markup, session, port):
    css = re.search(r'assets/graphFixture-[\w-]+\.css', (dist / 'audit-design.html').read_text()).group(0)
    out = {}
    for theme in ['light', 'dark']:
        for name, html in markup.items():
            page = dist / f'p3-probe-{name}-{theme}.html'
            page.write_text(f'<!doctype html><html data-theme="{theme}"><head><meta charset="utf-8"><link rel="stylesheet" href="{css}"></head><body>{html}</body></html>')
            C.ab(session, 'open', f'http://127.0.0.1:{port}/{page.name}')
            print('opened', session, page.name, flush=True)
            src = "(() => { const e = document.getElementById('t'); const r = {}; for (const p of %s) r[p] = getComputedStyle(e).getPropertyValue(p); const a = getComputedStyle(e, '::after'); r['after-bg'] = a.backgroundColor; return r; })()" % json.dumps(PROPS)
            out[f'{name}-{theme}'] = C.js(session, src)
    return out

C.BROWSER_ARGS[:] = json.loads(C.MANIFEST.read_text()).get('browser', {}).get('args', [])
before = run(pathlib.Path('.visual/p3-dist-before').resolve(), OLD, 'p3probe-b')
after = run(pathlib.Path('.visual/p3-dist-after2').resolve(), NEW, 'p3probe-a')
for s in ['p3probe-b', 'p3probe-a']:
    try: C.ab(s, 'close', timeout=30)
    except Exception: pass
bad = 0
for k in before:
    diffs = {p: (before[k][p], after[k][p]) for p in before[k] if before[k][p] != after[k][p]}
    if diffs: bad += 1
    keyvals = {p: after[k][p] for p in ('position', 'left', 'top', 'width', 'height', 'transform', 'transform-origin', 'margin-top', 'color', 'background-color', 'after-bg')}
    print(k, 'SAME' if not diffs else f'DIFF {diffs}', json.dumps(keyvals, ensure_ascii=False))
json.dump({'before': before, 'after': after}, open('.visual/scratch/probe.json', 'w'), ensure_ascii=False, indent=1)
print('cases', len(before), 'diff', bad)
sys.exit(1 if bad else 0)
