#!/usr/bin/env python3
"""Scratch: computed-style dump of every element in every scene (P2a before/after equivalence).
usage: python3 .visual/p2a-probe/cdump.py <distDir> <out.json> [--only scene,..] [--detail keysfile]
"""
import json, pathlib, subprocess, sys, time, urllib.request, os, signal, concurrent.futures
sys.path.insert(0, str(pathlib.Path('scripts/visual-baseline').resolve()))
import capture as C

DUMP_JS = r"""(() => {
  const fnv = (s) => { let h = 2166136261; for (let i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 16777619); } return (h >>> 0).toString(36); };
  const all = [document.documentElement, ...document.querySelectorAll('html *')];
  const out = [];
  const DETAIL = __DETAIL__;
  const detail = {};
  all.forEach((el, i) => {
    const key = i + ':' + el.tagName + '.' + (typeof el.className === 'string' ? el.className.trim().replace(/\s+/g, '.') : '');
    for (const pe of [null, '::before', '::after', '::placeholder', '::marker']) {
      if (pe === '::placeholder' && !(el.tagName === 'INPUT' || el.tagName === 'TEXTAREA')) continue;
      if (pe === '::marker' && getComputedStyle(el).display !== 'list-item') continue;
      const cs = getComputedStyle(el, pe);
      if (pe && (pe === '::before' || pe === '::after') && cs.content === 'none') continue;
      const parts = [];
      for (let k = 0; k < cs.length; k++) { const p = cs[k]; parts.push(p + ':' + cs.getPropertyValue(p)); }
      parts.sort();
      const s = parts.join(';');
      const kk = key + (pe || '');
      out.push(kk + '=' + fnv(s));
      if (DETAIL.includes(kk)) detail[kk] = parts;
    }
  });
  return {n: out.length, h: out, detail};
})()"""


def start(dist, port):
    vite = C.FRONTEND / 'node_modules' / '.bin' / 'vite'
    proc = subprocess.Popen([str(vite), 'preview', '--config', 'audit.vite.config.ts', '--outDir', str(dist), '--host', '127.0.0.1', '--port', str(port), '--strictPort'],
                            cwd=C.FRONTEND, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
    for _ in range(100):
        try:
            with urllib.request.urlopen(f'http://127.0.0.1:{port}/audit-design.html', timeout=2) as r:
                if r.status == 200: return proc
        except Exception:
            time.sleep(0.3)
    raise SystemExit('preview did not start')


def run_theme(theme, scenes, port, session, height, dpr, blank, detail):
    res = {}
    C.ab(session, 'set', 'media', theme)
    for scene in scenes:
        if theme not in scene['themes']: continue
        for width in scene['widths']:
            name = f'{scene["name"]}-{theme}-{width}'
            C.ab(session, 'set', 'viewport', str(width), str(height), str(dpr))
            C.ab(session, 'open', f'http://127.0.0.1:{port}/{blank}')
            C.ab(session, 'storage', 'local', 'clear')
            C.ab(session, 'storage', 'session', 'clear')
            C.ab(session, 'open', C.url_for(port, scene, theme))
            C.ab(session, 'wait', '--load', 'networkidle')
            C.js(session, 'document.fonts.ready.then(() => true)')
            C.js(session, f"(() => {{ const s = document.createElement('style'); s.textContent = {json.dumps(C.FREEZE_CSS)}; document.head.appendChild(s); return true; }})()")
            for action in scene['actions']:
                C.run_action(session, action)
            C.ab(session, 'wait', str(int(scene['settleMs'])))
            res[name] = C.js(session, DUMP_JS.replace('__DETAIL__', json.dumps(detail.get(name, []))))
            print(name, res[name]['n'], flush=True)
    return res


def main():
    dist = pathlib.Path(sys.argv[1]).resolve(); out = pathlib.Path(sys.argv[2])
    only = None; detail = {}
    if '--only' in sys.argv: only = set(sys.argv[sys.argv.index('--only') + 1].split(','))
    if '--detail' in sys.argv: detail = json.loads(pathlib.Path(sys.argv[sys.argv.index('--detail') + 1]).read_text())
    manifest = json.loads(C.MANIFEST.read_text())
    C.BROWSER_ARGS[:] = manifest.get('browser', {}).get('args', [])
    scenes = [s for s in manifest['scenes'] if not only or s['name'] in only]
    if detail:
        scenes = [s for s in scenes if any(k.startswith(s['name'] + '-') for k in detail)]
    blank = sorted(dist.glob('assets/audit-tile-*.svg'))[-1].relative_to(dist).as_posix()
    port = C.free_port(); proc = start(dist, port)
    run_id = f'{os.getpid()}'
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            fs = [pool.submit(run_theme, t, scenes, port, f'cd-{t}-{run_id}', int(manifest['viewport']['height']), int(manifest['viewport']['deviceScaleFactor']), blank, detail) for t in ['light', 'dark']]
            res = {}
            for f in fs: res.update(f.result())
    finally:
        for t in ['light', 'dark']:
            try: C.ab(f'cd-{t}-{run_id}', 'close', timeout=30)
            except Exception: pass
        C.stop_preview(proc)
    out.write_text(json.dumps(res))
    print('pages', len(res))

if __name__ == "__main__":
    main()
