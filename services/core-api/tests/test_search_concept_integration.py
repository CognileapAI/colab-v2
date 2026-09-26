import hashlib,json
import pytest
from conftest import LAB_A,ACC_A_RES,ACC_A_PROF,TOKEN_RES,TOKEN_PROF,TOKEN_B,DS_A2,auth
from test_search_changes import sources,scoped
from test_search_refresh_tools import make_tools
from colab_core.app.main import API_PREFIX
from colab_core.app.search_refresh_runner import run_batch

pytestmark=pytest.mark.search_golden


def kit(factory):
    node={'concept_id':'rain','label':'강수','kind':'주제','expandable':True,'source_note':'fixture'}
    alias={**node,'concept_id':'rain-alt','label':'rain-alias'}
    edges=[{'src':'rain','dst':'rain-alt','relation':'같은 말이다','source_note':'fixture'}]
    proof={'node':node,'edges':edges,'neighbors':[node,alias]}
    digest=lambda v:hashlib.sha256(json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    entries={'discovery':'b'*64,'concept:rain':digest(['dictionary-first-one-hop-fanout-six-v1',node,edges,[node,alias]])}
    body={'protocol':'ontology-manifest-v1','entries':entries};manifest={**body,'version':digest(body)}
    class Port:
        def load_manifest(self):return manifest
        def lookup(self,**kwargs):return {'version':manifest['version'],'concepts':[proof]}
        def propose(self,source,concepts):
            return {'selections':[{'concept_id':'rain','predicate':'file_name','quote':'강수'}]} if any(f['predicate']=='file_name' and '강수' in str(f['value']) for f in source['facts']) else {'selections':[]}
    return make_tools(factory,Port())


class Search:
    def interpret(self,**kwargs):return {'terms':['rain-alias'],'topic':None,'source':'literal','isDataQuery':True,'degraded':False,'degradedReason':None}


def search(client,token=TOKEN_RES):
    return client.post(f'{API_PREFIX}/dataset-searches',headers=auth(token),json={'query':'rain-alias','limit':100})


def test_selected_file_concept_reaches_real_search_and_revoked_body_disappears(sources,sql,session_factory,p2_client):
    sql("UPDATE d3_file SET file_name='강수.csv' WHERE id=:id",{'id':sources[1]})
    result=run_batch(kit(session_factory),max_jobs=10)
    assert result['failed']==0
    assert result['ready']==2,result
    client=p2_client();client.app.state.searches=Search()
    response=search(client,TOKEN_PROF)
    assert response.status_code==200,response.text
    hit=next((i for i in response.json()['items'] if i['datasetId']==sources[0]),None)
    # 「관련 개념」 항목이 이유를 말하고, 내부 기법 이름(온톨로지)은 화면 문구에 쓰지 않는다
    # (intent `2026-09-25-search-rationale-separation.md` Q7).
    assert hit is not None and '온톨로지' not in hit['rationale'] and '강수' in hit['rationale'],response.json()
    concept=[f for f in hit['rationaleFacts'] if f['kind']=='concept']
    assert concept and any('강수' in i for i in concept[0]['items']),hit['rationaleFacts']
    # ⭑ **⟨2026-09-18 · 어드바이저 지적⟩ 이 시험의 `TOKEN_B` 음성은 「회수」의 증거가 아니다.**
    #   실측으로 확인했다 — **잠그기 전에도** `TOKEN_B` 의 검색 결과는 빈 집합이다. `sources` 는
    #   A 연구실 자료이고 `TOKEN_B` 는 B 연구실 교수라 **연구실 경계**가 먼저 지운다.
    #   따라서 잠근 뒤의 `TOKEN_B` 음성은 **처음부터 공허**했다(이 병합이 만든 결함은 아니다).
    #   아래 한 줄이 그 사실을 실행 가능한 형태로 못박는다 — 경계 음성을 회수 음성으로 읽지 않는다.
    assert search(client,TOKEN_B).json()['items']==[], '잠그기 전에도 타 연구실에는 0건이다'
    sql("INSERT INTO d2_dataset_access(dataset_id,lab_id,state) VALUES (:id,current_lab_id(),'잠김') ON CONFLICT(dataset_id) DO UPDATE SET state='잠김'",{'id':sources[0]})
    # ⭑ ⟨2026-09-18 develop 동기화⟩ 잠근 뒤 검색에 남는 주체가 둘이다 —
    #   소유자(연구원 · `0032_private_owner_access`)와 자기 연구실 관리자(교수 · `0033_admin_body_access`).
    assert sources[0] in {i['datasetId'] for i in search(client,TOKEN_PROF).json()['items']}
    assert sources[0] in {i['datasetId'] for i in search(client).json()['items']}
    # 경계는 잠금과 **무관하게** 그대로다 — 위 잠금 전 단언과 같은 값이어야 한다.
    assert search(client,TOKEN_B).json()['items']==[]
    # ⚠ **열린 질문 — 이 시험에는 「회수 음성」이 없다.** 이 병합에서 `TOKEN_PROF` 음성을
    #   양성으로 바꾸면서(교수 = 연구실 관리자) HTTP 층에 남은 음성은 위의 **경계** 하나뿐이다.
    #   「회수되면 검색에서 사라진다」를 여기서 재려면 관리자도 소유자도 아닌 **같은 연구실**
    #   주체의 토큰이 필요한데 시드에 그런 계정이 없다(`conftest.ACC_A_OUTSIDER` 는 SQL 층 전용).
    #   갈래 = ⑴ 픽스처에 일반 구성원 토큰을 신설해 이 자리를 그 주체로 다시 세운다,
    #   ⑵ 이 시험의 회수 판정을 걷고 `test_search_facts`·`test_search_ontology` 의 SQL 층에 맡긴다.
    #   임의로 고르지 않는다 — 보고서 「후속 커밋」 절과 인계 요약에 올려 사람에게 넘겼다.


def test_changed_source_is_not_searchable_through_old_selection(sources,sql,session_factory,p2_client):
    sql("UPDATE d3_file SET file_name='강수.csv' WHERE id=:id",{'id':sources[1]})
    assert run_batch(kit(session_factory),max_jobs=10)['failed']==0
    client=p2_client();client.app.state.searches=Search()
    assert sources[0] in {i['datasetId'] for i in search(client).json()['items']}
    sql("UPDATE d3_file SET file_name='unrelated.csv' WHERE id=:id",{'id':sources[1]})
    assert sources[0] not in {i['datasetId'] for i in search(client).json()['items']}


@pytest.mark.parametrize('stale',[False,True])
def test_large_concept_history_does_not_break_search(sources,sql,session_factory,p2_client,stale,record_property):
    from time import perf_counter
    from colab_core.kernel.ids import Ulid
    from colab_core.domains import d3_search_ontology as ontology
    sql("UPDATE d3_file SET file_name='강수.csv' WHERE id=:id",{'id':sources[1]})
    worker=kit(session_factory)
    assert run_batch(worker,max_jobs=10)['failed']==0
    base=sql('''SELECT m.binding_id,b.fact_snapshot_id FROM d3_search_concept_match m
        JOIN d3_search_ontology_binding b ON b.id=m.binding_id WHERE m.dataset_id=:id''',{'id':sources[0]})[0]
    copies=[{'file':str(Ulid.generate()),'fact':str(Ulid.generate()),'binding':str(Ulid.generate())} for _ in range(1001)]
    args={'copies':json.dumps(copies),'source':sources[1],'binding':base['binding_id'],'fact':base['fact_snapshot_id']}
    sql('''INSERT INTO d3_file(id,lab_id,dataset_id,kind,file_name,storage_key)
      SELECT c.file,f.lab_id,f.dataset_id,f.kind,f.file_name,'fixture/'||c.file
      FROM jsonb_to_recordset(CAST(:copies AS jsonb)) AS c(file text,fact text,binding text)
      CROSS JOIN d3_file f WHERE f.id=:source''',args)
    sql('''UPDATE d3_search_change SET processed_version=requested_version WHERE source_id IN (
      SELECT c.file FROM jsonb_to_recordset(CAST(:copies AS jsonb)) AS c(file text))''',args)
    sql('''INSERT INTO d3_search_fact_snapshot(id,lab_id,dataset_id,source_kind,source_id,source_version,
        file_revision,evidence_revision,source_sha256,extractor_version,status,facts)
      SELECT c.fact,f.lab_id,f.dataset_id,f.source_kind,c.file,1,f.file_revision,f.evidence_revision,
        f.source_sha256,f.extractor_version,f.status,f.facts
      FROM jsonb_to_recordset(CAST(:copies AS jsonb)) AS c(file text,fact text,binding text)
      CROSS JOIN d3_search_fact_snapshot f WHERE f.id=:fact''',args)
    sql('''INSERT INTO d3_search_ontology_binding(id,lab_id,fact_snapshot_id,ontology_version,expected_dependencies)
      SELECT c.binding,b.lab_id,c.fact,b.ontology_version,b.expected_dependencies
      FROM jsonb_to_recordset(CAST(:copies AS jsonb)) AS c(file text,fact text,binding text)
      CROSS JOIN d3_search_ontology_binding b WHERE b.id=:binding''',args)
    sql('''INSERT INTO d3_search_ontology_dependency(lab_id,binding_id,dependency_key,digest)
      SELECT d.lab_id,c.binding,d.dependency_key,d.digest
      FROM jsonb_to_recordset(CAST(:copies AS jsonb)) AS c(binding text)
      CROSS JOIN d3_search_ontology_dependency d WHERE d.binding_id=:binding''',args)
    sql('''INSERT INTO d3_search_selection_receipt(lab_id,binding_id,selector_version)
      SELECT r.lab_id,c.binding,r.selector_version FROM jsonb_to_recordset(CAST(:copies AS jsonb)) AS c(binding text)
      CROSS JOIN d3_search_selection_receipt r WHERE r.binding_id=:binding''',args)
    sql('''INSERT INTO d3_search_concept_match(lab_id,binding_id,dataset_id,concept_id,label,quote,source_locator,terms)
      SELECT m.lab_id,c.binding,m.dataset_id,m.concept_id,m.label,m.quote,m.source_locator,m.terms
      FROM jsonb_to_recordset(CAST(:copies AS jsonb)) AS c(binding text)
      CROSS JOIN d3_search_concept_match m WHERE m.binding_id=:binding''',args)
    if stale:
        with scoped(session_factory) as s:
            old=ontology.current_manifest(s);new={**old,'entries':{**old['entries'],'discovery':'c'*64}}
            new['version']=hashlib.sha256(json.dumps({k:new[k] for k in ('protocol','entries')},ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
            ontology.publish(s,new,expected_previous=old['version'])
    client=p2_client();client.app.state.searches=Search()
    from sqlalchemy import event
    from sqlalchemy.engine import Engine
    timings=[]
    def before(conn,cursor,statement,parameters,context,executemany):
        context.search_started=perf_counter()
    def after(conn,cursor,statement,parameters,context,executemany):
        timings.append((round(perf_counter()-context.search_started,3),statement[:160]))
    event.listen(Engine,'before_cursor_execute',before)
    event.listen(Engine,'after_cursor_execute',after)
    started=perf_counter()
    try:
        response=search(client)
    finally:
        event.remove(Engine,'before_cursor_execute',before)
        event.remove(Engine,'after_cursor_execute',after)
    elapsed=perf_counter()-started
    record_property('search_seconds',round(elapsed,3))
    record_property('slow_sql',json.dumps(sorted(timings,reverse=True)[:6]))
    assert response.status_code==200,response.text
    ids={i['datasetId'] for i in response.json()['items']}
    assert (sources[0] in ids) is (not stale)
    assert elapsed<10, f'1,002 connections took {elapsed:.3f}s to search; SQL: {sorted(timings,reverse=True)[:6]}'


@pytest.mark.parametrize('change',['missing','tampered','extra','no-discovery','unrelated-manifest'])
def test_search_checks_actual_dependencies_not_only_expected(sources,sql,session_factory,p2_client,change):
    from colab_core.domains import d3_search_ontology as ontology
    sql("UPDATE d3_file SET file_name='강수.csv' WHERE id=:id",{'id':sources[1]})
    result=run_batch(kit(session_factory),max_jobs=10)
    assert result['failed']==0,result
    bindings=sql('SELECT binding_id FROM d3_search_concept_match WHERE dataset_id=:id',{'id':sources[0]})
    assert bindings,{'run':result,'queue':sql('SELECT * FROM d3_search_change'),'facts':sql('SELECT source_kind,status,facts FROM d3_search_fact_snapshot')}
    binding=bindings[0]['binding_id']
    if change in ('missing','no-discovery'):
        sql('DELETE FROM d3_search_ontology_dependency WHERE binding_id=:id AND dependency_key=:key',
            {'id':binding,'key':'discovery' if change=='no-discovery' else 'concept:rain'})
    elif change=='tampered':
        sql("UPDATE d3_search_ontology_dependency SET digest=:digest WHERE binding_id=:id AND dependency_key='concept:rain'",{'id':binding,'digest':'f'*64})
    elif change=='extra':
        sql("INSERT INTO d3_search_ontology_dependency(lab_id,binding_id,dependency_key,digest) VALUES (current_lab_id(),:id,'extra',:digest)",{'id':binding,'digest':'f'*64})
    else:
        with scoped(session_factory) as s:
            old=ontology.current_manifest(s)
            body={'protocol':old['protocol'],'entries':{**old['entries'],'concept:unrelated':'d'*64}}
            new={**body,'version':hashlib.sha256(json.dumps(body,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()}
            ontology.publish(s,new,expected_previous=old['version'])
    client=p2_client();client.app.state.searches=Search()
    response=search(client)
    assert response.status_code==200,response.text
    ids={i['datasetId'] for i in response.json()['items']}
    assert (sources[0] in ids) is (change=='unrelated-manifest')


def test_connection_cannot_claim_a_different_dataset(sources,sql,session_factory):
    from sqlalchemy.exc import DBAPIError
    sql("UPDATE d3_file SET file_name='강수.csv' WHERE id=:id",{'id':sources[1]})
    result=run_batch(kit(session_factory),max_jobs=10)
    assert result['failed']==0 and result['ready']==2,result
    with pytest.raises(DBAPIError) as error:
        sql('UPDATE d3_search_concept_match SET dataset_id=:other WHERE dataset_id=:id',{'other':DS_A2,'id':sources[0]})
    assert error.value.orig.sqlstate=='42501'


def test_repeated_source_changes_each_publish_current_connection(sources,sql,session_factory):
    worker=kit(session_factory)
    for revision in range(20):
        sql('UPDATE d3_file SET file_name=:name WHERE id=:id',{'id':sources[1],'name':f'강수-{revision}.csv'})
        result=run_batch(worker,max_jobs=10)
        rows=sql('SELECT m.binding_id,f.facts FROM d3_search_concept_match m JOIN d3_search_ontology_binding b ON b.id=m.binding_id JOIN d3_search_fact_snapshot f ON f.id=b.fact_snapshot_id WHERE m.dataset_id=:id',{'id':sources[0]})
        assert result['failed']==0 and len(rows)==1,{'iteration':revision,'run':result,'queue':sql('SELECT * FROM d3_search_change'),'rows':rows}
        assert any(f['predicate']=='file_name' and f['value']==f'강수-{revision}.csv' for f in rows[0]['facts'])
