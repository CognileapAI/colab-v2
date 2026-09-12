"""Frozen reference metadata + real evidence/search API; interpretation is a frozen HTTP double."""
import copy
import json
from pathlib import Path

import pytest

from conftest import ACC_A_RES, DS_A2, LAB_A, TOKEN_RES, auth
from test_search_relay import fake_ai  # noqa: F401 — reuse the real HTTP test transport
from colab_core.app.main import API_PREFIX
from colab_core.kernel.ids import Ulid


pytestmark = pytest.mark.search_golden


ROOT=Path(__file__).resolve().parents[3]
REPORTS=ROOT/'dev-package/reports/stage3-ai-search-plan'


def test_reference_golden_candidates_and_honest_limits_through_api(p2_client,sql,fake_ai):
    datasets=json.loads((REPORTS/'dev-data-snapshot.json').read_text())['datasets']
    packet=json.loads((REPORTS/'stage-evidence-packet-02.json').read_text())['items']
    cases=json.loads((ROOT/'eval/k4-search/golden-cases.json').read_text())['cases']
    interpretations=json.loads((REPORTS/'expanded-normalized-02.json').read_text())['expansion']['responses']
    for dataset in datasets:
        sql('''INSERT INTO d3_dataset(id,lab_id,owner_account_id,uploader_account_id,source_label)
               VALUES(:id,:lab,:account,:account,:source)''',
            {'id':dataset['id'],'lab':LAB_A,'account':ACC_A_RES,'source':dataset['source_label']})
        sql('''INSERT INTO d3_dataset_description(dataset_id,lab_id,name,topic,summary)
               VALUES(:id,:lab,:name,:topic,:summary)''',
            {'id':dataset['id'],'lab':LAB_A,'name':dataset['name'],'topic':dataset['topic'],'summary':dataset['summary']})
        sql('INSERT INTO d3_dataset_autometa(dataset_id,lab_id) VALUES(:id,:lab)',{'id':dataset['id'],'lab':LAB_A})
        for file in dataset['files']:
            grid=file['kind']=='기준 격자 파일'
            sql('''INSERT INTO d3_file(id,lab_id,dataset_id,kind,file_name,storage_key,carries_lat,carries_lon)
                   VALUES(:id,:lab,:dataset,:kind,:name,:storage,:lat,:lon)''',
                {'id':file['id'],'lab':LAB_A,'dataset':dataset['id'],'kind':file['kind'],
                 'name':file['file_name'],'storage':'fixture/'+file['id'],
                 'lat':grid and 'lat' in file['file_name'].lower(),'lon':grid and 'lon' in file['file_name'].lower()})
    for dataset in datasets:
        for edge in dataset['parents']:
            sql('''INSERT INTO d4_lineage_edge(id,lab_id,child_dataset_id,parent_dataset_id,parent_role,origin,confirmed_by_account_id,confirmed_at)
                   VALUES(:id,:lab,:child,:parent,:role,'manual',:account,now())''',
                {'id':str(Ulid.generate()),'lab':LAB_A,'child':dataset['id'],'parent':edge['parent_dataset_id'],
                 'role':edge['parent_role'],'account':ACC_A_RES})
    client=p2_client(ai_base_url=fake_ai['url'])
    by_name={d['name']:d for d in datasets}
    for item in packet:
        dataset=by_name[item['dataset_name']]
        file=next(f for f in dataset['files'] if f['file_name']==item['file_name'])
        response=client.put(f"{API_PREFIX}/datasets/{dataset['id']}/files/{file['id']}/search-evidence",
            headers=auth(TOKEN_RES),json={'expectedRevision':0,'expectedFileRevision':1,
                'facts':item['facts'],'source':item['source'],'status':'reviewed'})
        assert response.status_code==200,(item['dataset_key'],item['file_name'],response.text)
    failures=[]; responses={}
    for case,interpretation in zip(cases,interpretations,strict=True):
        fake_ai['body']={k:v for k,v in copy.deepcopy(interpretation).items() if k!='id'}
        response=client.post(f'{API_PREFIX}/dataset-searches',headers=auth(TOKEN_RES),
                             json={'query':case['query'],'limit':100})
        assert response.status_code==200,response.text
        responses[case['id']]=response.json()
        ids={i['datasetId'] for i in response.json()['items']} & set(case['scope'])
        if case['mode']=='retrieval' and not set(case['required'])<=ids: failures.append((case['id'],'missing',set(case['required'])-ids))
        if case['mode']=='empty' and ids: failures.append((case['id'],'unexpected',ids))
    assert not failures,failures
    quality=' '.join(i['rationale'] for i in responses['SEARCH-GOLD-011']['items'])
    native=' '.join(i['rationale'] for i in responses['SEARCH-GOLD-012']['items'])
    roles=' '.join(i['rationale'] for i in responses['SEARCH-GOLD-005']['items'])
    assert '미확인' in quality and '품질' in quality
    assert '불일치' in native and '2000m' in native and '직접 관측이 아닌' in native
    assert 'HLS_S30_NDVI_mean_202305.tif' in roles and '검증 자료' in roles and '보조 입력' in roles
    # Evidence for a different topic must not erase legacy metadata candidates,
    # especially locked candidates whose body facts were never available.
    fake_ai['body']=copy.deepcopy(interpretations[0])
    fake_ai['body']['interpretation']['terms']=['강우']
    fake_ai['body']['interpretation']['topic']=None
    response=client.post(f'{API_PREFIX}/dataset-searches',headers=auth(TOKEN_RES),
                         json={'query':'월평균 NDVI','limit':100})
    assert response.status_code==200,response.text
    locked=next(i for i in response.json()['items'] if i['datasetId']==DS_A2)
    assert 'a2-body' not in locked['rationale'] and '출처 #' not in locked['rationale']
