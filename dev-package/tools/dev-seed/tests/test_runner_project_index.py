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
