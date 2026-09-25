"""Dedicated writer startup and fixed bounded callback transport."""
import importlib
import importlib.util
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
import pytest


def config():
    name='colab_ai.kernel.knowledge_config'
    assert importlib.util.find_spec(name), 'dedicated writer configuration missing'
    return importlib.import_module(name).KnowledgeSettings


def env():
    return {'COLAB_KNOWLEDGE_ENABLED':'true','COLAB_AI_KNOWLEDGE_WRITER_DB_URL':'postgresql+psycopg://invalid/db',
            'COLAB_KNOWLEDGE_WRITER_TOKEN':'writer','COLAB_KNOWLEDGE_CALLBACK_TOKEN':'callback',
            'COLAB_AI_SERVICE_TOKEN':'read','COLAB_KNOWLEDGE_SOURCE_URL':'http://127.0.0.1:12345',
            'COLAB_KNOWLEDGE_TIMEOUT_SECONDS':'2','COLAB_KNOWLEDGE_READER_TOKEN':'reader',
            'COLAB_KNOWLEDGE_DELETION_ENABLED':'false'}


@pytest.mark.parametrize('change',[{'COLAB_KNOWLEDGE_DELETION_TOKEN':'writer'},
    {'COLAB_KNOWLEDGE_DELETION_TOKEN':'callback'},{'COLAB_KNOWLEDGE_DELETION_TOKEN':'reader'},
    {'COLAB_KNOWLEDGE_DELETION_TOKEN':'read'},{'COLAB_KNOWLEDGE_DELETION_LAB':'invalid'},
    {'COLAB_KNOWLEDGE_DELETION_TOKEN':None},{'COLAB_KNOWLEDGE_DELETION_LAB':None}])
def test_deletion_capability_requires_distinct_token_and_fixed_lab(change):
    values={**env(),'COLAB_KNOWLEDGE_DELETION_ENABLED':'true',
            'COLAB_KNOWLEDGE_DELETION_TOKEN':'deletion','COLAB_KNOWLEDGE_DELETION_LAB':'0'*26,**change}
    values={key:value for key,value in values.items() if value is not None}
    with pytest.raises(ValueError):config().from_env(values)


def test_active_knowledge_requires_explicit_deletion_mode():
    values=env();values.pop('COLAB_KNOWLEDGE_DELETION_ENABLED')
    with pytest.raises(ValueError):config().from_env(values)


def test_health_reports_disabled_deletion_and_exposes_no_route():
    from fastapi.testclient import TestClient
    from colab_ai.app.knowledge_app import create_app
    with TestClient(create_app(config().from_env(env()))) as client:
        assert client.get('/healthz').json()['deletion_enabled'] is False
        assert client.post('/internal/knowledge/invalidate',json={}).status_code==404


@pytest.mark.parametrize('status',[401,403,503])
def test_deletion_transport_preserves_forbidden_vs_outage(status):
    from types import SimpleNamespace
    from colab_ai.app.source_authority_client import SourceAuthorityClient,DeletionAuthority
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def do_POST(self):
            assert self.path=='/internal/knowledge/deletion/validate'
            assert self.headers.get('X-CoLAB-Session') is None
            self.send_response(status);self.end_headers()
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    thread=Thread(target=server.serve_forever,daemon=True);thread.start()
    try:
        authority=DeletionAuthority(SourceAuthorityClient('http://127.0.0.1:'+str(server.server_port),token='deletion',timeout=1))
        command=SimpleNamespace(model_dump=lambda **kwargs:{})
        if status==503:
            with pytest.raises(ValueError,match='source authority unavailable'):authority.validate(command)
        else:assert authority.validate(command)=='forbidden'
    finally:
        server.shutdown();server.server_close();thread.join(timeout=2)


def test_disabled_does_not_require_writer_secrets():
    settings=config().from_env({'COLAB_KNOWLEDGE_ENABLED':'false'})
    assert settings.enabled is False


def test_disabled_app_exposes_no_writer_route():
    from fastapi.testclient import TestClient
    name='colab_ai.app.knowledge_app'
    assert importlib.util.find_spec(name), 'separate knowledge entrypoint missing'
    app=importlib.import_module(name).create_app(config().from_env({'COLAB_KNOWLEDGE_ENABLED':'false'}))
    with TestClient(app) as client:
        assert client.post('/internal/knowledge/replace',json={}).status_code == 404
        assert client.post('/internal/knowledge/read',json={}).status_code == 404


@pytest.mark.parametrize('other', ['writer', 'callback', 'read'])
def test_reader_credential_must_be_distinct(other):
    values = env(); values['COLAB_KNOWLEDGE_READER_TOKEN'] = other
    with pytest.raises(ValueError):
        config().from_env(values)


@pytest.mark.parametrize('path',['replace','read'])
def test_non_ascii_writer_header_is_unauthorized_envelope(path):
    from fastapi.testclient import TestClient
    from colab_ai.app.knowledge_app import create_app
    app=create_app(config().from_env(env()))
    with TestClient(app) as client:
        response=client.post('/internal/knowledge/'+path,json={},headers=[(b'authorization',b'Bearer \xff')])
    assert response.status_code==401
    assert set(response.json())=={'code','message'}
    assert response.headers['cache-control']=='no-store'


@pytest.mark.parametrize('key', list(env()))
def test_enabled_missing_required_configuration_is_rejected(key):
    values=env(); values.pop(key)
    with pytest.raises(ValueError): config().from_env(values)


@pytest.mark.parametrize('key,value', [('COLAB_KNOWLEDGE_WRITER_TOKEN','read'),('COLAB_KNOWLEDGE_CALLBACK_TOKEN','writer'),
    ('COLAB_KNOWLEDGE_TIMEOUT_SECONDS','nan'),('COLAB_KNOWLEDGE_TIMEOUT_SECONDS','0'),
    ('COLAB_KNOWLEDGE_SOURCE_URL','http://user:secret@127.0.0.1')])
def test_unsafe_configuration_is_rejected(key,value):
    values=env();values[key]=value
    with pytest.raises(ValueError):config().from_env(values)


@pytest.mark.parametrize('mode',['redirect','large','unavailable','forbidden'])
@pytest.mark.parametrize('reading',[False,True])
def test_callback_transport_fails_closed(mode,reading):
    name='colab_ai.app.source_authority_client'
    assert importlib.util.find_spec(name), 'fixed source callback missing'
    client_type=importlib.import_module(name).SourceAuthorityClient
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args): pass
        def do_POST(self):
            self.send_response(302 if mode=='redirect' else 503 if mode=='unavailable' else 401 if mode=='forbidden' else 200)
            if mode=='redirect':self.send_header('Location','http://127.0.0.1:1/secret')
            self.end_headers()
            if mode=='large':self.wfile.write(b'x'*1025)
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    thread=Thread(target=server.serve_forever,daemon=True);thread.start()
    try:
        client=client_type('http://127.0.0.1:'+str(server.server_port),token='callback',timeout=1,max_bytes=1024)
        with pytest.raises(ValueError,match='forbidden' if mode=='forbidden' else 'source authority unavailable'):
            if reading:
                from types import SimpleNamespace
                client.read(SimpleNamespace(model_dump=lambda **kwargs: {}),session_token='tracked-session')
            else:client.request({'command':{}},session_token='tracked-session')
    finally:
        server.shutdown();server.server_close();thread.join(timeout=2)
