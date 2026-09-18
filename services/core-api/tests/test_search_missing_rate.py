"""`maxMissingRatePercent` — 결측률 술어는 **원본 칸에서 파생된 수치**를 데이터셋 단위로 읽는다.

왜 이 자리인가 (`dev-package/intent/2026-09-18-missing-rate-predicate-recon.md` 증보 3 · 판정 3=㈐-2):
`d3_dataset_variable.missing_rate` 는 자유 입력 text 이고 그 입력 계약(`fe-core.yaml` `missingRate`
· PRD-16)은 **바뀌지 않는다**. 대신 같은 표에 생성 컬럼 `missing_rate_percent` 를 두어 파싱 가능한
문면만 수치로 남기고, 파싱 불가·범위 밖은 NULL 로 두어 **등록을 막지 않는다**.

술어가 `file_checks` 가 아니라 `where` 에 사는 이유: 결측률은 파일이 아니라 데이터셋의 **대표 변수**
사실이다. `descriptionAll`·`uploadedMonth` 와 같은 자리다. `d3_search_evidence` 의 facts 로 전재하면
사본 동기화 주체가 없어진다(증보 3 ㈎ 의 문제).

⚠ 이 파일은 「값이 채워져 있다」를 주장하지 않는다. 로컬 실측(같은 intent)에서 staging 22행 중 0행,
개발 5행 중 1행만 채워져 있었다. 여는 것은 기능이고 채움은 등록 쪽의 일이다.
"""
from __future__ import annotations

import datetime as dt
import json

import pytest
from conftest import ACC_A_RES, LAB_A, TOKEN_RES, auth

pytestmark = pytest.mark.search_golden

CLOCK = dt.datetime(2026, 9, 13, 3, tzinfo=dt.timezone.utc)

#: 세 술어를 섞지 않기 위해 모든 픽스처가 같은 파일 사실을 쓴다 — 갈라지는 축은 결측률 하나다.
FACTS = {'variable': 'precipitation', 'region': 'seoul', 'representation': 'spatial_grid'}

#: `(ordinal, name, missing_rate, is_representative)`
NO_VARIABLE_ROWS: tuple = ()


def _dataset(sql, client, *, name, variables=NO_VARIABLE_ROWS):
    from colab_core.app.main import API_PREFIX
    from colab_core.kernel.ids import Ulid

    dataset, file = str(Ulid.generate()), str(Ulid.generate())
    sql('''INSERT INTO d3_dataset(id,lab_id,owner_account_id,uploader_account_id,uploaded_at)
           VALUES(:id,:lab,:account,:account,:uploaded)''',
        {'id': dataset, 'lab': LAB_A, 'account': ACC_A_RES, 'uploaded': CLOCK})
    sql('''INSERT INTO d3_dataset_description(dataset_id,lab_id,name,summary)
           VALUES(:id,:lab,:name,'결측률 술어 픽스처')''',
        {'id': dataset, 'lab': LAB_A, 'name': name})
    sql('INSERT INTO d3_dataset_autometa(dataset_id,lab_id) VALUES(:id,:lab)',
        {'id': dataset, 'lab': LAB_A})
    sql('''INSERT INTO d3_file(id,lab_id,dataset_id,kind,file_name,storage_key)
           VALUES(:id,:lab,:dataset,'본체','rain.npy',:key)''',
        {'id': file, 'lab': LAB_A, 'dataset': dataset, 'key': 'missing-rate-fixture/' + file})
    for ordinal, variable_name, missing_rate, representative in variables:
        sql('''INSERT INTO d3_dataset_variable(dataset_id,lab_id,ordinal,name,missing_rate,is_representative)
               VALUES(:id,:lab,:ordinal,:name,:rate,:rep)''',
            {'id': dataset, 'lab': LAB_A, 'ordinal': ordinal, 'name': variable_name,
             'rate': missing_rate, 'rep': representative})
    response = client.put(f'{API_PREFIX}/datasets/{dataset}/files/{file}/search-evidence',
                          headers=auth(TOKEN_RES),
                          json={'expectedRevision': 0, 'expectedFileRevision': 1, 'status': 'reviewed',
                                'facts': FACTS,
                                'source': {'label': '합성 결측률 픽스처', 'locator': '제품 사양 1절',
                                           'text': json.dumps(FACTS)}})
    assert response.status_code == 200, response.text
    return dataset


def _search(session_factory, conditions):
    from colab_core.domains import d3_client_search
    from colab_core.kernel.auth import Subject
    from colab_core.kernel.ids import Ulid
    from colab_core.kernel.scope import read_only_scope

    with read_only_scope(session_factory,
                         Subject(account_id=Ulid(ACC_A_RES), lab_id=Ulid(LAB_A))) as session:
        rows, _capped = d3_client_search.candidates(session, dict(conditions))
    return {row['dataset_id'] for row in rows}


@pytest.fixture()
def fixtures(p2_client, sql):
    """결측률 다섯 갈래. 파일 사실은 전부 같고 대표 변수의 문면만 다르다."""
    client = p2_client()
    return {
        # 파싱 가능·1% 이하
        'low': _dataset(sql, client, name='결측률 0.2% 자료',
                        variables=[(1, '강수량', '0.2%', True)]),
        # 파싱 가능·1% 초과. 두 번째 행은 낮지만 **대표가 아니다** — 대표 아닌 행으로 통과하면 안 된다.
        'high': _dataset(sql, client, name='결측률 20% 자료',
                         variables=[(1, '강수량', '20%', True), (2, '기온', '0.1%', False)]),
        # 수치로 읽을 수 없는 자유 문면 — 등록은 막지 않고 술어에서만 빠진다.
        'text': _dataset(sql, client, name='결측률 낮음 자료',
                         variables=[(1, '강수량', '낮음', True)]),
        # 칸이 비어 있는 행
        'null': _dataset(sql, client, name='결측률 미기재 자료',
                         variables=[(1, '강수량', None, True)]),
        # 변수 행 자체가 없는 데이터셋
        'none': _dataset(sql, client, name='변수 행 없는 자료'),
    }


def test_representative_missing_rate_is_a_dataset_level_predicate(fixtures, session_factory):
    found = _search(session_factory, {'maxMissingRatePercent': 1})
    assert fixtures['low'] in found, '0.2% 는 1% 이하다'
    for key in ('high', 'text', 'null', 'none'):
        assert fixtures[key] not in found, f'{key} 가 1% 이하로 들어왔다'


def test_upper_bound_is_inclusive_and_widening_admits_the_higher_rate(fixtures, session_factory):
    assert fixtures['low'] in _search(session_factory, {'maxMissingRatePercent': 0.2})
    widened = _search(session_factory, {'maxMissingRatePercent': 20})
    assert fixtures['low'] in widened and fixtures['high'] in widened
    # 넓혀도 **파싱 불가·미기재는 끝까지 들어오지 않는다** — 조용한 후보 확대가 없다.
    for key in ('text', 'null', 'none'):
        assert fixtures[key] not in _search(session_factory, {'maxMissingRatePercent': 100})


def test_unknown_predicate_still_raises(fixtures, session_factory):
    with pytest.raises(ValueError, match='unsupported typed predicate'):
        _search(session_factory, {'missingRatePercent': 1})


@pytest.mark.parametrize('bad', [True, '1', None, -1, 100.5, float('nan')])
def test_argument_must_be_a_percentage_number(fixtures, session_factory, bad):
    # 「지원하지 않는 술어」로 떨어지는 것과 다른 실패다 — 메시지로 갈라 둔다.
    with pytest.raises(ValueError, match='maxMissingRatePercent'):
        _search(session_factory, {'maxMissingRatePercent': bad})


def test_research_context_accepts_the_new_key_within_bounds():
    from colab_core.app.client_search import validate_context
    from colab_core.kernel import errors

    assert validate_context({'research': {'maxMissingRatePercent': 1}})
    for bad in (True, '1', -1, 100.5, float('inf')):
        with pytest.raises(errors.ApiError) as raised:
            validate_context({'research': {'maxMissingRatePercent': bad}})
        assert raised.value.status_code == 400


def test_adjudication_reads_the_dataset_value_not_the_file_facts():
    """SQL 이 이미 거른 조건을 화면 판정이 `unknown` 으로 되돌리지 않는다."""
    from colab_core.app.client_search import evaluate

    plan = {'conditions': {'maxMissingRatePercent': 1}}
    row = {'file_id': 'f1', 'file_name': 'rain.npy', 'facts': dict(FACTS),
           'source': {'label': 'fixture', 'locator': 'section 1', 'sha256': 'a' * 64}}
    assert evaluate(plan, {'missing_rate_percent': 0.2}, [row])['status'] == 'supported'
    assert evaluate(plan, {'missing_rate_percent': 20}, [row])['status'] == 'contradicted'
    assert evaluate(plan, {'missing_rate_percent': None}, [row])['status'] == 'unknown'
    assert evaluate(plan, {}, [row])['status'] == 'unknown'
