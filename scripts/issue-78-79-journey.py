"""Issues 78/79: required metadata, persisted registration and pending-upload recovery."""
import hashlib
import json
import os
import subprocess
from pathlib import Path


def run(command, args, session):
    if not args.upload_file or not args.artifacts:
        raise RuntimeError('real upload file and artifacts required')
    root = Path(__file__).resolve().parents[1]
    out = args.artifacts.resolve()
    out.mkdir(parents=True, exist_ok=True)
    evidence = {'session': session, 'environment': 'disposable local API/DB/viz', 'steps': [],
                'sourceHashes': {name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in (
                    'frontend/src/components/upload/UploadModal.tsx',
                    'frontend/src/components/upload/PreviewPanel.tsx',
                    'frontend/src/components/upload/RegisterArea.tsx',
                    'frontend/src/components/common/VariableTable.tsx',
                    'contracts/seams/fe-core.yaml',
                    'services/core-api/src/colab_core/app/routes/ingestion.py')}}

    def save():
        (out / 'journey.json').write_text(json.dumps(evidence, ensure_ascii=False, indent=2))

    def record(step):
        evidence['steps'].append(step)
        save()
        print('PASS:', step, flush=True)

    def selector(testid):
        return f'[data-testid="{testid}"]'

    def click(testid):
        command('scrollintoview', selector(testid))
        command('click', selector(testid))

    def check(js):
        if not json.loads(command('eval', js).strip()):
            raise AssertionError(js)

    def snap(name):
        (out / (name + '.txt')).write_text(command('snapshot'))
        command('screenshot', str(out / (name + '.png')))

    def close():
        click('upload-close')
        if json.loads(command('eval', "!!document.querySelector('[data-testid=upload-close-confirm]')").strip()):
            command('find', 'role', 'button', 'click', '--name', '닫고 나가기', '--exact')
        command('wait', '--fn', "!document.querySelector('[data-testid=upload-modal]')")

    try:
        click('gnb-upload')
        command('upload', selector('up-drop-input'), str(args.upload_file.resolve()))
        for attempt in range(6):
            try:
                command('wait', selector('reg-open') + ':not(:disabled)')
                break
            except RuntimeError as error:
                if 'Wait timed out' not in str(error) or attempt == 5:
                    raise
        check("!document.querySelector('[data-testid=reg-viewonly]') && !!document.querySelector('[data-testid=reg-open]')")
        snap('01-next-only')
        record('real upload accepted; next enabled; preview-only choice absent')
        url = command('get', 'url').strip()
        click('reg-open')
        command('wait', selector('reg-s1'))
        check("!!document.querySelector('[data-testid=up-preview]')")
        if command('get', 'url').strip() != url:
            raise AssertionError('registration entry changed route')
        snap('02-register-preview')
        record('next opens classification in same modal and keeps preview')
        close()
        command('reload')
        command('wait', '[data-testid^="unfinished-register-"]')
        command('click', '[data-testid^="unfinished-register-"]')
        command('wait', selector('reg-s1'))
        check("!!document.querySelector('[data-testid=up-preview]') && !document.querySelector('[data-testid=reg-viewonly]')")
        snap('03-restored-after-reload')
        record('closing and reloading preserves accepted upload; registration resumes')
        command('find', 'role', 'button', 'click', '--name', '② 메타데이터 입력', '--exact')
        command('wait', selector('reg-s2'))
        command('fill', selector('reg-summary'), 'Issue 78 required metadata browser verification')
        click('reg-period-open')
        click('reg-period-unit-일')
        for part, value in [('year', '2025'), ('month', '06'), ('day', '01')]:
            command('fill', selector('reg-period-pop-start-' + part), value)
        click('reg-period-apply')
        click('reg-next')
        command('wait', selector('reg-s3'))
        click('reg-done')
        command('wait', selector('reg-s2'))
        check("document.activeElement?.id === 'reg-interval-value'")
        snap('04-interval-required')
        record('missing interval blocks registration and focuses metadata input')
        command('fill', selector('reg-interval-value'), '10')
        command('select', selector('reg-interval-unit'), '분')
        click('reg-next')
        command('wait', selector('reg-s3'))
        click('reg-done')
        check("document.activeElement?.id === 'reg-source-url'")
        snap('05-source-required')
        record('missing Lv0 source blocks registration and focuses URL input')
        command('fill', selector('reg-source-url'), 'https://example.org/issue78')
        command('fill', selector('reg-source-downloaded-on'), '2025-06-01')
        snap('06-ready-to-register')
        task = os.environ.get('E2E_GATE_TASK')
        if task:
            env = {**os.environ, 'COLAB_TASK_ID': task, 'AB_SESSION': session,
                   'COLAB_VISUAL_URLS': command('get', 'url').strip()}
            with (out / 'final-gates.log').open('w') as log:
                result = subprocess.run(['python3', 'scripts/agent-bridge.py', 'run-tool', 'gate', '--', 'task'],
                                        cwd=root, env=env, stdout=log, stderr=log)
            evidence['finalGateExitCode'] = result.returncode
            save()
            if result.returncode:
                raise AssertionError('declared gate set failed')
        click('reg-done')
        command('wait', selector('detail-header'))
        command('reload')
        command('wait', selector('detail-header'))
        check("document.body.innerText.includes('10분') || document.body.innerText.includes('10 분')")
        check("document.querySelector('[data-testid=ig-source-url]')?.innerText.includes('https://example.org/issue78')")
        check("document.querySelector('[data-testid=ig-source-downloaded-on]')?.innerText.includes('2025-06-01')")
        snap('07-persisted-detail')
        record('complete registration succeeds; interval and Lv0 source persist after reload')
        evidence['status'] = 'passed'
        save()
    except Exception as error:
        evidence.update(status='failed', failure=str(error))
        save()
        snap('failure')
        raise
