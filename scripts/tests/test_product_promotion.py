import hashlib, json
from pathlib import Path
import subprocess
import sys
import pytest
from scripts.product_promotion import build_approval


SCRIPT = Path(__file__).resolve().parents[1] / 'product_promotion.py'


@pytest.mark.parametrize('head_repo,head_ref,base_ref,expected', [
    ('example/repo', 'develop', 'product', 0),
    ('fork/repo', 'develop', 'product', 1),
    ('example/repo', 'feature/change', 'product', 1),
    ('example/repo', 'develop', 'develop', 1),
])
def test_promotion_check_rejects_wrong_source_before_merge(tmp_path, head_repo, head_ref, base_ref, expected):
    event = {'repository': {'full_name': 'example/repo'}, 'pull_request': {
        'base': {'ref': base_ref, 'sha': 'a' * 40, 'repo': {'full_name': 'example/repo'}},
        'head': {'ref': head_ref, 'sha': 'b' * 40, 'repo': {'full_name': head_repo}},
    }}
    path = tmp_path / 'event.json'
    path.write_text(json.dumps(event))
    result = subprocess.run([sys.executable, str(SCRIPT), '--event', str(path),
                             '--repository', 'example/repo'], capture_output=True, text=True)
    assert result.returncode == expected
    if expected == 0:
        assert json.loads(result.stdout) == {'base_sha': 'a' * 40, 'head_sha': 'b' * 40}

def test_approval_binds_manifest_and_all_required_success_checks(tmp_path):
    manifest=tmp_path/'manifest.json';manifest.write_text('{"reset":{"bucket":"prod"}}')
    event={'repository':{'full_name':'example/repo'},'pull_request':{'number':7,'merge_commit_sha':'c'*40,'base':{'ref':'product','sha':'a'*40,'repo':{'full_name':'example/repo'}},'head':{'ref':'develop','sha':'b'*40,'repo':{'full_name':'example/repo'}}}}
    checks=[{'name':'ci','head_sha':'c'*40,'status':'completed','conclusion':'success','app':{'id':1}},{'name':'security','head_sha':'c'*40,'status':'completed','conclusion':'success','app':{'id':2}}]
    required=[{'name':'ci','app_id':1},{'name':'security','app_id':2}]
    value=build_approval(event,'example/repo',manifest,required,checks)
    assert value=={'schema':'colab-product-promotion/1','pr_number':7,'base_sha':'a'*40,'head_sha':'b'*40,'check_sha':'c'*40,'manifest_sha256':hashlib.sha256(manifest.read_bytes()).hexdigest(),'required_checks':required}

@pytest.mark.parametrize('checks', [[],[{'name':'ci','head_sha':'c'*40,'status':'completed','conclusion':'failure','app':{'id':1}}],[{'name':'ci','head_sha':'c'*40,'status':'completed','conclusion':'success','app':{'id':9}}]])
def test_approval_rejects_missing_failed_or_wrong_source_checks(tmp_path,checks):
    manifest=tmp_path/'manifest';manifest.write_text('{}');event={'repository':{'full_name':'example/repo'},'pull_request':{'number':7,'merge_commit_sha':'c'*40,'base':{'ref':'product','sha':'a'*40,'repo':{'full_name':'example/repo'}},'head':{'ref':'develop','sha':'b'*40,'repo':{'full_name':'example/repo'}}}}
    with pytest.raises(ValueError,match='필수 검사'):build_approval(event,'example/repo',manifest,[{'name':'ci','app_id':1}],checks)
