#!/usr/bin/env python3
"""Capture the visual baseline defined by scenes.json.

Spec: dev-package/prd/specs/S-DESIGN-STRUCTURE-P0-20260924.md (P0).
Drives agent-browser through `python3 scripts/agent-bridge.py run-tool browser` (same call shape as
dev-package/reports/design-consistency/20260912/representative/capture.py) against the static audit
build served by `vite preview --config audit.vite.config.ts` on a free local port.

Viewports and input mode (spec dev-package/prd/specs/S-DEVICE-WIDTH-INPUT-20260926.md L0a · scenes schema 2): the
manifest lists viewports {id, width, height, input}; a scene uses all of them unless it lists `viewports` ids. Input
is fixed when the browser launches: one launch wrapper per input (Chrome + browser.args + browser.inputArgs[input]) is
written to a temporary folder without spaces and passed to agent-browser as the executable. One session per
theme × input. Before each screenshot the page state (theme, innerWidth, innerHeight, devicePixelRatio,
(pointer: coarse), (hover: hover)) is compared with the viewport; a mismatch stops the run with 78.

Output: <out>/<scene>-<theme>-<viewport id>.png + <out>/index.json. Default out: frontend/.visual/<label>/.
Exit codes: 0 = all captures written; 78 = could not capture (build, server, browser, manifest, missing file,
page state differs from the declared viewport or input).
"""
from __future__ import annotations

import argparse
import concurrent.futures
import datetime
import hashlib
import json
import os
import pathlib
import re
import shlex
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
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


# Page media state each input's launch wrapper must produce (checked before every screenshot).
INPUT_MEDIA = {'touch': {'coarse': True, 'hover': False}, 'mouse': {'coarse': False, 'hover': True}}

# Session name -> launch wrapper path (set in main). Passed on every call; only the call that launches the
# session's browser uses it.
SESSION_EXEC: dict[str, str] = {}


class CaptureError(RuntimeError):
    pass


def rel(path: pathlib.Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def ab(session: str, *args: str, stdin: str | None = None, timeout: int = 90) -> str:
    launch = ['--executable-path', SESSION_EXEC[session]] if session in SESSION_EXEC else []
    cmd =['python3', str(ROOT / 'scripts/agent-bridge.py'), 'run-tool', 'browser', '--', '--session', session, *launch, *args]
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


def chrome_binary() -> pathlib.Path:
    """The Chrome agent-browser would launch: AGENT_BROWSER_EXECUTABLE_PATH, else its newest installed Chrome."""
    env = os.environ.get('AGENT_BROWSER_EXECUTABLE_PATH')
    if env:
        found = [pathlib.Path(env)]
    else:
        version = lambda p: tuple(int(n) for n in re.findall(r'\d+', p.parent.name))
        found = sorted((pathlib.Path.home() / '.agent-browser' / 'browsers').glob('chrome-*/chrome'), key=version)
    if not found or not found[-1].is_file() or not os.access(found[-1], os.X_OK):
        raise CaptureError('browser executable missing (AGENT_BROWSER_EXECUTABLE_PATH or ~/.agent-browser/browsers/chrome-*/chrome)')
    return found[-1]


def write_wrappers(folder: pathlib.Path, chrome: pathlib.Path, base_args: list[str], input_args: dict[str, list[str]]) -> dict[str, str]:
    """One launch wrapper per input: Chrome with browser.args + that input's args, then agent-browser's own args."""
    if re.search(r'\s', str(folder)):
        raise CaptureError(f'wrapper folder has whitespace: {folder}')
    wrappers = {}
    for name, extra in input_args.items():
        path = folder / f'chrome-{name}'
        path.write_text('#!/bin/sh\nexec ' + ' '.join(shlex.quote(a) for a in [str(chrome), *base_args, *extra]) + ' "$@"\n')
        path.chmod(0o755)
        wrappers[name] = str(path)
    return wrappers


def reveal_script(selector: str) -> str:
    """Page script run before `click`: scroll the target into the window only when its box is not fully inside it.

    Orchestrator decision for spec S-DEVICE-WIDTH-INPUT-20260926 L0a (spec gap: a click target outside the window is
    first brought inside). agent-browser 0.27.0 `click` does not scroll: at 844x390 the upload open button sat at
    y=411.7 and the click did not land. A target already fully inside the window is not scrolled at all.
    Returns 'scrolled' | 'inside' | 'absent'; a missing target is left to the click itself to report."""
    return (f"(() => {{ const el = document.querySelector({json.dumps(selector)}); if (!el) return 'absent'; "
            "const r = el.getBoundingClientRect(); "
            "if (r.top >= 0 && r.left >= 0 && r.bottom <= innerHeight && r.right <= innerWidth) return 'inside'; "
            "el.scrollIntoView({block: 'nearest', inline: 'nearest'}); return 'scrolled'; })()")


def run_action(session: str, action: dict) -> None:
    (kind, value), = action.items()
    if kind == 'click':
        if js(session, reveal_script(value)) == 'scrolled':
            print(f'  click {value}: scrolled into view', flush=True)
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


def capture_session(theme: str, input_name: str, scenes: list[dict], viewports: dict[str, dict], port: int, out: pathlib.Path,
                    session: str, dpr: int, blank: str) -> list[dict]:
    """All captures of one theme whose viewport declares `input_name`, in one browser launched with that input's wrapper."""
    results = []
    ab(session, 'set', 'media', theme)
    for scene in scenes:
        if theme not in scene['themes']:
            continue
        for vp_id in scene['viewports']:
            vp = viewports[vp_id]
            if vp['input'] != input_name:
                continue
            width, height = vp['width'], vp['height']
            name = f'{scene["name"]}-{theme}-{vp_id}'
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
            state = js(session, "({theme: document.documentElement.dataset.theme, width: innerWidth, height: innerHeight, "
                                "dpr: devicePixelRatio, coarse: matchMedia('(pointer: coarse)').matches, "
                                "hover: matchMedia('(hover: hover)').matches})")
            want = {'theme': theme, 'width': width, 'height': height, 'dpr': dpr, **INPUT_MEDIA[vp['input']]}
            if state != want:
                raise CaptureError(f'{name}: page state {state} does not match viewport {vp_id} {want}')
            path = out / f'{name}.png'
            shot = ['screenshot', str(path)]
            if scene['fullPage']:
                shot.append('--full')
            ab(session, *shot)
            if not path.exists() or path.stat().st_size == 0:
                raise CaptureError(f'{name}: screenshot missing or empty')
            errors = ab(session, 'errors').strip()
            data = path.read_bytes()
            results.append({'name': name, 'scene': scene['name'], 'theme': theme, 'viewport': vp_id, 'width': width,
                            'height': height, 'input': vp['input'], 'file': path.name,
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
    ap.add_argument('--parallel', type=int, choices=[1, 2, 3, 4], default=2,
                    help='sessions in parallel (one per theme x input, max 4)')
    ap.add_argument('--only', help='comma-separated scene names (debug; diff.mjs rejects a partial set with 78)')
    ap.add_argument('--force-input', choices=sorted(INPUT_MEDIA),
                    help='launch every session with this input wrapper (state-check proof: a viewport declaring the other input ends 78)')
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
    viewport_list = manifest.get('viewports') or []
    viewports = {v.get('id'): v for v in viewport_list}
    browser = manifest.get('browser', {})
    input_args = browser.get('inputArgs', {})
    problems = []
    if manifest.get('schema') != 'colab-visual-scenes/2':
        problems.append(f'schema {manifest.get("schema")!r} is not colab-visual-scenes/2')
    if not viewport_list or len(viewports) != len(viewport_list):
        problems.append('viewports missing or ids not unique')
    for v in viewport_list:
        if not (isinstance(v.get('width'), int) and isinstance(v.get('height'), int) and v['width'] > 0 and v['height'] > 0):
            problems.append(f'viewport {v.get("id")}: width/height must be positive integers')
        if v.get('input') not in INPUT_MEDIA or v.get('input') not in input_args:
            problems.append(f'viewport {v.get("id")}: input {v.get("input")!r} has no browser.inputArgs or no known media state')
    for s in scenes:
        s['viewports'] = s.get('viewports', list(viewports))
        unknown_vp = [i for i in s['viewports'] if i not in viewports]
        if 'widths' in s or not s['viewports'] or unknown_vp or len(set(s['viewports'])) != len(s['viewports']):
            problems.append(f'scene {s["name"]}: viewports {s["viewports"]} (unknown {unknown_vp}) or legacy widths')
    if problems:
        print('::visual-capture:: manifest: ' + '; '.join(problems), file=sys.stderr)
        return READINESS
    expected = sum(len(s['viewports']) * len(s['themes']) for s in scenes)
    base_args = browser.get('args', [])
    dpr = int(manifest['deviceScaleFactor'])

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
    inputs = sorted({viewports[i]['input'] for s in scenes for i in s['viewports']})
    sessions = {(t, i): f'vb-{t}-{i}-{run_id}' for t in themes for i in inputs}
    wrap_dir = pathlib.Path(tempfile.mkdtemp(prefix='vb-wrap-'))
    preview = None
    started = datetime.datetime.now(datetime.timezone.utc)
    try:
        wrappers = write_wrappers(wrap_dir, chrome_binary(), base_args, input_args)
        for (_, i), s in sessions.items():
            SESSION_EXEC[s] = wrappers[args.force_input or i]
        port = free_port()
        preview = start_preview(port)
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.parallel) as pool:
            futures = [pool.submit(capture_session, t, i, scenes, viewports, port, out, s, dpr, blank) for (t, i), s in sessions.items()]
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
        shutil.rmtree(wrap_dir, ignore_errors=True)

    order = {n: i for i, n in enumerate(names)}
    vp_order = list(viewports)
    captures.sort(key=lambda c: (order[c['scene']], themes.index(c['theme']), vp_order.index(c['viewport'])))
    pngs = sorted(p.name for p in out.glob('*.png'))
    if len(captures) != expected or len(pngs) != expected or any(c['bytes'] == 0 for c in captures):
        print(f'::visual-capture:: expected {expected} PNGs, wrote {len(pngs)}', file=sys.stderr)
        return READINESS
    index = {
        'schema': 'colab-visual-index/2',
        'manifest': rel(MANIFEST),
        'manifestSha256': hashlib.sha256(manifest_bytes).hexdigest(),
        'gitHead': git('rev-parse', 'HEAD'),
        'gitDirty': bool(git('status', '--porcelain', '--untracked-files=no')),
        'capturedAt': started.isoformat(timespec='seconds'),
        'finishedAt': datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds'),
        'buildDir': rel(BUILD_DIR),
        'built': not args.skip_build,
        'parallel': args.parallel,
        'browserArgs': base_args,
        'inputArgs': input_args,
        'forcedInput': args.force_input,
        'deviceScaleFactor': dpr,
        'viewports': viewport_list,
        'scenes': names,
        'captureCount': len(captures),
        'captures': captures,
    }
    (out / 'index.json').write_text(json.dumps(index, ensure_ascii=False, indent=2) + '\n')
    print(f'{len(captures)} captures -> {rel(out)}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
