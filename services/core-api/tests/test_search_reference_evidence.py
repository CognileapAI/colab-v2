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
REPORTS=ROOT/'eval/k4-search/fixtures/reference'


#: Packet items whose file is not in the v2 corpus (description documents that were not re-registered;
#: wu4-golden-proposal-2026-09-25.md §1-1). They are dropped by name here, never silently.
PACKET_FILES_ABSENT_FROM_V2=frozenset({
    '#processing_description_Precipitation.docx','#processing_description_NDVI.docx',
    '01.가뭄 데이터 여는 코드.ipynb','[Data Info]SPI-4weeks.docx','[Data Info]SPEI-4weeks.docx'})


def seed_reference_corpus(p2_client,sql,fake_ai):
    """Snapshot v2 datasets (fixed IDs) + evidence packet into the throwaway DB. Returns (client, datasets).

    Shared with `test_k4_interpreter_probe.py` so the K4 probe measures on the same corpus.
    The packet is keyed by the v1 bundle names; items are bound to the v2 dataset that holds the same
    file (signed correspondence ①: body files identical by name and size).
    """
    datasets=json.loads((REPORTS/'dev-data-snapshot-v2.json').read_text())['datasets']
    packet=json.loads((REPORTS/'stage-evidence-packet-02.json').read_text())['items']
    for dataset in datasets:
        sql('''INSERT INTO d3_dataset(id,lab_id,owner_account_id,uploader_account_id,source_label,processing_level_user_set)
               VALUES(:id,:lab,:account,:account,:source,:level)''',
            {'id':dataset['id'],'lab':LAB_A,'account':ACC_A_RES,'source':dataset['source_label'],
             'level':dataset['processing_level']})
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
    by_file={}
    for dataset in datasets:
        for file in dataset['files']:
            by_file.setdefault(file['file_name'],[]).append((dataset,file))
    absent={item['file_name'] for item in packet if item['file_name'] not in by_file}
    assert absent==PACKET_FILES_ABSENT_FROM_V2,absent^PACKET_FILES_ABSENT_FROM_V2
    for item in packet:
        if item['file_name'] in absent: continue
        assert len(by_file[item['file_name']])==1,('packet file held by two datasets',item['file_name'])
        (dataset,file),=by_file[item['file_name']]
        response=client.put(f"{API_PREFIX}/datasets/{dataset['id']}/files/{file['id']}/search-evidence",
            headers=auth(TOKEN_RES),json={'expectedRevision':0,'expectedFileRevision':1,
                'facts':item['facts'],'source':item['source'],'status':'reviewed'})
        assert response.status_code==200,(item['dataset_key'],item['file_name'],response.text)
    return client,datasets


#: WU4 (2026-09-25) — retrieval questions that the product misses on the v2 corpus with the frozen
#: interpretations (expanded-normalized-02.json). Explicit exemption, 4 of 9 retrieval questions.
#: The failure set must match exactly: a new miss turns red, and a closed gap also turns red so the
#: entry is removed. Re-measurement and the fix belong to WU5 (corpus metadata, not this test).
V2_RETRIEVAL_GAPS={
    'SEARCH-GOLD-005':('DEM·Aspect·LULC_2023·HLS 의 v2 이름·요약·파일 근거가 frozen 해석 낱말과 맞지 않아 4건 모두 '
                       '결과에 없다. 같은 이유로 HLS 역할 근거 문장 검사도 이 면제에 묶인다'),
    'SEARCH-GOLD-006':('rn15_sample 1건이 결과에 없다 — v2 이름·요약(「rn15 15분 누적강수를 …」)이 frozen 해석 낱말'
                       '(강수·검증에 등)과 낱말 단위로 맞지 않는다. pred_sample 은 찾는다'),
    'SEARCH-GOLD-008':'frozen 해석 topic=가뭄, v2 28건 topic 전부 null — 주제 필터가 SPI·SPEI 를 거른다',
    'SEARCH-GOLD-009':'008 과 같은 원인(topic=가뭄 · v2 topic null)',
}


def test_reference_golden_candidates_and_honest_limits_through_api(p2_client,sql,fake_ai):
    cases=json.loads((ROOT/'eval/k4-search/golden-cases.json').read_text())['cases']
    interpretations=json.loads((REPORTS/'expanded-normalized-02.json').read_text())['expansion']['responses']
    client,datasets=seed_reference_corpus(p2_client,sql,fake_ai)
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
    # Explicit exemption (count + reason): the failure set must equal V2_RETRIEVAL_GAPS exactly.
    assert {f[0] for f in failures}==set(V2_RETRIEVAL_GAPS) and all(f[1]=='missing' for f in failures),[(f[0],f[1],len(f[2])) for f in failures]
    quality=' '.join(i['rationale'] for i in responses['SEARCH-GOLD-011']['items'])
    native=' '.join(i['rationale'] for i in responses['SEARCH-GOLD-012']['items'])
    roles=' '.join(i['rationale'] for i in responses['SEARCH-GOLD-005']['items'])
    assert '미확인' in quality and '품질' in quality
    assert '불일치' in native and '2000m' in native and '직접 관측이 아닌' in native
    if 'SEARCH-GOLD-005' not in V2_RETRIEVAL_GAPS:
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
