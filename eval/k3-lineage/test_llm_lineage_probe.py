"""러너의 판정 함수만 여는 offline 시험. **망·모델·DB 0건.**

K4 선례(`eval/k4-search/test_llm_interpreter_probe.py`)와 같은 자리다 — 실측 러너가
내는 수치는 그 자체가 산출물이라 되돌려 세지 못한다. 그래서 **오판 방지**를 여기서 본다:
정답 0건 · 후보 중복 · 순위 없음 · 빈 응답 · 지어낸 고유명사 · 규격 위반 한 장.
"""
import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1] / 'services/ai-service/src'))

import llm_lineage_probe as probe  # noqa: E402

CAND_A = {'datasetId': '01M1SCC27AN4NZD3K978YFDCVD',
          'name': '강수 — HSR 레이더 합성 반사도 (Lv.0)',
          'topic': '강우·강수', 'summary': 'HSR 합성 반사도 원자료',
          'sourceLabel': '기상청', 'processingLevel': 0}
CAND_B = {'datasetId': '01M1SCC8BZZJSCEW4MRPE4W9M8',
          'name': '강수 — RN15 지상 15분 누적 강수 (Lv.0)', 'topic': '강우·강수'}
FILE_META = {'fileName': 'precip_wgs84_crop.npy', 'kind': '본체'}


def _case(**over):
    case = dict(id='K3-LIN-001', child_dataset_id='01M1SCGM0K7FACRYTCWVMDDBY8',
                child_name='강수 — WGS84 변환·연구대상지 crop 표본 (Lv.1)',
                topic='강우·강수', file_meta=dict(FILE_META),
                dataset_name_draft='강수 — WGS84 변환·연구대상지 crop 표본 (Lv.1)',
                subject='강우·강수', candidates=[dict(CAND_A), dict(CAND_B)],
                parents=[dict(parent_dataset_id=CAND_A['datasetId'],
                              parent_name=CAND_A['name'], parent_role='주입력'),
                         dict(parent_dataset_id=CAND_B['datasetId'],
                              parent_name=CAND_B['name'], parent_role='보조입력')])
    case.update(over)
    return case


class TokenTests(unittest.TestCase):
    def test_한_글자_조각과_구분자는_토큰이_아니다(self):
        self.assertEqual(probe.rationale_tokens('HSR 레이더 · 0 m'), ['hsr', '레이더'])

    def test_라틴_어간에_붙은_조사를_갈라_낸다(self):
        # 한국어 조사는 라틴 어간에 그대로 붙는다. 한 토큰으로 두면 원문에 실재하는
        # `npy`·`202305` 가 「지어낸 고유명사」로 잡힌다 — 1회차 실측의 오판 12건이 이것이다.
        self.assertEqual(probe.rationale_tokens('GK2A_NDVI_mean_202305.tif는'),
                         ['gk2a', 'ndvi', 'mean', '202305', 'tif'])
        # 갈라 낸 한 글자 조사(`가`·`와`)는 2글자 미만이라 그대로 떨어진다.
        self.assertEqual(probe.rationale_tokens('npy가 0.5 km와'), ['npy', 'km'])

    def test_조사가_붙은_라틴_어간은_hard_위반이_아니다(self):
        g = probe.grounding('hsr_sample.npy와 같은 계열', CAND_A, _case(
            file_meta={'fileName': 'hsr_sample.npy', 'kind': '본체'}))
        self.assertEqual(g['hard'], [])

    def test_빈_근거는_토큰_0건이다(self):
        self.assertEqual(probe.rationale_tokens(''), [])
        self.assertEqual(probe.rationale_tokens(None), [])


class GroundingTests(unittest.TestCase):
    def test_후보와_파일_메타에_있는_말만_쓰면_위반이_없다(self):
        g = probe.grounding('HSR 합성 반사도 원자료', CAND_A, _case())
        self.assertEqual(g['missing'], [])
        self.assertTrue(g['ok'])

    def test_어미가_붙으면_엄격_판정이_걸린다(self):
        # 「원자료다」는 메타의 「원자료」와 부분문자열로 맞지 않는다. **한국어 어미가
        # 만드는 오판**이고, 지어낸 고유명사와 같은 칸에 세면 수치가 뜻을 잃는다.
        g = probe.grounding('HSR 합성 반사도 원자료다', CAND_A, _case())
        self.assertEqual(g['missing'], ['원자료다'])
        self.assertEqual(g['hard'], [])
        self.assertTrue(g['ok'])
        self.assertFalse(g['strict_ok'])

    def test_지어낸_고유명사는_hard_위반이다(self):
        g = probe.grounding('MODIS 위성에서 온 자료다', CAND_A, _case())
        self.assertIn('modis', g['hard'])
        self.assertFalse(g['ok'])

    def test_한글_산문_토큰은_soft_로_갈라_센다(self):
        # 「만든」은 메타 원문에 없지만 고유명사·수치가 아니다 — intent J3 의 red 대상과 갈린다.
        g = probe.grounding('HSR 로 만든 자료', CAND_A, _case())
        self.assertEqual(g['hard'], [])
        self.assertIn('만든', g['soft'])
        self.assertTrue(g['ok'])          # hard 가 0 이면 J3 red 조건에 걸리지 않는다
        self.assertFalse(g['strict_ok'])  # 엄격 판정은 별도로 남는다

    def test_업로드_파일명에만_있는_말도_실재로_센다(self):
        g = probe.grounding('crop 표본에 쓴 원자료', CAND_A, _case())
        self.assertEqual(g['hard'], [])

    def test_다른_후보에만_있는_말은_실재가_아니다(self):
        g = probe.grounding('RN15 지상 자료', CAND_A, _case())
        self.assertIn('rn15', g['hard'])


class RankTests(unittest.TestCase):
    def test_순위는_1부터_세고_없으면_None_이다(self):
        sugg = [dict(parent_dataset_id='X'), dict(parent_dataset_id='Y')]
        self.assertEqual(probe.rank_of('Y', sugg), 2)
        self.assertIsNone(probe.rank_of('Z', sugg))

    def test_같은_ID_가_두_번_오면_첫_자리만_센다(self):
        sugg = [dict(parent_dataset_id='X'), dict(parent_dataset_id='X')]
        self.assertEqual(probe.rank_of('X', sugg), 1)

    def test_제안_0건이면_엣지는_hit_이_아니다(self):
        hits = probe.edge_hits(_case(), [])
        self.assertEqual(len(hits), 2)
        self.assertTrue(all(h['rank'] is None and not h['hit1'] and not h['hit3'] for h in hits))

    def test_정답_0건인_케이스도_터지지_않는다(self):
        self.assertEqual(probe.edge_hits(_case(parents=[]), []), [])


class RawReadTests(unittest.TestCase):
    def test_JSON_이_아니면_원시_제안_0건이다(self):
        self.assertEqual(probe.read_raw('not json'), [])
        self.assertEqual(probe.read_raw(''), [])
        self.assertEqual(probe.read_raw(json.dumps({'items': []})), [])

    def test_울타리를_친_JSON_도_읽는다(self):
        raw = '```json\n{"suggestions": [{"parentDatasetId": "X"}]}\n```'
        self.assertEqual(probe.read_raw(raw), [{'parentDatasetId': 'X'}])


class FormatTests(unittest.TestCase):
    def test_퍼센트와_enum_밖_확신도를_함께_센다(self):
        v = probe.format_violations({'parentDatasetId': 'X', 'confidence': '80%',
                                     'rationale': '확률 80% 로 맞다', 'suggestedParentRole': '주입력'})
        self.assertIn('confidence_enum', v)
        self.assertIn('percent', v)

    def test_여러_줄_근거와_빈_근거를_가른다(self):
        self.assertIn('rationale_multiline', probe.format_violations(
            {'confidence': '확실', 'rationale': '첫 줄\n둘째 줄'}))
        self.assertIn('rationale_blank', probe.format_violations(
            {'confidence': '확실', 'rationale': '   '}))

    def test_규격대로면_위반_0건이다(self):
        self.assertEqual(probe.format_violations(
            {'parentDatasetId': 'X', 'confidence': '애매', 'rationale': 'HSR 반사도다',
             'suggestedParentRole': '보조입력'}), [])

    def test_역할이_계약_밖이면_센다(self):
        self.assertIn('role_enum', probe.format_violations(
            {'confidence': '모름', 'rationale': 'ㄱ', 'suggestedParentRole': '입력'}))


class OutsideTests(unittest.TestCase):
    def test_후보_밖_ID_를_센다(self):
        raw = [{'parentDatasetId': CAND_A['datasetId']}, {'parentDatasetId': '01ZZZ'}]
        self.assertEqual(probe.outside_ids(raw, _case()), ['01ZZZ'])

    def test_ID_가_없는_장은_후보_밖으로_세지_않는다(self):
        self.assertEqual(probe.outside_ids([{'confidence': '확실'}], _case()), [])


class ControlTests(unittest.TestCase):
    def test_대조군은_정답_부모만_빼고_입력을_건드리지_않는다(self):
        case = _case()
        control = probe.without_true_parents(case)
        self.assertEqual([c['datasetId'] for c in control['candidates']], [])
        self.assertEqual(len(case['candidates']), 2)   # 원본 무변
        self.assertEqual(control['group'], 'control')

    def test_정답_아닌_후보는_남는다(self):
        other = {'datasetId': '01M1SCGM0K7FACRYTCWVMDDBY8', 'name': '다른 자료'}
        control = probe.without_true_parents(_case(candidates=[dict(CAND_A), other]))
        self.assertEqual([c['datasetId'] for c in control['candidates']], [other['datasetId']])


class CalibrationTests(unittest.TestCase):
    def test_확신도_x_정오_교차표(self):
        rows = [dict(suggestions=[dict(parent_dataset_id=CAND_A['datasetId'], confidence='확실'),
                                  dict(parent_dataset_id='01ZZZ', confidence='애매')],
                     true_parent_ids=[CAND_A['datasetId']])]
        table = probe.calibration(rows)
        self.assertEqual(table['확실'], {'correct': 1, 'wrong': 0})
        self.assertEqual(table['애매'], {'correct': 0, 'wrong': 1})
        self.assertEqual(table['모름'], {'correct': 0, 'wrong': 0})

    def test_제안_0건이면_표가_비어도_터지지_않는다(self):
        self.assertEqual(probe.calibration([]),
                         {'확실': {'correct': 0, 'wrong': 0}, '애매': {'correct': 0, 'wrong': 0},
                          '모름': {'correct': 0, 'wrong': 0}})


class DeterminismTests(unittest.TestCase):
    def test_두_회차가_같으면_갈린_자식_0건이다(self):
        one = [dict(child_dataset_id='C1', suggestions=[dict(parent_dataset_id='X', confidence='확실',
                                                             suggested_parent_role='주입력')])]
        self.assertEqual(probe.determinism([one, one]), {'C1': 1})

    def test_확신도만_갈려도_갈린_것으로_센다(self):
        one = [dict(child_dataset_id='C1', suggestions=[dict(parent_dataset_id='X', confidence='확실',
                                                             suggested_parent_role='주입력')])]
        two = [dict(child_dataset_id='C1', suggestions=[dict(parent_dataset_id='X', confidence='애매',
                                                             suggested_parent_role='주입력')])]
        self.assertEqual(probe.determinism([one, two]), {'C1': 2})


class SuggesterTests(unittest.TestCase):
    """제품 생산자를 **그대로** 세우고 전송만 감싼다 — 판정이 아니라 배선 확인이다."""

    def test_제품_파서가_후보_밖_ID_를_버리고_전송이_지연을_기록한다(self):
        # ⭑ ⟨2026-09-24 · K3 `WU-S3`⟩ 제품 파서가 읽는 모양이 **인용**으로 바뀌었다 —
        #   확신도·근거 문장은 모델에게 묻지 않고, 인용이 0건인 후보는 제안이 아니다.
        raw = json.dumps({'suggestions': [
            {'parentDatasetId': CAND_A['datasetId'], 'suggestedParentRole': '주입력',
             'evidence': [{'field': 'fileName', 'uploadValue': 'precip_wgs84_crop.npy',
                           'candidateValue': 'HSR'}]},
            {'parentDatasetId': '01ZZZZZZZZZZZZZZZZZZZZZZZZ', 'suggestedParentRole': '주입력',
             'evidence': [{'field': 'crs', 'uploadValue': 'EPSG:4326',
                           'candidateValue': 'EPSG:4326'}]}]})
        transport = probe.FakeTransport(raw)
        row = probe.run_case(_case(), probe.build_suggester('m', transport, 8.0), transport)
        self.assertEqual([s['parent_dataset_id'] for s in row['suggestions']], [CAND_A['datasetId']])
        self.assertEqual(row['raw_suggestions'], 2)
        self.assertEqual(row['dropped'], 1)
        self.assertEqual(row['outside_candidate_ids'], ['01ZZZZZZZZZZZZZZZZZZZZZZZZ'])
        self.assertIsNotNone(row['seconds'])

    def test_빈_배열이면_빈_제안과_사유가_남는다(self):
        transport = probe.FakeTransport(json.dumps({'suggestions': []}))
        row = probe.run_case(_case(), probe.build_suggester('m', transport, 8.0), transport)
        self.assertEqual(row['suggestions'], [])
        self.assertTrue(row['empty_declaration'])

    def test_전송이_터지면_지연과_사유가_남고_러너가_계속_돈다(self):
        transport = probe.FakeTransport(TimeoutError('timed out'))
        row = probe.run_case(_case(), probe.build_suggester('m', transport, 8.0), transport)
        self.assertEqual(row['suggestions'], [])
        self.assertEqual(row['error'], 'TimeoutError')
        self.assertIsNotNone(row['seconds'])


if __name__ == '__main__':
    unittest.main()
