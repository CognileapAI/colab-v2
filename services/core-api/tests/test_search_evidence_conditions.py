from colab_core.app.search_evidence_conditions import assess, candidates, parse, supported_facts


def record(file='f1', dataset='d1', **facts):
    return dict(file_id=file, dataset_id=dataset, file_name=file+'.npy', file_kind='본체',
                facts=facts, source={'label': '처리 설명서', 'locator': '입력 절'})


def test_conditions_must_be_supported_by_same_file():
    rows = [record(roles=['prediction']), record('f2', model='U-Net')]
    selected, excluded = candidates(parse('U-Net 강우 예측 자료'), rows, {'d1': {'f1','f2'}})
    assert not selected and not excluded


def test_complete_explicit_role_mismatch_can_exclude_but_incomplete_cannot():
    row = record(roles=['index'], model='SPI')
    criteria = parse('U-Net 가뭄 예측 자료')
    assert candidates(criteria, [row], {'d1': {'f1'}}) == ([], ['d1'])
    assert candidates(criteria, [row], {'d1': {'f1','unreviewed'}}) == ([], [])


def test_quality_never_becomes_verified_from_a_reviewed_file():
    checks = assess(parse('결측률 0% 식생'), record(interpolated=True)['facts'])
    assert checks['품질'][0] == 'unknown'


def test_native_resolution_mismatch_is_related_not_silently_removed():
    rows = [record(directObservation=False, nativeResolutionM=2000, cadence='monthly')]
    criteria = parse('100m로 직접 관측한 월평균 NDVI')
    assert assess(criteria, rows[0]['facts'])['직접 관측'][0] == 'contradicted'
    assert candidates(criteria, rows, {'d1': {'f1'}})[1] == []
    # 카드 근거는 확인된 조건만 싣는다 — 불일치·미확인 조건은 근거 항목이 되지 않는다
    # (intent `2026-09-25-search-rationale-separation.md` Q6).
    facts = supported_facts(criteria, rows)
    assert facts and all('\n' not in f for f in facts)
    # 출처(설명서 이름·절)는 카드 항목에 싣지 않는다 — 상세 「검색 근거」가 보인다
    # (intent `2026-09-26-rationale-facts-wording.md` ①).
    assert not [f for f in facts if '처리 설명서' in f or '입력 절' in f or '출처' in f]
    assert not [f for f in facts if '불일치' in f or '미확인' in f or '직접 관측' in f]


def test_supported_fact_is_the_reason_sentence_without_source():
    """dev 캡처 질의의 파일 근거 항목 — 「{파일명}에서 {조건} 조건이 맞았어요」에서 끝난다
    (intent `2026-09-26-rationale-facts-wording.md` ①)."""
    criteria = parse('강우 예측 pred_sample.npy 파일의 바로 앞 입력 데이터셋')
    facts = supported_facts(criteria, [record('pred_sample', roles=['prediction'])])
    assert facts == ['pred_sample.npy에서 파일 역할(예측 결과) 조건이 맞았어요']


def test_unknown_subject_cannot_expand_by_date_alone():
    rows = [record(period={'start':'2023-05-01','end':'2023-05-31'})]
    assert candidates(parse('2023년 5월 해수 온도'), rows, {'d1': {'f1'}}) == ([], [])


def test_alternative_roles_and_explicit_exclusion_are_distinguished():
    assert set(parse('강우 예측 결과와 검증에 쓴 자료')['roles']) == {'prediction','validation'}
    assert parse('강우 예측이면서 검증인 자료')['unsupported']
    assert parse('SPEI 말고 SPI 가뭄')['variable'] == 'SPI'


def test_source_text_cannot_insert_line_breaks_into_rationale():
    r=record(cadence='monthly')
    r['source']['label']='문서\n이름'; r['file_name']='파일\r이름'
    facts = supported_facts(parse('월평균 NDVI'), [r])
    assert facts and all('\n' not in f and '\r' not in f for f in facts)


def test_unknown_region_is_not_declared_geographically_disjoint():
    assert assess(parse('제주 식생'), {'region':'한반도'})['지역'][0] == 'unknown'


def test_index_exception_does_not_hide_another_negation():
    assert parse('SPEI 말고 SPI, 예측 제외')['unsupported']


def test_multiple_date_bounds_are_not_reduced_to_first_month():
    criteria=parse('2020년 1월부터 2021년 12월까지 강우')
    result=assess(criteria,{'period':{'start':'2020-01-01','end':'2020-01-31'}})
    assert result['기간'][0]!='supported'


def test_abbreviated_month_and_day_ranges_are_not_first_date_claims():
    for query in ('2020년 1월부터 12월까지 강우', '2020년 1월 1일부터 31일까지 강우', '2020년 1월~12월 강우'):
        assert parse(query)['period'] is None


# ── 지역 포함 관계 한 단계 (intent `2026-09-26-region-containment-expansion.md`) ──────────

def test_peninsula_region_is_supported_by_direct_children_with_the_parent_named():
    criteria = parse('한반도 강우 자료')
    assert assess(criteria, {'region': '남한'})['지역'] == ('supported', '남한 — 한반도 안의 지역')
    assert assess(criteria, {'region': '대한민국'})['지역'] == ('supported', '대한민국 — 한반도 안의 지역')
    assert assess(criteria, {'region': '충청권'})['지역'] == ('supported', '충청권 — 한반도 안의 지역')
    assert assess(criteria, {'region': '한반도'})['지역'] == ('supported', '한반도')
    assert assess(criteria, {'region': 'Korea'})['지역'] == ('supported', 'Korea')


def test_peninsula_region_does_not_widen_by_substring():
    criteria = parse('한반도 가뭄 자료')
    assert assess(criteria, {'region': '대한민국시군구'})['지역'][0] == 'unknown'
    assert assess(criteria, {'region': '경기남부충청'})['지역'][0] == 'unknown'


def test_south_korea_query_never_reaches_the_peninsula():
    """상향 금지 — 「남한」 질의는 표기 일치로만 맞춘다. 한반도는 지리적 배타도 아니므로 unknown 이다."""
    criteria = parse('남한 식생 자료')
    assert criteria['region'] == '남한'
    assert assess(criteria, {'region': '한반도'})['지역'][0] == 'unknown'
    assert assess(criteria, {'region': 'Korea'})['지역'][0] == 'unknown'
    assert assess(criteria, {'region': '남한'})['지역'] == ('supported', '남한')
    # 강·산 이름은 지역 조건이 아니다.
    assert 'region' not in parse('남한강 수질 강우 자료')
    assert 'region' not in parse('남한산성 식생 자료')


def test_peninsula_candidates_and_card_fact_name_the_containment():
    rows = [record('f1', 'd1', region='남한'), record('f2', 'd2', region='대한민국시군구')]
    criteria = parse('한반도 강우 자료')
    included, excluded = candidates(criteria, rows, {'d1': {'f1'}, 'd2': {'f2'}})
    assert included == ['d1'] and excluded == []
    assert supported_facts(criteria, [rows[0]]) == ['f1.npy에서 지역(남한 — 한반도 안의 지역) 조건이 맞았어요']
    # 표기가 같아 맞은 지역은 세부를 붙이지 않는다(종전 문장 그대로).
    assert supported_facts(criteria, [record('f3', region='한반도')]) == ['f3.npy에서 지역 조건이 맞았어요']
