from fastapi.testclient import TestClient
from colab_ai.app.main import create_app
from colab_ai.kernel.config import Settings


def test_manifest_requires_configured_service_identity():
    client=TestClient(create_app(Settings()))
    assert client.get('/ontology-manifest').status_code==503


def test_manifest_checks_token_before_reading_dictionary(monkeypatch):
    from colab_ai.app import ontology_manifest
    monkeypatch.setattr(ontology_manifest,'load_manifest',lambda engine:{'version':'test'})
    client=TestClient(create_app(Settings(service_token='test-secret',dict_db_url='postgresql+psycopg://unused')))
    assert client.get('/ontology-manifest').status_code==401
    assert client.get('/ontology-manifest',headers={'Authorization':'Bearer wrong'}).status_code==401
    r=client.get('/ontology-manifest',headers={'Authorization':'Bearer test-secret'})
    assert r.status_code==200 and r.json()=={'version':'test'}


def test_unavailable_dictionary_does_not_look_like_empty_knowledge():
    client=TestClient(create_app(Settings(service_token='test-secret')))
    r=client.get('/ontology-manifest',headers={'Authorization':'Bearer test-secret'})
    assert r.status_code==503 and 'test-secret' not in r.text


def test_service_token_file_configuration(tmp_path):
    token=tmp_path/'token';token.write_text('test-secret\n')
    settings=Settings.from_env({'COLAB_AI_SERVICE_TOKEN_FILE':str(token)})
    assert settings.service_token=='test-secret'
    assert 'test-secret' not in repr(settings)
