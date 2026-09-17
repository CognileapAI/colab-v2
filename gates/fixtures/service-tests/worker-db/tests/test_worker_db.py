"""Worker DB routing does not share pipeline state or accept missing URLs."""
import os
from types import SimpleNamespace
import pytest
import xdist_core_db


def test_pipeline_workers_receive_distinct_owned_database_entries(tmp_path,monkeypatch):
    monkeypatch.setenv('COLAB_SERVICE_DB_MODE','pipeline-worker')
    monkeypatch.setenv('COLAB_CORE_XDIST_DB_DIR',str(tmp_path))
    admin=tmp_path/'admin';admin.mkdir()
    monkeypatch.setenv('COLAB_CORE_XDIST_ADMIN_DB_DIR',str(admin))
    observed=[]
    for worker in ('gw0','gw1'):
        (tmp_path/worker).write_text('unit-database-'+worker)
        (admin/worker).write_text('unit-admin-'+worker)
        xdist_core_db.pytest_configure(SimpleNamespace(workerinput={'workerid':worker}))
        observed.append(os.environ['COLAB_PIPELINE_DB_URL'])
    assert observed==['unit-database-gw0','unit-database-gw1']


@pytest.mark.parametrize('missing',['directory','file','empty'])
def test_pipeline_worker_missing_database_fails_closed(tmp_path,monkeypatch,missing):
    monkeypatch.setenv('COLAB_SERVICE_DB_MODE','pipeline-worker')
    monkeypatch.delenv('COLAB_CORE_XDIST_DB_DIR',raising=False)
    if missing!='directory':
        monkeypatch.setenv('COLAB_CORE_XDIST_DB_DIR',str(tmp_path))
    if missing=='empty':
        (tmp_path/'gw0').write_text('')
    with pytest.raises(pytest.UsageError):
        xdist_core_db.pytest_configure(SimpleNamespace(workerinput={'workerid':'gw0'}))
