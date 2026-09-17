"""Real GRIB upload, preview layout and connected-parent declaration journey."""
import hashlib
import io
import json
import os
import subprocess
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import urlopen

from PIL import Image
from sqlalchemy import create_engine, text


def run(command, args, session):
    if not args.upload_file or not args.viz_python or not args.artifacts:
        raise RuntimeError('real GRIB file, viz service and artifacts required')
    root = Path(__file__).resolve().parents[1]
    out = args.artifacts.resolve()
    out.mkdir(parents=True, exist_ok=True)
    evidence = {'session': session, 'environment': 'disposable local API/DB/viz', 'steps': [],
                'sourceSha256': hashlib.sha256(args.upload_file.read_bytes()).hexdigest()}
    evidence['codeHashes'] = {p: hashlib.sha256((root / p).read_bytes()).hexdigest() for p in (
        'frontend/src/components/preview/PreviewPickRow.tsx',
        'frontend/src/components/preview/preview.css',
        'frontend/src/components/lineage/LineageStep.tsx',
        'services/viz-render/src/colab_viz/domains/d7_visualization/preview.py')}
    def save():
        (out / 'journey.json').write_text(json.dumps(evidence, ensure_ascii=False, indent=2))
    def record(step, **values):
        evidence['steps'].append({'step': step, **values})
        save()
        print('PASS:', step, flush=True)
    def sel(t):
        return f'[data-testid="{t}"]'
    def ev(js):
        return json.loads(command('eval', js).strip())
    def click(t):
        command('scrollintoview', sel(t))
        command('click', sel(t))
    def fill(t, v):
        command('fill', sel(t), v)
    def wait_long(*parts):
        for attempt in range(6):
            try:
                return command('wait', *parts)
            except RuntimeError as error:
                if 'Wait timed out' not in str(error) or attempt == 5:
                    raise
                print('Still waiting for real GRIB processing:', attempt + 1, flush=True)
    def snap(name):
        (out / (name + '.txt')).write_text(command('snapshot'))
        command('screenshot', str(out / (name + '.png')))
    def stage(n, target):
        command('focus', f'[data-testid="reg-steps"] button:nth-of-type({n})')
        command('press', 'Enter')
        command('wait', sel(target))
    def connect():
        click('lin-add')
        command('wait', sel('lin-pick-0000000000000000000000DSA1'))
        click('lin-pick-0000000000000000000000DSA1')
        command('find', 'role', 'button', 'click', '--name', '이 데이터로 연결', '--exact')
        command('wait', '--fn', "!document.querySelector('[data-testid=lin-picker]')")
        command('wait', sel('lin-del'))
    def drawn(t):
        command('wait', '--fn', f"(()=>{{const i=document.querySelector({json.dumps(sel(t))});return i?.complete&&i.naturalWidth>0}})()")
    def layout(prefix, label):
        for width in (1440, 390):
            command('set', 'viewport', str(width), '1000')
            command('scrollintoview', sel(prefix + '-pick-variable'))
            data = ev("""(()=>{const row=document.querySelector(%s);const box=row.getBoundingClientRect();
                return {rowWidth:row.clientWidth,rowScroll:row.scrollWidth,fields:[...row.querySelectorAll('label')].map(l=>{
                const s=l.querySelector('select'),r=s.getBoundingClientRect(),t=l.querySelector('span'),tr=t.getBoundingClientRect();
                return {left:r.left,right:r.right,fieldWidth:l.getBoundingClientRect().width,boxLeft:box.left,boxRight:box.right,labelHeight:tr.height,
                lineHeight:parseFloat(getComputedStyle(t).lineHeight),title:s.title,value:s.value};})};})()""" % json.dumps(sel(prefix + '-pick-row')))
            evidence.setdefault('layout', []).append({'screen': label, 'width': width, **data})
            snap(f'{label}-{width}')
            save()
            if data['rowScroll'] > data['rowWidth'] + 2 or any(
                f['fieldWidth'] > 182 or f['left'] < f['boxLeft'] - 2 or f['right'] > f['boxRight'] + 2
                or f['labelHeight'] > f['lineHeight'] + 2 for f in data['fields']):
                raise AssertionError(label + ': picker grows beyond its fixed size, overflows or label wraps')
            full = ev("(()=>{const s=document.querySelector(%s);return {title:s.title,text:s.selectedOptions[0].textContent}})()" % json.dumps(sel(prefix + '-pick-variable')))
            if not full['title'] or full['title'] != full['text']:
                raise AssertionError(label + ': selected full label is not retained')
            if width == 390:
                disclosure = sel(prefix + '-pick-values')
                command('click', disclosure + ' summary')
                command('scrollintoview', disclosure)
                expanded = ev("""(()=>{const d=document.querySelector(%s);return {open:d.open,text:d.textContent,
                  width:d.clientWidth,scroll:d.scrollWidth,values:[...d.querySelectorAll('dd')].map(x=>({w:x.clientWidth,s:x.scrollWidth}))};})()""" % json.dumps(disclosure))
                snap(label + '-narrow-full-values')
                if not expanded['open'] or full['text'] not in expanded['text'] or expanded['scroll'] > expanded['width'] + 2 or any(v['s'] > v['w'] + 2 for v in expanded['values']):
                    raise AssertionError(label + ': expanded full values are missing or clipped')
                command('click', disclosure + ' summary')
        command('set', 'viewport', '1440', '1000')
        record(label + ' picker fits at desktop and narrow widths')
    def images(label, variable):
        drawn('up-preview-image')
        drawn('up-thumb-img')
        data = ev("""(()=>{const m=document.querySelector('[data-testid=up-preview-image]'),t=document.querySelector('[data-testid=up-thumb-img]');
          return {main:m.src,thumb:t.src,variable:m.dataset.previewVariable,width:m.naturalWidth,height:m.naturalHeight};})()""")
        if data['variable'] != variable:
            raise AssertionError('render does not match selected variable')
        paths = [urlsplit(data[k]).path for k in ('main', 'thumb')]
        # Artifacts are content-addressed independently; paths alone do not prove a shared render.
        for kind in ('main', 'thumb'):
            parsed = urlsplit(data[kind])
            if parsed.hostname not in ('127.0.0.1', 'localhost'):
                raise RuntimeError('only local E2E artifact URLs may be inspected')
            with urlopen(data[kind], timeout=30) as response:
                content = response.read()
            (out / (label + '-' + kind + '.png')).write_bytes(content)
            im = Image.open(io.BytesIO(content)).convert('RGBA')
            alpha = im.getchannel('A')
            data[kind + 'AlphaBBox'] = alpha.getbbox()
            data[kind + 'OpaqueFraction'] = sum(v > 0 for v in alpha.getdata()) / (im.width * im.height)
        evidence.setdefault('images', []).append({'label': label, **data, 'paths': paths})
        save()
        if not 0.8 <= data['width'] / data['height'] <= 1.3 or data['mainOpaqueFraction'] < 0.99:
            raise AssertionError('global Mercator image is stretched or mostly transparent')
        record(label + ' decoded current-variable map and thumbnail', **data)
        return data
    try:
        command('set', 'viewport', '1440', '1000')
        command('find', 'role', 'button', 'click', '--name', '업로드', '--exact')
        command('upload', sel('up-drop-input'), str(args.upload_file.resolve()))
        wait_long('[data-testid="up-analyze"][data-stage="3"]')
        click('reg-open')
        command('wait', sel('reg-category'))
        wait_long('[data-testid="up-pick-variable"]:not(:disabled)')
        choices = ev("[...document.querySelector('[data-testid=up-pick-variable]').options].map(o=>o.value)")
        variable = next(v for v in choices if v.startswith('grib:15:'))
        command('select', sel('up-pick-variable'), variable)
        wait_long('--fn', f"document.querySelector('[data-testid=up-preview-image]')?.dataset.previewVariable === {json.dumps(variable)}")
        command('click', 'details.up-preview-options > summary')
        first = images('message15', variable)
        layout('up', 'upload')
        click('pv-expand')
        command('wait', sel('pvx-pick-variable'))
        layout('pvx', 'expanded')
        command('press', 'Escape')
        command('upload', sel('up-thumb-input'), str(out / 'message15-thumb.png'))
        custom = ev("document.querySelector('[data-testid=up-thumb-img]').src")
        variable2 = next(v for v in choices if v.startswith('grib:14:'))
        command('select', sel('up-pick-variable'), variable2)
        wait_long('--fn', f"document.querySelector('[data-testid=up-preview-image]')?.dataset.previewVariable === {json.dumps(variable2)}")
        if ev("document.querySelector('[data-testid=up-thumb-img]').src") != custom:
            raise AssertionError('variable selection overwrote custom representative image')
        command('find', 'role', 'button', 'click', '--name', '자동 그림 사용', '--exact')
        second = images('message14', variable2)
        if first['main'] == second['main'] or first['thumb'] == second['thumb']:
            raise AssertionError('both automatic images must refresh with variable selection')
        record('manual representative preserved during selection; automatic fallback refreshed both artifacts')
        palette = ev("(()=>{const s=document.querySelector('[data-testid=up-style-palette]');return [...s.options].find(o=>o.value!==s.value)?.value})()")
        if not palette:
            raise AssertionError('no alternative palette available for render correspondence check')
        command('select', sel('up-style-palette'), palette)
        click('up-preview-draw')
        wait_long('--fn', f"document.querySelector('[data-testid=up-preview-image]')?.src && document.querySelector('[data-testid=up-preview-image]').src !== {json.dumps(second['main'])}")
        recolored = images('message14-palette', variable2)
        if recolored['thumb'] == second['thumb']:
            raise AssertionError('automatic thumbnail did not reflect palette change')
        record('same variable palette change refreshed both render artifacts', palette=palette)
        command('select', sel('reg-level'), 'Lv1')
        stage(2, 'reg-name')
        name = 'Issue 73 82 ' + session
        fill('reg-name', name)
        fill('reg-summary', 'Real GRIB preview and connected-parent declaration verification')
        fill('reg-crs', 'EPSG:4326')
        click('reg-period-open')
        click('reg-period-unit-일')
        for side in ('start', 'end'):
            for part, value in (('year', '2025'), ('month', '09'), ('day', '01')):
                fill(f'reg-period-pop-{side}-{part}', value)
        click('reg-period-apply')
        stage(3, 'reg-done')
        command('check', sel('lin-unknown-check'))
        connect()
        if ev("Boolean(document.querySelector('[data-testid=lin-unknown]'))"):
            raise AssertionError('confirmed parent leaves unknown declaration visible')
        snap('connected-hidden')
        command('find', 'role', 'button', 'click', '--name', '지우기', '--exact')
        command('wait', sel('lin-unknown-check'))
        if not ev("document.querySelector('[data-testid=lin-unknown-check]').checked"):
            raise AssertionError('removing parent lost previous declaration state')
        connect()
        record('confirmed parent hides declaration; removal restores previous checked state')
        click('reg-done')
        command('wait', sel('detail-header'))
        command('reload')
        command('wait', sel('detail-header'))
        drawn('preview-single-image')
        command('wait', '[data-testid="dt-pick-variable"]:not(:disabled)')
        command('select', sel('dt-pick-variable'), variable)
        command('wait', '[data-testid="dt-pick-variable"]:not(:disabled)')
        drawn('preview-single-image')
        layout('dt', 'detail')
        engine = create_engine(os.environ['E2E_DATABASE_URL'].split('\t')[0], future=True)
        try:
            with engine.begin() as conn:
                conn.execute(text('SET TRANSACTION READ ONLY'))
                conn.execute(text("SELECT set_config('app.current_lab','0000000000000000000000000A',true)"))
                conn.execute(text("SELECT set_config('app.current_account','000000000000000000000000A1',true)"))
                rows = conn.execute(text('SELECT dataset_id FROM d3_dataset_description WHERE name=:name'), {'name': name}).all()
                if len(rows) != 1:
                    raise AssertionError('registration did not persist exactly one dataset')
                parents = conn.execute(text('SELECT parent_dataset_id FROM d4_lineage_edge WHERE child_dataset_id=:id'), {'id': rows[0][0]}).scalars().all()
                if parents != ['0000000000000000000000DSA1']:
                    raise AssertionError('registered parent edge differs from user selection')
        finally:
            engine.dispose()
        if 'A 강우 원자료' not in command('snapshot'):
            raise AssertionError('connected parent did not persist after reload')
        record('registered GRIB and parent remain after reload')
        snap('final-detail')
        evidence['status'] = 'passed'
        save()
        task = os.environ.get('E2E_GATE_TASK')
        if task:
            gate_env = {**os.environ, 'COLAB_TASK_ID': task, 'AB_SESSION': session,
                        'COLAB_VISUAL_URLS': command('get', 'url').strip()}
            with (out / 'final-gates.log').open('w') as log:
                result = subprocess.run(['python3', 'scripts/agent-bridge.py', 'run-tool', 'gate', '--', 'task'],
                                        cwd=root, env=gate_env, stdout=log, stderr=log)
            evidence['finalGateExitCode'] = result.returncode
            save()
            if result.returncode:
                raise AssertionError('final gate set failed; see final-gates.log')
    except Exception as error:
        evidence['status'] = 'failed'
        evidence['failure'] = str(error)
        save()
        snap('failure')
        raise
