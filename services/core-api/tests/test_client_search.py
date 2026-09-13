"""Client golden questions: independent expectations and adversarial same-file facts."""
import datetime as dt
import json
from pathlib import Path

import pytest

from colab_core.app.client_search import plan_query, evaluate, respond

pytestmark = pytest.mark.search_golden
CLOCK = dt.datetime(2026, 9, 13, 3, tzinfo=dt.timezone.utc)
CASES = json.loads((Path(__file__).resolve().parents[3] / 'eval/k4-search/client-golden.json').read_text())['cases']


@pytest.mark.parametrize('case', CASES, ids=lambda c: c['id'])
def test_client_intents(case):
    plan = plan_query(case['query'], now=CLOCK)
    assert plan['intent'] == case['intent']
    for key, value in case['expected'].items():
        if not key.startswith('missing'):
            assert plan['conditions'][key] == value


def evidence(**facts):
    return {'file_id':'f1','file_name':'rain.npy','facts':facts,
            'source':{'label':'fixture','locator':'section 1','sha256':'a'*64}}


def test_npy_is_not_spatial_and_air_temperature_is_not_lst():
    plan = plan_query(CASES[2]['query'], now=CLOCK)
    base = dict(variable='precipitation', region='seoul')
    assert evaluate(plan, {'summary':''}, [evidence(**base)])['status'] == 'unknown'
    assert evaluate(plan, {'summary':''}, [evidence(**base, representation='spatial_grid')])['status'] == 'supported'
    wrong = evidence(variable='air_temperature', region='seoul', representation='spatial_grid')
    assert evaluate(plan, {'summary':''}, [wrong])['status'] == 'contradicted'


def test_example_format_does_not_exclude_spatial_csv():
    plan=plan_query(CASES[2]['query'],now=CLOCK)
    assert 'format' not in plan['conditions']
    row=evidence(variable='precipitation',region='seoul',representation='point_observations')
    row['file_name']='seoul-rain.csv'
    assert evaluate(plan,{},[row])['status']=='supported'
    strict=plan_query('서울 강수량 공간자료 중 NPY 형식만 모아줘',now=CLOCK)
    assert strict['conditions']['format']=='npy'
    assert evaluate(strict,{},[row])['status']=='contradicted'


def test_never_mix_files_to_satisfy_conditions():
    plan = plan_query(CASES[2]['query'], now=CLOCK)
    rows = [evidence(variable='precipitation', region='jeju', representation='spatial_grid'),
            evidence(variable='air_temperature', region='seoul', representation='spatial_grid')]
    rows[1]['file_id'] = 'f2'
    assert evaluate(plan, {}, rows)['status'] == 'contradicted'


def test_description_and_and_coverage_are_not_upload_time():
    plan = plan_query(CASES[4]['query'], now=CLOCK)
    facts = [evidence(period={'start':'2025-02-01','end':'2025-12-31'})]
    assert evaluate(plan, {'summary':'한강 수질 측정'}, facts)['status'] == 'supported'
    assert evaluate(plan, {'summary':'한강 측정','name':'수질'}, facts)['status'] == 'contradicted'
    assert evaluate(plan, {'summary':'한강 수질','created_at':CLOCK}, [])['status'] == 'unknown'


def test_resolution_inclusive_unknown_and_resampling():
    plan = plan_query(CASES[6]['query'], now=CLOCK)
    common = dict(region='korean_peninsula', platform='satellite', representation='spatial_grid')
    for resolution, status in [(10,'supported'), (5,'supported'), (30,'contradicted')]:
        assert evaluate(plan, {}, [evidence(**common, nativeResolutionM=resolution)])['status'] == status
    assert evaluate(plan, {}, [evidence(**common, gridResolutionM=5)])['status'] == 'unknown'


def test_missing_research_and_reference_are_questions_not_zero_claims():
    for index in (0,1,3):
        result = respond(plan_query(CASES[index]['query'], now=CLOCK), [], truncated=False)
        assert result['status'] == 'clarification'
        assert result['questions']
        assert '0건' not in result['text']


def test_seoul_month_boundary_and_unit_conversion():
    plan = plan_query(CASES[5]['query'], now=dt.datetime(2026,8,31,15,tzinfo=dt.timezone.utc))
    assert plan['conditions']['uploadedMonth'] == '2026-09'
    assert plan_query('한반도 위성 영상 해상도 0.01km 이하 제일 선명한 자료',now=CLOCK)['conditions']['maxResolutionM'] == 10


def test_research_conflict_requires_clarification():
    plan = plan_query(CASES[0]['query'], now=CLOCK,
                      context={'research':{'variable':'air_temperature','statistics':['monthly_mean_daily_max']}})
    assert plan['questions']
    assert 'land_surface_temperature' == plan['conditions']['variable']


def _dataset(sql, client, facts, *, name='클라이언트 검증 자료', summary='한강 수질 측정', file_name='rain.npy', uploaded=CLOCK):
    from conftest import LAB_A, ACC_A_RES, TOKEN_RES, auth
    from colab_core.kernel.ids import Ulid
    from colab_core.app.main import API_PREFIX
    dataset, file = str(Ulid.generate()), str(Ulid.generate())
    sql('''INSERT INTO d3_dataset(id,lab_id,owner_account_id,uploader_account_id,uploaded_at)
           VALUES(:id,:lab,:account,:account,:uploaded)''',{'id':dataset,'lab':LAB_A,'account':ACC_A_RES,'uploaded':uploaded})
    sql('''INSERT INTO d3_dataset_description(dataset_id,lab_id,name,summary)
           VALUES(:id,:lab,:name,:summary)''',{'id':dataset,'lab':LAB_A,'name':name,'summary':summary})
    sql('INSERT INTO d3_dataset_autometa(dataset_id,lab_id) VALUES(:id,:lab)',{'id':dataset,'lab':LAB_A})
    sql('''INSERT INTO d3_file(id,lab_id,dataset_id,kind,file_name,storage_key)
           VALUES(:id,:lab,:dataset,'본체',:name,:key)''',{'id':file,'lab':LAB_A,'dataset':dataset,'name':file_name,'key':'client-fixture/'+file})
    r=client.put(f'{API_PREFIX}/datasets/{dataset}/files/{file}/search-evidence',headers=auth(TOKEN_RES),
        json={'expectedRevision':0,'expectedFileRevision':1,'status':'reviewed','facts':facts,
              'source':{'label':'합성 골든 픽스처','locator':'제품 사양 1절','text':json.dumps(facts)}})
    assert r.status_code==200,r.text
    return dataset,file


@pytest.mark.parametrize('index',range(7),ids=[c['id']+'-API' for c in CASES])
def test_client_golden_through_real_api(p2_client,sql,monkeypatch,index):
    from colab_core.app import client_search
    from colab_core.app.main import API_PREFIX
    from conftest import TOKEN_RES, auth
    original = client_search.plan_query
    monkeypatch.setattr(client_search,'plan_query',lambda query,**kw:original(query,now=CLOCK,**kw))
    client = p2_client()
    context = {}
    span={'start':'2025-01-01','end':'2025-12-31'}
    facts = [
        {'variable':'land_surface_temperature','region':'seoul','period':span,'statistics':['monthly_mean']},
        {'variable':'land_surface_temperature','region':'seoul','period':span,'statistics':['monthly_mean'],'platform':'satellite'},
        {'variable':'precipitation','region':'seoul','representation':'spatial_grid'},
        {'variable':'wind_speed','region':'jeju','period':span},
        {'period':span},
        {'variable':'particulate_matter','provider':'환경부','directObservation':True},
        {'region':'korean_peninsula','platform':'satellite','representation':'spatial_grid','nativeResolutionM':10.0},
    ][index]
    if index in (0,1):
        context={'research':{'variable':'land_surface_temperature','region':'seoul','period':span,'statistics':['monthly_mean']}}
    if index==3:
        _,file=_dataset(sql,client,{'variable':'precipitation','region':'jeju','period':span},name='기준 제주 강수')
        context={'referenceFileId':file}
    good,_ = _dataset(sql,client,facts)
    wrong=dict(facts)
    if index in (0,1,2,3): wrong['variable']='air_temperature'
    elif index==4: wrong['period']={'start':'2024-01-01','end':'2024-12-31'}
    elif index==5: wrong['directObservation']=False
    else: wrong['nativeResolutionM']=30.0
    bad,_ = _dataset(sql,client,wrong,name='제외해야 하는 자료')
    r=client.post(f'{API_PREFIX}/dataset-searches',headers=auth(TOKEN_RES),json={'query':CASES[index]['query'],'context':context})
    assert r.status_code==200,r.text
    body=r.json()
    assert body['assessment']['status']=='answered',body
    ids={r['datasetId'] for r in body['items']}
    assert good in ids and bad not in ids,body
    assert body['totalCount']==1,body
    assert body['assessment']['comparisons'][0]['source']['label']=='합성 골든 픽스처'


def test_reference_permission_and_stale_evidence(p2_client,sql):
    from conftest import TOKEN_RES, auth, FILE_B1
    from colab_core.app.main import API_PREFIX
    client=p2_client()
    r=client.post(f'{API_PREFIX}/dataset-searches',headers=auth(TOKEN_RES),
                  json={'query':CASES[3]['query'],'context':{'referenceFileId':FILE_B1}})
    assert r.status_code==404
    dataset,file=_dataset(sql,client,{'variable':'precipitation','region':'seoul','representation':'spatial_grid'})
    sql('UPDATE d3_file SET storage_key=storage_key WHERE id=:id',{'id':file})
    r=client.post(f'{API_PREFIX}/dataset-searches',headers=auth(TOKEN_RES),json={'query':CASES[2]['query']})
    assert r.status_code==200,r.text
    assert dataset not in {i['datasetId'] for i in r.json()['items']}


@pytest.mark.parametrize('context',[{'labId':'other'},{'research':{'variable':[]}},{'research':{'period':{'start':'2025-02-30','end':'2025-03-01'}}},{'research':{'maxResolutionM':True}}])
def test_invalid_context_rejected(p2_client,context):
    from conftest import TOKEN_RES,auth
    from colab_core.app.main import API_PREFIX
    r=p2_client().post(f'{API_PREFIX}/dataset-searches',headers=auth(TOKEN_RES),json={'query':CASES[0]['query'],'context':context})
    assert r.status_code==400,r.text


def test_precise_description_and_month_range_do_not_broaden():
    p=plan_query(CASES[4]['query'],now=CLOCK)
    assert evaluate(p,{'summary':'한 강 수질'},[evidence(period={'start':'2025-01-01','end':'2025-12-31'})])['status']=='contradicted'
    p=plan_query('2025년 1월부터 12월까지 지표면 온도 추천',now=CLOCK)
    assert p['questions']


def test_older_matching_record_is_not_crowded_out_by_recent_irrelevant_data(p2_client,sql):
    from conftest import TOKEN_RES,auth,LAB_A,ACC_A_RES
    from colab_core.app.main import API_PREFIX
    from colab_core.kernel.ids import Ulid
    client=p2_client()
    good,_=_dataset(sql,client,{'variable':'precipitation','region':'seoul','representation':'spatial_grid'},uploaded=CLOCK-dt.timedelta(days=400))
    # No bodies/evidence: these recent unrelated records must not consume the
    # typed candidate budget. Only metadata is needed to reproduce the failure.
    for _ in range(205):
        id=str(Ulid.generate())
        sql('INSERT INTO d3_dataset(id,lab_id,owner_account_id,uploader_account_id) VALUES(:id,:lab,:a,:a)',{'id':id,'lab':LAB_A,'a':ACC_A_RES})
        sql("INSERT INTO d3_dataset_description(dataset_id,lab_id,name) VALUES(:id,:lab,'관련 없는 신규 자료')",{'id':id,'lab':LAB_A})
    r=client.post(f'{API_PREFIX}/dataset-searches',headers=auth(TOKEN_RES),json={'query':CASES[2]['query']})
    assert r.status_code==200,r.text
    assert r.json()['assessment']['status']=='answered'
    assert [i['datasetId'] for i in r.json()['items']]==[good]


def test_client_spatial_csv_correction_through_api(p2_client,sql):
    from conftest import TOKEN_RES,auth
    from colab_core.app.main import API_PREFIX
    client=p2_client()
    good,_=_dataset(sql,client,{'variable':'precipitation','region':'seoul','representation':'point_observations'},file_name='seoul-rain.csv')
    for query,expected in [(CASES[2]['query'],True),('서울 강수량 공간자료 중 NPY 형식만 모아줘',False)]:
        r=client.post(f'{API_PREFIX}/dataset-searches',headers=auth(TOKEN_RES),json={'query':query})
        assert r.status_code==200,r.text
        assert (good in {i['datasetId'] for i in r.json()['items']}) == expected,r.json()


def test_file_replacement_during_search_cannot_publish_old_evidence(p2_client,sql,monkeypatch):
    from conftest import TOKEN_RES,auth
    from colab_core.app.main import API_PREFIX
    from colab_core.domains import d3_client_search
    client=p2_client()
    good,file=_dataset(sql,client,{'variable':'precipitation','region':'seoul','representation':'point_observations'},file_name='seoul-rain.csv')
    original=d3_client_search.candidates
    def changing(*args,**kwargs):
        result=original(*args,**kwargs)
        sql('UPDATE d3_file SET storage_key=storage_key WHERE id=:id',{'id':file})
        return result
    monkeypatch.setattr(d3_client_search,'candidates',changing)
    r=client.post(f'{API_PREFIX}/dataset-searches',headers=auth(TOKEN_RES),json={'query':CASES[2]['query']})
    assert r.status_code==200,r.text
    assert good not in {i['datasetId'] for i in r.json()['items']}
    assert r.json()['assessment']['comparisons']==[]
    assert r.json()['assessment']['status']=='partial'


def test_verified_filter_precedes_candidate_limit(p2_client,sql,monkeypatch):
    from conftest import TOKEN_RES,auth,LAB_A,ACC_A_PROF
    from colab_core.app.main import API_PREFIX
    from colab_core.domains import d3_client_search
    client=p2_client()
    facts={'variable':'precipitation','region':'seoul','representation':'point_observations'}
    good,_=_dataset(sql,client,facts,uploaded=CLOCK-dt.timedelta(days=400))
    _dataset(sql,client,facts,uploaded=CLOCK)
    sql('''INSERT INTO d2_verified(dataset_id,lab_id,verified,approver_account_id,approved_at)
           VALUES(:id,:lab,true,:prof,now())''',{'id':good,'lab':LAB_A,'prof':ACC_A_PROF},account_id=ACC_A_PROF)
    monkeypatch.setattr(d3_client_search,'LIMIT',1)
    r=client.post(f'{API_PREFIX}/dataset-searches',headers=auth(TOKEN_RES),json={'query':CASES[2]['query'],'verified':True})
    assert r.status_code==200,r.text
    assert r.json()['assessment']['status']=='answered',r.json()
    assert [i['datasetId'] for i in r.json()['items']]==[good]
    assert r.json()['items'][0]['verified'] is True
