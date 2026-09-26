"""「1시간 이하」 — 주기(산출 간격) 상한 술어. 두 경로가 같은 커널 도우미로 판정한다.

intent `dev-package/intent/2026-09-26-cadence-range-predicate.md`.
  · 정의(Ted 2026-09-26 「측정 간격같은데 1시간이하는 산출간격(주기)」) — 「N 이하」 = 산출 간격(cadence) ≤ N.
  · 순서의 정본은 `contracts/search/semantics.json` `cadenceSeconds` 한 곳이다(생성물 두 벌).
  · 모르는·표에 없는 주기는 범위 술어를 맞추지 않는다(unknown 은 supported 가 아니다).
  · 주기는 정본 선언값의 전재이며 파일 시간축 실측이 아니다 — 범위 비교는 선언값 비교다.
  · 기존 등호 술어 `cadence` 의 뜻은 바꾸지 않는다.
"""
import datetime as dt
import pathlib

import pytest
import yaml

from colab_core.app import search_evidence_conditions as sec
from colab_core.app.client_search import evaluate, plan_query
from colab_core.kernel import cadence_scope as cs
from colab_core.kernel.search_semantics import SEMANTICS

pytestmark = pytest.mark.search_golden
CLOCK = dt.datetime(2026, 9, 13, 3, tzinfo=dt.timezone.utc)
REPO = pathlib.Path(__file__).resolve().parents[3]
HOUR = 3600

WITHIN_HOUR = ('5min', '10min', '15min', 'hourly')
BEYOND_HOUR = ('daily', 'weekly', 'monthly', 'yearly')


# ── 커널 도우미 (순수) ─────────────────────────────────────────────────────────

def test_cadence_order_covers_exactly_the_contract_enum():
    """순서표 키 = 계약 `SearchEvidenceFacts.cadence` enum. 값 추가가 순서표를 빠뜨리면 여기서 red."""
    seam = yaml.safe_load((REPO / 'contracts/seams/fe-core.yaml').read_text(encoding='utf-8'))
    enum = seam['components']['schemas']['SearchEvidenceFacts']['properties']['cadence']['enum']
    assert set(SEMANTICS['cadenceSeconds']) == set(enum)
    ordered = sorted(SEMANTICS['cadenceSeconds'], key=SEMANTICS['cadenceSeconds'].get)
    assert ordered == ['5min', '10min', '15min', 'hourly', 'daily', 'weekly', 'monthly', 'yearly']


@pytest.mark.parametrize('value', WITHIN_HOUR)
def test_sub_hour_cadences_pass_one_hour(value):
    assert cs.cadence_within(value, HOUR) is True


@pytest.mark.parametrize('value', BEYOND_HOUR)
def test_coarser_cadences_fail_one_hour(value):
    assert cs.cadence_within(value, HOUR) is False


@pytest.mark.parametrize('value', [None, '', '30min', 'hourly ', 3600, True])
def test_unknown_or_unmapped_cadence_is_unknown_never_supported(value):
    assert cs.cadence_within(value, HOUR) is None


def test_boundary_is_inclusive_and_values_list_is_ordered():
    assert cs.cadence_within('15min', 900) is True
    assert cs.cadence_within('15min', 899) is False
    assert cs.cadences_within(HOUR) == ['5min', '10min', '15min', 'hourly']
    assert cs.cadences_within(1800) == ['5min', '10min', '15min']
    assert cs.cadences_within(60) == []


@pytest.mark.parametrize('bad', [0, -1, float('nan'), float('inf'), True, '3600', None])
def test_limit_must_be_a_positive_finite_number(bad):
    with pytest.raises(ValueError):
        cs.cadences_within(bad)


@pytest.mark.parametrize('text,seconds', [
    ('시간해상도 1시간 이하', HOUR), ('시간해상도가 한 시간 이하인 강수', HOUR), ('한시간 이하', HOUR),
    ('60분 이하', HOUR), ('30분 이내 자료', 1800), ('2 시간 이내', 2 * HOUR), ('1.5시간 이하', 5400),
])
def test_range_phrases_parse_to_seconds(text, seconds):
    assert cs.parse_max_cadence_seconds(text) == seconds


@pytest.mark.parametrize('text', ['1시간', '1시간 간격', '시간별 강수', '1시간 이상', '1시간 미만',
                                  '5 km 이하', '0분 이하', '15분 누적강수', '대한 시간표'])
def test_non_range_phrases_do_not_parse(text):
    assert cs.parse_max_cadence_seconds(text) is None


# ── 경로 1 (plan_query, evaluate) ─────────────────────────────────────────────

@pytest.mark.parametrize('query', ['시간해상도 1시간 이하 강수 자료', '한 시간 이하 강수 자료',
                                   '60분 이하 강수 자료'])
def test_plan_query_turns_range_phrase_into_the_predicate(query):
    c = plan_query(query, now=CLOCK)['conditions']
    assert c['maxCadenceSeconds'] == HOUR
    assert 'cadence' not in c


def test_plan_query_thirty_minutes_within():
    assert plan_query('30분 이내 강수 자료', now=CLOCK)['conditions']['maxCadenceSeconds'] == 1800


def test_plan_query_plain_hour_is_not_a_range_and_existing_equality_is_unchanged():
    """「1시간」만으로는 범위가 아니다. 기존 등호 주기 조건(일별·월별)의 뜻도 그대로다."""
    assert 'maxCadenceSeconds' not in plan_query('1시간 간격 강수 자료', now=CLOCK)['conditions']
    assert plan_query('월별 강수 자료', now=CLOCK)['conditions'].get('cadence') == 'monthly'
    assert 'maxCadenceSeconds' not in plan_query('월별 강수 자료', now=CLOCK)['conditions']
    # 공간 해상도 「이하」와 섞이지 않는다.
    c = plan_query('시간해상도 1시간 이하, 공간해상도 5 km 이하 한반도 강수자료', now=CLOCK)['conditions']
    assert c['maxCadenceSeconds'] == HOUR and c['maxResolutionM'] == 5000


def test_plan_query_range_alone_does_not_change_routing():
    """범위 술어 하나만으로 경로 1 인식(recognized)을 세우지 않는다 — 제품 갈림은 그대로다."""
    assert plan_query('시간해상도 1시간 이하 강수 자료', now=CLOCK)['recognized'] is False


def _row(**facts):
    return {'file_id': 'f1', 'file_name': 'rain.nc', 'facts': facts,
            'source': {'label': 'fixture', 'locator': 's1', 'sha256': 'a' * 64}}


def test_evaluate_supported_contradicted_unknown():
    plan = plan_query('시간해상도 1시간 이하 강수 자료', now=CLOCK)
    for value in WITHIN_HOUR:
        assert evaluate(plan, {}, [_row(cadence=value)])['checks']['maxCadenceSeconds'] == 'supported'
    assert evaluate(plan, {}, [_row(cadence='daily')])['checks']['maxCadenceSeconds'] == 'contradicted'
    assert evaluate(plan, {}, [_row()])['checks']['maxCadenceSeconds'] == 'unknown'
    assert evaluate(plan, {}, [_row(cadence='30min')])['checks']['maxCadenceSeconds'] == 'unknown'


def test_equality_cadence_predicate_keeps_its_meaning():
    plan = {'intent': 'discover', 'conditions': {'cadence': 'hourly'}}
    assert evaluate(plan, {}, [_row(cadence='hourly')])['status'] == 'supported'
    assert evaluate(plan, {}, [_row(cadence='15min')])['status'] == 'contradicted'


# ── 경로 2 (search_evidence_conditions.parse, assess) ─────────────────────────

def test_path2_parses_the_same_range_and_judges_with_the_same_helper():
    criteria = sec.parse('시간해상도 1시간 이하 강수 자료')
    assert criteria['maxCadenceSeconds'] == HOUR and 'cadence' not in criteria
    for value in WITHIN_HOUR:
        assert sec.assess(criteria, {'cadence': value})['주기 범위'][0] == 'supported'
    assert sec.assess(criteria, {'cadence': 'daily'})['주기 범위'][0] == 'contradicted'
    assert sec.assess(criteria, {})['주기 범위'] == ('unknown', '근거 없음')
    assert sec.assess(criteria, {'cadence': '30min'})['주기 범위'][0] == 'unknown'


@pytest.mark.parametrize('query,seconds', [('한 시간 이하 강우 자료', HOUR), ('30분 이내 강우 자료', 1800),
                                           ('60분 이하 강우 자료', HOUR)])
def test_path2_phrases_match_path1(query, seconds):
    assert sec.parse(query)['maxCadenceSeconds'] == seconds
    assert plan_query(query, now=CLOCK)['conditions']['maxCadenceSeconds'] == seconds


def test_path2_card_says_declared_value_not_measured_axis():
    """카드 근거 — 범위 비교는 등록 설명의 선언값 비교이며 파일 시간축 실측이 아니다(Ted 2026-09-26)."""
    rows = [dict(file_id='f1', dataset_id='d1', file_name='rn15.nc', file_kind='본체',
                 facts={'cadence': '15min'}, source={'label': 'x', 'locator': 'y'})]
    facts = sec.supported_facts(sec.parse('1시간 이하 강우 자료'), rows)
    assert facts == ['rn15.nc에서 주기 범위(15분 — 1시간 이하 · 등록 설명의 선언값, 파일 시간축 실측 아님) 조건이 맞았어요']


def test_path2_fifteen_minutes_is_a_cadence_mention_but_accumulation_is_not():
    assert sec.parse('한반도 15분 주기 강수 자료')['cadence'] == '15min'
    assert 'cadence' not in sec.parse('15분 누적강수 강우 자료')
    # 기존 5분·10분·시간별 값은 그대로다.
    assert sec.parse('5분 레이더 강우')['cadence'] == '5min'
    assert sec.parse('10분 간격 강우')['cadence'] == '10min'
    assert sec.parse('시간별 강우')['cadence'] == 'hourly'


def test_path2_range_phrase_is_not_read_as_equality():
    """「10분 이내」는 10분 등호가 아니라 범위다 — 5분 자료도 맞는다."""
    criteria = sec.parse('10분 이내 강우 자료')
    assert criteria['maxCadenceSeconds'] == 600 and 'cadence' not in criteria
    assert sec.assess(criteria, {'cadence': '5min'})['주기 범위'][0] == 'supported'
