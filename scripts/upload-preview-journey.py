"""Actual browser journey for the approved upload preview plan.

Invoked by e2e-login.py inside its disposable DB, local storage and worker run.
No production credentials, data, or mock API responses are used.
"""
from pathlib import Path
import hashlib
import json
import os
import re
import zipfile

from sqlalchemy import create_engine, text


def run(command, args, session):
    if not args.upload_file or not args.artifacts or not args.viz_python:
        raise RuntimeError('journey requires upload-file, artifacts and viz-python')
    out = args.artifacts.resolve()
    out.mkdir(parents=True, exist_ok=True)
    source = args.upload_file.resolve()
    unsupported = getattr(args, 'expect_unsupported', False)
    contract_expansion = getattr(args, 'contract_expansion', False)
    evidence = {'session': session, 'file': source.name, 'bytes': source.stat().st_size,
                'sha256': hashlib.sha256(source.read_bytes()).hexdigest(), 'steps': []}
    def record(step):
        evidence['steps'].append(step)
        (out / 'journey.json').write_text(json.dumps(evidence, ensure_ascii=False, indent=2))
        print('PASS:', step, flush=True)
    def click(testid):
        command('scrollintoview', f'[data-testid="{testid}"]')
        command('click', f'[data-testid="{testid}"]')
    def click_named_button(name):
        interactive = command('snapshot', '-i')
        match = re.search(rf'button {re.escape(json.dumps(name, ensure_ascii=False))} \[ref=(e\d+)\]', interactive)
        if not match:
            raise AssertionError('button is not available: ' + name)
        command('focus', '@' + match.group(1))
        command('press', 'Enter')
    def wait(testid):
        command('wait', f'[data-testid="{testid}"]')
    def snap(name):
        (out / (name + '.txt')).write_text(command('snapshot'))
        command('screenshot', str(out / (name + '.png')))
    def drawn(selector):
        command('wait', '--fn', f'Array.from(document.querySelectorAll({json.dumps(selector)})).some(i=>i.complete && i.naturalWidth>0)')
    def scoped_dataset_rows(dataset_name):
        engine = create_engine(os.environ['E2E_DATABASE_URL'], pool_pre_ping=True, future=True)
        try:
            with engine.begin() as connection:
                connection.execute(text('SET TRANSACTION READ ONLY'))
                connection.execute(text("SELECT set_config('app.current_lab', :value, true)"),
                                   {'value': '0000000000000000000000000A'})
                connection.execute(text("SELECT set_config('app.current_account', :value, true)"),
                                   {'value': '000000000000000000000000A1'})
                rows = connection.execute(text("""
                    SELECT d.id, x.human_grid_description,
                           (SELECT count(*) FROM d3_dataset_representative_image r
                             WHERE r.dataset_id = d.id) AS representative_images
                      FROM d3_dataset d
                      JOIN d3_dataset_description x ON x.dataset_id = d.id
                     WHERE x.name = :name AND d.deleted_at IS NULL
                     ORDER BY d.id
                """), {'name': dataset_name}).mappings().all()
                return [dict(row) for row in rows]
        finally:
            engine.dispose()
    try:
        command('set', 'viewport', '1440', '1000')
        command('find', 'role', 'button', 'click', '--name', '업로드', '--exact')
        snap('01-empty')
        if contract_expansion:
            width = int(re.search(r'\d+', command(
                'eval',
                'Math.round(document.querySelector(\'[data-testid="upload-modal"]\').getBoundingClientRect().width)',
            )).group())
            evidence['initialModalWidthPx'] = width
            if width != 620:
                raise AssertionError(f'initial upload modal width is {width}px, expected 620px')
            record('1440x1000 initial upload modal is 620px wide')
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
        if contract_expansion:
            invalid_image = out / 'invalid-representative.png'
            invalid_image.write_bytes(b'not a png image\n')
            command('upload', '[data-testid="up-thumb-input"]', str(invalid_image))
            if invalid_image.name not in command('get', 'value', '[data-testid="up-thumb-input"]'):
                raise AssertionError('invalid representative image was not retained for the server rejection path')
            record('invalid PNG bytes selected before dataset creation')
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
            if contract_expansion:
                command('fill', '[data-testid="reg-grid-description"]', '사람이 적은 HDF 격자 설명')
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
            if contract_expansion:
                command('fill', '[aria-label="데이터셋 이름 또는 파일명 검색"]', 'a1-body.csv')
                command('wait', '--text', 'a1-body.csv')
                picker = command('get', 'text', '[data-testid="lin-picker"]')
                if 'A 강우 원자료' not in picker or 'a1-body.csv' not in picker:
                    raise AssertionError('filename search did not show the accessible DSA1 candidate and filename')
                record('lineage candidate searched by accessible body filename and displayed DSA1 filename')
            wait('lin-pick-0000000000000000000000DSA1')
            click('lin-pick-0000000000000000000000DSA1')
            if '이 데이터로 연결' in command('snapshot'):
                command('find', 'role', 'button', 'click', '--name', '이 데이터로 연결', '--exact')
            command('fill', '[data-testid="lin-method"]', '브라우저 실파일 변환 검수')
            click('lin-confirm')
        snap('07-connections')
        click('reg-done')
        if contract_expansion:
            wait('up-created-recovery')
            recovery = command('snapshot')
            if '데이터셋은 만들었지만 대표 그림을 저장하지 못했어요' not in recovery:
                raise AssertionError('invalid image did not reach the representative-image recovery state')
            if command('eval', "Boolean(document.querySelector('[data-testid=reg-name], .up-file-management'))").strip() != 'false':
                raise AssertionError('registration metadata or original-file management remained editable after creation')
            rows = scoped_dataset_rows(name)
            if len(rows) != 1 or rows[0]['representative_images'] != 0:
                raise AssertionError('failed representative image path did not preserve exactly one dataset without an image')
            evidence['datasetCreateProof'] = {
                'afterInvalidImage': rows,
                'invalidImageRejected': True,
            }
            snap('07-recovery')
            record('invalid image PUT was rejected; recovery keeps exactly one created dataset and locks saved inputs')
            command('upload', '[data-testid="up-thumb-input"]', str(out / '04-preview.png'))
            command('find', 'role', 'button', 'click', '--name', '대표 그림 다시 저장', '--exact')
        command('wait', '--fn', '!document.querySelector(\'[data-testid="upload-modal"]\')')
        wait('detail-header')
        url = command('get', 'url').strip()
        evidence['url'] = url
        if contract_expansion:
            dataset_id = url.rstrip('/').split('/')[-1]
            rows = scoped_dataset_rows(name)
            if len(rows) != 1 or rows[0]['id'] != dataset_id or rows[0]['representative_images'] != 1:
                raise AssertionError('valid image retry did not reuse the one created dataset')
            evidence['datasetCreateProof']['afterValidRetry'] = rows
            drawn('img[alt="사용자 대표 그림"]')
            record('valid PNG retry stored on the same dataset and decoded as the custom image')
        command('reload')
        wait('detail-header')
        if contract_expansion:
            drawn('img[alt="사용자 대표 그림"]')
            record('custom representative image remains decoded after detail reload')
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
        if contract_expansion:
            human_grid = command('get', 'text', '[data-testid="ig-grid-human"]')
            automatic_grid = command('get', 'text', '[data-testid="ig-grid-automatic"]')
            if human_grid.strip() != '사람이 적은 HDF 격자 설명' or '자동 판독:' not in automatic_grid:
                raise AssertionError('detail did not show human grid text with automatic analysis as supporting text')
            evidence['gridBeforeClear'] = {'human': human_grid.strip(), 'automatic': automatic_grid.strip()}
            record('human grid description is primary and automatic analysis remains supporting text')
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
        if contract_expansion:
            first_src = command('get', 'attr', 'img[alt="사용자 대표 그림"]', 'src').strip()
            command('upload', '[data-testid="detail-representative-input"]', str(out / '08-detail.png'))
            click_named_button('대표 그림 저장')
            command('wait', '--fn', f'document.querySelector(\'img[alt="사용자 대표 그림"]\')?.src !== {json.dumps(first_src)}')
            drawn('img[alt="사용자 대표 그림"]')
            second_src = command('get', 'attr', 'img[alt="사용자 대표 그림"]', 'src').strip()
            if first_src == second_src:
                raise AssertionError('representative image replacement did not commit a new decoded object URL')
            command('reload')
            wait('detail-header')
            drawn('img[alt="사용자 대표 그림"]')
            record('detail replaced the representative image and retained it after reload')
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
        if contract_expansion:
            command('focus', '[data-testid="edit-gridDescription"]')
            command('press', 'Control+A')
            command('press', 'Backspace')
            if command('get', 'value', '[data-testid="edit-gridDescription"]').strip():
                raise AssertionError('human grid description input did not clear before save')
        snap('09-edit')
        click('detail-edit-save')
        command('wait', '--fn', '!document.querySelector(\'[data-testid="detail-edit-form"]\')')
        command('reload')
        wait('detail-header')
        detail = command('snapshot')
        for expected in (name + ' edited', summary + ' edited'):
            if expected not in detail:
                raise AssertionError('edit did not persist: ' + expected)
        if contract_expansion:
            cleared_rows = scoped_dataset_rows(name + ' edited')
            if len(cleared_rows) != 1 or cleared_rows[0]['human_grid_description'] is not None:
                raise AssertionError('server retained the human grid description after the clear save')
            automatic_primary = command('get', 'text', '[data-testid="ig-grid-human"]').strip()
            if not automatic_primary or automatic_primary == '사람이 적은 HDF 격자 설명':
                raise AssertionError('clearing human grid description did not restore automatic grid as primary')
            if command('eval', "Boolean(document.querySelector('[data-testid=ig-grid-automatic]'))").strip() != 'false':
                raise AssertionError('automatic grid remained duplicated as supporting text after human text was cleared')
            evidence['gridAfterClear'] = {'primary': automatic_primary, 'supportingTextPresent': False}
            record('clearing human grid text restored automatic analysis as the primary value after reload')
        record('edited name and description persisted after reload')
        if contract_expansion:
            click_named_button('자동 그림 사용')
            command('wait', '--fn', '!document.querySelector(\'img[alt="사용자 대표 그림"]\')')
            command('reload')
            wait('detail-header')
            if command('eval', "Boolean(document.querySelector('img[alt=\"사용자 대표 그림\"]'))").strip() != 'false':
                raise AssertionError('custom representative image returned after automatic-image deletion and reload')
            drawn('[data-testid="preview-single-image"], [data-testid="dt-preview-salvage-image"]')
            rows = scoped_dataset_rows(name + ' edited')
            if len(rows) != 1 or rows[0]['representative_images'] != 0:
                raise AssertionError('automatic-image deletion did not remove the custom image metadata')
            evidence['datasetCreateProof']['afterAutomaticFallback'] = rows
            snap('09-automatic-fallback')
            record('automatic-image action removed the custom image and preserved the decoded automatic preview after reload')
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
