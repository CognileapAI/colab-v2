from colab_core.app.search_evidence_conditions import assess, candidates, explain, parse


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
    line = explain('기존 근거.', criteria, rows)
    assert '불일치' in line and '처리 설명서' in line and '\n' not in line


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
    assert '\n' not in explain('기존 근거.', parse('월평균 NDVI'), [r])


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
