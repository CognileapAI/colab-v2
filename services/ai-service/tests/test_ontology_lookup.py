from copy import deepcopy
import pytest
from test_ontology_manifest import content
from colab_ai.app.ontology_manifest import build_manifest


def test_lookup_returns_bounded_versioned_one_hop_proof():
    from colab_ai.app.ontology_lookup import lookup
    data=content(); version=build_manifest(data)['version']
    result=lookup(data,query='강수 자료',expected_version=version)
    assert result['version']==version
    assert [p['node']['concept_id'] for p in result['concepts']]==['rain']
    assert {n['concept_id'] for n in result['concepts'][0]['neighbors']}=={'rain','rain-alt'}
    assert result['concepts'][0]['edges'][0]['relation']=='같은 말이다'


def test_lookup_rejects_stale_version_and_unbounded_query():
    from colab_ai.app.ontology_lookup import lookup
    with pytest.raises(ValueError):lookup(content(),query='강수',expected_version='0'*64)
    with pytest.raises(ValueError):lookup(content(),query='x'*16001,expected_version=build_manifest(content())['version'])


def test_lookup_does_not_expand_to_every_concept():
    from colab_ai.app.ontology_lookup import lookup
    result=lookup(content(),query='no matching word',expected_version=build_manifest(content())['version'])
    assert result['concepts']==[]


def test_lookup_http_auth_and_stale(monkeypatch):
    from fastapi.testclient import TestClient
    from colab_ai.app.main import create_app
    from colab_ai.app import ontology_manifest
    from colab_ai.kernel.config import Settings
    monkeypatch.setattr(ontology_manifest,'load_content',lambda engine:content())
    client=TestClient(create_app(Settings(service_token='fixture',dict_db_url='postgresql+psycopg://unused')))
    body={'query':'강수','expected_version':build_manifest(content())['version']}
    assert client.post('/ontology-concepts',json=body).status_code==401
    r=client.post('/ontology-concepts',json=body,headers={'Authorization':'Bearer fixture'})
    assert r.status_code==200 and len(r.json()['concepts'])==1
    body['expected_version']='0'*64
    assert client.post('/ontology-concepts',json=body,headers={'Authorization':'Bearer fixture'}).status_code==409


def test_lookup_rejects_unauthorized_before_consuming_body(monkeypatch):
    from fastapi.testclient import TestClient
    from starlette.requests import Request
    from colab_ai.app.main import create_app
    from colab_ai.kernel.config import Settings
    async def must_not_read(self):
        raise AssertionError('unauthorized request body was consumed')
    monkeypatch.setattr(Request,'body',must_not_read)
    client=TestClient(create_app(Settings(service_token='fixture')))
    assert client.post('/ontology-concepts',content=b'ignored').status_code==401
