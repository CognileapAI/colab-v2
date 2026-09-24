#!/usr/bin/env python3
"""scratch (P2a ⓒ): force states in the real browser and record computed style. usage: states.py <dist> <out.json>"""
import json, sys, pathlib, os
sys.path.insert(0, str(pathlib.Path('scripts/visual-baseline').resolve()))
sys.path.insert(0, str(pathlib.Path('.visual/p2a-probe').resolve()))
import capture as C
from cdump import start

CASES = [
    # name, scene, width, how, selector, props
    ('btn-primary:hover (members.css 삭제 · .btn:hover 좁힘)', 'upload-link', 1440, 'hover', '.modal-takeover .btn.btn-primary', ['background-color']),
    ('btn-secondary:hover (.btn:hover 좁힘)', 'lab-dialog', 1440, 'hover', '.btn.btn-secondary', ['background-color']),
    ('plain .btn:hover (.btn:hover 유지)', 'upload-link', 1440, 'hover', '.modal-takeover .btn:not(.btn-primary):not(.btn-secondary)', ['background-color']),
    ('btn-primary:active (DS#83)', 'upload-link', 1440, 'active', '.modal-takeover .btn.btn-primary', ['background-color']),
    ('search-hero button:active (DS#83)', 'lab', 1440, 'active', '.search-hero button', ['background-color']),
    ('.inp[readonly] (upload.css 삭제)', 'upload-metadata', 1440, 'readonly', '.modal-takeover .inp', ['background-color', 'color']),
    ('.login-input:focus-visible (login.css 삭제)', 'login', 1440, 'focus', '.login-input', ['outline-style', 'outline-width', 'outline-color', 'outline-offset', 'border-top-color']),
    ('.pcard:focus-visible (project.css outline-offset 삭제)', 'projects', 1440, 'focus', '.pcard', ['outline-style', 'outline-width', 'outline-color', 'outline-offset']),
    ('.modal-takeover button:focus-visible (선택자에서 뺌)', 'upload', 1440, 'focus', '.modal-takeover button:not(.inp):not(.sel)', ['outline-style', 'outline-width', 'outline-color', 'outline-offset']),
    ('.modal-takeover .inp:focus-visible (유지)', 'upload-metadata', 1440, 'focus', '.modal-takeover .inp', ['outline-style', 'outline-width', 'outline-offset', 'border-top-color']),
    ('button:focus-visible 일반 (DS#129 버림)', 'catalog', 1440, 'focus', '.tbl thead th > .thf', ['outline-style', 'outline-width', 'outline-color', 'outline-offset']),
    ('.lin-picker li > button[aria-pressed="true"] (DS#170)', 'lineage-picker', 1440, 'pressed', '.lin-picker li > button', ['background-color']),
    ('.lin-picker li > button:hover', 'lineage-picker', 1440, 'hover', '.lin-picker li > button', ['background-color', 'color']),
    ('.mainnav a:hover', 'catalog', 1440, 'hover', '.mainnav a', ['background-color', 'color']),
    ('.gnb-upload:hover (DS#127 color)', 'catalog', 1440, 'hover', '.gnb-upload', ['background-color', 'color']),
    ('.tbl td.rowact .ra 행 hover (opacity 삭제)', 'catalog', 1440, 'hover', '.tbl tbody tr.clk', ['opacity@.tbl tbody tr.clk td.rowact .ra']),
]

PROBE = r"""((sel, props) => { const el = document.querySelector(sel); if (!el) return {missing: true};
  const out = {}; for (const p of props) { const [prop, other] = p.split('@'); const t = other ? document.querySelector(other) : el;
    out[p] = t ? getComputedStyle(t).getPropertyValue(prop) : 'MISSING'; }
  let fv = null; try { fv = el.matches(':focus-visible'); } catch (e) {}
  return {out, focusVisible: fv, hover: el.matches(':hover'), active: el.matches(':active'), tag: el.tagName + '.' + el.className}; })"""


def main():
    dist = pathlib.Path(sys.argv[1]).resolve(); outp = pathlib.Path(sys.argv[2])
    manifest = json.loads(C.MANIFEST.read_text()); C.BROWSER_ARGS[:] = manifest['browser']['args']
    scenes = {s['name']: s for s in manifest['scenes']}
    blank = sorted(dist.glob('assets/audit-tile-*.svg'))[-1].relative_to(dist).as_posix()
    port = C.free_port(); proc = start(dist, port); ses = f'st-{os.getpid()}'
    res = []
    try:
        for name, scene_name, width, how, sel, props in CASES:
            scene = scenes[scene_name]
            C.ab(ses, 'set', 'viewport', str(width), '900', '1')
            C.ab(ses, 'open', f'http://127.0.0.1:{port}/{blank}'); C.ab(ses, 'storage', 'local', 'clear'); C.ab(ses, 'storage', 'session', 'clear')
            C.ab(ses, 'open', C.url_for(port, scene, 'light')); C.ab(ses, 'wait', '--load', 'networkidle')
            C.js(ses, "(() => { const s = document.createElement('style'); s.textContent = '* { transition: none !important; animation: none !important; }'; document.head.appendChild(s); return true; })()")
            for a in scene['actions']: C.run_action(ses, a)
            C.ab(ses, 'wait', str(int(scene['settleMs'])))
            if scene_name == 'lineage-picker':  # no li > button in today's ParentPicker DOM — inject one probe element
                C.js(ses, "(() => { const p = document.querySelector('.lin-picker'); const u = document.createElement('ul'); u.innerHTML = '<li><button type=\"button\">probe</button></li>'; p.prepend(u); return true; })()")
            C.ab(ses, 'mouse', 'move', '1', '1')
            probe = f"({PROBE})({json.dumps(sel)}, {json.dumps(props)})"
            base = C.js(ses, probe)
            forced = None; note = ''
            try:
                if base.get('missing'):
                    note = '요소 없음'
                elif how == 'hover':
                    C.ab(ses, 'scrollintoview', sel); C.ab(ses, 'hover', sel)
                elif how == 'focus':
                    C.ab(ses, 'scrollintoview', sel); C.ab(ses, 'press', 'Shift'); C.ab(ses, 'focus', sel)
                elif how == 'readonly':
                    C.js(ses, f"(() => {{ document.querySelector({json.dumps(sel)}).setAttribute('readonly', ''); return true; }})()")
                elif how == 'pressed':
                    C.js(ses, f"(() => {{ document.querySelector({json.dumps(sel)}).setAttribute('aria-pressed', 'true'); return true; }})()")
                elif how == 'active':
                    C.ab(ses, 'scrollintoview', sel)
                    r = C.js(ses, f"(() => {{ const b = document.querySelector({json.dumps(sel)}).getBoundingClientRect(); return [Math.round(b.x + b.width / 2), Math.round(b.y + b.height / 2)]; }})()")
                    C.ab(ses, 'mouse', 'move', str(r[0]), str(r[1])); C.ab(ses, 'mouse', 'down', 'left')
                if not base.get('missing'):
                    forced = C.js(ses, probe)
                if how == 'active':
                    C.ab(ses, 'mouse', 'up', 'left')
            except C.CaptureError as e:
                note = f'강제 실패: {str(e)[:160]}'
            res.append({'name': name, 'scene': scene_name, 'width': width, 'how': how, 'selector': sel, 'base': base, 'forced': forced, 'note': note})
            print(name, json.dumps(forced and forced.get('out'), ensure_ascii=False), note, flush=True)
    finally:
        try: C.ab(ses, 'close', timeout=30)
        except Exception: pass
        C.stop_preview(proc)
    outp.write_text(json.dumps(res, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
