#!/usr/bin/env python3
"""Capture the visual baseline defined by scenes.json.

Spec: dev-package/prd/specs/S-DESIGN-STRUCTURE-P0-20260924.md (P0).
Drives agent-browser through `python3 scripts/agent-bridge.py run-tool browser` (same call shape as
dev-package/reports/design-consistency/20260912/representative/capture.py) against the static audit
build served by `vite preview --config audit.vite.config.ts` on a free local port.

Output: <out>/<name>-<theme>-<width>.png + <out>/index.json. Default out: frontend/.visual/<label>/.
Exit codes: 0 = all captures written; 78 = could not capture (build, server, browser, manifest, missing file).
"""
from __future__ import annotations

import argparse
import concurrent.futures
import datetime
import hashlib
import json
import os
import pathlib
import signal
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

HERE = pathlib.Path(__file__).resolve().parent
FRONTEND = HERE.parents[1]
ROOT = FRONTEND.parent
MANIFEST = HERE / 'scenes.json'
BUILD_DIR = ROOT / '.codex' / 'upload-preview-audit'  # audit.vite.config.ts build.outDir
READINESS = 78

# Injected after document.fonts.ready and before actions (spec: determinism).
FREEZE_CSS = '* { animation: none !important; transition: none !important; caret-color: transparent !important; }'


class CaptureError(RuntimeError):
    pass


def rel(path: pathlib.Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def ab(session: str, *args: str, stdin: str | None = None, timeout: int = 90) -> str:
    cmd = ['python3', str(ROOT / 'scripts/agent-bridge.py'), 'run-tool', 'browser', '--', '--session', session, *args]
    try:
        r = subprocess.run(cmd, cwd=ROOT, input=stdin, text=True, capture_output=True, timeout=timeout)
    except subprocess.TimeoutExpired as e:
        raise CaptureError(f'agent-browser timed out: {" ".join(args[:2])}') from e
    if r.returncode:
        raise CaptureError(f'agent-browser {" ".join(args[:2])} failed ({r.returncode}): {(r.stderr + r.stdout).strip()[-800:]}')
    return r.stdout


def js(session: str, source: str):
    out = ab(session, 'eval', '--stdin', '--json', stdin=source)
    data = json.loads(out)
    if not data.get('success'):
        raise CaptureError(f'page script failed: {data.get("error")}')
    return data['data']['result']


def free_port() -> int:
    with socket.socket() as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]


def start_preview(port: int) -> subprocess.Popen:
    vite = FRONTEND / 'node_modules' / '.bin' / 'vite'
    if not vite.exists():
        raise CaptureError(f'{rel(vite)} missing - run npm ci in frontend/')
    proc = subprocess.Popen(
        [str(vite), 'preview', '--config', 'audit.vite.config.ts', '--host', '127.0.0.1', '--port', str(port), '--strictPort'],
        cwd=FRONTEND, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
    deadline = time.time() + 30
    url = f'http://127.0.0.1:{port}/audit-design.html'
    while time.time() < deadline:
        if proc.poll() is not None:
            raise CaptureError(f'vite preview exited with {proc.returncode}')
        try:
            with urllib.request.urlopen(url, timeout=2) as resp:
                if resp.status == 200:
                    return proc
        except (urllib.error.URLError, ConnectionError, TimeoutError):
            time.sleep(0.3)
    stop_preview(proc)
    raise CaptureError(f'vite preview did not answer on {url} within 30s')


def stop_preview(proc: subprocess.Popen | None) -> None:
    if proc is None or proc.poll() is not None:
        return
    try:
        os.killpg(proc.pid, signal.SIGTERM)
        proc.wait(timeout=10)
    except (ProcessLookupError, subprocess.TimeoutExpired):
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass


def run_action(session: str, action: dict) -> None:
    (kind, value), = action.items()
    if kind == 'click':
        ab(session, 'click', value)
    elif kind == 'wait':
        ab(session, 'wait', str(int(value)))
    elif kind == 'waitFor':
        ab(session, 'wait', value)
    elif kind == 'select':
        ab(session, 'select', value[0], value[1])
    elif kind == 'scrollIntoView':
        ab(session, 'scrollintoview', value)
    elif kind == 'pickFile':
        # agent-browser 0.27.0 `upload` leaves the page unresponsive to Runtime.evaluate afterwards
        # (measured 2026-09-24), so the file is placed through DataTransfer in the page instead.
        spec = json.dumps(value)
        picked = js(session, f"""(() => {{ const s = {spec}; const input = document.querySelector(s.selector);
          if (!input) return 0; const dt = new DataTransfer(); dt.items.add(new File([new Uint8Array(s.bytes)], s.name));
          input.files = dt.files; input.dispatchEvent(new Event('change', {{bubbles: true}})); return input.files.length; }})()""")
        if picked != 1:
            raise CaptureError(f'pickFile: {value["selector"]} not found')
    else:
        raise CaptureError(f'unknown action {kind}')


def url_for(port: int, scene: dict, theme: str) -> str:
    query = {'theme': theme, **scene['query']}
    acct = scene['account']
    query.update({'upload': '1' if acct['upload'] else '0', 'labSettings': '1' if acct['labSettings'] else '0',
                  'operator': '1' if acct['operator'] else '0'})
    return f'http://127.0.0.1:{port}/{scene["entry"]}?{urllib.parse.urlencode(query)}'


def capture_theme(theme: str, scenes: list[dict], port: int, out: pathlib.Path, session: str, height: int, dpr: int, blank: str) -> list[dict]:
    results = []
    ab(session, 'set', 'media', theme)
    for scene in scenes:
        if theme not in scene['themes']:
            continue
        for width in scene['widths']:
            name = f'{scene["name"]}-{theme}-{width}'
            ab(session, 'set', 'viewport', str(width), str(height), str(dpr))
            # Empty storage for every capture: open a same-origin static asset (no app code), clear, then open the scene.
            ab(session, 'open', f'http://127.0.0.1:{port}/{blank}')
            ab(session, 'storage', 'local', 'clear')
            ab(session, 'storage', 'session', 'clear')
            ab(session, 'open', url_for(port, scene, theme))
            ab(session, 'wait', '--load', 'networkidle')
            js(session, 'document.fonts.ready.then(() => true)')
            js(session, f"(() => {{ const s = document.createElement('style'); s.dataset.visualBaseline = 'freeze'; s.textContent = {json.dumps(FREEZE_CSS)}; document.head.appendChild(s); return true; }})()")
            for action in scene['actions']:
                run_action(session, action)
            ab(session, 'wait', str(int(scene['settleMs'])))
            state = js(session, '({theme: document.documentElement.dataset.theme, width: innerWidth, dpr: devicePixelRatio})')
            if state.get('theme') != theme or state.get('width') != width or state.get('dpr') != dpr:
                raise CaptureError(f'{name}: page state {state} does not match theme={theme} width={width} dpr={dpr}')
            path = out / f'{name}.png'
            shot = ['screenshot', str(path)]
            if scene['fullPage']:
                shot.append('--full')
            ab(session, *shot)
            if not path.exists() or path.stat().st_size == 0:
                raise CaptureError(f'{name}: screenshot missing or empty')
            errors = ab(session, 'errors').strip()
            data = path.read_bytes()
            results.append({'name': name, 'scene': scene['name'], 'theme': theme, 'width': width, 'file': path.name,
                            'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest(), 'fullPage': scene['fullPage'],
                            'pageErrors': errors})
            print(f'{name} {len(data)}B', flush=True)
    return results


def git(*args: str) -> str:
    r = subprocess.run(['git', *args], cwd=ROOT, text=True, capture_output=True)
    return r.stdout.strip() if r.returncode == 0 else ''


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument('--label', help='output to frontend/.visual/<label>/')
    group.add_argument('--out', help='output directory')
    ap.add_argument('--skip-build', action='store_true', help='reuse the existing audit build')
    ap.add_argument('--parallel', type=int, choices=[1, 2], default=2, help='sessions in parallel (one per theme, max 2)')
    ap.add_argument('--only', help='comma-separated scene names (debug; diff.mjs rejects a partial set with 78)')
    args = ap.parse_args()

    out = (FRONTEND / '.visual' / args.label) if args.label else pathlib.Path(args.out).resolve()
    manifest_bytes = MANIFEST.read_bytes()
    manifest = json.loads(manifest_bytes)
    scenes = manifest['scenes']
    if args.only:
        wanted = set(args.only.split(','))
        unknown = wanted - {s['name'] for s in scenes}
        if unknown:
            print(f'::visual-capture:: unknown scenes {sorted(unknown)}', file=sys.stderr)
            return READINESS
        scenes = [s for s in scenes if s['name'] in wanted]
    names = [s['name'] for s in scenes]
    if len(set(names)) != len(names) or not scenes:
        print('::visual-capture:: manifest has duplicate or no scenes', file=sys.stderr)
        return READINESS
    expected = sum(len(s['widths']) * len(s['themes']) for s in scenes)
    height = int(manifest['viewport']['height'])
    dpr = int(manifest['viewport']['deviceScaleFactor'])

    out.mkdir(parents=True, exist_ok=True)
    for old in out.glob('*.png'):
        old.unlink()
    (out / 'index.json').unlink(missing_ok=True)

    if not args.skip_build:
        r = subprocess.run(['npm', 'run', 'audit:build'], cwd=FRONTEND, text=True, capture_output=True)
        if r.returncode:
            print(f'::visual-capture:: npm run audit:build failed ({r.returncode})\n{(r.stdout + r.stderr)[-2000:]}', file=sys.stderr)
            return READINESS
    if not (BUILD_DIR / 'audit-design.html').exists():
        print(f'::visual-capture:: audit build missing at {rel(BUILD_DIR)}', file=sys.stderr)
        return READINESS
    tiles = sorted(BUILD_DIR.glob('assets/audit-tile-*.svg'))
    if not tiles:
        print(f'::visual-capture:: no static asset (assets/audit-tile-*.svg) in {rel(BUILD_DIR)} to clear storage from', file=sys.stderr)
        return READINESS
    blank = tiles[-1].relative_to(BUILD_DIR).as_posix()

    run_id = f'{os.getpid()}-{int(time.time())}'
    themes = sorted({t for s in scenes for t in s['themes']}, key=['light', 'dark'].index)
    sessions = {t: f'vb-{t}-{run_id}' for t in themes}
    preview = None
    started = datetime.datetime.now(datetime.timezone.utc)
    try:
        port = free_port()
        preview = start_preview(port)
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.parallel) as pool:
            futures = [pool.submit(capture_theme, t, scenes, port, out, sessions[t], height, dpr, blank) for t in themes]
            captures = [c for f in futures for c in f.result()]
    except CaptureError as e:
        print(f'::visual-capture:: {e}', file=sys.stderr)
        return READINESS
    finally:
        for s in sessions.values():
            try:
                ab(s, 'close', timeout=30)
            except CaptureError:
                pass
        stop_preview(preview)

    order = {n: i for i, n in enumerate(names)}
    captures.sort(key=lambda c: (order[c['scene']], themes.index(c['theme']), c['width']))
    pngs = sorted(p.name for p in out.glob('*.png'))
    if len(captures) != expected or len(pngs) != expected or any(c['bytes'] == 0 for c in captures):
        print(f'::visual-capture:: expected {expected} PNGs, wrote {len(pngs)}', file=sys.stderr)
        return READINESS
    index = {
        'schema': 'colab-visual-index/1',
        'manifest': rel(MANIFEST),
        'manifestSha256': hashlib.sha256(manifest_bytes).hexdigest(),
        'gitHead': git('rev-parse', 'HEAD'),
        'gitDirty': bool(git('status', '--porcelain', '--untracked-files=no')),
        'capturedAt': started.isoformat(timespec='seconds'),
        'finishedAt': datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds'),
        'buildDir': rel(BUILD_DIR),
        'built': not args.skip_build,
        'parallel': args.parallel,
        'scenes': names,
        'captureCount': len(captures),
        'captures': captures,
    }
    (out / 'index.json').write_text(json.dumps(index, ensure_ascii=False, indent=2) + '\n')
    print(f'{len(captures)} captures -> {rel(out)}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
