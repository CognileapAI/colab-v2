"""Evaluate the real browser extraction script against independently built DOMs."""
import importlib.util
import json
from pathlib import Path
import subprocess
import pytest

ROOT = Path(__file__).resolve().parents[4]
SPEC = importlib.util.spec_from_file_location('project_runner', Path(__file__).parents[1] / 'runner.py')
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)
ID = '01M2EWQH8CES9TDC39FSFMKXVQ'


def install_dom(monkeypatch, html):
    def evaluate(script, **kwargs):
        program = '''const {JSDOM}=require('jsdom');
const input=JSON.parse(require('fs').readFileSync(0,'utf8'));
const dom=new JSDOM(input.html,{runScripts:'outside-only'});
console.log(dom.window.eval(input.script));'''
        result = subprocess.run(['node', '-e', program], cwd=ROOT / 'frontend',
                                input=json.dumps({'html': html, 'script': script}),
                                capture_output=True, text=True, check=True)
        return json.loads(result.stdout)
    monkeypatch.setattr(runner, 'js', evaluate)


@pytest.mark.parametrize('html', [
    f'<a data-testid="project-card-{ID}" href="/projects/{ID}"><h3 class="pc-t">관측 연구</h3><p>설명과 지표 8개</p></a>',
    f'<table><tbody><tr data-testid="project-trow-{ID}"><td class="pname">관측 연구<span class="chip">닫힘</span></td><td>8개</td></tr></tbody></table>',
])
def test_project_identity_comes_from_exact_name_and_row_id(monkeypatch, html):
    install_dom(monkeypatch, html)
    assert runner.project_index() == {'관측 연구': ID}


def test_duplicate_project_names_are_not_silently_collapsed(monkeypatch):
    other = '01M2EWQH8CES9TDC39FSFMKXVR'
    install_dom(monkeypatch, f'<a data-testid="project-card-{ID}"><h3 class="pc-t">같은 이름</h3></a>'
                f'<a data-testid="project-card-{other}"><h3 class="pc-t">같은 이름</h3></a>')
    with pytest.raises(runner.Fail):
        runner.project_index()


def test_account_result_ignores_empty_list_status(monkeypatch):
    from types import SimpleNamespace
    monkeypatch.setattr(runner, 'CFG', SimpleNamespace(dry_run=False))
    install_dom(monkeypatch, '<div class="login"><div><section data-testid="account-create"></section></div>'
                '<div hidden><section><p role="status">조건에 맞는 계정이 없어요.</p></section></div>'
                '<p role="status">계정을 추가했어요.</p></div>')
    assert runner.js('JSON.stringify(document.querySelector(' + json.dumps(runner.ACCOUNT_CSS['status']) + ')?.textContent || "")') == '계정을 추가했어요.'


def test_account_failure_stops_before_next_account(monkeypatch):
    from types import SimpleNamespace
    monkeypatch.setattr(runner, 'CFG', SimpleNamespace(accounts_file='unused', force=False, dry_run=False))
    entries = [{'email': 'a@example.org', 'name': 'A', 'role': '교수', 'lab': 'L', 'admin': True},
               {'email': 'b@example.org', 'name': 'B', 'role': '교수', 'lab': 'L', 'admin': True}]
    monkeypatch.setattr(runner, 'load_accounts_file', lambda _: entries)
    monkeypatch.setattr(runner, 'account_initial_password', lambda: 'test-only')
    for name in ('log', 'save_state', 'open_url', 'activate'):
        monkeypatch.setattr(runner, name, lambda *a, **k: None)
    monkeypatch.setattr(runner, 'wait_css', lambda *a: True)
    monkeypatch.setattr(runner, 'js', lambda *a, **k: True)
    calls = []
    def failed(*args):
        calls.append(args[1]['email'])
        return 'failed', 'validation rejected'
    monkeypatch.setattr(runner, 'create_account', failed)
    st = {'steps': {}}
    with pytest.raises(runner.Fail):
        runner.phase_accounts(st, {})
    assert calls == ['a@example.org']
    assert st['steps']['accounts']['status'] == 'partial'


@pytest.mark.parametrize('entry,accepted', [
    ({'role': '교수', 'admin': True}, False),
    ({'role': '', 'admin': True}, True),
    ({'role': '', 'admin': False}, False),
    ({'role': '', 'lab': 'L', 'admin': True}, False),
])
def test_account_affiliation_must_be_explicit_pair(tmp_path, entry, accepted):
    path = tmp_path / 'accounts.json'
    path.write_text(json.dumps([dict(email='a@example.org', name='A', **entry)]))
    path.chmod(0o600)
    if accepted:
        assert runner.load_accounts_file(path)[0]['role'] == ''
    else:
        with pytest.raises(runner.Fail):
            runner.load_accounts_file(path)


def test_account_form_opens_creation_tab_before_editing(monkeypatch):
    from types import SimpleNamespace
    monkeypatch.setattr(runner, 'CFG', SimpleNamespace(dry_run=False))
    selected = []
    monkeypatch.setattr(runner, 'activate', lambda css, *args: selected.append(css))
    monkeypatch.setattr(runner, 'wait_css', lambda *args: True)
    def browser(script, **kwargs):
        assert selected, "creation tab must be activated before checking visibility"
        return True
    monkeypatch.setattr(runner, 'js', browser)
    runner.open_account_form()
    assert selected == ['[role="tablist"][aria-label="계정 관리 탭"] [role="tab"]:last-child']


def test_account_form_waits_for_delayed_visibility(monkeypatch):
    from types import SimpleNamespace
    monkeypatch.setattr(runner, 'CFG', SimpleNamespace(dry_run=False))
    monkeypatch.setattr(runner, 'activate', lambda *args: None)
    monkeypatch.setattr(runner, 'wait_css', lambda *args: True)
    monkeypatch.setattr(runner.time, 'sleep', lambda *args: None)
    visibility = iter([False, False, True])
    monkeypatch.setattr(runner, 'js', lambda *args: next(visibility))
    runner.open_account_form()
