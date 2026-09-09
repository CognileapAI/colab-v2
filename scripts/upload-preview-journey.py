"""Actual browser journey for the approved upload preview plan.

Invoked by e2e-login.py inside its disposable DB, local storage and worker run.
No production credentials, data, or mock API responses are used.
"""
from pathlib import Path
import hashlib
import json
import re
import zipfile


def run(command, args, session):
    if not args.upload_file or not args.artifacts or not args.viz_python:
        raise RuntimeError('journey requires upload-file, artifacts and viz-python')
    out = args.artifacts.resolve()
    out.mkdir(parents=True, exist_ok=True)
    source = args.upload_file.resolve()
    unsupported = getattr(args, 'expect_unsupported', False)
    evidence = {'session': session, 'file': source.name, 'bytes': source.stat().st_size,
                'sha256': hashlib.sha256(source.read_bytes()).hexdigest(), 'steps': []}
    def record(step):
        evidence['steps'].append(step)
        (out / 'journey.json').write_text(json.dumps(evidence, ensure_ascii=False, indent=2))
        print('PASS:', step, flush=True)
    def click(testid):
        command('scrollintoview', f'[data-testid="{testid}"]')
        command('click', f'[data-testid="{testid}"]')
    def wait(testid):
        command('wait', f'[data-testid="{testid}"]')
    def snap(name):
        (out / (name + '.txt')).write_text(command('snapshot'))
        command('screenshot', str(out / (name + '.png')))
    def drawn(selector):
        command('wait', '--fn', f'Array.from(document.querySelectorAll({json.dumps(selector)})).some(i=>i.complete && i.naturalWidth>0)')
    try:
        command('set', 'viewport', '1440', '1000')
        command('find', 'role', 'button', 'click', '--name', '업로드', '--exact')
        snap('01-empty')
        command('upload', '[data-testid="up-drop-input"]', str(source), *[str(p.resolve()) for p in args.extra_file])
        command('wait', '[data-testid="up-analyze"][data-stage="3"]')
        snap('02-analyzed')
        click('reg-open')
        wait('reg-category')
        record('actual upload and worker analysis; registration classification opened')
        snap('03-classification')
        if args.grid_file:
            wait('up-grid-input')
            command('upload', '[data-testid="up-grid-input"]', *[str(p.resolve()) for p in args.grid_file])
            wait('up-grid-accept')
            snap('03-grid-position')
            click('up-grid-accept')
            record('actual reference grid uploaded and its position confirmed')
        # Server palette readiness is separate from upload readiness.
        command('wait', '--fn', 'document.querySelector(\'[data-testid="up-style-palette"]\')?.options.length > 0')
        preview_html = command('get', 'html', '[data-testid="up-preview"]')
        if args.grid_file and 'up-preview-options' in preview_html:
            command('scrollintoview', 'details.up-preview-options > summary')
            command('click', 'details.up-preview-options > summary')
            click('up-preview-draw')
        elif 'up-preview-options' not in preview_html and 'up-preview-draw' in preview_html:
            command('wait', '[data-testid="up-preview-draw"]:not(:disabled)')
            click('up-preview-draw')
        if unsupported:
            command('wait', '[data-testid="up-preview-slot"][data-preview-slot-state="failed"]')
            record('unsupported render has a terminal explanation; registration remains available')
            snap('04-preview-unsupported')
        else:
            drawn('[data-testid="up-preview-image"], [data-testid="up-preview-thumb"]')
            record('upload render image decoded by browser')
            if getattr(args, 'expect_partial', False):
                wait('up-preview-partial')
                partial = command('get', 'text', '[data-testid="up-preview-partial"]')
                if '조각 2개 중 1개' not in partial or args.extra_file[0].name not in partial:
                    raise AssertionError('partial render did not identify the omitted original')
                record('partial render identifies one unreadable file while showing readable data')
            snap('04-preview')
            click('pv-expand')
            snap('05-expanded')
            command('press', 'Escape')
            record('preview expanded and closed by Escape')
        click('reg-next')
        wait('reg-name')
        name = 'UI journey ' + session
        summary = 'Actual file browser journey: ' + source.name
        command('fill', '[data-testid="reg-name"]', name)
        command('fill', '[data-testid="reg-summary"]', summary)
        if args.connections:
            command('fill', '[data-testid="reg-crs"]', 'EPSG:4326')
            command('fill', '[data-testid="reg-interval-value"]', '10')
            command('select', '[data-testid="reg-interval-unit"]', '분')
            command('fill', '[data-testid="vt-name-0"]', 'Fpar_500m 검수')
            command('fill', '[data-testid="vt-unit-0"]', '%')
            click('reg-period-open')
            click('reg-period-unit-일')
            for side, values in [('start', ('2019', '09', '30')), ('end', ('2019', '10', '07'))]:
                for field, value in zip(('year', 'month', 'day'), values):
                    command('fill', f'[data-testid="reg-period-pop-{side}-{field}"]', value)
            click('reg-period-apply')
        snap('06-metadata')
        click('reg-next')
        wait('reg-done')
        if args.connections:
            command('fill', '[data-testid="reg-source"]', '실파일 검수 원천')
            command('select', '[data-testid="reg-proj-select"]', '0000000000000000000000PRJA')
            command('find', 'role', 'button', 'click', '--name', '+ 추가', '--exact')
            click('reg-proj-quick-open')
            command('fill', '[aria-label="과제·논문 이름"]', '실파일 프로젝트 ' + session)
            command('find', 'role', 'button', 'click', '--name', '만들고 담기', '--exact')
            command('wait', '--fn', '!document.querySelector(\'[data-testid="reg-proj-quick"]\')')
            click('lin-add')
            wait('lin-pick-0000000000000000000000DSA1')
            click('lin-pick-0000000000000000000000DSA1')
            if '이 데이터로 연결' in command('snapshot'):
                command('find', 'role', 'button', 'click', '--name', '이 데이터로 연결', '--exact')
            command('fill', '[data-testid="lin-method"]', '브라우저 실파일 변환 검수')
            click('lin-confirm')
        snap('07-connections')
        click('reg-done')
        command('wait', '--fn', '!document.querySelector(\'[data-testid="upload-modal"]\')')
        wait('detail-header')
        url = command('get', 'url').strip()
        evidence['url'] = url
        command('reload')
        wait('detail-header')
        if unsupported:
            wait('not-renderable')
        else:
            drawn('[data-testid="preview-single-image"], [data-testid="dt-preview-salvage-image"]')
        detail = command('snapshot')
        if getattr(args, 'expect_partial', False):
            wait('partial-failure')
            if args.extra_file[0].name not in command('get', 'text', '[data-testid="partial-failure"]'):
                raise AssertionError('detail lost partial render warning')
        for expected in (name, summary, source.name):
            if expected not in detail:
                raise AssertionError('detail lost saved field: ' + expected)
        record('registered name, description and source filename persist after reload; ' + ('unsupported format explanation visible' if unsupported else 'rendered image visible'))
        if args.grid_file and 'preview-cursor-hud' not in command('get', 'html', '[data-testid="dataset-preview"]'):
            raise AssertionError('accepted actual reference grid did not produce a map with coordinates')
        if not unsupported and 'preview-cursor-hud' in command('get', 'html', '[data-testid="dataset-preview"]'):
            layer = '[data-testid="preview-layers"]'
            command('scrollintoview', '[data-testid="preview-zoom"]')
            before = command('get', 'attr', layer, 'style').strip()
            command('click', '[data-testid="preview-zoom"] button:first-child')
            after = command('get', 'attr', layer, 'style').strip()
            if before == after:
                raise AssertionError('map zoom did not change its displayed transform')
            command('click', '[data-testid="preview-zoom"] button:nth-child(3)')
            if before != command('get', 'attr', layer, 'style').strip():
                raise AssertionError('map reset did not restore its original transform')
            command('scrollintoview', '[data-testid="preview-viewport"]')
            command('hover', '[data-testid="preview-viewport"]')
            hud = command('get', 'text', '[data-testid="preview-cursor-hud"]')
            if not re.search(r'위도\s+-?\d', hud) or not re.search(r'경도\s+-?\d', hud):
                raise AssertionError('map cursor did not show numeric latitude and longitude')
            record('actual map zoom, reset and cursor latitude/longitude work')
        if args.connections:
            for expected in ('A 논문', '실파일 프로젝트 ' + session, 'Fpar_500m 검수', 'A 강우 원자료', '브라우저 실파일 변환 검수', '실파일 검수 원천', '10분'):
                if expected not in detail:
                    raise AssertionError('saved connection or metadata missing: ' + expected)
            record('project, lineage method, source and observation interval persist')
            node = '[data-testid="lin-node"][data-dataset-id="0000000000000000000000DSA1"]'
            command('scrollintoview', node)
            command('click', node)
            command('wait', '--fn', "location.pathname === '/datasets/0000000000000000000000DSA1'")
            command('open', url)
            wait('detail-header')
            record('parent lineage node navigates to its actual dataset')
            command('scrollintoview', '[data-testid="lin-rows"]')
            command('find', 'role', 'button', 'click', '--name', '가공 방식 수정', '--exact')
            command('find', 'label', '가공 방식', 'fill', '실파일 계보 수정 확인')
            command('find', 'role', 'button', 'click', '--name', '가공 방식 저장', '--exact')
            command('wait', '--text', '실파일 계보 수정 확인')
            command('reload')
            wait('detail-header')
            if '실파일 계보 수정 확인' not in command('snapshot'):
                raise AssertionError('lineage method edit did not persist')
            command('scrollintoview', '[data-testid="lin-rows"]')
            command('find', 'role', 'button', 'click', '--name', '연결 제거', '--exact')
            command('find', 'role', 'button', 'click', '--name', '이 연결 제거', '--exact')
            command('wait', '--fn', '!document.querySelector(\'[data-testid="lin-node"][data-dataset-id="0000000000000000000000DSA1"]\')')
            command('reload')
            wait('detail-header')
            if 'A 강우 원자료' in command('snapshot'):
                raise AssertionError('lineage removal did not persist')
            click('lin-edit')
            click('lin-pick-0000000000000000000000DSA1')
            command('fill', '[data-testid="lin-fix-method"]', '실파일 재연결 확인')
            click('lin-fix-save')
            command('wait', '--fn', '!document.querySelector(\'[data-testid="lin-fix-modal"]\')')
            command('reload')
            wait('detail-header')
            if '실파일 재연결 확인' not in command('snapshot'):
                raise AssertionError('lineage re-add did not persist')
            record('lineage method edit, relation removal and re-add persisted after reload')
        snap('08-detail')
        click('detail-edit-open')
        wait('edit-name')
        if args.connections:
            for field, expected in [('start', '2019-09-30'), ('end', '2019-10-07')]:
                value = command('get', 'value', f'[data-testid="edit-period-{field}"]').strip()
                if not value.startswith(expected):
                    raise AssertionError('observation period did not persist: ' + value)
            record('quick-created project, variable row and exact observation dates persisted')
        command('fill', '[data-testid="edit-name"]', name + ' edited')
        command('fill', '[data-testid="edit-summary"]', summary + ' edited')
        snap('09-edit')
        click('detail-edit-save')
        command('wait', '--fn', '!document.querySelector(\'[data-testid="detail-edit-form"]\')')
        command('reload')
        wait('detail-header')
        detail = command('snapshot')
        for expected in (name + ' edited', summary + ' edited'):
            if expected not in detail:
                raise AssertionError('edit did not persist: ' + expected)
        record('edited name and description persisted after reload')
        click('dt-files-toggle')
        wait('dt-files')
        download = out / ('download-' + source.name)
        original_button = '[aria-label=' + json.dumps(source.name + ' 다운로드', ensure_ascii=False) + ']'
        command('scrollintoview', original_button)
        command('download', original_button, str(download))
        if hashlib.sha256(download.read_bytes()).hexdigest() != evidence['sha256']:
            raise AssertionError('download bytes differ from actual source')
        record('browser original file download SHA256 matches uploaded source')
        if args.extra_file:
            archive = out / 'bundle.zip'
            command('scrollintoview', '[data-testid="detail-download"]')
            command('download', '[data-testid="detail-download"]', str(archive))
            with zipfile.ZipFile(archive) as bundle:
                expected = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in [source, *args.extra_file]}
                actual = {Path(n).name: hashlib.sha256(bundle.read(n)).hexdigest() for n in bundle.namelist() if not n.endswith('/')}
                if actual != expected:
                    raise AssertionError('bundle file count or content hash mismatch')
            record('bundle has every original file with matching SHA256')
        snap('10-final')
    except Exception as error:
        evidence['failure'] = str(error)
        (out / 'journey.json').write_text(json.dumps(evidence, ensure_ascii=False, indent=2))
        snap('failure')
        raise
