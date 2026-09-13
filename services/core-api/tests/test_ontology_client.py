import json
import pytest
from test_search_ontology import manifest


def client():
    from colab_core.app.ontology_client import OntologyHttpClient
    return OntologyHttpClient


def test_client_rejects_missing_credentials():
    with pytest.raises(ValueError): client()('http://ai',token='')


def test_client_validates_body_and_actual_size():
    import http.server
    import threading
    body=json.dumps(manifest()).encode()
    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            assert self.path=='/ontology-manifest'
            assert self.headers['Authorization']=='Bearer test-secret'
            self.send_response(200);self.end_headers();self.wfile.write(body)
        def log_message(self,*args): pass
    server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    try:
        url=f'http://127.0.0.1:{server.server_port}'
        assert client()(url,token='test-secret').load_manifest()==manifest()
        with pytest.raises(ValueError): client()(url,token='test-secret',max_bytes=10).load_manifest()
        body=b'{"version":"wrong"}'
        with pytest.raises(ValueError): client()(url,token='test-secret').load_manifest()
    finally:
        server.shutdown();server.server_close();thread.join()


def test_redirect_is_not_followed_and_errors_do_not_expose_token():
    import http.server
    import threading
    visited=[]
    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            visited.append(self.path)
            self.send_response(302);self.send_header('Location','/other');self.end_headers()
        def log_message(self,*args):pass
    server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    try:
        with pytest.raises(ValueError) as err:client()(f'http://127.0.0.1:{server.server_port}',token='test-secret').load_manifest()
        assert visited==['/ontology-manifest']
        assert 'test-secret' not in str(err.value)
    finally:server.shutdown();server.server_close();thread.join()


def test_timeout_is_reported_as_failure(monkeypatch):
    c=client()('http://ai',token='test-secret')
    def timeout(*args,**kwargs):raise TimeoutError('test-secret')
    monkeypatch.setattr(c._opener,'open',timeout)
    with pytest.raises(ValueError,match='^ontology manifest request failed$'):c.load_manifest()


def test_proposal_http_projects_only_facts_and_flat_verified_concepts():
    import http.server,threading
    seen=[]
    class Handler(http.server.BaseHTTPRequestHandler):
        def do_POST(self):
            seen.append((self.path,self.headers.get('Authorization'),json.loads(self.rfile.read(int(self.headers['Content-Length'])))))
            self.send_response(200);self.end_headers();self.wfile.write(b'{"selections":[]}')
        def log_message(self,*args):pass
    server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    try:
        adapter=client()(f'http://127.0.0.1:{server.server_port}',token='fixture')
        source={'facts':[{'predicate':'name','value':'rain'}],'source_sha256':'not part of proposal wire'}
        proof={'node':{'concept_id':'rain','label':'강수'},'edges':[],'neighbors':[]}
        assert adapter.propose(source,[proof])=={'selections':[]}
        path,authorization,body=seen[0]
        assert path=='/search-concept-proposals' and authorization=='Bearer fixture'
        assert body['source']=={'facts':source['facts']}
        assert body['concepts'][0]['concept_id']=='rain' and 'node' not in body['concepts'][0]
    finally:server.shutdown();server.server_close();thread.join()
