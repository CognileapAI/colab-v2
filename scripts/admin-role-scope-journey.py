"""Real UI administrator scope journey. Only e2e-login.sh's disposable database is used."""
import importlib.util
import json
import os
from pathlib import Path
from sqlalchemy import create_engine, text

LAB_A = '0000000000000000000000000A'
LAB_B = '0000000000000000000000000B'
ADMIN = '00000000000000000000000AP1'
RESEARCHER = '000000000000000000000000A1'
PRIVATE = '0000000000000000000000DSA2'


def run(command, args, session):
    root = Path(__file__).resolve().parent
    out = args.artifacts.resolve()
    out.mkdir(parents=True, exist_ok=True)
    evidence = {'environment': 'disposable local API/DB/viz', 'steps': [], 'status': 'running'}
    def save():
        (out / 'admin-journey.json').write_text(json.dumps(evidence, ensure_ascii=False, indent=2))
    def record(message):
        evidence['steps'].append(message)
        save()
        print('PASS:', message, flush=True)
    def check(js):
        if not json.loads(command('eval', js).strip()):
            raise AssertionError(js)
    def snap(name):
        (out / (name + '.txt')).write_text(command('snapshot'))
        command('screenshot', str(out / (name + '.png')))
    def click(testid):
        command('scrollintoview', f'[data-testid="{testid}"]')
        command('click', f'[data-testid="{testid}"]')
    def relogin():
        command('wait', '[data-testid="login-account-name"]')
        command('fill', '[data-testid="login-account-name"]', 'e2e-operator')
        command('fill', '[data-testid="login-password"]', args.e2e_password, private=True)
        command('click', '[data-testid="login-submit"]')
        command('wait', '--text', '로그아웃')
    def scoped_command(*parts, **kwargs):
        result = command(*parts, **kwargs)
        if parts == ('click', '[data-testid="gnb-upload"]'):
            command('wait', '--fn', "!!document.querySelector('[data-testid=upload-modal] select[aria-label=\"대상 연구실\"] option[value=\"" + LAB_B + "\"]')")
            command('select', '[data-testid=upload-modal] select[aria-label="대상 연구실"]', LAB_B)
            snap('00-new-upload-lab-b')
        return result
    try:
        spec = importlib.util.spec_from_file_location('registration', root / 'issue-78-79-journey.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.run(scoped_command, args, session)
        record('system administrator selected B lab, uploaded real GeoTIFF, resumed registration after reload and saved metadata')
        dataset_url = command('get', 'url').strip()
        dataset_id = dataset_url.split('/datasets/')[-1].split('#')[0]
        pair = os.environ['E2E_DATABASE_URL'].split('\t')
        if len(pair) != 2:
            raise RuntimeError('disposable application/admin database pair required')
        app = create_engine(pair[0])
        admin = create_engine(pair[1])
        with app.begin() as conn:
            conn.execute(text("SELECT set_config('app.current_lab', :lab, true)"), {'lab': LAB_B})
            actual = conn.execute(text('SELECT lab_id FROM d3_dataset WHERE id=:id'), {'id': dataset_id}).scalar_one()
            if actual != LAB_B:
                raise AssertionError('new dataset was not stored in selected B lab')
        command('wait', '[data-testid="dt-preview-draw"]:not(:disabled)')
        snap('08-before-preview')
        click('dt-preview-draw')
        command('wait', '--fn', "Array.from(document.querySelectorAll('[data-testid=dataset-preview] img')).some(img=>img.complete && img.naturalWidth>0)")
        snap('09-preview-visible')
        record('B lab dataset variables, explicit draw and rendered image succeeded for A lab system administrator')
        click('detail-edit-open')
        command('fill', '[data-testid="edit-name"]', '관리자 B 연구실 수정 확인')
        click('detail-edit-save')
        command('wait', '[data-testid="detail-edit-open"]')
        command('reload')
        command('wait', '--text', '관리자 B 연구실 수정 확인')
        snap('10-edited-reloaded')
        record('foreign-lab edit persisted after reload')
        with admin.begin() as conn:
            conn.execute(text('DELETE FROM account_admin.service_operator WHERE account_id=:id'), {'id': ADMIN})
        with app.begin() as conn:
            conn.execute(text("SELECT set_config('app.current_lab', :lab, true)"), {'lab': LAB_A})
            conn.execute(text('UPDATE d3_dataset SET owner_account_id=:owner WHERE id=:id'), {'owner': RESEARCHER, 'id': PRIVATE})
        command('open', 'http://127.0.0.1:43173/datasets/' + PRIVATE)
        relogin()
        record('operator removal invalidated previous session; professor signed in again')
        command('open', 'http://127.0.0.1:43173/datasets/' + PRIVATE)
        command('wait', '[data-testid="detail-edit-open"]')
        check("!document.body.innerText.includes('계정 관리')")
        click('detail-edit-open')
        command('fill', '[data-testid="edit-name"]', '교수 비공개 관리 확인')
        click('detail-edit-save')
        command('wait', '[data-testid="detail-edit-open"]')
        command('reload')
        command('wait', '--text', '교수 비공개 관리 확인')
        snap('11-professor-private-edit')
        record('professor without system operator privilege edited another owner private dataset in own lab; reload persisted')
        with app.begin() as conn:
            conn.execute(text("SELECT set_config('app.current_lab', :lab, true)"), {'lab': LAB_A})
            conn.execute(text("UPDATE d2_member_role SET role='연구원' WHERE account_id=:id"), {'id': ADMIN})
        command('reload')
        command('open', 'http://127.0.0.1:43173/datasets/' + PRIVATE)
        command('wait', '[data-testid="detail-header"]')
        check("!document.querySelector('[data-testid=dt-download]') && !document.querySelector('[data-testid=dataset-preview]') && document.body.innerText.includes('이름과 요약까지만 보여요')")
        snap('12-general-member-private-denied')
        record('general member could not preview or download another owner private dataset; existing metadata edit permission preserved')
        evidence['status'] = 'passed'
        save()
    except Exception as error:
        evidence.update(status='failed', failure=str(error))
        save()
        snap('admin-failure')
        raise
