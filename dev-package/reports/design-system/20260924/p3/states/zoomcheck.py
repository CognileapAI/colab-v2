"""Scratch P3: preview-done scene, base state and after one zoom-in click — preview-layers attributes and
computed transform, on the before build and the after2 build."""
import json, pathlib, sys
sys.path.insert(0, str(pathlib.Path('scripts/visual-baseline').resolve()))
sys.path.insert(0, str(pathlib.Path('.visual/scratch').resolve()))
import capture as C
import cdump_p3 as D

READ = """(() => { const e = document.querySelector('[data-testid=preview-layers]'); if (!e) return null;
  const cs = getComputedStyle(e); return { zoom: e.getAttribute('data-zoom-scale'), inline: e.getAttribute('style'),
  transform: cs.transform, origin: cs.transformOrigin, rect: JSON.stringify(e.getBoundingClientRect()) }; })()"""

manifest = json.loads(C.MANIFEST.read_text())
C.BROWSER_ARGS[:] = manifest.get('browser', {}).get('args', [])
scene = next(s for s in manifest['scenes'] if s['name'] == 'preview-done')
out = {}
for label, dist in [('before', '.visual/p3-dist-before'), ('after', '.visual/p3-dist-after2')]:
    dist = pathlib.Path(dist).resolve()
    port = C.free_port(); proc = D.start(dist, port); sess = f'p3zoom-{label}'
    try:
        for theme in ['light', 'dark']:
            C.ab(sess, 'set', 'media', theme)
            C.ab(sess, 'set', 'viewport', '1440', '900', '1')
            C.ab(sess, 'open', C.url_for(port, scene, theme))
            C.ab(sess, 'wait', '--load', 'networkidle')
            C.ab(sess, 'wait', '800')
            base = C.js(sess, READ)
            C.js(sess, "(() => { const b = [...document.querySelectorAll('button')].find(x => x.getAttribute('aria-label') === '확대' || x.textContent.trim() === '확대'); if (b) b.click(); return !!b; })()")
            C.ab(sess, 'wait', '500')
            zoomed = C.js(sess, READ)
            out[f'{label}-{theme}'] = {'base': base, 'zoomed': zoomed}
    finally:
        try: C.ab(sess, 'close', timeout=30)
        except Exception: pass
        C.stop_preview(proc)
for k, v in out.items():
    print(k, json.dumps(v, ensure_ascii=False))
same = all(out[f'before-{t}'][s][f] == out[f'after-{t}'][s][f] for t in ['light', 'dark'] for s in ['base', 'zoomed'] for f in ['zoom', 'transform', 'origin', 'rect'])
json.dump(out, open('.visual/scratch/zoomcheck.json', 'w'), ensure_ascii=False, indent=1)
print('computed same', same)
