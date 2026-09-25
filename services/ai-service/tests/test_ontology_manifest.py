"""Content revisions, including lexical discovery and one-hop dependencies."""
from copy import deepcopy


def api():
    from colab_ai.app import ontology_manifest
    return ontology_manifest


def content():
    return {'methods': [], 'topics': [], 'places': [], 'concepts': [
        {'concept_id':'rain','kind':'주제','label':'강수','expandable':True,'source_note':'test'},
        {'concept_id':'ndvi','kind':'주제','label':'식생','expandable':True,'source_note':'test'},
        {'concept_id':'rain-alt','kind':'주제','label':'강우','expandable':True,'source_note':'test'},
    ], 'edges': [{'src':'rain','dst':'rain-alt','relation':'같은 말이다','source_note':'test'}]}


def test_manifest_is_stable_across_row_order_and_timestamps():
    a=content(); b=deepcopy(a)
    b['concepts'].reverse()
    for row in b['concepts']: row['created_at']='different time'
    assert api().build_manifest(a)==api().build_manifest(b)


def test_neighbor_semantics_changes_related_digest_only():
    a=content(); b=deepcopy(a); b['concepts'][2]['expandable']=False
    old,new=api().build_manifest(a),api().build_manifest(b)
    assert old['version']!=new['version']
    assert old['entries']['discovery']==new['entries']['discovery']
    assert old['entries']['concept:rain']!=new['entries']['concept:rain']
    assert old['entries']['concept:ndvi']==new['entries']['concept:ndvi']


def test_new_alias_changes_discovery_even_without_a_concept():
    a=content(); b=deepcopy(a); b['places']=[{'alias':'새 지명','place_name':'새 지역','source_note':'test'}]
    assert api().build_manifest(a)['entries']['discovery']!=api().build_manifest(b)['entries']['discovery']


def test_edge_removal_invalidates_both_endpoints():
    a=content(); b=deepcopy(a); b['edges']=[]
    old,new=api().build_manifest(a),api().build_manifest(b)
    for key in ['concept:rain','concept:rain-alt']:
        assert old['entries'][key]!=new['entries'][key]


import pytest


@pytest.mark.dictdb
def test_manifest_reads_real_dictionary_in_one_statement(dict_db_url):
    from sqlalchemy import event
    from colab_ai.kernel.db import make_engine
    engine=make_engine(dict_db_url)
    statements=[]
    event.listen(engine,'before_cursor_execute',lambda conn,cursor,statement,params,context,many: statements.append(statement))
    try:
        result=api().load_manifest(engine)
        assert len(statements)==1
        assert statements[0].lstrip().startswith('SELECT')
        assert 'discovery' in result['entries']
        assert len(result['entries'])>1
        assert result==api().load_manifest(engine)
    finally:
        engine.dispose()
def test_typed_semantics_version_invalidates_discovery(monkeypatch):
    from colab_ai.app import ontology_manifest
    content={k:[] for k in ('methods','topics','places','concepts','edges')}
    before=ontology_manifest.build_manifest(content)
    monkeypatch.setattr(ontology_manifest,'SEMANTIC_VERSION','changed-for-test')
    after=ontology_manifest.build_manifest(content)
    assert before['entries']['discovery'] != after['entries']['discovery']
    assert before['version'] != after['version']
