"""지역 포함 관계 한 단계 — 「한반도」 조건이 그 직계 하위(남한 · 충청권)의 reviewed 사실을 맞춘다.

intent `dev-package/intent/2026-09-26-region-containment-expansion.md` 안전 규칙 1~6 을 고정한다.
  1 하향 전용 — 「남한」 조건은 한반도 자료를 맞추지 않는다(상향 금지).
  2 깊이 1 — 표의 하위의 하위는 펴지 않는다(전이 폐포 금지).
  4 reviewed 만 — 초안 사실은 확장 대상이 아니다(근거 읽기가 reviewed 전용).
  5 압축 후 정확 일치 — 「대한민국시군구」 ≠ 「대한민국」(부분 문자열 금지).
  6 reference_match 는 기준 파일 지역을 그대로 쓴다(넓히지 않는다).
"""
import datetime as dt
import json

import pytest

from colab_core.app.client_search import evaluate, plan_query
from colab_core.kernel import region_scope as rs
from colab_core.kernel.search_semantics import SEMANTICS

pytestmark = pytest.mark.search_golden
CLOCK = dt.datetime(2026, 9, 13, 3, tzinfo=dt.timezone.utc)

#: 완료 정의 ① 축자 — 「한반도」의 표기 집합.
PENINSULA_SET = {'한반도', 'Korea', '남한', '대한민국', '충청권', 'southern Gyeonggi and Chungcheong regions'}


def _c(value):
    return rs.compact(value)


# ── 도우미 (순수) ──────────────────────────────────────────────────────────────

def test_peninsula_scope_is_itself_plus_direct_children_and_their_aliases():
    scope = rs.region_scope('korean_peninsula')
    assert set(scope) == {_c('korean_peninsula')} | {_c(v) for v in PENINSULA_SET}
    # 경유 하위 — 한반도 자신(과 그 별칭)은 None, 하위는 하위 라벨.
    assert scope[_c('한반도')] is None and scope[_c('Korea')] is None
    assert scope[_c('남한')] == '남한' and scope[_c('대한민국')] == '남한'
    assert scope[_c('충청권')] == '충청권'
    assert scope[_c('southern Gyeonggi and Chungcheong regions')] == '충청권'


def test_children_are_not_query_aliases_of_the_parent():
    """상향 누수의 통로 — 하위를 `regions` 별칭에 넣으면 「남한」 질의가 korean_peninsula 가 된다."""
    for parent, entry in SEMANTICS['regionWithin'].items():
        aliases = {_c(a) for a in SEMANTICS['regions'][parent]}
        for child, child_aliases in entry['within'].items():
            assert not ({_c(child), *(_c(a) for a in child_aliases)} & aliases), (parent, child)
        # 사실 쪽 별칭(Korea)도 질의 별칭이 아니다 — 「South Korea」가 부분 문자열로 한반도가 된다.
        assert not ({_c(a) for a in entry.get('placeAliases', [])} & aliases)
    assert 'region' not in plan_query('남한 지역 공간자료 npy 찾아줘', now=CLOCK)['conditions']
    assert 'region' not in plan_query('South Korea 지역 공간자료 npy 찾아줘', now=CLOCK)['conditions']


def test_upward_is_never_supported():
    """「남한」(표에 없는 식별자 — 기준 파일 지역처럼 원문 그대로 온 값)은 자기 자신만 맞춘다."""
    assert rs.region_scope('남한') == {_c('남한'): None}
    assert rs.region_match('남한', '한반도') == (False, None)
    assert rs.region_match('남한', 'Korea') == (False, None)
    assert rs.region_match('충청권', '한반도') == (False, None)


def test_depth_two_is_never_expanded(monkeypatch):
    """하위가 제 하위를 가져도 부모의 범위는 한 단계에서 멈춘다(전이 폐포 금지)."""
    regions = dict(SEMANTICS['regions'], south_korea=['남한'])
    within = dict(SEMANTICS['regionWithin'],
                  south_korea={'place': '남한', 'placeAliases': [], 'within': {'서울': ['서울특별시']}})
    monkeypatch.setitem(SEMANTICS, 'regions', regions)
    monkeypatch.setitem(SEMANTICS, 'regionWithin', within)
    assert rs.region_match('south_korea', '서울') == (True, '서울')
    assert rs.region_match('korean_peninsula', '서울') == (False, None)
    assert rs.region_match('korean_peninsula', '서울특별시') == (False, None)


def test_exact_after_compaction_only_no_substring():
    assert rs.region_match('korean_peninsula', '대한민국') == (True, '남한')
    assert rs.region_match('korean_peninsula', ' 대한 민국 ') == (True, '남한')
    assert rs.region_match('korean_peninsula', 'SOUTHERN_Gyeonggi-and Chungcheong regions') == (True, '충청권')
    assert rs.region_match('korean_peninsula', '대한민국시군구') == (False, None)
    assert rs.region_match('korean_peninsula', '경기남부충청') == (False, None)
    assert rs.region_match('korean_peninsula', '남한강') == (False, None)
    assert rs.region_match('korean_peninsula', None) == (False, None)


def test_expand_false_is_the_previous_exact_vocabulary():
    assert set(rs.region_scope('korean_peninsula', expand=False)) == {_c('korean_peninsula'), _c('한반도')}
    assert set(rs.region_scope('seoul')) == {_c('seoul'), *(_c(a) for a in SEMANTICS['regions']['seoul'])}


# ── 경로 1 판정 (순수) ────────────────────────────────────────────────────────

def _row(**facts):
    return {'file_id': 'f1', 'file_name': 'x.npy', 'facts': facts, 'source': {'label': 'fixture'}}


@pytest.mark.parametrize('region,status', [
    ('한반도', 'supported'), ('Korea', 'supported'), ('남한', 'supported'), ('대한민국', 'supported'),
    ('충청권', 'supported'), ('southern Gyeonggi and Chungcheong regions', 'supported'),
    ('대한민국시군구', 'contradicted'), ('경기남부충청', 'contradicted'), ('전지구', 'contradicted'),
])
def test_path1_peninsula_condition_supports_direct_children(region, status):
    plan = {'intent': 'discover', 'conditions': {'region': 'korean_peninsula'}}
    assert evaluate(plan, {}, [_row(region=region)])['status'] == status


def test_path1_upward_is_contradicted():
    plan = {'intent': 'discover', 'conditions': {'region': '남한'}}
    assert evaluate(plan, {}, [_row(region='한반도')])['status'] == 'contradicted'
    assert evaluate(plan, {}, [_row(region='남한')])['status'] == 'supported'


def test_path1_reference_match_keeps_the_reference_region():
    """안전 규칙 6 — 「같은 지역」은 포함 관계와 다른 질문이다."""
    plan = {'intent': 'reference_match', 'conditions': {'region': 'korean_peninsula'}}
    assert evaluate(plan, {}, [_row(region='남한')])['status'] == 'contradicted'
    assert evaluate(plan, {}, [_row(region='한반도')])['status'] == 'supported'


# ── 경로 1 SQL (실 API · 일회용 DB) ─────────────────────────────────────────────

def _dataset(sql, client, facts, *, name, status='reviewed'):
    from conftest import LAB_A, ACC_A_RES, TOKEN_RES, auth
    from colab_core.kernel.ids import Ulid
    from colab_core.app.main import API_PREFIX
    dataset, file = str(Ulid.generate()), str(Ulid.generate())
    sql('''INSERT INTO d3_dataset(id,lab_id,owner_account_id,uploader_account_id,uploaded_at)
           VALUES(:id,:lab,:account,:account,:uploaded)''',
        {'id': dataset, 'lab': LAB_A, 'account': ACC_A_RES, 'uploaded': CLOCK})
    sql('''INSERT INTO d3_dataset_description(dataset_id,lab_id,name,summary)
           VALUES(:id,:lab,:name,'지역 포함 관계 픽스처')''', {'id': dataset, 'lab': LAB_A, 'name': name})
    sql('INSERT INTO d3_dataset_autometa(dataset_id,lab_id) VALUES(:id,:lab)', {'id': dataset, 'lab': LAB_A})
    sql('''INSERT INTO d3_file(id,lab_id,dataset_id,kind,file_name,storage_key)
           VALUES(:id,:lab,:dataset,'본체','grid.npy',:key)''',
        {'id': file, 'lab': LAB_A, 'dataset': dataset, 'key': 'region-fixture/' + file})
    r = client.put(f'{API_PREFIX}/datasets/{dataset}/files/{file}/search-evidence', headers=auth(TOKEN_RES),
                   json={'expectedRevision': 0, 'expectedFileRevision': 1, 'status': status, 'facts': facts,
                         'source': {'label': '지역 픽스처', 'locator': '1절', 'text': json.dumps(facts)}})
    assert r.status_code == 200, r.text
    return dataset, file


def _search(client, query, context=None):
    from conftest import TOKEN_RES, auth
    from colab_core.app.main import API_PREFIX
    r = client.post(f'{API_PREFIX}/dataset-searches', headers=auth(TOKEN_RES),
                    json={'query': query, 'context': context or {}})
    assert r.status_code == 200, r.text
    return r.json()


def test_path1_sql_peninsula_reaches_reviewed_children_only(p2_client, sql, monkeypatch):
    from colab_core.app import client_search
    original = client_search.plan_query
    monkeypatch.setattr(client_search, 'plan_query', lambda q, **kw: original(q, now=CLOCK, **kw))
    client = p2_client()
    grid = {'representation': 'spatial_grid'}
    good = {region: _dataset(sql, client, {**grid, 'region': region}, name=f'포함 {region}')[0]
            for region in ('한반도', '남한', '대한민국', '충청권', 'southern Gyeonggi and Chungcheong regions', 'Korea')}
    bad = {region: _dataset(sql, client, {**grid, 'region': region}, name=f'제외 {region}')[0]
           for region in ('대한민국시군구', '경기남부충청', '전지구')}
    draft, _ = _dataset(sql, client, {**grid, 'region': '남한'}, name='초안 남한', status='draft')
    body = _search(client, '한반도 지역 영상 자료 찾아줘')
    assert body['assessment']['conditions']['region'] == 'korean_peninsula', body['assessment']
    ids = {item['datasetId'] for item in body['items']}
    assert set(good.values()) <= ids, body
    assert not (set(bad.values()) & ids), body
    assert draft not in ids, '초안 사실은 확장 대상이 아니다(안전 규칙 4)'
    # 결정 2 ㈎ — 경로 1 카드 문장·checks 는 그대로다(계약 무변경).
    south = next(c for c in body['assessment']['comparisons'] if c['datasetId'] == good['남한'])
    assert south['checks']['region'] == 'supported'


def test_path1_sql_reference_match_does_not_expand(p2_client, sql):
    client = p2_client()
    span = {'start': '2025-01-01', 'end': '2025-12-31'}
    _, reference = _dataset(sql, client, {'variable': 'precipitation', 'region': '한반도', 'period': span},
                            name='기준 한반도 강수')
    same, _ = _dataset(sql, client, {'variable': 'wind_speed', 'region': '한반도', 'period': span}, name='같은 지역')
    child, _ = _dataset(sql, client, {'variable': 'wind_speed', 'region': '남한', 'period': span}, name='하위 지역')
    body = _search(client, '내가 어제 받은 강수량 자료와 같은 기간의 풍속 데이터 찾아줘',
                   {'referenceFileId': reference})
    ids = {item['datasetId'] for item in body['items']}
    assert same in ids and child not in ids, body


def test_path1_sql_upward_reference_never_reaches_the_parent(p2_client, sql):
    client = p2_client()
    span = {'start': '2025-01-01', 'end': '2025-12-31'}
    _, reference = _dataset(sql, client, {'variable': 'precipitation', 'region': '남한', 'period': span},
                            name='기준 남한 강수')
    parent, _ = _dataset(sql, client, {'variable': 'wind_speed', 'region': '한반도', 'period': span}, name='상위 지역')
    same, _ = _dataset(sql, client, {'variable': 'wind_speed', 'region': '남한', 'period': span}, name='같은 남한')
    body = _search(client, '내가 어제 받은 강수량 자료와 같은 기간의 풍속 데이터 찾아줘',
                   {'referenceFileId': reference})
    ids = {item['datasetId'] for item in body['items']}
    assert same in ids and parent not in ids, body


def test_path1_candidates_upward_probe_on_the_domain(p2_client, sql, session_factory):
    """probe 모양 그대로 — `{"region": "남한"}` 은 한반도 사실을 부르지 않는다(상향 누수 0)."""
    from conftest import ACC_A_RES, LAB_A
    from colab_core.domains import d3_client_search
    from colab_core.kernel.auth import Subject
    from colab_core.kernel.ids import Ulid
    from colab_core.kernel.scope import read_only_scope
    client = p2_client()
    parent, _ = _dataset(sql, client, {'region': '한반도'}, name='상위')
    child, _ = _dataset(sql, client, {'region': '남한'}, name='하위')
    with read_only_scope(session_factory, Subject(account_id=Ulid(ACC_A_RES), lab_id=Ulid(LAB_A))) as session:
        up = {r['dataset_id'] for r in d3_client_search.candidates(session, {'region': '남한'})[0]}
        down = {r['dataset_id'] for r in d3_client_search.candidates(session, {'region': 'korean_peninsula'})[0]}
        ref = {r['dataset_id'] for r in d3_client_search.candidates(
            session, {'region': 'korean_peninsula'}, expand_region=False)[0]}
    assert child in up and parent not in up
    assert {parent, child} <= down
    assert parent in ref and child not in ref
